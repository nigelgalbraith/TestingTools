# EmailConstants.py
from __future__ import annotations

from modules.state_machine_utils import result_available

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
    browse_pst_emails,
    clear_pst_files,
    convert_pst_to_eml,
    convert_pst_to_mbox,
    extract_pst_attachments,
    extract_pst_contacts,
    get_email_details,
    get_pst_email_files,
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
WORK_DIR = "work_dir"
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
            WORK_DIR: str,
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
    "List emails": {
        "verb": "list",
        "prompt": "List emails? [y/n]: ",
        "execute_state": "LIST_EMAILS",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "View email": {
        "verb": "view",
        "prompt": "View email? [y/n]: ",
        "execute_state": "VIEW_EMAIL",
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
        "when": lambda job, meta, ctx: result_available(ctx, 'pst_files') and (bool(ctx.get('pst_files'))),
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


VIEW_EMAIL_PRE = [
    {
        "phase": "pre",
        "fn": get_pst_email_files,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][WORK_DIR],
        ],
        "result": "email_files",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_pst') and (bool(ctx.get('selected_pst'))),
    },
    {
        "phase": "pre",
        "fn": select_email_folder,
        "args": [
            lambda job, meta, ctx: ctx.get("email_files", []),
        ],
        "result": "selected_folder_emails",
        "when": lambda job, meta, ctx: result_available(ctx, 'email_files') and (bool(ctx.get('email_files'))),
    },
    {
        "phase": "pre",
        "fn": select_email,
        "args": [
            lambda job, meta, ctx: "Select an email",
            lambda job, meta, ctx: ctx.get("selected_folder_emails", []),
        ],
        "result": "selected_email",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_folder_emails') and (isinstance(ctx.get('selected_folder_emails'), list) and bool(ctx.get('selected_folder_emails'))),
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
            lambda job, meta, ctx: ctx["selected_search_config"]
        ],
        "result": "search_configs",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_search_config'),
    },
    {
        "phase": "pre",
        "fn": validate_json_schema,
        "args": [
            lambda job, meta, ctx: ctx["search_configs"],
            EMAIL_SEARCH_SCHEMA_PATH,
            "Email search configurations",
        ],
        "result": "validated_search_configs",
        "when": lambda job, meta, ctx: result_available(ctx, 'search_configs'),
    },
    {
        "phase": "pre",
        "fn": dict,
        "args": [lambda job, meta, ctx: zip(
            ctx.get("selected_search_config") or [], ctx["validated_search_configs"]
        )],
        "result": "search_configs_by_path",
        "when": lambda job, meta, ctx: result_available(ctx, 'validated_search_configs', 'selected_search_config'),
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
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_pst') and (bool(ctx.get('selected_pst'))),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: ctx.get("summary_rows", []),
            ["Item", "Count"],
            lambda job, meta, ctx: "PST Summary",
        ],
        "result": "summary_ok",
        "when": lambda job, meta, ctx: result_available(ctx, 'summary_rows') and (bool(ctx.get('summary_rows'))),
    },
]


LIST_EMAILS_EXEC = [
    {
        "phase": "exec",
        "fn": browse_pst_emails,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
        ],
        "result": "list_ok",
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_pst') and (bool(ctx.get('selected_pst'))),
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
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_email') and (bool(ctx.get('selected_email'))),
    },
    {
        "phase": "exec",
        "fn": display_email_details,
        "args": [
            lambda job, meta, ctx: ctx.get("email_details"),
        ],
        "result": "view_ok",
        "when": lambda job, meta, ctx: result_available(ctx, 'email_details') and (bool(ctx.get('email_details'))),
    },
    {
        "phase": "exec",
        "fn": print,
        "args": [
            lambda job, meta, ctx: ctx.get("email_details", {}).get("Body", ""),
        ],
        "result": "body_ok",
        "when": lambda job, meta, ctx: result_available(ctx, 'email_details') and (bool(ctx.get('email_details'))),
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
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_pst') and (bool(ctx.get('selected_pst'))),
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
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_pst') and (bool(ctx.get('selected_pst'))),
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
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_pst') and (bool(ctx.get('selected_pst'))),
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
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_pst') and (bool(ctx.get('selected_pst'))),
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
        "when": lambda job, meta, ctx: result_available(ctx, 'selected_pst') and (bool(ctx.get('selected_pst'))),
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
        "when": lambda job, meta, ctx: result_available(ctx, 'search_configs_by_path') and (bool(ctx.get('search_configs_by_path'))),
    },
    {
        "phase": "exec",
        "fn": display_email_search_results,
        "args": [
            lambda job, meta, ctx: ctx.get("search_results", []),
            lambda job, meta, ctx: ctx.get("search_configs_by_path"),
        ],
        "result": "search_ok",
        "when": lambda job, meta, ctx: result_available(ctx, 'search_results', 'search_configs_by_path') and (isinstance(ctx.get('search_results'), list)),
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
        "when": lambda job, meta, ctx: result_available(ctx, 'search_configs_by_path') and (bool(ctx.get('search_configs_by_path'))),
    },
    {
        "phase": "exec",
        "fn": display_email_search_results,
        "args": [
            lambda job, meta, ctx: ctx.get("search_results", []),
            lambda job, meta, ctx: ctx.get("search_configs_by_path"),
        ],
        "result": "view_ok",
        "when": lambda job, meta, ctx: result_available(ctx, 'search_results', 'search_configs_by_path') and (isinstance(ctx.get('search_results'), list)),
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
    "LIST_EMAILS": {
        "pipeline": [
            *PST_SINGLE_SELECTION_PRE,
            *LIST_EMAILS_EXEC,
        ],
        "label": "LIST_COMPLETE",
    },
    "VIEW_EMAIL": {
        "pipeline": [
            *PST_SINGLE_SELECTION_PRE,
            *VIEW_EMAIL_PRE,
            *VIEW_EMAIL_EXEC,
        ],
        "label": "VIEW_COMPLETE",
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
