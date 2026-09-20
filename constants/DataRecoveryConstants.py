# DataRecoveryConstants.py
from __future__ import annotations

from typing import Any, Dict

from modules.data_recovery_utils import (
    get_drive_list,
    get_recovery_status,
    restore_recovery_permissions,
    run_ddrescue_image,
    run_photorec,
    run_testdisk,
    select_drive,
)
from modules.display_utils import (
    display_config_doc,
    print_dict_table,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

CONFIG_PATH = "config/DataRecoveryConfig.json"
TOOL_TYPE = "Data Recovery"
CONFIG_DOC = "doc/DataRecoveryDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

GENERAL_KEY = "general"
LOG_DESTINATION_KEY = "log_destination"
DESTINATION_KEY = "destination"
DDRESCUE_RETRIES_KEY = "ddrescue_retries"


# ---------------------------------------------------------------------
# VALIDATION CONFIG
# ---------------------------------------------------------------------

VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        GENERAL_KEY: dict,
    },
}


# ---------------------------------------------------------------------
# SECONDARY VALIDATION
# ---------------------------------------------------------------------

SECONDARY_VALIDATION: Dict[str, Any] = {
    GENERAL_KEY: {
        "required_job_fields": {
            DESTINATION_KEY: str,
            LOG_DESTINATION_KEY: str,
            DDRESCUE_RETRIES_KEY: int,
        },
        "allow_empty": False,
    }
}


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
    "fn": get_recovery_status,
    "args": [
        lambda job, meta, ctx: meta[GENERAL_KEY][DESTINATION_KEY],
    ],
    "id_field": "data_recovery",
    "active_rule": {
        "field": "ready",
        "equals": True,
    },
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = [
    "gddrescue",
    "testdisk",
    "util-linux",
]


# ---------------------------------------------------------------------
# PLAN CONFIG
# ---------------------------------------------------------------------

PLAN_COLUMN_ORDER = [GENERAL_KEY]
OPTIONAL_PLAN_COLUMNS = {}


# ---------------------------------------------------------------------
# ACTIONS
# ---------------------------------------------------------------------

ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {
        "title": "Select a Data Recovery operation",
    },
    "List drives": {
        "verb": "list",
        "prompt": "List detected drives? [y/n]: ",
        "execute_state": "LIST_DRIVES",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Create recovery image": {
        "verb": "image",
        "prompt": "Create a recovery image with ddrescue? [y/n]: ",
        "execute_state": "CREATE_RECOVERY_IMAGE",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Resume recovery image": {
        "verb": "resume",
        "prompt": "Resume a ddrescue recovery image? [y/n]: ",
        "execute_state": "RESUME_RECOVERY_IMAGE",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Launch TestDisk": {
        "verb": "testdisk",
        "prompt": "Launch TestDisk for the selected drive? [y/n]: ",
        "execute_state": "TESTDISK",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Launch PhotoRec": {
        "verb": "photorec",
        "prompt": "Launch PhotoRec for the selected drive? [y/n]: ",
        "execute_state": "PHOTOREC",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Restore recovery permissions": {
        "verb": "permissions",
        "prompt": "Restore recovery files to the sudo user? [y/n]: ",
        "execute_state": "RESTORE_PERMISSIONS",
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
# PRE PHASE BLOCKS
# ---------------------------------------------------------------------

DRIVE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": get_drive_list,
        "args": [],
        "result": "drive_list",
    },
    {
        "phase": "pre",
        "fn": select_drive,
        "args": [
            lambda job, meta, ctx: "Select the recovery source drive",
            lambda job, meta, ctx: ctx.get("drive_list", []),
            lambda job, meta, ctx: meta[GENERAL_KEY][DESTINATION_KEY],
        ],
        "result": "selected_drive",
        "when": lambda job, meta, ctx: bool(ctx.get("drive_list")),
    },
]


# ---------------------------------------------------------------------
# SHARED EXEC PHASE BLOCKS
# ---------------------------------------------------------------------

RESTORE_PERMISSIONS_EXEC = [
    {
        "phase": "exec",
        "fn": restore_recovery_permissions,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][DESTINATION_KEY],
        ],
        "result": "permissions_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("permissions_result", []),
            lambda job, meta, ctx: [
                "Destination",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "Recovery Permissions",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("permissions_result")),
    },
]

