# EthernetConstants.py
from __future__ import annotations
from typing import Dict, Any

from modules.display_utils import (
    display_config_doc,
    select_from_list,
    print_dict_table,
)

from modules.network_utils import (
    get_interfaces,
    get_connected_interfaces,
    get_interface_status,
    analyze_interface,
)

from modules.portscan_utils import (
    get_arp_neighbors,
    get_arp_neighbor_rows,
    prompt_for_target,
    scan_tcp_ports,
)

# === CONFIG PATHS ===
CONFIG_PATH = "config/NetworkConfig.json"
TOOL_TYPE = "NetworkScanner"
CONFIG_DOC = "doc/NetworkDoc.json"

# === JSON KEYS ===
GENERAL_KEY = "general"
PORT_SCAN_KEY = "port_scan"
PORTS_KEY = "ports"
TIMEOUT_KEY = "timeout"
WORKERS_KEY = "workers"

# === VALIDATION CONFIG ===
VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        GENERAL_KEY: dict,
        PORT_SCAN_KEY: dict,
    },
}

# === SECONDARY VALIDATION ===
SECONDARY_VALIDATION: Dict[str, Any] = {
    PORT_SCAN_KEY: {
        "required_job_fields": {
            PORTS_KEY: list,
            TIMEOUT_KEY: (int, float),
            WORKERS_KEY: int,
        },
        "allow_empty": False,
    }
}
# === USER REQUIREMENTS ===
REQUIRED_USER = "root"

ACTIVE_LABEL = "CONNECTED"
INACTIVE_LABEL = "DISCONNECTED"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": get_interface_status,
    "args": [],
    "id_field": "device",
    "active_rule": {"field": "state", "equals": "connected"},
}


# === DEPENDENCIES ===
DEPENDENCIES = [
    "network-manager",
    "iproute2",
]

# === PLAN CONFIG ===
PLAN_COLUMN_ORDER = [GENERAL_KEY]
OPTIONAL_PLAN_COLUMNS = {}

# === ACTIONS ===
ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": "Select a Network operation"},

    "Analyze network": {
        "verb": "analyze",
        "prompt": "Analyze selected network interface? [y/n]: ",
        "execute_state": "ANALYZE_NETWORK",
        "post_state": "PACKAGE_STATUS",
        "skip_prepare_plan": False,
        "skip_confirm": False,
    },

    "Show Neighbours": {
        "verb": "arp_scan",
        "prompt": "Run ARP scan? [y/n]: ",
        "execute_state": "ARP_SCAN",
        "post_state": "PACKAGE_STATUS",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },

    "Port scan host": {
        "verb": "portscan",
        "prompt": "Run TCP port scan? [y/n]: ",
        "execute_state": "PORT_SCAN",
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

INTERFACE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": get_interfaces,
        "args": [lambda job, meta, ctx: None],
        "result": "interfaces",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select a network interface",
            lambda job, meta, ctx: ctx.get("interfaces", []),
        ],
        "result": "selected_interface",
        "when": lambda job, meta, ctx: len(ctx.get("interfaces", [])) > 0,
    },
]


CONNECTED_INTERFACE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": get_connected_interfaces,
        "args": [
            lambda job, meta, ctx: None,
        ],
        "result": "interfaces",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select a connected network interface",
            lambda job, meta, ctx: ctx.get("interfaces", []),
        ],
        "result": "selected_interface",
        "when": lambda job, meta, ctx: len(ctx.get("interfaces", [])) > 0,
    },
]

