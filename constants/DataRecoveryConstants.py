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
    "args": ["meta.general.destination"],
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
            "Select the recovery source drive",
            "drive_list",
            "meta.general.destination",
        ],
        "when": "drive_list",
        "result": "selected_drive",
    },
]

# ---------------------------------------------------------------------
# SHARED EXEC PHASE BLOCKS
# ---------------------------------------------------------------------

RESTORE_PERMISSIONS_EXEC = [
    {
        "phase": "exec",
        "fn": restore_recovery_permissions,
        "args": ["meta.general.destination"],
        "result": "permissions_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            "permissions_result",
            ["Destination", "Result", "Status"],
            "Recovery Permissions",
        ],
        "when": "permissions_result",
        "result": "print_dict_table_result",
    },
]

LOG_PERMISSIONS_EXEC = [
    {
        "phase": "exec",
        "fn": restore_recovery_permissions,
        "args": ["meta.general.log_destination"],
        "result": "log_permissions_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            "log_permissions_result",
            ["Destination", "Result", "Status"],
            "Log Permissions",
        ],
        "when": "log_permissions_result",
        "result": "print_dict_table_result",
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
            "drive_list",
            ["Device", "Model", "Size", "Type", "Interface"],
            "Detected Drives",
        ],
        "when": "drive_list",
        "result": "print_dict_table_result",
    },
]

CREATE_RECOVERY_IMAGE_EXEC = [
    {
        "phase": "exec",
        "fn": run_ddrescue_image,
        "args": [
            "selected_drive",
            "meta.general.destination",
            "meta.general.ddrescue_retries",
            False,
        ],
        "when": "selected_drive",
        "result": "recovery_image",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            "recovery_image",
            ["Source", "Image", "Map", "Result", "Status"],
            "Recovery Image",
        ],
        "when": "recovery_image",
        "result": "print_dict_table_result",
    },
]

RESUME_RECOVERY_IMAGE_EXEC = [
    {
        "phase": "exec",
        "fn": run_ddrescue_image,
        "args": [
            "selected_drive",
            "meta.general.destination",
            "meta.general.ddrescue_retries",
            True,
        ],
        "when": "selected_drive",
        "result": "recovery_image",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            "recovery_image",
            ["Source", "Image", "Map", "Result", "Status"],
            "Resume Recovery Image",
        ],
        "when": "recovery_image",
        "result": "print_dict_table_result",
    },
]

TESTDISK_EXEC = [
    {
        "phase": "exec",
        "fn": run_testdisk,
        "args": [
            "selected_drive",
            "meta.general.log_destination",
        ],
        "when": "selected_drive",
        "result": "testdisk_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            "testdisk_result",
            ["Device", "Result", "Status"],
            "TestDisk",
        ],
        "when": "testdisk_result",
        "result": "print_dict_table_result",
    },
]

PHOTOREC_EXEC = [
    {
        "phase": "exec",
        "fn": run_photorec,
        "args": [
            "selected_drive",
            "meta.general.destination",
        ],
        "when": "selected_drive",
        "result": "photorec_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            "photorec_result",
            ["Device", "Destination", "Result", "Status"],
            "PhotoRec",
        ],
        "when": "photorec_result",
        "result": "print_dict_table_result",
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
# PIPELINE STATES
# ---------------------------------------------------------------------

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "LIST_DRIVES": {
        "pipeline": [
            *LIST_DRIVES_EXEC,
        ],
        "label": "LIST_DRIVES_COMPLETE",
    },
    "CREATE_RECOVERY_IMAGE": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *CREATE_RECOVERY_IMAGE_EXEC,
            *RESTORE_PERMISSIONS_EXEC,
        ],
        "label": "CREATE_RECOVERY_IMAGE_COMPLETE",
    },
    "RESUME_RECOVERY_IMAGE": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *RESUME_RECOVERY_IMAGE_EXEC,
            *RESTORE_PERMISSIONS_EXEC,
        ],
        "label": "RESUME_RECOVERY_IMAGE_COMPLETE",
    },
    "TESTDISK": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *TESTDISK_EXEC,
            *LOG_PERMISSIONS_EXEC,
        ],
        "label": "TESTDISK_COMPLETE",
    },
    "PHOTOREC": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *PHOTOREC_EXEC,
            *RESTORE_PERMISSIONS_EXEC,
        ],
        "label": "PHOTOREC_COMPLETE",
    },
    "RESTORE_PERMISSIONS": {
        "pipeline": [
            *RESTORE_PERMISSIONS_EXEC,
        ],
        "label": "RESTORE_PERMISSIONS_COMPLETE",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "DONE",
    },
}