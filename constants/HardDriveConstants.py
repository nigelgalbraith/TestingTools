# HardDriveConstants.py
from __future__ import annotations

from modules.state_machine_utils import result_available

from typing import Any, Dict

from modules.display_utils import (
    display_config_doc,
    print_dict_table,
)
from modules.harddrive_utils import (
    detect_windows_installations,
    get_disk_overview,
    get_drive_diagnostic_status,
    get_drive_information,
    get_drive_list,
    get_encryption_status,
    get_filesystem_usage,
    get_full_drive_diagnostic,
    get_smart_attributes,
    get_smart_health,
    get_smart_test_history,
    get_temperature_wear,
    run_long_smart_test,
    run_read_benchmark,
    run_short_smart_test,
    select_drive,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

CONFIG_PATH = "config/HardDriveConfig.json"
TOOL_TYPE = "Hard Drive Tools"
CONFIG_DOC = "doc/HardDriveDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

GENERAL_KEY = "general"

TEMPERATURE_WARNING_KEY = "temperature_warning"
WEAR_WARNING_KEY = "wear_warning"
BENCHMARK_SIZE_MB_KEY = "benchmark_size_mb"
DISK_USAGE_WARNING_KEY = "disk_usage_warning"


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
            WEAR_WARNING_KEY: (int, float),
            BENCHMARK_SIZE_MB_KEY: int,
            DISK_USAGE_WARNING_KEY: (int, float),
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
    "fn": get_drive_diagnostic_status,
    "args": [],
    "id_field": "harddrive",
    "active_rule": {
        "field": "ready",
        "equals": True,
    },
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = [
    "smartmontools",
    "nvme-cli",
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
        "title": "Select a Hard Drive operation",
    },
    "List drives": {
        "verb": "list",
        "prompt": "List detected drives? [y/n]: ",
        "execute_state": "LIST_DRIVES",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Disk and partition overview": {
        "verb": "overview",
        "prompt": "Show disk and partition overview? [y/n]: ",
        "execute_state": "DISK_OVERVIEW",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Filesystem usage": {
        "verb": "filesystem",
        "prompt": "Show filesystem usage? [y/n]: ",
        "execute_state": "FILESYSTEM_USAGE",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Detect Windows installations": {
        "verb": "windows",
        "prompt": "Search for Windows installations? [y/n]: ",
        "execute_state": "WINDOWS_INSTALLATIONS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Check encryption / BitLocker": {
        "verb": "encryption",
        "prompt": "Check drive for encryption or BitLocker? [y/n]: ",
        "execute_state": "ENCRYPTION_STATUS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Drive information": {
        "verb": "info",
        "prompt": "Show drive information? [y/n]: ",
        "execute_state": "DRIVE_INFORMATION",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "SMART health": {
        "verb": "smart-health",
        "prompt": "Check SMART health? [y/n]: ",
        "execute_state": "SMART_HEALTH",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "SMART attributes": {
        "verb": "smart-attributes",
        "prompt": "Show SMART attributes? [y/n]: ",
        "execute_state": "SMART_ATTRIBUTES",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Temperature and wear": {
        "verb": "wear",
        "prompt": "Check drive temperature and wear? [y/n]: ",
        "execute_state": "TEMPERATURE_WEAR",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "SMART self-test history": {
        "verb": "smart-history",
        "prompt": "Show SMART self-test history? [y/n]: ",
        "execute_state": "SMART_TEST_HISTORY",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Run short SMART test": {
        "verb": "smart-short",
        "prompt": "Run short SMART test? [y/n]: ",
        "execute_state": "SMART_SHORT_TEST",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Run long SMART test": {
        "verb": "smart-long",
        "prompt": "Run long SMART test? [y/n]: ",
        "execute_state": "SMART_LONG_TEST",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Read benchmark": {
        "verb": "benchmark",
        "prompt": "Run read benchmark? [y/n]: ",
        "execute_state": "READ_BENCHMARK",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Full hard drive diagnostic": {
        "verb": "full",
        "prompt": "Run full hard drive diagnostic? [y/n]: ",
        "execute_state": "FULL_DRIVE_DIAGNOSTIC",
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
            lambda job, meta, ctx: "Select a drive",
            lambda job, meta, ctx: ctx.get("drive_list", []),
        ],
        "result": "selected_drive",
        "when": lambda job, meta, ctx: result_available(ctx, 'drive_list') and (bool(ctx.get('drive_list'))),
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
            [
                "Device",
                "Model",
                "Size",
                "Type",
                "Interface",
            ],
            lambda job, meta, ctx: "Detected Drives",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'drive_list') and (bool(ctx.get('drive_list'))),
    },
]


DISK_OVERVIEW_EXEC = [
    {
        "phase": "exec",
        "fn": get_disk_overview,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
        ],
        "result": "disk_overview",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("disk_overview", []),
            [
                "Device",
                "Type",
                "Size",
                "Filesystem",
                "Mount",
            ],
            lambda job, meta, ctx: "Disk and Partition Overview",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'disk_overview') and (bool(ctx.get('disk_overview'))),
    },
]


FILESYSTEM_USAGE_EXEC = [
    {
        "phase": "exec",
        "fn": get_filesystem_usage,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
            lambda job, meta, ctx: meta[GENERAL_KEY][DISK_USAGE_WARNING_KEY],
        ],
        "result": "filesystem_usage",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("filesystem_usage", []),
            [
                "Filesystem",
                "Size",
                "Used",
                "Available",
                "Usage",
                "Status",
            ],
            lambda job, meta, ctx: "Filesystem Usage",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'filesystem_usage') and (bool(ctx.get('filesystem_usage'))),
    },
]


