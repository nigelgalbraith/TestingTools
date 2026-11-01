#!/usr/bin/env python3

"""
state_machine_utils.py

Utilities for the TestingTools state machine: constants loading,
early CLI parsing, argument resolution, pipeline conditions and execution.
"""


from __future__ import annotations

import argparse
import importlib
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------
# COMMAND LINE ARGUMENTS
# ---------------------------------------------------------------------


def load_constants_from_module(module_path: str, required: list[str]):
    """Import a constants module and return a namespace-like object of uppercase attributes."""
    mod = importlib.import_module(module_path)
    consts = {name: getattr(mod, name) for name in dir(mod) if name.isupper()}
    missing = [n for n in required if n not in consts]
    if missing:
        raise SystemExit(
            f"[FATAL] Constants module '{module_path}' is missing: {', '.join(missing)}"
        )
    return type("Constants", (), consts)()


def parse_args_early() -> argparse.Namespace:
    """Parse only the --constants flag early, before full constants-dependent parsing."""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument(
        "--constants",
        help="Python module path for constants (e.g. constants.FunctionConstants)",
    )
    return p.parse_known_args()[0]

# ---------------------------------------------------------------------
# ARGUMENT RESOLUTION AND CONDITIONS
# ---------------------------------------------------------------------

def resolve_arg(spec: Any, job: str, meta: Dict[str, Any], ctx: Dict[str, Any]) -> Any:
    """Resolve pipeline arguments, including nested and dynamic context references."""
    if isinstance(spec, dict) and set(spec) == {"literal"}:
        return spec["literal"]
    if callable(spec):
        return spec(job, meta, ctx)
    if isinstance(spec, str):
        if spec == "job":
            return job
        if spec == "meta":
            return meta
        if spec == "ctx":
            return ctx
        if spec.startswith("?"):
            return meta.get(spec[1:])
        if spec in ctx:
            return ctx[spec]
        if spec.startswith("meta.") or spec.startswith("ctx."):
            value = meta if spec.startswith("meta.") else ctx
            for key in spec.split(".")[1:]:
                if key.startswith("$"):
                    key = ctx.get(key[1:])
                if isinstance(value, dict):
                    if key not in value:
                        return None
                    value = value[key]
                elif isinstance(value, (list, tuple)) and isinstance(key, str) and key.isdigit():
                    index = int(key)
                    if index >= len(value):
                        return None
                    value = value[index]
                else:
                    return None
            return value
        if spec in meta:
            return meta[spec]
    return spec




def check_when(cond: Any, job: str, meta: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    """Evaluate pipeline conditions using lists for AND and strings for OR."""
    if cond is None:
        return True
    if callable(cond):
        return bool(cond(job, meta, ctx))
    if isinstance(cond, list):
        return all(check_when(part, job, meta, ctx) for part in cond)
    if isinstance(cond, str):
        if " or " in cond:
            return any(check_when(part.strip(), job, meta, ctx) for part in cond.split(" or "))
        valid = cond in ("job", "meta", "ctx") or cond in ctx or cond in meta or cond.startswith(("meta.", "ctx."))
        result = valid and bool(resolve_arg(cond, job, meta, ctx))
        if result:
            print(f"[OK] Condition met: {cond}")
        else:
            print(f"[SKIP] Condition not met: {cond}")
        return result
    return bool(cond)


def run_pipeline_steps(
    job: Optional[str], meta: Dict[str, Any], pipeline: List[Dict[str, Any]],
    *, phase: str, label: str, ctx: Dict[str, Any],
) -> bool:
    """Execute one phase; ctx belongs to one run and is shared across phases.

    Both phases continue after exceptions. Loaders block confirmation after pre
    errors; exec always finishes eligible independent and cleanup steps. Only
    exceptions mean execution failure; return-value truthiness is never status.
    """
    if phase not in ("pre", "exec"):
        raise ValueError(f"Unknown pipeline phase: {phase!r}")
    for step in pipeline:
        if step.get("phase") not in ("pre", "exec"):
            raise ValueError("Every pipeline step requires phase pre or exec.")
    history = ctx.setdefault("steps", [])
    scheduled = []
    for step in pipeline:
        if step.get("phase") != phase:
            continue
        entry = {"step": getattr(step.get("fn"), "__name__", "pipeline step"),
                 "phase": phase, "status": "pending",
                 "result_key": step.get("result")}
        history.append(entry)
        scheduled.append((step, entry))
    for step, entry in scheduled:
        try:
            fn = step["fn"]
            if not callable(fn):
                raise TypeError("Pipeline step requires callable 'fn'.")
            if not isinstance(step["args"], list):
                raise TypeError("Pipeline step 'args' must be a list.")
            key = step["result"]
            if not isinstance(key, str) or not key or key == "steps":
                raise ValueError("Pipeline step requires a non-reserved result key.")
            if not check_when(step.get("when"), job, meta, ctx):
                entry.update(status="skipped", reason="when condition was false (dependency unavailable or condition unmet)")
                continue
            entry["status"] = "running"
            args = [resolve_arg(a, job, meta, ctx) for a in step["args"]]
            value = fn(*args)
            ctx[key] = value
            entry["status"] = "success"
        except Exception as exc:
            message = (f"File not found: {exc.filename}"
                       if isinstance(exc, FileNotFoundError) and exc.filename else str(exc))
            entry.update(status="failed", error=message, error_type=type(exc).__name__)
            if not getattr(exc, "reported", False):
                print(f"[ERROR] {entry['step']} failed → {message}")
    success = not any(s["status"] == "failed" for s in history)
    suffix = " (pre)" if phase == "pre" else ""
    print(f"{label}{suffix}: {'Success' if success else 'Failed'}")
    return success
