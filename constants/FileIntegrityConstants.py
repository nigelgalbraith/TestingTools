# FileIntegrityConstants.py
from __future__ import annotations


from typing import Any, Dict

from modules.display_utils import (
    display_config_doc,
    print_dict_table,
)
from modules.file_integrity_utils import (
    compare_files,
    create_manifest,
    find_duplicate_files,
    get_integrity_status,
    hash_directory,
    hash_file,
    prompt_expected_hash,
    prompt_manifest_path,
    restore_integrity_permissions,
    select_file,
    verify_file_hash,
    verify_manifest,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

CONFIG_PATH = "config/FileIntegrityConfig.json"
TOOL_TYPE = "File Integrity"
CONFIG_DOC = "doc/FileIntegrityDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

GENERAL_KEY = "general"
ALGORITHM_KEY = "algorithm"
TARGET_DIR_KEY = "target_dir"
MANIFEST_DIR_KEY = "manifest_dir"


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
            ALGORITHM_KEY: str,
            TARGET_DIR_KEY: str,
            MANIFEST_DIR_KEY: str,
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
    "fn": get_integrity_status,
    "args": [
        lambda job, meta, ctx: meta[GENERAL_KEY][ALGORITHM_KEY],
        lambda job, meta, ctx: meta[GENERAL_KEY][TARGET_DIR_KEY],
        lambda job, meta, ctx: meta[GENERAL_KEY][MANIFEST_DIR_KEY],
    ],
    "id_field": "file_integrity",
    "active_rule": {
        "field": "ready",
        "equals": True,
    },
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = []


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
        "title": "Select a File Integrity operation",
    },
    "Hash file": {
        "verb": "hash",
        "prompt": "Hash the selected file? [y/n]: ",
        "execute_state": "HASH_FILE",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Verify file hash": {
        "verb": "verify",
        "prompt": "Verify the selected file hash? [y/n]: ",
        "execute_state": "VERIFY_FILE_HASH",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Hash directory": {
        "verb": "hash-directory",
        "prompt": "Hash the configured target directory? [y/n]: ",
        "execute_state": "HASH_DIRECTORY",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Compare files": {
        "verb": "compare-files",
        "prompt": "Compare the selected files? [y/n]: ",
        "execute_state": "COMPARE_FILES",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Find duplicate files": {
        "verb": "duplicates",
        "prompt": "Scan the configured target directory for duplicate files? [y/n]: ",
        "execute_state": "FIND_DUPLICATES",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Create checksum manifest": {
        "verb": "manifest",
        "prompt": "Create a checksum manifest for the configured target directory? [y/n]: ",
        "execute_state": "CREATE_MANIFEST",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Verify checksum manifest": {
        "verb": "verify-manifest",
        "prompt": "Verify the selected checksum manifest? [y/n]: ",
        "execute_state": "VERIFY_MANIFEST",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": False,
    },
    "Restore manifest permissions": {
        "verb": "permissions",
        "prompt": "Restore manifest files to the sudo user? [y/n]: ",
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

FILE_PRE = [
    {
        "phase": "pre",
        "fn": select_file,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][TARGET_DIR_KEY],
            lambda job, meta, ctx: "Select a file",
        ],
        "result": "selected_file",
    },
]


VERIFY_FILE_PRE = [
    {
        "phase": "pre",
        "fn": select_file,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][TARGET_DIR_KEY],
            lambda job, meta, ctx: "Select a file to verify",
        ],
        "result": "selected_file",
    },
    {
        "phase": "pre",
        "fn": prompt_expected_hash,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][ALGORITHM_KEY] if ctx.get("selected_file") else None,
        ],
        "result": "expected_hash",
    },
    {
        "phase": "pre",
        "fn": lambda file_path, expected_hash: bool(file_path and expected_hash),
        "args": [
            lambda job, meta, ctx: ctx.get("selected_file"),
            lambda job, meta, ctx: ctx.get("expected_hash"),
        ],
        "result": "verify_ready",
    },
]


FILE_PAIR_PRE = [
    {
        "phase": "pre",
        "fn": select_file,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][TARGET_DIR_KEY],
            lambda job, meta, ctx: "Select the first file",
        ],
        "result": "first_file",
    },
    {
        "phase": "pre",
        "fn": select_file,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][TARGET_DIR_KEY] if ctx.get("first_file") else None,
            lambda job, meta, ctx: "Select the second file",
        ],
        "result": "second_file",
    },
    {
        "phase": "pre",
        "fn": lambda first, second: bool(first and second),
        "args": [
            lambda job, meta, ctx: ctx.get("first_file"),
            lambda job, meta, ctx: ctx.get("second_file"),
        ],
        "result": "file_pair_ready",
    },
]


MANIFEST_PRE = [
    {
        "phase": "pre",
        "fn": prompt_manifest_path,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][MANIFEST_DIR_KEY],
        ],
        "result": "selected_manifest",
    },
]


# ---------------------------------------------------------------------
# EXEC PHASE BLOCKS
# ---------------------------------------------------------------------

