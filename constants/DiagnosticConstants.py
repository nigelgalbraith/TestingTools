# DiagnosticConstants.py
from __future__ import annotations

from typing import Any, Dict

from modules.diagnostic_utils import (
    get_battery_health,
    get_cpu_info,
    get_diagnostic_status,
    get_full_diagnostic_report,
    get_hardware_devices,
    get_memory_status,
    get_system_errors,
    get_system_summary,
    get_temperature_status,
)
from modules.display_utils import (
    display_config_doc,
    print_dict_table,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

CONFIG_PATH = "config/DiagnosticConfig.json"
TOOL_TYPE = "Diagnostics"
CONFIG_DOC = "doc/DiagnosticDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

GENERAL_KEY = "general"
CPU_KEY = "cpu"
CPU_FIELDS_KEY = "fields"
COMMAND_TIMEOUT_KEY = "command_timeout"
KERNEL_ERROR_LIMIT_KEY = "kernel_error_limit"

TEMPERATURE_WARNING_KEY = "temperature_warning"
MEMORY_USAGE_WARNING_KEY = "memory_usage_warning"


# ---------------------------------------------------------------------
# VALIDATION CONFIG
# ---------------------------------------------------------------------

VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        GENERAL_KEY: dict,
        CPU_KEY: dict,
    },
}


# ---------------------------------------------------------------------
# SECONDARY VALIDATION
# ---------------------------------------------------------------------

SECONDARY_VALIDATION: Dict[str, Any] = {
    GENERAL_KEY: {
        "required_job_fields": {
            TEMPERATURE_WARNING_KEY: (int, float),
            MEMORY_USAGE_WARNING_KEY: (int, float),
            COMMAND_TIMEOUT_KEY: (int, float),
            KERNEL_ERROR_LIMIT_KEY: int,
        },
        "allow_empty": False,
    },
    CPU_KEY: {
        "required_job_fields": {CPU_FIELDS_KEY: dict},
        "allow_empty": False,
    },
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
    "fn": get_diagnostic_status,
    "args": [],
    "id_field": "diagnostic",
    "active_rule": {
        "field": "ready",
        "equals": True,
    },
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = [
    "pciutils",
    "usbutils",
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
        "title": "Select a Diagnostic operation",
    },
    "System summary": {
        "verb": "system",
        "prompt": "Show system summary? [y/n]: ",
        "execute_state": "SYSTEM_SUMMARY",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "CPU information": {
        "verb": "cpu",
        "prompt": "Show CPU information? [y/n]: ",
        "execute_state": "CPU_INFORMATION",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Memory status": {
        "verb": "memory",
        "prompt": "Show memory status? [y/n]: ",
        "execute_state": "MEMORY_STATUS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Temperatures": {
        "verb": "temperature",
        "prompt": "Check system temperatures? [y/n]: ",
        "execute_state": "TEMPERATURE_STATUS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Battery health": {
        "verb": "battery",
        "prompt": "Check battery health? [y/n]: ",
        "execute_state": "BATTERY_HEALTH",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Hardware devices": {
        "verb": "hardware",
        "prompt": "Show detected hardware devices? [y/n]: ",
        "execute_state": "HARDWARE_DEVICES",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Check system errors": {
        "verb": "errors",
        "prompt": "Check system and kernel errors? [y/n]: ",
        "execute_state": "SYSTEM_ERRORS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Full diagnostic report": {
        "verb": "full",
        "prompt": "Run full system diagnostic? [y/n]: ",
        "execute_state": "FULL_DIAGNOSTIC",
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
# EXEC PHASE BLOCKS
# ---------------------------------------------------------------------

SYSTEM_SUMMARY_EXEC = [
    {
        "phase": "exec",
        "fn": get_system_summary,
        "args": [],
        "result": "system_summary",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("system_summary", []),
            ["Key", "Value"],
            lambda job, meta, ctx: "System Summary",
        ],
        "result": 'print_dict_table_result',
    },
]


CPU_INFORMATION_EXEC = [
    {
        "phase": "exec",
        "fn": get_cpu_info,
        "args": [lambda job, meta, ctx: meta[CPU_KEY][CPU_FIELDS_KEY], lambda job, meta, ctx: meta[GENERAL_KEY][COMMAND_TIMEOUT_KEY]],
        "result": "cpu_info",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("cpu_info", []),
            ["Key", "Value"],
            lambda job, meta, ctx: "CPU Information",
        ],
        "result": 'print_dict_table_result',
    },
]


MEMORY_STATUS_EXEC = [
    {
        "phase": "exec",
        "fn": get_memory_status,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][MEMORY_USAGE_WARNING_KEY],
        ],
        "result": "memory_status",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("memory_status", []),
            ["Metric", "Value", "Status"],
            lambda job, meta, ctx: "Memory Status",
        ],
        "result": 'print_dict_table_result',
    },
]


TEMPERATURE_STATUS_EXEC = [
    {
        "phase": "exec",
        "fn": get_temperature_status,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][TEMPERATURE_WARNING_KEY],
        ],
        "result": "temperature_status",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("temperature_status", []),
            ["Sensor", "Temperature", "Status"],
            lambda job, meta, ctx: "System Temperatures",
        ],
        "result": 'print_dict_table_result',
    },
]


