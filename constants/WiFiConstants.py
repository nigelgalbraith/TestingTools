# WiFiScannerConstants.py
from __future__ import annotations
from typing import Dict, Any

from modules.display_utils import (
    display_config_doc, 
    select_from_list, 
    print_dict_table, 
)

from modules.wifi_utils import (
    get_wireless_interfaces,
    scan_networks,
    check_wifi_status,
    show_network_details,
    build_network_choices, 
    select_network_from_scan,
)

# === CONFIG PATHS ===
CONFIG_PATH = "config/WiFiConfig.json"
TOOL_TYPE = "WiFiScanner"
CONFIG_DOC = "doc/WiFiDoc.json"

# ==== JSON SCHEMA ===
GENERAL_KEY = "general"
SCAN_TIMEOUT_KEY = "scan_timeout"
NETWORK_SUMMARY_COLUMNS_KEY = "network_summary_columns"
NETWORK_SUMMARY_NAME_KEY = "name"
NETWORK_SUMMARY_KEY_KEY = "key"
NETWORK_SUMMARY_COLUMN_PATTERN = "pattern"

# === VALIDATION CONFIG ===
VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        GENERAL_KEY: dict,
        NETWORK_SUMMARY_COLUMNS_KEY: list,
    },
}


# === SECONDARY VALIDATION ===
SECONDARY_VALIDATION: Dict[str, Any] = {
    GENERAL_KEY: {
        "required_job_fields": {
            SCAN_TIMEOUT_KEY: int,
        },
        "allow_empty": False,
    },

    NETWORK_SUMMARY_COLUMNS_KEY: {
        "required_job_fields": {
            NETWORK_SUMMARY_NAME_KEY: str,
            NETWORK_SUMMARY_KEY_KEY: str,
            NETWORK_SUMMARY_COLUMN_PATTERN: str,
        },
        "allow_empty": False,
    },
}

# === USER / LABELS ===
REQUIRED_USER = "root"
ACTIVE_LABEL = "CONNECTED"
INACTIVE_LABEL = "DISCONNECTED"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": check_wifi_status,
    "args": [],
    "id_field": "device",
    "active_rule": {"field": "state", "equals": "connected"},
}

# === PLAN COLUMNS ===
PLAN_COLUMN_ORDER = [
    GENERAL_KEY,
]

OPTIONAL_PLAN_COLUMNS = {}

# === DEPENDENCIES ===
DEPENDENCIES = [
    "iw",
    "network-manager",
]

# === ACTIONS ===
ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": "Select a WiFi operation"},

    "Scan for networks": {
        "verb": "scan",
        "prompt": "Start WiFi scan? [y/n]: ",
        "execute_state": "SCAN_NETWORKS",
        "post_state": "PACKAGE_STATUS",
        "skip_prepare_plan": False,
        "skip_confirm": False,
    },

    "Analyze a network": {
        "verb": "analyze",
        "prompt": "Analyze selected network? [y/n]: ",
        "execute_state": "ANALYZE_NETWORK",
        "post_state": "PACKAGE_STATUS",
        "skip_prepare_plan": True,
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

# === REUSABLE STEP BLOCKS ===
INTERFACE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": get_wireless_interfaces,
        "args": [
            lambda job, meta, ctx: 10,
        ],
        "result": "interfaces",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select a wifi interface",
            lambda job, meta, ctx: ctx.get("interfaces", []),
        ],
        "result": "selected_interface",
        "when": lambda job, meta, ctx: len(ctx.get("interfaces", [])) > 0,
    },
]

NETWORK_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": scan_networks,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_interface"),
            lambda job, meta, ctx: meta[GENERAL_KEY][SCAN_TIMEOUT_KEY],
            lambda job, meta, ctx: meta.get(NETWORK_SUMMARY_COLUMNS_KEY, []),
            lambda job, meta, ctx: "managed",
        ],
        "result": "networks",
    },
    {
        "phase": "pre",
        "fn": build_network_choices,
        "args": [
            lambda job, meta, ctx: ctx.get("networks", []),
            lambda job, meta, ctx: meta.get(NETWORK_SUMMARY_COLUMNS_KEY, []),
        ],
        "result": "network_choices",
        "when": lambda job, meta, ctx: bool(ctx.get("networks")),
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select a network",
            lambda job, meta, ctx: ctx.get("network_choices", []),
        ],
        "result": "selected_network_choice",
        "when": lambda job, meta, ctx: bool(ctx.get("network_choices")),
    },
    {
        "phase": "pre",
        "fn": select_network_from_scan,
        "args": [
            lambda job, meta, ctx: ctx.get("networks", []),
            lambda job, meta, ctx: ctx.get("selected_network_choice"),
            lambda job, meta, ctx: meta.get(NETWORK_SUMMARY_COLUMNS_KEY, []),
        ],
        "result": "selected_network",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_network_choice")),
    },
]


# --- EXEC PHASE STEPS ---
SCAN_NETWORKS_EXEC = [
    {
        "phase": "exec",
        "fn": scan_networks,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_interface"),
            lambda job, meta, ctx: meta[GENERAL_KEY][SCAN_TIMEOUT_KEY],
            lambda job, meta, ctx: meta.get(NETWORK_SUMMARY_COLUMNS_KEY, []),
            lambda job, meta, ctx: "managed",
        ],
        "result": "networks",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("networks", []),
            lambda job, meta, ctx: [
                col.get(NETWORK_SUMMARY_KEY_KEY)
                for col in meta.get(NETWORK_SUMMARY_COLUMNS_KEY, [])
            ],
            lambda job, meta, ctx: "Available Networks",
        ],
        "result": "display_ok",
        "when": lambda job, meta, ctx: bool(ctx.get("networks")),
    },
]

ANALYZE_NETWORK_EXEC = [
    {
        "phase": "exec",
        "fn": show_network_details,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_interface"),
            lambda job, meta, ctx: ctx.get("selected_network", {}),
            lambda job, meta, ctx: meta[GENERAL_KEY].get(SCAN_TIMEOUT_KEY, 8),
        ],
        "result": "analysis_ok",
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
ANALYZE_NETWORK_STEPS_PRE = (
    INTERFACE_SELECTION_PRE +
    NETWORK_SELECTION_PRE
)

# === PIPELINES ===

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {

    "SCAN_NETWORKS": {
        "pipeline": [
            *INTERFACE_SELECTION_PRE,
            *SCAN_NETWORKS_EXEC,
        ],
        "label": "SCAN_COMPLETE",
        "success_key": "display_ok",
    },

    "ANALYZE_NETWORK": {
        "pipeline": [
            *ANALYZE_NETWORK_STEPS_PRE,
            *ANALYZE_NETWORK_EXEC,
        ],
        "label": "ANALYZE_COMPLETE",
        "success_key": "analysis_ok",
    },

    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "DONE",
        "success_key": "ok",
    },
}