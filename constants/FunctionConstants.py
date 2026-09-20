# FunctionConstants.py
from __future__ import annotations

from typing import Dict, Any

from modules.display_utils import (
    display_config_doc,
    select_from_list,
)
from modules.function_utils import (
    get_function_status,
    load_module_functions,
    load_module_function_docs,
    scan_function_usage,
    print_usage_summary,
    print_functions_summary,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

CONFIG_PATH = "config/FunctionsConfig.json"
TOOL_TYPE = "Functions"
CONFIG_DOC = "doc/FunctionDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

KEY_MODULES = "Modules"
KEY_MODULE_FOLDER = "ModuleFolder"
KEY_CHECK_FOLDERS = "CheckFolders"
KEY_CHECK_FILES = "CheckFiles"


# ---------------------------------------------------------------------
# VALIDATION CONFIG
# ---------------------------------------------------------------------

VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        KEY_MODULES: list,
        KEY_MODULE_FOLDER: str,
        KEY_CHECK_FOLDERS: list,
        KEY_CHECK_FILES: list,
    },
}


# ---------------------------------------------------------------------
# SECONDARY VALIDATION
# ---------------------------------------------------------------------

SECONDARY_VALIDATION: Dict[str, Any] = {}


# ---------------------------------------------------------------------
# USER REQUIREMENTS
# ---------------------------------------------------------------------

REQUIRED_USER = "standard"

ACTIVE_LABEL = "READY"
INACTIVE_LABEL = "NOT_READY"


# ---------------------------------------------------------------------
# STATUS CHECK CONFIG
# ---------------------------------------------------------------------

STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": get_function_status,
    "args": [
        KEY_MODULES,
        KEY_MODULE_FOLDER,
    ],
    "id_field": "module",
    "active_rule": {"field": "ready", "equals": True},
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = []


# ---------------------------------------------------------------------
# PLAN CONFIG
# ---------------------------------------------------------------------

PLAN_COLUMN_ORDER = [
    KEY_MODULES,
    KEY_MODULE_FOLDER,
    KEY_CHECK_FOLDERS,
    KEY_CHECK_FILES,
]


OPTIONAL_PLAN_COLUMNS = {}


# ---------------------------------------------------------------------
# ACTIONS
# ---------------------------------------------------------------------

ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": "Select a Function operation"},
    "Analyze functions": {
        "verb": "analyze",
        "prompt": "Run static function-usage scan now? [y/n]: ",
        "execute_state": "ANALYZE_FUNCTIONS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Show functions": {
        "verb": "show",
        "prompt": "Show module functions and docstrings now? [y/n]: ",
        "execute_state": "SHOW_FUNCTIONS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Show config help": {
        "verb": "help",
        "prompt": "Show config help now? [y/n]: ",
        "execute_state": "SHOW_CONFIG_DOC",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Cancel": {
        "verb": "cancel",
        "prompt": "",
        "execute_state": "FINALIZE",
        "post_state": "FINALIZE",
        "skip_prepare_plan": True,
    },
}


# ---------------------------------------------------------------------
# REUSABLE STEP BLOCKS
# ---------------------------------------------------------------------

MODULE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            "Select a Python module",
            KEY_MODULES,
        ],
        "result": "selected_module",
    },
]


# ---------------------------------------------------------------------
# EXEC PHASE STEPS
# ---------------------------------------------------------------------

ANALYZE_FUNCTIONS_EXEC = [
    {
        "phase": "exec",
        "fn": load_module_functions,
        "args": [
            KEY_MODULE_FOLDER,
            lambda job, meta, ctx: ctx["selected_module"],
        ],
        "result": "module_functions",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_module")),
    },
    {
        "phase": "exec",
        "fn": scan_function_usage,
        "args": [
            lambda job, meta, ctx: ctx.get("module_functions", {}),
            KEY_CHECK_FOLDERS,
            KEY_CHECK_FILES,
            KEY_MODULE_FOLDER,
        ],
        "result": "scan_result",
        "when": lambda job, meta, ctx: "module_functions" in ctx and not ctx.get("errors"),
    },
    {
        "phase": "exec",
        "fn": print_usage_summary,
        "args": [
            lambda job, meta, ctx: ctx["selected_module"],
            lambda job, meta, ctx: ctx.get("scan_result", {}),
        ],
        "when": lambda job, meta, ctx: bool(ctx.get("scan_result")),
    },
    {
        "phase": "exec",
        "fn": lambda ctx: "scan_result" in ctx and not ctx.get("errors"),
        "args": [
            lambda job, meta, ctx: ctx,
        ],
        "result": "ok",
    },
]


SHOW_FUNCTIONS_EXEC = [
    {
        "phase": "exec",
        "fn": load_module_function_docs,
        "args": [
            KEY_MODULE_FOLDER,
            lambda job, meta, ctx: ctx["selected_module"],
        ],
        "result": "fn_docs",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_module")),
    },
    {
        "phase": "exec",
        "fn": print_functions_summary,
        "args": [
            lambda job, meta, ctx: ctx["selected_module"],
            lambda job, meta, ctx: ctx.get("fn_docs", {}),
        ],
        "when": lambda job, meta, ctx: "fn_docs" in ctx,
    },
    {
        "phase": "exec",
        "fn": lambda ctx: "fn_docs" in ctx and not ctx.get("errors"),
        "args": [
            lambda job, meta, ctx: ctx,
        ],
        "result": "ok",
    },
]


SHOW_CONFIG_DOC_EXEC = [
    {
        "phase": "exec",
        "fn": display_config_doc,
        "args": [CONFIG_DOC],
        "result": "ok",
    },
]


# ---------------------------------------------------------------------
# PIPELINES
# ---------------------------------------------------------------------

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "ANALYZE_FUNCTIONS": {
        "pipeline": [
            *MODULE_SELECTION_PRE,
            *ANALYZE_FUNCTIONS_EXEC,
        ],
        "label": "ANALYZE_COMPLETE",
        "success_key": "ok",
    },
    "SHOW_FUNCTIONS": {
        "pipeline": [
            *MODULE_SELECTION_PRE,
            *SHOW_FUNCTIONS_EXEC,
        ],
        "label": "SHOW_FUNCTIONS_COMPLETE",
        "success_key": "ok",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "DONE",
        "success_key": "ok",
    },
}