WINDOWS_INSTALLATIONS_EXEC = [
    {
        "phase": "exec",
        "fn": detect_windows_installations,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
        ],
        "result": "windows_installations",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("windows_installations", []),
            [
                "Device",
                "Filesystem",
                "Windows",
                "Mount",
            ],
            lambda job, meta, ctx: "Windows Installations",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'windows_installations') and (bool(ctx.get('windows_installations'))),
    },
]


ENCRYPTION_STATUS_EXEC = [
    {
        "phase": "exec",
        "fn": get_encryption_status,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
        ],
        "result": "encryption_status",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("encryption_status", []),
            [
                "Device",
                "Filesystem",
                "Encryption",
                "Status",
            ],
            lambda job, meta, ctx: "Encryption / BitLocker Status",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'encryption_status') and (bool(ctx.get('encryption_status'))),
    },
]


DRIVE_INFORMATION_EXEC = [
    {
        "phase": "exec",
        "fn": get_drive_information,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
        ],
        "result": "drive_information",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("drive_information", []),
            [
                "Device",
                "Model",
                "Serial",
                "Firmware",
                "Capacity",
                "Interface",
            ],
            lambda job, meta, ctx: "Drive Information",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'drive_information') and (bool(ctx.get('drive_information'))),
    },
]


SMART_HEALTH_EXEC = [
    {
        "phase": "exec",
        "fn": get_smart_health,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
        ],
        "result": "smart_health",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("smart_health", []),
            [
                "Device",
                "Health",
                "Status",
            ],
            lambda job, meta, ctx: "SMART Health",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'smart_health') and (bool(ctx.get('smart_health'))),
    },
]


SMART_ATTRIBUTES_EXEC = [
    {
        "phase": "exec",
        "fn": get_smart_attributes,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
        ],
        "result": "smart_attributes",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("smart_attributes", []),
            [
                "Device",
                "Attribute",
                "Value",
                "Raw",
                "Status",
            ],
            lambda job, meta, ctx: "SMART Attributes",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'smart_attributes') and (bool(ctx.get('smart_attributes'))),
    },
]


TEMPERATURE_WEAR_EXEC = [
    {
        "phase": "exec",
        "fn": get_temperature_wear,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
            lambda job, meta, ctx: meta[GENERAL_KEY][TEMPERATURE_WARNING_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][WEAR_WARNING_KEY],
        ],
        "result": "temperature_wear",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("temperature_wear", []),
            [
                "Device",
                "Temperature",
                "Wear",
                "Status",
            ],
            lambda job, meta, ctx: "Temperature and Wear",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'temperature_wear') and (bool(ctx.get('temperature_wear'))),
    },
]


SMART_TEST_HISTORY_EXEC = [
    {
        "phase": "exec",
        "fn": get_smart_test_history,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
        ],
        "result": "smart_test_history",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("smart_test_history", []),
            [
                "Device",
                "Test",
                "Result",
                "Lifetime Hours",
            ],
            lambda job, meta, ctx: "SMART Self-test History",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'smart_test_history') and (bool(ctx.get('smart_test_history'))),
    },
]


