# EmailConstants.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict

from modules.json_utils import load_json, validate_json_schema
from modules.display_utils import (
    display_config_doc,
    print_dict_table,
    select_from_list,
    display_readme,
)
from modules.email_utils import (
    convert_pst_to_eml,
    convert_pst_to_mbox,
    extract_pst_attachments,
    extract_pst_contacts,
    get_email_details,
    get_pst_summary,
    select_email,
    select_email_folder,
    extract_pst_calendars,
    list_email_search_configs,
    run_email_searches,
    display_email_search_results,
    load_email_search_results,
    select_pst_files,
    run_pst_files,
    display_email_details,
    get_extracted_email_files,
    get_extracted_mbox_files,
    get_mbox_messages,
    get_mbox_email_details,
)

from modules.file_utils import (
    get_directory_status,
    get_files_by_extension,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

EMAIL_SEARCH_SCHEMA_PATH = "schemas/EmailSearchSchema.json"
CONFIG_PATH = "config/EmailConfig.json"
TOOL_TYPE = "Email"
CONFIG_DOC = "doc/EmailDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

LOCATIONS_KEY = "locations"
PST_DIR = "pst_dir"
MBOX_DIR = "mbox_dir"
EML_DIR = "eml_dir"
CONTACTS_DIR = "contacts_dir"
CALENDARS_DIR = "calendars_dir"
ATTACHMENTS_DIR = "attachments_dir"
SEARCH_README = "search_readme_path"
SEARCH_CONFIGS_KEY = "search_configs"

# ---------------------------------------------------------------------
# VALIDATION CONFIG
# ---------------------------------------------------------------------


VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        LOCATIONS_KEY: dict,
        SEARCH_CONFIGS_KEY: list,
    },
}


# ---------------------------------------------------------------------
# SECONDARY VALIDATION
# ---------------------------------------------------------------------

SECONDARY_VALIDATION: Dict[str, Any] = {
    LOCATIONS_KEY: {
        "required_job_fields": {
            PST_DIR: str,
            MBOX_DIR: str,
            EML_DIR: str,
            CONTACTS_DIR: str,
            CALENDARS_DIR: str,
            ATTACHMENTS_DIR: str,
            SEARCH_README: str,
        },
        "allow_empty": False,
    }
}


# ---------------------------------------------------------------------
# USER REQUIREMENTS
# ---------------------------------------------------------------------

REQUIRED_USER = "standard"

ACTIVE_LABEL = "DATA PRESENT"
INACTIVE_LABEL = "NO DATA PRESENT"


# ---------------------------------------------------------------------
# STATUS CHECK CONFIG
# ---------------------------------------------------------------------

STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": get_directory_status,
    "args": [
        lambda job, meta, ctx: meta[LOCATIONS_KEY][PST_DIR],
    ],
    "id_field": "location",
    "active_rule": {"field": "state", "equals": "data_present"},
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = [
    "pst-utils",
    "python3-jsonschema"
]


# ---------------------------------------------------------------------
# PLAN CONFIG
# ---------------------------------------------------------------------

PLAN_COLUMN_ORDER = [
    LOCATIONS_KEY,
]


OPTIONAL_PLAN_COLUMNS = {}



# ---------------------------------------------------------------------
# ACTIONS
# ---------------------------------------------------------------------


ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": "Select an Email operation"},
    "View PST summary": {
        "verb": "summary",
        "prompt": "View PST summary? [y/n]: ",
        "execute_state": "VIEW_PST_SUMMARY",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Convert PST to mbox": {
        "verb": "convert",
        "prompt": "Convert PST file to mbox? [y/n]: ",
        "execute_state": "CONVERT_PST_MBOX",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": False,
        "skip_confirm": False,
    },
    "Convert PST to EML": {
        "verb": "convert",
        "prompt": "Convert PST file to EML? [y/n]: ",
        "execute_state": "CONVERT_PST_EML",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": False,
        "skip_confirm": False,
    },
    "Extract contacts": {
        "verb": "extract",
        "prompt": "Extract contacts? [y/n]: ",
        "execute_state": "EXTRACT_CONTACTS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": False,
        "skip_confirm": False,
    },
    "Extract calendars": {
        "verb": "extract",
        "prompt": "Extract calendars? [y/n]: ",
        "execute_state": "EXTRACT_CALENDARS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": False,
        "skip_confirm": False,
    },
    "Extract attachments": {
        "verb": "extract",
        "prompt": "Extract attachments? [y/n]: ",
        "execute_state": "EXTRACT_ATTACHMENTS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": False,
        "skip_confirm": False,
    },
    "View MBOX emails": {
        "verb": "view",
        "prompt": "View MBOX emails? [y/n]: ",
        "execute_state": "VIEW_MBOX",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "View EML emails": {
        "verb": "view",
        "prompt": "View EML emails? [y/n]: ",
        "execute_state": "VIEW_EML",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Search emails": {
        "verb": "search",
        "prompt": "Search emails? [y/n]: ",
        "execute_state": "SEARCH_EMAILS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "View Search Results": {
        "verb": "view_search_results",
        "prompt": "View saved email search results? [y/n]: ",
        "execute_state": "VIEW_SEARCH_RESULTS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "View Email Search Help": {
        "verb": "search_help",
        "prompt": "View email search help? [y/n]: ",
        "execute_state": "SHOW_EMAIL_SEARCH_HELP",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
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

PST_SINGLE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": get_files_by_extension,
        "args": [
            lambda job, meta, ctx: meta[LOCATIONS_KEY][PST_DIR],
            lambda job, meta, ctx: ".pst",
        ],
        "result": "pst_files",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select a PST file",
            lambda job, meta, ctx: ctx.get("pst_files", []),
        ],
        "result": "selected_pst",
    },
]