BATTERY_HEALTH_EXEC = [
    {
        "phase": "exec",
        "fn": get_battery_health,
        "args": [],
        "result": "battery_health",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("battery_health", []),
            ["Key", "Value"],
            lambda job, meta, ctx: "Battery Health",
        ],
        "result": 'print_dict_table_result',
    },
]


HARDWARE_DEVICES_EXEC = [
    {
        "phase": "exec",
        "fn": get_hardware_devices,
        "args": [lambda job, meta, ctx: meta[GENERAL_KEY][COMMAND_TIMEOUT_KEY]],
        "result": "hardware_devices",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("hardware_devices", []),
            ["Type", "Device"],
            lambda job, meta, ctx: "Hardware Devices",
        ],
        "result": 'print_dict_table_result',
    },
]


SYSTEM_ERRORS_EXEC = [
    {
        "phase": "exec",
        "fn": get_system_errors,
        "args": [lambda job, meta, ctx: meta[GENERAL_KEY][COMMAND_TIMEOUT_KEY], lambda job, meta, ctx: meta[GENERAL_KEY][KERNEL_ERROR_LIMIT_KEY]],
        "result": "system_errors",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("system_errors", []),
            ["Source", "Message", "Status"],
            lambda job, meta, ctx: "System Errors",
        ],
        "result": 'print_dict_table_result',
    },
]


FULL_DIAGNOSTIC_EXEC = [
    {
        "phase": "exec",
        "fn": get_full_diagnostic_report,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][TEMPERATURE_WARNING_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][MEMORY_USAGE_WARNING_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][COMMAND_TIMEOUT_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][KERNEL_ERROR_LIMIT_KEY],
        ],
        "result": "diagnostic_report",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("diagnostic_report", []),
            ["Check", "Result", "Status"],
            lambda job, meta, ctx: "Full Diagnostic Report",
        ],
        "result": 'print_dict_table_result',
    },
]


SHOW_CONFIG_DOC_EXEC = [
    {
        "phase": "exec",
        "fn": display_config_doc,
        "args": [CONFIG_DOC],
        "result": 'display_config_doc_result',
    },
]


# ---------------------------------------------------------------------
# PIPELINE STATES
# ---------------------------------------------------------------------

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "SYSTEM_SUMMARY": {
        "pipeline": [
            *SYSTEM_SUMMARY_EXEC,
        ],
        "label": "SYSTEM_SUMMARY_COMPLETE",
    },
    "CPU_INFORMATION": {
        "pipeline": [
            *CPU_INFORMATION_EXEC,
        ],
        "label": "CPU_INFORMATION_COMPLETE",
    },
    "MEMORY_STATUS": {
        "pipeline": [
            *MEMORY_STATUS_EXEC,
        ],
        "label": "MEMORY_STATUS_COMPLETE",
    },
    "TEMPERATURE_STATUS": {
        "pipeline": [
            *TEMPERATURE_STATUS_EXEC,
        ],
        "label": "TEMPERATURE_STATUS_COMPLETE",
    },
    "BATTERY_HEALTH": {
        "pipeline": [
            *BATTERY_HEALTH_EXEC,
        ],
        "label": "BATTERY_HEALTH_COMPLETE",
    },
    "HARDWARE_DEVICES": {
        "pipeline": [
            *HARDWARE_DEVICES_EXEC,
        ],
        "label": "HARDWARE_DEVICES_COMPLETE",
    },
    "SYSTEM_ERRORS": {
        "pipeline": [
            *SYSTEM_ERRORS_EXEC,
        ],
        "label": "SYSTEM_ERRORS_COMPLETE",
    },
    "FULL_DIAGNOSTIC": {
        "pipeline": [
            *FULL_DIAGNOSTIC_EXEC,
        ],
        "label": "FULL_DIAGNOSTIC_COMPLETE",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "DONE",
    },
}