# EmailConstants.py
from __future__ import annotations
from typing import Dict, Any

from modules.display_utils import (
    display_config_doc,
    select_from_list,
)

from modules.file_utils import (
        get_directory_status,
        get_files_by_extension,
)

from modules.email_utils import (
    convert_pst_to_mbox,
)

# === CONFIG PATHS ===
CONFIG_PATH = "config/EmailConfig.json"
TOOL_TYPE = "Email"
CONFIG_DOC = "doc/EmailDoc.json"

# === JSON KEYS ===
LOCATIONS_KEY = "locations"
SOURCE_DIR = "source_dir"
DEST_DIR = "dest_dir"

VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        LOCATIONS_KEY: dict,
    },
}

SECONDARY_VALIDATION: Dict[str, Any] = {
    LOCATIONS_KEY: {
        "required_job_fields": {
            SOURCE_DIR: str,
            DEST_DIR: str,
        },
        "allow_empty": False,
    }
}

# === USER REQUIREMENTS ===
REQUIRED_USER = "standard"

ACTIVE_LABEL = "DATA PRESENT"
INACTIVE_LABEL = "NO DATA PRESENT"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": get_directory_status,
    "args": [
        lambda job, meta, ctx: meta[LOCATIONS_KEY][SOURCE_DIR],
    ],
    "id_field": "location",
    "active_rule": {"field": "state", "equals": "data_present"},
}

# === DEPENDENCIES ===
DEPENDENCIES = [
    "pst-utils"
]

# === PLAN CONFIG ===
PLAN_COLUMN_ORDER = [
    LOCATIONS_KEY,
]

OPTIONAL_PLAN_COLUMNS = {}

# === ACTIONS ===
ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": "Select an Email operation"},

    "Convert PST to mbox": {
        "verb": "convert",
        "prompt": "Convert PST file to mbox? [y/n]: ",
        "execute_state": "CONVERT_EMAIL",
        "post_state": "PACKAGE_STATUS",
        "skip_prepare_plan": False,
        "skip_confirm": False,
    },

    "Show config help": {
        "verb": "help",
        "prompt": "Show config help now? [y/n]: ",
        "execute_state": "SHOW_CONFIG_DOC",
        "post_state": "PACKAGE_STATUS",
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


# ============================================================
# PRE PHASE BLOCKS
# ============================================================

PST_FILE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": get_files_by_extension,
        "args": [
            lambda job, meta, ctx: meta[LOCATIONS_KEY][SOURCE_DIR],
            lambda job, meta, ctx: ".pst",
        ],
        "result": "pst_files",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select a PST file",
            lambda job, meta, ctx: ctx.get("pst_files", []),
        ],
        "result": "selected_pst",
        "when": lambda job, meta, ctx: len(ctx.get("pst_files", [])) > 0,
    },
]

# ============================================================
# EXEC PHASE BLOCKS
# ============================================================

CONVERT_EMAIL_EXEC = [
    {
        "phase": "exec",
        "fn": convert_pst_to_mbox,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][DEST_DIR],
        ],
        "result": "convert_ok",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_pst")),
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


# === STEP GROUPS ===


# ============================================================
# PIPELINE STATES
# ============================================================

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {

    "CONVERT_EMAIL": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *CONVERT_EMAIL_EXEC,
        ],
        "label": "CONVERT_COMPLETE",
        "success_key": "convert_ok",
    },

    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "DONE",
        "success_key": "ok",
    },
}