PST_FILE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": select_pst_files,
        "args": [
            lambda job, meta, ctx: meta[LOCATIONS_KEY][PST_DIR],
        ],
        "result": "selected_pst",
    },
]




VIEW_MBOX_PRE = [
    {
        "phase": "pre",
        "fn": get_extracted_mbox_files,
        "args": [
            lambda job, meta, ctx: meta[LOCATIONS_KEY][MBOX_DIR],
        ],
        "result": "mbox_files",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select an MBOX file",
            lambda job, meta, ctx: ctx.get("mbox_files") or [],
        ],
        "result": "selected_mbox",
    },
    {
        "phase": "pre",
        "fn": get_mbox_messages,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_mbox"),
        ],
        "result": "mbox_messages",
    },
    {
        "phase": "pre",
        "fn": select_email,
        "args": [
            lambda job, meta, ctx: "Select an MBOX email",
            lambda job, meta, ctx: ctx.get("mbox_messages") or [],
        ],
        "result": "selected_mbox_message",
    },
]

VIEW_EML_PRE = [
    {
        "phase": "pre",
        "fn": get_extracted_email_files,
        "args": [
            lambda job, meta, ctx: meta[LOCATIONS_KEY][EML_DIR],
        ],
        "result": "email_files",
    },
    {
        "phase": "pre",
        "fn": select_email_folder,
        "args": [
            lambda job, meta, ctx: ctx.get("email_files") or [],
        ],
        "result": "selected_folder_emails",
    },
    {
        "phase": "pre",
        "fn": select_email,
        "args": [
            lambda job, meta, ctx: "Select an email",
            lambda job, meta, ctx: ctx.get("selected_folder_emails") or [],
        ],
        "result": "selected_email",
    },
]


VIEW_MBOX_EXEC = [
    {
        "phase": "exec",
        "fn": get_mbox_email_details,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_mbox"),
            lambda job, meta, ctx: ctx.get("selected_mbox_message"),
        ],
        "result": "email_details",
    },
    {
        "phase": "exec",
        "fn": display_email_details,
        "args": [
            lambda job, meta, ctx: ctx.get("email_details"),
        ],
        "result": "view_ok",
    },
]

VIEW_EML_EXEC = [
    {
        "phase": "exec",
        "fn": get_email_details,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_email"),
        ],
        "result": "email_details",
    },
    {
        "phase": "exec",
        "fn": display_email_details,
        "args": [
            lambda job, meta, ctx: ctx.get("email_details"),
        ],
        "result": "view_ok",
    },
]


SEARCH_EMAILS_PRE = [
    {
        "phase": "pre",
        "fn": list_email_search_configs,
        "args": [lambda job, meta, ctx: meta[SEARCH_CONFIGS_KEY]],
        "result": "selected_search_config",
    },
    {
        "phase": "pre",
        "fn": load_json,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_search_config") or []
        ],
        "result": "search_configs",
    },
    {
        "phase": "pre",
        "fn": validate_json_schema,
        "args": [
            lambda job, meta, ctx: ctx.get("search_configs", []),
            EMAIL_SEARCH_SCHEMA_PATH,
            "Email search configurations",
        ],
        "result": "validated_search_configs",
    },
    {
        "phase": "pre",
        "fn": dict,
        "args": [lambda job, meta, ctx: zip(
            ctx.get("selected_search_config") or [], ctx.get("validated_search_configs") or []
        )],
        "result": "search_configs_by_path",
    },
]

# ---------------------------------------------------------------------
# EXEC PHASE BLOCKS
# ---------------------------------------------------------------------


VIEW_PST_SUMMARY_EXEC = [
    {
        "phase": "exec",
        "fn": get_pst_summary,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
        ],
        "result": "summary_rows",
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("summary_rows") or None,
            ["Item", "Count"],
            lambda job, meta, ctx: "PST Summary",
        ],
        "result": "summary_ok",
    },
]


VIEW_EMAIL_EXEC = [
    {
        "phase": "exec",
        "fn": get_email_details,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_email"),
        ],
        "result": "email_details",
    },
    {
        "phase": "exec",
        "fn": display_email_details,
        "args": [
            lambda job, meta, ctx: ctx.get("email_details"),
        ],
        "result": "view_ok",
    },
]



