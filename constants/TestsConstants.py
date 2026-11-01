
# constants/TestsConstants.py
from __future__ import annotations
from typing import Any, Dict
from modules.display_utils import display_config_doc, select_from_list
from modules.test_utils import get_test_status, load_test_pipelines, check_pipeline_structure

# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

CONFIG_PATH = "config/TestsConfig.json"
TOOL_TYPE = "Tests"
CONFIG_DOC = "doc/TestsDoc.json"

# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

MODULES_KEY = "ConstantsModules"

# ---------------------------------------------------------------------
# VALIDATION CONFIG
# ---------------------------------------------------------------------

VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        MODULES_KEY: list,
    },
}
SECONDARY_VALIDATION: Dict[str, Any] = {}

# ---------------------------------------------------------------------
# USER REQUIREMENTS
# ---------------------------------------------------------------------

REQUIRED_USER = "root"
ACTIVE_LABEL = "READY"
INACTIVE_LABEL = "NOT_READY"

# ---------------------------------------------------------------------
# STATUS CHECK CONFIG
# ---------------------------------------------------------------------

STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": get_test_status,
    "args": [MODULES_KEY],
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

PLAN_COLUMN_ORDER = [MODULES_KEY]
OPTIONAL_PLAN_COLUMNS: Dict[str, Any] = {}

# ---------------------------------------------------------------------
# ACTIONS
# ---------------------------------------------------------------------

ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": "Pipeline Tests"},
    "Run tests": {
        "verb": "test",
        "prompt": "Check pipeline structures? [y/n]: ",
        "execute_state": "RUN_TESTS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Show config help": {
        "verb": "help",
        "prompt": "Show config help now? [y/n]: ",
        "execute_state": "SHOW_CONFIG_DOC",
        "post_state": "MENU_SELECTION",
        "skip_group_select": True,
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
# EXEC PHASE STEPS
# ---------------------------------------------------------------------


RUN_TESTS_EXEC = [
    {
        "phase": "exec",
        "fn": select_from_list,
        "args": [
            "Select constants module to test",
            MODULES_KEY,
            True,
        ],
        "result": "selected_modules",
    },
    {
        "phase": "exec",
        "fn": load_test_pipelines,
        "args": ["selected_modules"],
        "when": "selected_modules",
        "result": "pipelines_loaded",
    },
    {
        "phase": "exec",
        "fn": check_pipeline_structure,
        "args": ["pipelines_loaded"],
        "when": "pipelines_loaded",
        "result": "validation_ok",
    },
]


SHOW_CONFIG_DOC_EXEC = [
    {
        "phase": "exec",
        "fn": display_config_doc,
        "args": [CONFIG_DOC],
        "result": "display_config_doc_result",
    },
]

# ---------------------------------------------------------------------
# PIPELINES
# ---------------------------------------------------------------------

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "RUN_TESTS": {
        "pipeline": [
            *RUN_TESTS_EXEC,
        ],
        "label": "TESTS_COMPLETE",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "DONE",
    },
}