LOG_PERMISSIONS_EXEC = [
    {
        "phase": "exec",
        "fn": restore_recovery_permissions,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][LOG_DESTINATION_KEY],
        ],
        "result": "log_permissions_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("log_permissions_result", []),
            lambda job, meta, ctx: [
                "Destination",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "Log Permissions",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("log_permissions_result")),
    },
]

# ---------------------------------------------------------------------
# EXEC PHASE BLOCKS
# ---------------------------------------------------------------------

LIST_DRIVES_EXEC = [
    {
        "phase": "exec",
        "fn": get_drive_list,
        "args": [],
        "result": "drive_list",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("drive_list", []),
            lambda job, meta, ctx: [
                "Device",
                "Model",
                "Size",
                "Type",
                "Interface",
            ],
            lambda job, meta, ctx: "Detected Drives",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("drive_list")),
    },
]


CREATE_RECOVERY_IMAGE_EXEC = [
    {
        "phase": "exec",
        "fn": run_ddrescue_image,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
            lambda job, meta, ctx: meta[GENERAL_KEY][DESTINATION_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][DDRESCUE_RETRIES_KEY],
            lambda job, meta, ctx: False,
        ],
        "result": "recovery_image",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_drive")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("recovery_image", []),
            lambda job, meta, ctx: [
                "Source",
                "Image",
                "Map",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "Recovery Image",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("recovery_image")),
    },
]


RESUME_RECOVERY_IMAGE_EXEC = [
    {
        "phase": "exec",
        "fn": run_ddrescue_image,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
            lambda job, meta, ctx: meta[GENERAL_KEY][DESTINATION_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][DDRESCUE_RETRIES_KEY],
            lambda job, meta, ctx: True,
        ],
        "result": "recovery_image",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_drive")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("recovery_image", []),
            lambda job, meta, ctx: [
                "Source",
                "Image",
                "Map",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "Resume Recovery Image",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("recovery_image")),
    },
]


TESTDISK_EXEC = [
    {
        "phase": "exec",
        "fn": run_testdisk,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
            lambda job, meta, ctx: meta[GENERAL_KEY][LOG_DESTINATION_KEY],
        ],
        "result": "testdisk_result",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_drive")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("testdisk_result", []),
            lambda job, meta, ctx: [
                "Device",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "TestDisk",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("testdisk_result")),
    },
]


PHOTOREC_EXEC = [
    {
        "phase": "exec",
        "fn": run_photorec,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
            lambda job, meta, ctx: meta[GENERAL_KEY][DESTINATION_KEY],
        ],
        "result": "photorec_result",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_drive")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("photorec_result", []),
            lambda job, meta, ctx: [
                "Device",
                "Destination",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "PhotoRec",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("photorec_result")),
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
# PIPELINE STATES
# ---------------------------------------------------------------------

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "LIST_DRIVES": {
        "pipeline": [
            *LIST_DRIVES_EXEC,
        ],
        "label": "LIST_DRIVES_COMPLETE",
        "success_key": "ok",
    },
    "CREATE_RECOVERY_IMAGE": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *CREATE_RECOVERY_IMAGE_EXEC,
            *RESTORE_PERMISSIONS_EXEC,
        ],
        "label": "CREATE_RECOVERY_IMAGE_COMPLETE",
        "success_key": "ok",
    },
    "RESUME_RECOVERY_IMAGE": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *RESUME_RECOVERY_IMAGE_EXEC,
            *RESTORE_PERMISSIONS_EXEC,
        ],
        "label": "RESUME_RECOVERY_IMAGE_COMPLETE",
        "success_key": "ok",
    },
    "TESTDISK": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *TESTDISK_EXEC,
            *LOG_PERMISSIONS_EXEC,
        ],
        "label": "TESTDISK_COMPLETE",
        "success_key": "ok",
    },
    "PHOTOREC": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *PHOTOREC_EXEC,
            *RESTORE_PERMISSIONS_EXEC,
        ],
        "label": "PHOTOREC_COMPLETE",
        "success_key": "ok",
    },
    "RESTORE_PERMISSIONS": {
        "pipeline": [
            *RESTORE_PERMISSIONS_EXEC,
        ],
        "label": "RESTORE_PERMISSIONS_COMPLETE",
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