PORT_SCAN_PRE = [
    {
        "phase": "pre",
        "fn": get_arp_neighbors,
        "args": [],
        "result": "neighbor_ips",
    },
    {
        "phase": "pre",
        "fn": lambda ips: (ips or []) + ["Enter manually"],
        "args": [lambda job, meta, ctx: ctx.get("neighbor_ips", [])],
        "result": "neighbor_choices",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select a target",
            lambda job, meta, ctx: ctx.get("neighbor_choices", []),
        ],
        "result": "selected_target",
    },
    {
        "phase": "pre",
        "fn": prompt_for_target,
        "args": [None],
        "result": "manual_target",
        "when": lambda job, meta, ctx: ctx.get("selected_target") == "Enter manually",
    },
    {
        "phase": "pre",
        "fn": lambda selected, manual: manual if selected == "Enter manually" else selected,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_target"),
            lambda job, meta, ctx: ctx.get("manual_target"),
        ],
        "result": "target",
    },
]




# ============================================================
# EXEC PHASE BLOCKS
# ============================================================

ANALYZE_NETWORK_EXEC = [
    {
        "phase": "exec",
        "fn": analyze_interface,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_interface"),
        ],
        "result": "analysis_rows",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_interface")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("analysis_rows", []),
            lambda job, meta, ctx: ["Key", "Value"],
            lambda job, meta, ctx: "Interface Details",
        ],
        "result": "analysis_ok",
        "when": lambda job, meta, ctx: bool(ctx.get("analysis_rows")),
    },
]


PORT_SCAN_EXEC = [
    {
        "phase": "exec",
        "fn": scan_tcp_ports,
        "args": [
            lambda job, meta, ctx: ctx.get("target"),
            lambda job, meta, ctx: meta[PORT_SCAN_KEY][PORTS_KEY],
            lambda job, meta, ctx: meta[PORT_SCAN_KEY].get(TIMEOUT_KEY, 0.5),
            lambda job, meta, ctx: meta[PORT_SCAN_KEY].get(WORKERS_KEY, 200),
        ],
        "result": "open_ports",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("open_ports", []),
            lambda job, meta, ctx: ["Port", "Service", "Note"],
            lambda job, meta, ctx: "Open TCP Ports",
        ],
        "result": "portscan_display_ok",
        "when": lambda job, meta, ctx: True,
    },
]

ARP_SCAN_EXEC = [
    {
        "phase": "exec",
        "fn": get_arp_neighbor_rows,
        "args": [],
        "result": "neighbors",
    },
    {
        "phase": "exec",
        "fn": lambda rows: bool(rows),
        "args": [lambda job, meta, ctx: ctx.get("neighbors", [])],
        "result": "arpscan_ok",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("neighbors", []),
            lambda job, meta, ctx: ["IP", "MAC", "Interface"],
            lambda job, meta, ctx: "ARP Neighbors",
        ],
        "result": "arpscan_display_ok",
        "when": lambda job, meta, ctx: bool(ctx.get("neighbors")),
    },
    {
        "phase": "exec",
        "fn": lambda: print("[INFO] No ARP neighbors found."),
        "args": [],
        "result": "arpscan_display_ok",
        "when": lambda job, meta, ctx: not bool(ctx.get("neighbors")),
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
PORT_SCAN_STEPS_PRE = (
    CONNECTED_INTERFACE_SELECTION_PRE +
    PORT_SCAN_PRE
)
    
# ============================================================
# PIPELINE STATES
# ============================================================

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {

    "ANALYZE_NETWORK": {
        "pipeline": [
            *CONNECTED_INTERFACE_SELECTION_PRE,
            *ANALYZE_NETWORK_EXEC,
        ],
        "label": "ANALYZE_COMPLETE",
        "success_key": "analysis_ok",
    },

    "ARP_SCAN": {
        "pipeline": [
            *ARP_SCAN_EXEC,
        ],
        "label": "ARP_SCAN_COMPLETE",
        "success_key": "arpscan_ok",
    },
    
    "PORT_SCAN": {
        "pipeline": [
            *PORT_SCAN_STEPS_PRE,
            *PORT_SCAN_EXEC,
        ],
        "label": "PORTSCAN_COMPLETE",
        "success_key": "portscan_display_ok",
    },

    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "DONE",
        "success_key": "ok",
    },
}
