# NetworkConstants.py
from __future__ import annotations

from typing import Any, Dict

from modules.display_utils import (
    display_config_doc,
    print_dict_table,
    select_from_list,
)
from modules.network_utils import (
    analyze_interface,
    get_connected_interfaces,
    get_interface_status,
    get_interfaces,
)
from modules.portscan_utils import (
    get_arp_neighbor_rows,
    get_arp_neighbors,
    scan_tcp_ports,
    build_target_choices,
    prompt_for_selected_target,
    display_no_arp_neighbors,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

CONFIG_PATH = "config/NetworkConfig.json"
TOOL_TYPE = "NetworkScanner"
CONFIG_DOC = "doc/NetworkDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

GENERAL_KEY = "general"
PORT_SCAN_KEY = "port_scan"
PORTS_KEY = "ports"
PORT_INFO_KEY = "port_info"
TIMEOUT_KEY = "timeout"
WORKERS_KEY = "workers"


# ---------------------------------------------------------------------
# VALIDATION CONFIG
# ---------------------------------------------------------------------

VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        GENERAL_KEY: dict,
        PORT_SCAN_KEY: dict,
    },
}


# ---------------------------------------------------------------------
# SECONDARY VALIDATION
# ---------------------------------------------------------------------

SECONDARY_VALIDATION: Dict[str, Any] = {
    PORT_SCAN_KEY: {
        "required_job_fields": {
            PORTS_KEY: list,
            PORT_INFO_KEY: dict,
            TIMEOUT_KEY: (int, float),
            WORKERS_KEY: int,
        },
        "allow_empty": False,
    }
}


# ---------------------------------------------------------------------
# USER REQUIREMENTS
# ---------------------------------------------------------------------

REQUIRED_USER = "root"

ACTIVE_LABEL = "CONNECTED"
INACTIVE_LABEL = "DISCONNECTED"


# ---------------------------------------------------------------------
# STATUS CHECK CONFIG
# ---------------------------------------------------------------------

STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": get_interface_status,
    "args": [],
    "id_field": "device",
    "active_rule": {"field": "state", "equals": "connected"},
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = [
    "network-manager",
    "iproute2",
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
    "_meta": {"title": "Select a Network operation"},
    "Analyze network": {
        "verb": "analyze",
        "prompt": "Analyze selected network interface? [y/n]: ",
        "execute_state": "ANALYZE_NETWORK",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": False,
        "skip_confirm": False,
    },
    "Show Neighbours": {
        "verb": "arp_scan",
        "prompt": "Run ARP scan? [y/n]: ",
        "execute_state": "ARP_SCAN",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Port scan host": {
        "verb": "portscan",
        "prompt": "Run TCP port scan? [y/n]: ",
        "execute_state": "PORT_SCAN",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": False,
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

INTERFACE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": get_interfaces,
        "args": [None],
        "result": "interfaces",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            "Select a network interface",
            "interfaces",
        ],
        "when": "interfaces",
        "result": "selected_interface",
    },
]

CONNECTED_INTERFACE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": get_connected_interfaces,
        "args": [None],
        "result": "interfaces",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            "Select a connected network interface",
            "interfaces",
        ],
        "when": "interfaces",
        "result": "selected_interface",
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
        "fn": build_target_choices,
        "args": ["neighbor_ips"],
        "result": "neighbor_choices",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            "Select a target",
            "neighbor_choices",
        ],
        "when": "neighbor_choices",
        "result": "selected_target",
    },
    {
        "phase": "pre",
        "fn": prompt_for_selected_target,
        "args": ["selected_target"],
        "when": "selected_target",
        "result": "target",
    },
]

# ---------------------------------------------------------------------
# EXEC PHASE BLOCKS
# ---------------------------------------------------------------------

ANALYZE_NETWORK_EXEC = [
    {
        "phase": "exec",
        "fn": analyze_interface,
        "args": ["selected_interface"],
        "when": "selected_interface",
        "result": "analysis_rows",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            "analysis_rows",
            ["Key", "Value"],
            "Interface Details",
        ],
        "when": "analysis_rows",
        "result": "analysis_ok",
    },
]


PORT_SCAN_EXEC = [
    {
        "phase": "exec",
        "fn": scan_tcp_ports,
        "args": [
            "target",
            "meta.port_scan.ports",
            "meta.port_scan.port_info",
            "meta.port_scan.timeout",
            "meta.port_scan.workers",
        ],
        "when": "target",
        "result": "open_ports",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            "open_ports",
            ["Port", "Service", "Note"],
            "Open TCP Ports",
        ],
        "when": "target",
        "result": "portscan_display_ok",
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
        "fn": print_dict_table,
        "args": [
            "neighbors",
            ["IP", "MAC", "Interface"],
            "ARP Neighbors",
        ],
        "when": "neighbors",
        "result": "arpscan_display_ok",
    },
    {
        "phase": "exec",
        "fn": display_no_arp_neighbors,
        "args": ["neighbors"],
        "result": "no_arp_neighbors_result",
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
# STEP GROUPS
# ---------------------------------------------------------------------

PORT_SCAN_STEPS_PRE = (
    CONNECTED_INTERFACE_SELECTION_PRE +
    PORT_SCAN_PRE
)

# ---------------------------------------------------------------------
# PIPELINE STATES
# ---------------------------------------------------------------------

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "ANALYZE_NETWORK": {
        "pipeline": [
            *CONNECTED_INTERFACE_SELECTION_PRE,
            *ANALYZE_NETWORK_EXEC,
        ],
        "label": "ANALYZE_COMPLETE",
    },
    "ARP_SCAN": {
        "pipeline": [
            *ARP_SCAN_EXEC,
        ],
        "label": "ARP_SCAN_COMPLETE",
    },
    "PORT_SCAN": {
        "pipeline": [
            *PORT_SCAN_STEPS_PRE,
            *PORT_SCAN_EXEC,
        ],
        "label": "PORTSCAN_COMPLETE",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "DONE",
    },
}
