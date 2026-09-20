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

TEMPERATURE_WARNING_KEY = "temperature_warning"
MEMORY_USAGE_WARNING_KEY = "memory_usage_warning"


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
            TEMPERATURE_WARNING_KEY: (int, float),
            MEMORY_USAGE_WARNING_KEY: (int, float),
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
            lambda job, meta, ctx: ["Key", "Value"],
            lambda job, meta, ctx: "System Summary",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("system_summary")),
    },
]


CPU_INFORMATION_EXEC = [
    {
        "phase": "exec",
        "fn": get_cpu_info,
        "args": [],
        "result": "cpu_info",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("cpu_info", []),
            lambda job, meta, ctx: ["Key", "Value"],
            lambda job, meta, ctx: "CPU Information",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("cpu_info")),
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
            lambda job, meta, ctx: ["Metric", "Value", "Status"],
            lambda job, meta, ctx: "Memory Status",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("memory_status")),
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
            lambda job, meta, ctx: ["Sensor", "Temperature", "Status"],
            lambda job, meta, ctx: "System Temperatures",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("temperature_status")),
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
            lambda job, meta, ctx: ["Key", "Value"],
            lambda job, meta, ctx: "Battery Health",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("battery_health")),
    },
]


HARDWARE_DEVICES_EXEC = [
    {
        "phase": "exec",
        "fn": get_hardware_devices,
        "args": [],
        "result": "hardware_devices",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("hardware_devices", []),
            lambda job, meta, ctx: ["Type", "Device"],
            lambda job, meta, ctx: "Hardware Devices",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("hardware_devices")),
    },
]


SYSTEM_ERRORS_EXEC = [
    {
        "phase": "exec",
        "fn": get_system_errors,
        "args": [],
        "result": "system_errors",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("system_errors", []),
            lambda job, meta, ctx: ["Source", "Message", "Status"],
            lambda job, meta, ctx: "System Errors",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("system_errors")),
    },
]


FULL_DIAGNOSTIC_EXEC = [
    {
        "phase": "exec",
        "fn": get_full_diagnostic_report,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][TEMPERATURE_WARNING_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][MEMORY_USAGE_WARNING_KEY],
        ],
        "result": "diagnostic_report",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("diagnostic_report", []),
            lambda job, meta, ctx: ["Check", "Result", "Status"],
            lambda job, meta, ctx: "Full Diagnostic Report",
        ],
        "result": "ok",
        "when": lambda job, meta, ctx: bool(ctx.get("diagnostic_report")),
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
    "SYSTEM_SUMMARY": {
        "pipeline": [
            *SYSTEM_SUMMARY_EXEC,
        ],
        "label": "SYSTEM_SUMMARY_COMPLETE",
        "success_key": "ok",
    },
    "CPU_INFORMATION": {
        "pipeline": [
            *CPU_INFORMATION_EXEC,
        ],
        "label": "CPU_INFORMATION_COMPLETE",
        "success_key": "ok",
    },
    "MEMORY_STATUS": {
        "pipeline": [
            *MEMORY_STATUS_EXEC,
        ],
        "label": "MEMORY_STATUS_COMPLETE",
        "success_key": "ok",
    },
    "TEMPERATURE_STATUS": {
        "pipeline": [
            *TEMPERATURE_STATUS_EXEC,
        ],
        "label": "TEMPERATURE_STATUS_COMPLETE",
        "success_key": "ok",
    },
    "BATTERY_HEALTH": {
        "pipeline": [
            *BATTERY_HEALTH_EXEC,
        ],
        "label": "BATTERY_HEALTH_COMPLETE",
        "success_key": "ok",
    },
    "HARDWARE_DEVICES": {
        "pipeline": [
            *HARDWARE_DEVICES_EXEC,
        ],
        "label": "HARDWARE_DEVICES_COMPLETE",
        "success_key": "ok",
    },
    "SYSTEM_ERRORS": {
        "pipeline": [
            *SYSTEM_ERRORS_EXEC,
        ],
        "label": "SYSTEM_ERRORS_COMPLETE",
        "success_key": "ok",
    },
    "FULL_DIAGNOSTIC": {
        "pipeline": [
            *FULL_DIAGNOSTIC_EXEC,
        ],
        "label": "FULL_DIAGNOSTIC_COMPLETE",
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