HASH_FILE_EXEC = [
    {
        "phase": "exec",
        "fn": hash_file,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_file"),
            lambda job, meta, ctx: meta[GENERAL_KEY][ALGORITHM_KEY],
        ],
        "result": "hash_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("hash_result") or None,
            [
                "File",
                "Algorithm",
                "Hash",
            ],
            lambda job, meta, ctx: "File Hash",
        ],
        "result": 'print_dict_table_result',
    },
]


VERIFY_FILE_HASH_EXEC = [
    {
        "phase": "exec",
        "fn": verify_file_hash,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_file"),
            lambda job, meta, ctx: ctx.get("expected_hash"),
            lambda job, meta, ctx: meta[GENERAL_KEY][ALGORITHM_KEY],
        ],
        "result": "verify_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("verify_result") or None,
            [
                "File",
                "Expected",
                "Actual",
                "Status",
            ],
            lambda job, meta, ctx: "File Hash Verification",
        ],
        "result": 'print_dict_table_result',
    },
]


HASH_DIRECTORY_EXEC = [
    {
        "phase": "exec",
        "fn": hash_directory,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][TARGET_DIR_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][ALGORITHM_KEY],
        ],
        "result": "directory_hashes",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("directory_hashes") or None,
            [
                "File",
                "Hash",
            ],
            lambda job, meta, ctx: "Directory Hashes",
        ],
        "result": 'print_dict_table_result',
    },
]


COMPARE_FILES_EXEC = [
    {
        "phase": "exec",
        "fn": compare_files,
        "args": [
            lambda job, meta, ctx: ctx.get("first_file"),
            lambda job, meta, ctx: ctx.get("second_file"),
            lambda job, meta, ctx: meta[GENERAL_KEY][ALGORITHM_KEY],
        ],
        "result": "compare_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("compare_result") or None,
            [
                "File 1",
                "File 2",
                "Status",
            ],
            lambda job, meta, ctx: "File Comparison",
        ],
        "result": 'print_dict_table_result',
    },
]


FIND_DUPLICATES_EXEC = [
    {
        "phase": "exec",
        "fn": find_duplicate_files,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][TARGET_DIR_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][ALGORITHM_KEY],
        ],
        "result": "duplicates",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("duplicates") or None,
            [
                "Hash",
                "Count",
                "Files",
            ],
            lambda job, meta, ctx: "Duplicate Files",
        ],
        "result": 'print_dict_table_result',
    },
]


CREATE_MANIFEST_EXEC = [
    {
        "phase": "exec",
        "fn": create_manifest,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][TARGET_DIR_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][MANIFEST_DIR_KEY],
            lambda job, meta, ctx: meta[GENERAL_KEY][ALGORITHM_KEY],
        ],
        "result": "manifest_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("manifest_result") or None,
            [
                "Directory",
                "Manifest",
                "Files",
                "Status",
            ],
            lambda job, meta, ctx: "Checksum Manifest",
        ],
        "result": 'print_dict_table_result',
    },
]


VERIFY_MANIFEST_EXEC = [
    {
        "phase": "exec",
        "fn": verify_manifest,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_manifest"),
        ],
        "result": "manifest_verify",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("manifest_verify") or None,
            [
                "File",
                "Status",
            ],
            lambda job, meta, ctx: "Manifest Verification",
        ],
        "result": 'print_dict_table_result',
    },
]


RESTORE_PERMISSIONS_EXEC = [
    {
        "phase": "exec",
        "fn": restore_integrity_permissions,
        "args": [
            lambda job, meta, ctx: meta[GENERAL_KEY][MANIFEST_DIR_KEY],
        ],
        "result": "permissions_result",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("permissions_result") or None,
            [
                "Destination",
                "Result",
                "Status",
            ],
            lambda job, meta, ctx: "Manifest Permissions",
        ],
        "result": "permissions_ok",
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
    "HASH_FILE": {
        "pipeline": [
            *FILE_PRE,
            *HASH_FILE_EXEC,
        ],
        "label": "HASH_FILE_COMPLETE",
    },
    "VERIFY_FILE_HASH": {
        "pipeline": [
            *VERIFY_FILE_PRE,
            *VERIFY_FILE_HASH_EXEC,
        ],
        "label": "VERIFY_FILE_HASH_COMPLETE",
    },
    "HASH_DIRECTORY": {
        "pipeline": [
            *HASH_DIRECTORY_EXEC,
        ],
        "label": "HASH_DIRECTORY_COMPLETE",
    },
    "COMPARE_FILES": {
        "pipeline": [
            *FILE_PAIR_PRE,
            *COMPARE_FILES_EXEC,
        ],
        "label": "COMPARE_FILES_COMPLETE",
    },
    "FIND_DUPLICATES": {
        "pipeline": [
            *FIND_DUPLICATES_EXEC,
        ],
        "label": "FIND_DUPLICATES_COMPLETE",
    },
    "CREATE_MANIFEST": {
        "pipeline": [
            *CREATE_MANIFEST_EXEC,
            *RESTORE_PERMISSIONS_EXEC,
        ],
        "label": "CREATE_MANIFEST_COMPLETE",
    },
    "VERIFY_MANIFEST": {
        "pipeline": [
            *MANIFEST_PRE,
            *VERIFY_MANIFEST_EXEC,
        ],
        "label": "VERIFY_MANIFEST_COMPLETE",
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