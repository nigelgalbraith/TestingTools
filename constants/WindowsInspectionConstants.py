# WindowsInspectionConstants.py
from __future__ import annotations

from typing import Any, Dict

from modules.display_utils import (
    display_config_doc,
    print_dict_table,
)
from modules.windows_inspection_utils import (
    check_mount_root,
    detect_windows_installations,
    get_installed_software,
    get_windows_info,
    get_windows_status,
    get_windows_users,
    inspect_registry_hives,
    inspect_services,
    inspect_startup_entries,
    select_windows_installation,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

CONFIG_PATH = "config/WindowsInspectionConfig.json"
TOOL_TYPE = "Offline Windows Inspection"
CONFIG_DOC = "doc/WindowsInspectionDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

GENERAL_KEY = "general"
MOUNT_ROOT_KEY = "mount_root"


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
            MOUNT_ROOT_KEY: str,
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
    "fn": get_windows_status,
    "args": [
        lambda job, meta, ctx: meta[GENERAL_KEY][MOUNT_ROOT_KEY],
    ],
    "id_field": "windows_inspection",
    "active_rule": {
        "field": "ready",
        "equals": True,
    },
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = [
    "util-linux",
    "ntfs-3g",
    "chntpw",
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
        "title": "Select an Offline Windows Inspection operation",
    },
    "Detect Windows installations": {
        "verb": "detect",
        "prompt": "Detect Windows installations? [y/n]: ",
        "execute_state": "DETECT_WINDOWS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Windows information": {
        "verb": "info",
        "prompt": "Inspect Windows information? [y/n]: ",
        "execute_state": "WINDOWS_INFO",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Windows users": {
        "verb": "users",
        "prompt": "Inspect Windows users? [y/n]: ",
        "execute_state": "WINDOWS_USERS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Registry hives": {
        "verb": "registry",
        "prompt": "Inspect Windows registry hives? [y/n]: ",
        "execute_state": "REGISTRY_HIVES",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Startup entries": {
        "verb": "startup",
        "prompt": "Inspect Windows startup entries? [y/n]: ",
        "execute_state": "STARTUP_ENTRIES",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Services": {
        "verb": "services",
        "prompt": "Inspect Windows services? [y/n]: ",
        "execute_state": "SERVICES",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Installed software": {
        "verb": "software",
        "prompt": "Inspect installed Windows software? [y/n]: ",
        "execute_state": "INSTALLED_SOFTWARE",
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

MOUNT_ROOT_PRE = [
    {
        "phase": "pre",
        "fn": check_mount_root,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][MOUNT_ROOT_KEY],
        ],
        "result": "mount_check",
    },
    {
        "phase": "pre",
        "fn": lambda rows: bool(rows and rows[0].get("ready")),
        "args": [
            lambda job, meta, ctx: ctx.get("mount_check", []),
        ],
        "result": "mount_ready",
    },
    {
        "phase": "pre",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("mount_check", []),
            lambda job, meta, ctx: [
                "Mount root",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "Mount Root Check",
        ],
        "result": "mount_check_displayed",
    },
]


WINDOWS_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": detect_windows_installations,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][MOUNT_ROOT_KEY],
        ],
        "result": "windows_installations",
        "when": lambda job, meta, ctx: bool(ctx.get("mount_ready")),
    },
    {
        "phase": "pre",
        "fn": select_windows_installation,
        "args": [
            lambda job, meta, ctx: ctx.get("windows_installations", []),
        ],
        "result": "selected_windows",
        "when": lambda job, meta, ctx: bool(ctx.get("mount_ready")),
    },
]


# ---------------------------------------------------------------------
# EXEC PHASE BLOCKS
# ---------------------------------------------------------------------

DETECT_WINDOWS_EXEC = [
    {
        "phase": "exec",
        "fn": detect_windows_installations,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][MOUNT_ROOT_KEY],
        ],
        "result": "windows_installations",
        "when": lambda job, meta, ctx: bool(ctx.get("mount_ready")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("windows_installations", []),
            lambda job, meta, ctx: [
                "Device",
                "Mount",
                "Windows",
            ],
            lambda job, meta, ctx: "Detected Windows Installations",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("mount_ready")) and bool(ctx.get("windows_installations")),
    },
]