CONVERT_PST_MBOX_EXEC = [
    {
        "phase": "exec",
        "fn": run_pst_files,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][MBOX_DIR],
            lambda job, meta, ctx: convert_pst_to_mbox,
        ],
        "result": "convert_ok",
    },
]


CONVERT_PST_EML_EXEC = [
    {
        "phase": "exec",
        "fn": run_pst_files,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][EML_DIR],
            lambda job, meta, ctx: convert_pst_to_eml,
        ],
        "result": "convert_ok",
    },
]


EXTRACT_CONTACTS_EXEC = [
    {
        "phase": "exec",
        "fn": run_pst_files,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][CONTACTS_DIR],
            lambda job, meta, ctx: extract_pst_contacts,
        ],
        "result": "extract_ok",
    },
]


EXTRACT_CALENDARS_EXEC = [
    {
        "phase": "exec",
        "fn": run_pst_files,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][CALENDARS_DIR],
            lambda job, meta, ctx: extract_pst_calendars,
        ],
        "result": "extract_ok",
    },
]


EXTRACT_ATTACHMENTS_EXEC = [
    {
        "phase": "exec",
        "fn": run_pst_files,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][ATTACHMENTS_DIR],
            lambda job, meta, ctx: extract_pst_attachments,
        ],
        "result": "extract_ok",
    },
]


SEARCH_EMAILS_EXEC = [
    {
        "phase": "exec",
        "fn": run_email_searches,
        "args": [
            lambda job, meta, ctx: ctx.get("search_configs_by_path"),
        ],
        "result": "search_results",
    },
    {
        "phase": "exec",
        "fn": display_email_search_results,
        "args": [
            lambda job, meta, ctx: ctx.get("search_results") if isinstance(ctx.get("search_configs_by_path"), dict) else None,
            lambda job, meta, ctx: ctx.get("search_configs_by_path"),
        ],
        "result": "search_ok",
    },
]


VIEW_SEARCH_RESULTS_EXEC = [
    {
        "phase": "exec",
        "fn": load_email_search_results,
        "args": [
            lambda job, meta, ctx: ctx.get("search_configs_by_path"),
        ],
        "result": "search_results",
    },
    {
        "phase": "exec",
        "fn": display_email_search_results,
        "args": [
            lambda job, meta, ctx: ctx.get("search_results") if isinstance(ctx.get("search_configs_by_path"), dict) else None,
            lambda job, meta, ctx: ctx.get("search_configs_by_path"),
        ],
        "result": "view_ok",
    },
]


SHOW_EMAIL_SEARCH_HELP_EXEC = [
    {
        "phase": "exec",
        "fn": display_readme,
        "args": [
            lambda job, meta, ctx: meta[LOCATIONS_KEY][SEARCH_README],
        ],
        "result": 'display_readme_result',
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
    "VIEW_PST_SUMMARY": {
        "pipeline": [
            *PST_SINGLE_SELECTION_PRE,
            *VIEW_PST_SUMMARY_EXEC,
        ],
        "label": "SUMMARY_COMPLETE",
    },
    "CONVERT_PST_MBOX": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *CONVERT_PST_MBOX_EXEC,
        ],
        "label": "CONVERT_COMPLETE",
    },
    "CONVERT_PST_EML": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *CONVERT_PST_EML_EXEC,
        ],
        "label": "CONVERT_COMPLETE",
    },
    "EXTRACT_CONTACTS": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *EXTRACT_CONTACTS_EXEC,
        ],
        "label": "EXTRACT_COMPLETE",
    },
    "EXTRACT_CALENDARS": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *EXTRACT_CALENDARS_EXEC,
        ],
        "label": "EXTRACT_COMPLETE",
    },
    "EXTRACT_ATTACHMENTS": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *EXTRACT_ATTACHMENTS_EXEC,
        ],
        "label": "EXTRACT_COMPLETE",
    },
    "VIEW_MBOX": {
        "pipeline": [
            *VIEW_MBOX_PRE,
            *VIEW_MBOX_EXEC,
        ],
        "label": "VIEW_MBOX_COMPLETE",
    },
    "VIEW_EML": {
        "pipeline": [
            *VIEW_EML_PRE,
            *VIEW_EML_EXEC,
        ],
        "label": "VIEW_EML_COMPLETE",
    },
    "SEARCH_EMAILS": {
        "pipeline": [
            *SEARCH_EMAILS_PRE,
            *SEARCH_EMAILS_EXEC,
        ],
        "label": "SEARCH_COMPLETE",
    },
    "VIEW_SEARCH_RESULTS": {
        "pipeline": [
            *SEARCH_EMAILS_PRE,
            *VIEW_SEARCH_RESULTS_EXEC,
        ],
        "label": "VIEW_SEARCH_RESULTS_COMPLETE",
    },
    "SHOW_EMAIL_SEARCH_HELP": {
        "pipeline": [*SHOW_EMAIL_SEARCH_HELP_EXEC],
        "label": "SHOW_EMAIL_SEARCH_HELP_COMPLETE",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "SHOW_CONFIG_COMPLETE",
    },
}