SMART_SHORT_TEST_EXEC = [
    {
        "phase": "exec",
        "fn": run_short_smart_test,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
        ],
        "result": "smart_short_test",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("smart_short_test", []),
            [
                "Device",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "Short SMART Test",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'smart_short_test') and (bool(ctx.get('smart_short_test'))),
    },
]


SMART_LONG_TEST_EXEC = [
    {
        "phase": "exec",
        "fn": run_long_smart_test,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
        ],
        "result": "smart_long_test",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("smart_long_test", []),
            [
                "Device",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "Long SMART Test",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'smart_long_test') and (bool(ctx.get('smart_long_test'))),
    },
]


READ_BENCHMARK_EXEC = [
    {
        "phase": "exec",
        "fn": run_read_benchmark,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
            lambda job, meta, ctx: meta[GENERAL_KEY][BENCHMARK_SIZE_MB_KEY],
        ],
        "result": "read_benchmark",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("read_benchmark", []),
            [
                "Device",
                "Read Speed",
                "Status",
            ],
            lambda job, meta, ctx: "Read Benchmark",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'read_benchmark') and (bool(ctx.get('read_benchmark'))),
    },
]


FULL_DRIVE_DIAGNOSTIC_EXEC = [
    {
        "phase": "exec",
        "fn": get_full_drive_diagnostic,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_drive"),
            lambda job, meta, ctx: meta[GENERAL_KEY][TEMPERATURE_WARNING_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][WEAR_WARNING_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][DISK_USAGE_WARNING_KEY],
        ],
        "result": "full_drive_diagnostic",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_drive') and (bool(ctx.get('selected_drive'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("full_drive_diagnostic", []),
            [
                "Device",
                "Check",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "Full Hard Drive Diagnostic",
        ],
        "result": 'print_dict_table_result',
        "when": lambda job, meta, ctx: result_available(ctx, 'full_drive_diagnostic') and (bool(ctx.get('full_drive_diagnostic'))),
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
    "LIST_DRIVES": {
        "pipeline": [
            *LIST_DRIVES_EXEC,
        ],
        "label": "LIST_DRIVES_COMPLETE",
    },
    "DISK_OVERVIEW": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *DISK_OVERVIEW_EXEC,
        ],
        "label": "DISK_OVERVIEW_COMPLETE",
    },
    "FILESYSTEM_USAGE": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *FILESYSTEM_USAGE_EXEC,
        ],
        "label": "FILESYSTEM_USAGE_COMPLETE",
    },
    "WINDOWS_INSTALLATIONS": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *WINDOWS_INSTALLATIONS_EXEC,
        ],
        "label": "WINDOWS_INSTALLATIONS_COMPLETE",
    },
    "ENCRYPTION_STATUS": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *ENCRYPTION_STATUS_EXEC,
        ],
        "label": "ENCRYPTION_STATUS_COMPLETE",
    },
    "DRIVE_INFORMATION": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *DRIVE_INFORMATION_EXEC,
        ],
        "label": "DRIVE_INFORMATION_COMPLETE",
    },
    "SMART_HEALTH": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *SMART_HEALTH_EXEC,
        ],
        "label": "SMART_HEALTH_COMPLETE",
    },
    "SMART_ATTRIBUTES": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *SMART_ATTRIBUTES_EXEC,
        ],
        "label": "SMART_ATTRIBUTES_COMPLETE",
    },
    "TEMPERATURE_WEAR": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *TEMPERATURE_WEAR_EXEC,
        ],
        "label": "TEMPERATURE_WEAR_COMPLETE",
    },
    "SMART_TEST_HISTORY": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *SMART_TEST_HISTORY_EXEC,
        ],
        "label": "SMART_TEST_HISTORY_COMPLETE",
    },
    "SMART_SHORT_TEST": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *SMART_SHORT_TEST_EXEC,
        ],
        "label": "SMART_SHORT_TEST_COMPLETE",
    },
    "SMART_LONG_TEST": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *SMART_LONG_TEST_EXEC,
        ],
        "label": "SMART_LONG_TEST_COMPLETE",
    },
    "READ_BENCHMARK": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *READ_BENCHMARK_EXEC,
        ],
        "label": "READ_BENCHMARK_COMPLETE",
    },
    "FULL_DRIVE_DIAGNOSTIC": {
        "pipeline": [
            *DRIVE_SELECTION_PRE,
            *FULL_DRIVE_DIAGNOSTIC_EXEC,
        ],
        "label": "FULL_DRIVE_DIAGNOSTIC_COMPLETE",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "DONE",
    },
}