#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import contextlib
import datetime
from enum import Enum, auto
from io import StringIO
from typing import Callable, Dict, List, Optional, Any
from contextlib import redirect_stdout

from modules.system_utils import check_account
from modules.json_utils import load_json, validate_required_fields
from modules.package_utils import check_package, ensure_dependencies_installed
from modules.display_utils import (
    format_status_summary,
    select_from_list,
    confirm,
    print_dict_table,
    pick_constants_interactively,
    wrap_in_box,
    format_config_help,
)
from modules.state_machine_utils import (
    load_constants_from_module,
    parse_args_early,
    resolve_arg,
    check_when,
)


REQUIRED_CONSTANTS = [
    "CONFIG_PATH",
    "VALIDATION_CONFIG",
    "SECONDARY_VALIDATION",
    "REQUIRED_USER",
    "ACTIONS",
    "STATUS_FN_CONFIG",
    "DEPENDENCIES",
    "ACTIVE_LABEL",
    "INACTIVE_LABEL",
    "PLAN_COLUMN_ORDER",
    "OPTIONAL_PLAN_COLUMNS",
    "PIPELINE_STATES",
    "CONFIG_DOC",
    "TOOL_TYPE",
]


AVAILABLE_CONSTANTS = {
    "WiFi utility": ("constants.WiFiConstants", 0),
    "Network utility": ("constants.NetworkConstants", 0),
}


class State(Enum):
    INITIAL = auto()
    DEP_CHECK = auto()
    DEP_INSTALL = auto()
    CONFIG_LOADING = auto()
    JSON_REQUIRED_KEYS_CHECK = auto()
    SECONDARY_VALIDATION = auto()
    DISPLAY_VERIFICATION = auto()
    PACKAGE_STATUS = auto()
    BUILD_ACTIONS = auto()
    MENU_SELECTION = auto()
    PIPELINE_PRE = auto()
    PREPARE_PLAN = auto()
    CONFIRM = auto()
    EXECUTE = auto()
    FINALIZE = auto()


def run_pipeline_steps(meta: Dict[str, Any],
                       pipeline: List[Dict[str, Any]],
                       *,
                       phase: str,
                       label: str,
                       success_key: str,
                       ctx: Dict[str, Any]) -> None:
    """Run pipeline steps for a given phase, storing outputs in ctx."""
    ctx.setdefault("errors", [])
    phase = (phase or "").strip().lower()
    for step in pipeline:
        fn = step.get("fn")
        if not callable(fn):
            raise TypeError("Pipeline step missing callable 'fn'.")
        step_phase = (step.get("phase") or "exec").strip().lower()
        if step_phase != phase:
            continue
        if not check_when(step.get("when"), None, meta, ctx):
            continue
        args = [resolve_arg(a, None, meta, ctx) for a in step.get("args", [])]
        try:
            result = fn(*args)
        except Exception as e:
            ctx["errors"].append({"step": getattr(fn, "__name__", "unknown"), "error": str(e)})
            print(f"[ERROR] {getattr(fn, '__name__', 'unknown')} failed → {e!r}")
            continue
        rkey = step.get("result")
        if rkey is not None:
            ctx[rkey] = result if result is not None else True
    errors = ctx.get("errors") or []
    default_success = (len(errors) == 0)
    override_success = None
    if success_key:
        if success_key in ctx:
            override_success = bool(ctx.get(success_key))
    success = override_success if override_success is not None else default_success
    if phase == "pre":
        print(f"{label} (pre): {'Success' if success else 'Failed'}")
        return
    print(f"{label}: {'Success' if success else 'Failed'}")