WINDOWS_INFO_EXEC = [
    {
        "phase": "exec",
        "fn": get_windows_info,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_windows"),
        ],
        "result": "windows_info",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_windows")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("windows_info", []),
            lambda job, meta, ctx: [
                "Field",
                "Value",
            ],
            lambda job, meta, ctx: "Windows Information",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("windows_info")),
    },
]


WINDOWS_USERS_EXEC = [
    {
        "phase": "exec",
        "fn": get_windows_users,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_windows"),
        ],
        "result": "windows_users",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_windows")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("windows_users", []),
            lambda job, meta, ctx: [
                "User",
                "Profile",
            ],
            lambda job, meta, ctx: "Windows Users",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("windows_users")),
    },
]


REGISTRY_HIVES_EXEC = [
    {
        "phase": "exec",
        "fn": inspect_registry_hives,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_windows"),
        ],
        "result": "registry_hives",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_windows")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("registry_hives", []),
            lambda job, meta, ctx: [
                "Hive",
                "Path",
                "Status",
            ],
            lambda job, meta, ctx: "Registry Hives",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("registry_hives")),
    },
]


STARTUP_ENTRIES_EXEC = [
    {
        "phase": "exec",
        "fn": inspect_startup_entries,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_windows"),
        ],
        "result": "startup_entries",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_windows")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("startup_entries", []),
            lambda job, meta, ctx: [
                "Location",
                "Entry",
            ],
            lambda job, meta, ctx: "Startup Entries",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("startup_entries")),
    },
]


SERVICES_EXEC = [
    {
        "phase": "exec",
        "fn": inspect_services,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_windows"),
        ],
        "result": "services",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_windows")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("services", []),
            lambda job, meta, ctx: [
                "Service",
                "Status",
            ],
            lambda job, meta, ctx: "Windows Services",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("services")),
    },
]


INSTALLED_SOFTWARE_EXEC = [
    {
        "phase": "exec",
        "fn": get_installed_software,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_windows"),
        ],
        "result": "installed_software",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_windows")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("installed_software", []),
            lambda job, meta, ctx: [
                "Name",
                "Version",
            ],
            lambda job, meta, ctx: "Installed Windows Software",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("installed_software")),
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
    "DETECT_WINDOWS": {
        "pipeline": [
            *MOUNT_ROOT_PRE,
            *DETECT_WINDOWS_EXEC,
        ],
        "label": "DETECT_WINDOWS_COMPLETE",
        "success_key": "mount_ready",
    },
    "WINDOWS_INFO": {
        "pipeline": [
            *MOUNT_ROOT_PRE,
            *WINDOWS_SELECTION_PRE,
            *WINDOWS_INFO_EXEC,
        ],
        "label": "WINDOWS_INFO_COMPLETE",
        "success_key": "selected_windows",
    },
    "WINDOWS_USERS": {
        "pipeline": [
            *MOUNT_ROOT_PRE,
            *WINDOWS_SELECTION_PRE,
            *WINDOWS_USERS_EXEC,
        ],
        "label": "WINDOWS_USERS_COMPLETE",
        "success_key": "selected_windows",
    },
    "REGISTRY_HIVES": {
        "pipeline": [
            *MOUNT_ROOT_PRE,
            *WINDOWS_SELECTION_PRE,
            *REGISTRY_HIVES_EXEC,
        ],
        "label": "REGISTRY_HIVES_COMPLETE",
        "success_key": "selected_windows",
    },
    "STARTUP_ENTRIES": {
        "pipeline": [
            *MOUNT_ROOT_PRE,
            *WINDOWS_SELECTION_PRE,
            *STARTUP_ENTRIES_EXEC,
        ],
        "label": "STARTUP_ENTRIES_COMPLETE",
        "success_key": "selected_windows",
    },
    "SERVICES": {
        "pipeline": [
            *MOUNT_ROOT_PRE,
            *WINDOWS_SELECTION_PRE,
            *SERVICES_EXEC,
        ],
        "label": "SERVICES_COMPLETE",
        "success_key": "selected_windows",
    },
    "INSTALLED_SOFTWARE": {
        "pipeline": [
            *MOUNT_ROOT_PRE,
            *WINDOWS_SELECTION_PRE,
            *INSTALLED_SOFTWARE_EXEC,
        ],
        "label": "INSTALLED_SOFTWARE_COMPLETE",
        "success_key": "selected_windows",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "DONE",
        "success_key": "ok",
    },
}