class StateMachine:
    def __init__(self, constants, *, auto_yes: bool = False, cli_action: Optional[str] = None,
                 status_only: bool = False, plan_only: bool = False,
                 config_path: Optional[str] = None) -> None:
        """Initialize machine state and fields."""
        self.state: State = State.INITIAL
        self.finalize_msg: Optional[str] = None
        self.auto_yes = auto_yes
        self.cli_action = cli_action
        self.status_only = status_only
        self.plan_only = plan_only
        self.config_path = config_path
        self.verification_outcomes: Dict[str, bool] = {}
        self.verification_notes: List[str] = []
        self.verification_ok: bool = True
        self.cfg: Dict[str, Any] = {}
        self.active: Optional[bool] = None
        self.current_action_key: Optional[str] = None
        self.actions: Dict[str, Dict[str, Any]] = {}
        self.c = constants
        self._pending_pipeline_spec: Optional[Dict[str, Any]] = None
        self._deps_install_list: List[str] = []
        self.runtime_ctx: Dict[str, Any] = {}


    def setup(self, required_user: str) -> None:
        """Initialize logging and verify user; advance to DEP_CHECK or FINALIZE."""
        for k, v in vars(self.c).items():
            if v is None:
                self.finalize_msg = f"Constant {k} is None."
                self.state = State.FINALIZE
                return
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if not check_account(expected_user=required_user):
            self.finalize_msg = "User account verification failed."
            self.state = State.FINALIZE
            return
        self.state = State.DEP_CHECK


    def dep_check(self, deps: List[str]) -> None:
        """Check dependencies and collect missing ones."""
        self._deps_install_list = []
        out = []
        for dep in deps:
            if check_package(dep):
                out.append(f"[OK]    {dep} is installed.")
            else:
                out.append(f"[MISS]  {dep} is missing.")
                self._deps_install_list.append(dep)
        if self._deps_install_list or out:
            print("\n  ==> Running Dependency Check")
            print(wrap_in_box(out, title="Dependency Check", indent=2, pad=1))
        self.state = State.DEP_INSTALL if self._deps_install_list else State.CONFIG_LOADING


    def dep_install(self) -> None:
        """Install missing dependencies in batch, verify each; fail fast on error."""
        if not self._deps_install_list:
            self.state = State.CONFIG_LOADING
            return
        out = [f"[INSTALL] Attempting batch install: {', '.join(self._deps_install_list)}"]
        ok = ensure_dependencies_installed(self._deps_install_list)
        if not ok:
            out.append("[WARN] Batch installer returned False; verifying individually.")
        for dep in list(self._deps_install_list):
            if check_package(dep):
                out.append(f"[DONE]   Installed: {dep}")
            else:
                out.append(f"[FAIL]   Still missing after install: {dep}")
                self.finalize_msg = f"{dep} still missing after install."
                out.append(self.finalize_msg)
                print("\n  ==> Running Dependency Check")
                print(wrap_in_box(out, title="Dependency Install", indent=2, pad=1))
                self.state = State.FINALIZE
                return
        self._deps_install_list = []
        print("\n  ==> Running Dependency Check")
        print(wrap_in_box(out, title="Dependency Install", indent=2, pad=1))
        self.state = State.CONFIG_LOADING


    def load_config(self, config_path: str) -> None:
        """Load single JSON config object and seed single active job."""
        resolved = self.config_path or config_path
        loaded = load_json(resolved)
        if not isinstance(loaded, dict):
            self.finalize_msg = f"Loaded config is not a JSON object: {resolved}"
            print(self.finalize_msg)
            self.state = State.FINALIZE
            return
        self.cfg = loaded
        ctx = {"User": self.c.REQUIRED_USER, "Config file": resolved}
        out_lines = [f"Using single config file: {resolved}"]
        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            print_dict_table([ctx], field_names=list(ctx.keys()), label="Run Context")
        out_lines.extend(buf.getvalue().splitlines())
        print("\n  ==> Loading Config")
        print(wrap_in_box(out_lines, indent=2, pad=1))
        self.verification_outcomes = {}
        self.verification_notes = []
        self.verification_ok = True
        self.state = State.JSON_REQUIRED_KEYS_CHECK


    def validate_json_required_keys(self, validation_config: Dict, object_type: type = dict) -> None:
        """Validate required fields against the single config object."""
        required_fields = (validation_config or {}).get("required_job_fields", {})
        if not required_fields:
            self.state = State.SECONDARY_VALIDATION
            return
        results = validate_required_fields({"cfg": self.cfg}, required_fields)
        primary_ok = True
        for field, expected in required_fields.items():
            types = expected if isinstance(expected, tuple) else (expected,)
            expected_str = " or ".join(t.__name__ for t in types)
            ok = bool(results.get(field, False))
            self.verification_outcomes[f"Config: {field} ({expected_str})"] = ok
            primary_ok = primary_ok and ok
        self.state = State.DISPLAY_VERIFICATION if not primary_ok else State.SECONDARY_VALIDATION


    def validate_secondary_keys(self, secondary_validation: Dict) -> None:
        """Validate nested required fields for config sections."""
        if not isinstance(secondary_validation, dict) or not secondary_validation:
            self.verification_notes.append("[INFO] No secondary validation rules defined; skipping.")
            self.state = State.DISPLAY_VERIFICATION
            return
        all_ok = True
        for section_key, spec in secondary_validation.items():
            if section_key == "example_config":
                continue
            if not isinstance(spec, dict):
                self.verification_outcomes[f"Secondary: {section_key} (invalid spec)"] = False
                all_ok = False
                continue
            required_fields = spec.get("required_job_fields") or {}
            allow_empty = bool(spec.get("allow_empty", False))
            if not required_fields:
                self.verification_outcomes[f"Secondary: {section_key} (no required_job_fields)"] = False
                all_ok = False
                continue
            section_val = self.cfg.get(section_key, None)
            if section_val is None:
                self.verification_outcomes[f"Secondary: {section_key} (missing section)"] = False
                all_ok = False
                continue
            if isinstance(section_val, dict):
                for field, expected in required_fields.items():
                    types = expected if isinstance(expected, tuple) else (expected,)
                    expected_str = " or ".join(t.__name__ for t in types)
                    if field not in section_val:
                        self.verification_outcomes[f"Secondary: {section_key}.{field} ({expected_str})"] = False
                        all_ok = False
                        continue
                    ok = isinstance(section_val.get(field), types)
                    self.verification_outcomes[f"Secondary: {section_key}.{field} ({expected_str})"] = ok
                    all_ok = all_ok and ok
                continue
            if isinstance(section_val, list):
                if allow_empty and len(section_val) == 0:
                    self.verification_outcomes[f"Secondary: {section_key} (empty allowed)"] = True
                    continue
                if len(section_val) == 0 and not allow_empty:
                    self.verification_outcomes[f"Secondary: {section_key} (empty not allowed)"] = False
                    all_ok = False
                    continue
                for idx, item in enumerate(section_val):
                    if not isinstance(item, dict):
                        self.verification_outcomes[f"Secondary: {section_key}[{idx}] (not a dict)"] = False
                        all_ok = False
                        continue
                    for field, expected in required_fields.items():
                        types = expected if isinstance(expected, tuple) else (expected,)
                        expected_str = " or ".join(t.__name__ for t in types)
                        if field not in item:
                            self.verification_outcomes[f"Secondary: {section_key}[{idx}].{field} ({expected_str})"] = False
                            all_ok = False
                            continue
                        ok = isinstance(item.get(field), types)
                        self.verification_outcomes[f"Secondary: {section_key}[{idx}].{field} ({expected_str})"] = ok
                        all_ok = all_ok and ok
                continue
            self.verification_outcomes[f"Secondary: {section_key} (invalid type {type(section_val).__name__})"] = False
            all_ok = False
        if not all_ok:
            self.verification_notes.append("[WARN] Secondary validation failed for one or more nested fields.")
        self.state = State.DISPLAY_VERIFICATION



    def display_verification_outcome(self, config_doc: Optional[str] = None) -> None:
        """Display combined verification results; exit on failure or continue on success."""
        if self.verification_outcomes:
            self.verification_ok = all(self.verification_outcomes.values())
        else:
            self.verification_ok = False
            self.verification_notes.append("[WARN] No verification outcomes were recorded.")
        summary = format_status_summary(self.verification_outcomes, label="Verification", labels={True: "Correct", False: "Incorrect"})
        out_lines: List[str] = summary.splitlines() if summary else []
        out_lines.extend(self.verification_notes)
        if not self.verification_ok:
            out_lines.append("")
            self.finalize_msg = "Verification failed: config does not match the expected structure."
            out_lines.append(self.finalize_msg)
            if config_doc:
                out_lines.append("")
                out_lines.extend(format_config_help(config_doc))
            else:
                out_lines.append("[WARN] No CONFIG_DOC provided; cannot show example/description.")
            print("\n  ==> Displaying Verification Outcome")
            print(wrap_in_box(out_lines, indent=2, pad=1))
            self.state = State.FINALIZE
            return
        print("\n  ==> Displaying Verification Outcome")
        print(wrap_in_box(out_lines, indent=2, pad=1))
        self.state = State.PACKAGE_STATUS


    def build_status_map(self, summary_label: str, installed_label: str, uninstalled_label: str, status_fn_config: Dict[str, Any]) -> None:
        """Compute status and print summary; advance accordingly."""
        fn = status_fn_config.get("fn")
        if not callable(fn):
            self.finalize_msg = "STATUS_FN_CONFIG.fn is missing or not callable."
            self.state = State.FINALIZE
            return
        arg_specs = status_fn_config.get("args", [])
        ctx = {}
        args = [resolve_arg(a, None, self.cfg, ctx) for a in arg_specs]
        rows = fn(*args) or []
        id_field = status_fn_config.get("id_field", "device")
        active_rule = status_fn_config.get("active_rule", {})
        rule_field = (active_rule or {}).get("field")
        rule_equals = (active_rule or {}).get("equals")
        status_dict: Dict[str, bool] = {}
        for r in rows:
            if not isinstance(r, dict):
                continue
            item_id = r.get(id_field)
            if not item_id:
                continue
            if rule_field is None:
                active = bool(r.get("active", False))
            else:
                active = (r.get(rule_field) == rule_equals)
            status_dict[str(item_id)] = bool(active)
        self.active = any(status_dict.values())
        summary = format_status_summary(
            status_dict,
            label=summary_label,
            count_keys=[installed_label, uninstalled_label],
            labels={True: installed_label, False: uninstalled_label},
        )
        out_lines = summary.splitlines() if summary else []
        if self.status_only:
            self.finalize_msg = "Status-only mode: no changes were made."
            out_lines.append(self.finalize_msg)
            print(f"\n  ==> Computing {summary_label} Status")
            print(wrap_in_box(out_lines, indent=2, pad=1))
            self.state = State.FINALIZE
            return
        print(f"\n  ==> Computing {summary_label} Status")
        print(wrap_in_box(out_lines, indent=2, pad=1))
        self.state = State.BUILD_ACTIONS


    def build_actions(self, base_actions: Dict[str, Dict[str, Any]]) -> None:
        """Build the main menu from ACTIONS, validating execute_state keys."""
        actions = dict(base_actions)
        cancel_spec = actions.pop("Cancel", None)
        for title, spec in list(actions.items()):
            exec_key = spec.get("execute_state")
            if exec_key in (None, "FINALIZE"):
                continue
            if exec_key not in self.c.PIPELINE_STATES:
                print(f"[WARN] Action '{title}' has unknown execute_state '{exec_key}'; removing from menu.")
                actions.pop(title, None)
        if cancel_spec is not None:
            actions["Cancel"] = cancel_spec
        self.actions = actions
        self.state = State.MENU_SELECTION


    def select_action(self) -> None:
        """Prompt for an action, or use CLI overrides; set the next state."""
        menu_title = self.actions.get("_meta", {}).get("title", "Select an option")
        options = [k for k in self.actions.keys() if k != "_meta"]
        if self.cli_action:
            if self.cli_action not in options:
                print(f"[ERROR] Invalid --action '{self.cli_action}'. Valid options: {options}")
                self.finalize_msg = "Invalid CLI action."
                self.state = State.FINALIZE
                return
            choice = self.cli_action
        else:
            choice = None
            while choice not in options:
                choice = select_from_list(menu_title, options)
                if choice not in options:
                    print("Invalid selection. Please choose a valid option.")
        self.current_action_key = choice
        spec = self.actions[choice]
        if spec.get("execute_state") == "FINALIZE":
            self.state = State.FINALIZE
            return
        exec_key = spec.get("execute_state")
        pipe_spec = self.c.PIPELINE_STATES.get(exec_key) if exec_key else None
        if not pipe_spec or "pipeline" not in pipe_spec:
            self.finalize_msg = f"Unknown/invalid execute_state '{exec_key}'."
            self.state = State.FINALIZE
            return
        pipeline = pipe_spec.get("pipeline")
        if not isinstance(pipeline, list):
            self.finalize_msg = f"Pipeline for '{exec_key}' must be a list of steps (Option B)."
            self.state = State.FINALIZE
            return
        self._pending_pipeline_spec = pipe_spec
        self.runtime_ctx = {}
        self.state = State.PIPELINE_PRE


    def run_pipeline_pre(self) -> None:
        """Run pre-phase steps, then advance to plan/confirm."""
        spec = self._pending_pipeline_spec or {}
        pipeline = spec.get("pipeline") or []
        label = spec.get("label", "DONE")
        success_key = spec.get("success_key", "ok")
        run_pipeline_steps(
            self.cfg,
            pipeline,
            phase="pre",
            label=label,
            success_key=success_key,
            ctx=self.runtime_ctx,
        )
        action_spec = self.actions.get(self.current_action_key or "", {})
        if self.plan_only:
            self.state = State.PREPARE_PLAN
            return
        if action_spec.get("skip_prepare_plan", False):
            self.state = State.CONFIRM
            return
        self.state = State.PREPARE_PLAN


    def prepare_plan(self, key_label: str, plan_columns: List[str]) -> None:
        """Print plan and move to CONFIRM (or finalize if plan-only)."""
        spec = self.actions[self.current_action_key]
        verb = (spec.get("verb") or "action")
        row: Dict[str, Any] = {}
        columns: List[str] = []
        for k in plan_columns:
            if k not in columns:
                columns.append(k)
            if k in self.cfg:
                row[k] = self.cfg[k]
        for rk, rv in (self.runtime_ctx or {}).items():
            if rk in row:
                continue
            row[rk] = rv
            if rk not in columns:
                columns.append(rk)
        buf = StringIO()
        with redirect_stdout(buf):
            print_dict_table([row], field_names=columns, label=f"Planned {verb.title()} ({key_label})")
        out_lines = buf.getvalue().splitlines()
        if out_lines and not out_lines[0].strip():
            out_lines = out_lines[1:]
        print(wrap_in_box(out_lines, indent=2, pad=1))
        if self.plan_only:
            self.finalize_msg = "Plan-only mode: no actions were executed."
            self.state = State.FINALIZE
            return
        self.state = State.CONFIRM


    def confirm_action(self) -> None:
        """Confirm the chosen action; advance to EXECUTE or bounce to MENU."""
        spec = self.actions[self.current_action_key]
        if spec.get("skip_confirm", False):
            proceed = True
        else:
            prompt = spec.get("prompt") or "Proceed? [y/n]: "
            proceed = True if self.auto_yes else confirm(prompt)
        if not proceed:
            print("User cancelled.")
            self.state = State.MENU_SELECTION
            return
        self.state = State.EXECUTE


    def run_pipeline_action(self) -> None:
        """Run exec-phase steps and then go to post_state."""
        spec = self._pending_pipeline_spec or {}
        pipeline = spec.get("pipeline") or []
        label = spec.get("label", "DONE")
        success_key = spec.get("success_key", "ok")
        action_spec = self.actions.get(self.current_action_key or "", {})
        post_state_name = action_spec.get("post_state") or "CONFIG_LOADING"
        run_pipeline_steps(
            self.cfg,
            pipeline,
            phase="exec",
            label=label,
            success_key=success_key,
            ctx=self.runtime_ctx,
        )
        self._pending_pipeline_spec = None
        try:
            self.state = State[post_state_name]
        except KeyError:
            print(f"[WARN] Unknown post_state '{post_state_name}', defaulting to CONFIG_LOADING.")
            self.state = State.CONFIG_LOADING


    def main(self) -> None:
        """Run the state machine with a dispatch table until FINALIZE."""
        handlers: Dict[State, Callable[[], None]] = {
            State.INITIAL:                  lambda: self.setup(self.c.REQUIRED_USER),
            State.DEP_CHECK:                lambda: self.dep_check(self.c.DEPENDENCIES),
            State.DEP_INSTALL:              lambda: self.dep_install(),
            State.CONFIG_LOADING:           lambda: self.load_config(self.c.CONFIG_PATH),
            State.JSON_REQUIRED_KEYS_CHECK: lambda: self.validate_json_required_keys(self.c.VALIDATION_CONFIG, dict),
            State.SECONDARY_VALIDATION:     lambda: self.validate_secondary_keys(self.c.SECONDARY_VALIDATION),
            State.DISPLAY_VERIFICATION:     lambda: self.display_verification_outcome(self.c.CONFIG_DOC),
            State.PACKAGE_STATUS:           lambda: self.build_status_map(self.c.TOOL_TYPE, self.c.ACTIVE_LABEL, self.c.INACTIVE_LABEL, self.c.STATUS_FN_CONFIG),
            State.BUILD_ACTIONS:            lambda: self.build_actions(self.c.ACTIONS),
            State.MENU_SELECTION:           lambda: self.select_action(),
            State.PIPELINE_PRE:             lambda: self.run_pipeline_pre(),
            State.PREPARE_PLAN:             lambda: self.prepare_plan(self.c.TOOL_TYPE, self.c.OPTIONAL_PLAN_COLUMNS.get(self.current_action_key, self.c.PLAN_COLUMN_ORDER)),
            State.CONFIRM:                  lambda: self.confirm_action(),
            State.EXECUTE:                  lambda: self.run_pipeline_action(),
        }
        try:
            while self.state != State.FINALIZE:
                handler = handlers.get(self.state)
                if handler:
                    handler()
                else:
                    print(f"Unknown state '{getattr(self.state, 'name', str(self.state))}', finalizing.")
                    self.finalize_msg = self.finalize_msg or "Unknown state encountered."
                    self.state = State.FINALIZE
        except KeyboardInterrupt:
            self.finalize_msg = "Interrupted by user."
            self.state = State.FINALIZE
        finally:
            if self.finalize_msg:
                print(self.finalize_msg)


def _parse_args_single(consts) -> argparse.Namespace:
    """Parse CLI args for single-config loader while keeping your existing pattern."""
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--constants", default=None, help="Constants module path, e.g. constants.DebSingleConstants")
    p.add_argument("--config", default=None, help="Override config path (defaults to CONFIG_PATH).")
    p.add_argument("--action", default=None, help="Action title (must match menu text).")
    p.add_argument("--yes", action="store_true", help="Auto-confirm prompts.")
    p.add_argument("--status", action="store_true", help="Status-only mode.")
    p.add_argument("--plan-only", action="store_true", help="Plan-only mode.")
    return p.parse_args()


if __name__ == "__main__":
    early = parse_args_early()
    constants_module = early.constants or pick_constants_interactively(AVAILABLE_CONSTANTS)
    consts = load_constants_from_module(constants_module, REQUIRED_CONSTANTS)
    args = _parse_args_single(consts)
    sm = StateMachine(
        consts,
        auto_yes=args.yes,
        cli_action=(None if args.status else args.action),
        status_only=args.status,
        plan_only=(False if args.status else args.plan_only),
        config_path=args.config,
    )
    sm.main()
