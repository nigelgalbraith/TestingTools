# EmailConstants.py
from __future__ import annotations

from typing import Dict, Any

from modules.display_utils import (
    display_config_doc,
    select_from_list,
    print_dict_table,
)
from modules.file_utils import (
    get_directory_status,
    get_files_by_extension,
)
from modules.email_utils import (
    get_pst_summary,
    browse_pst_emails,
    get_pst_email_files,
    get_email_details,
    convert_pst_to_mbox,
    convert_pst_to_eml,
    extract_pst_contacts,
    extract_pst_attachments,
    select_email,
    select_email_folder,
    clear_pst_files,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

CONFIG_PATH = "config/EmailConfig.json"
TOOL_TYPE = "Email"
CONFIG_DOC = "doc/EmailDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

LOCATIONS_KEY = "locations"
SOURCE_DIR = "source_dir"
DEST_DIR = "dest_dir"
WORK_DIR = "work_dir"


VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        LOCATIONS_KEY: dict,
    },
}


SECONDARY_VALIDATION: Dict[str, Any] = {
    LOCATIONS_KEY: {
        "required_job_fields": {
            SOURCE_DIR: str,
            DEST_DIR: str,
            WORK_DIR: str,
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
        lambda job, meta, ctx: meta[LOCATIONS_KEY][SOURCE_DIR],
    ],
    "id_field": "location",
    "active_rule": {"field": "state", "equals": "data_present"},
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = [
    "pst-utils"
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
    "Extract attachments": {
        "verb": "extract",
        "prompt": "Extract attachments? [y/n]: ",
        "execute_state": "EXTRACT_ATTACHMENTS",
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

PST_FILE_SELECTION_PRE = [
    {
        "phase": "pre",
        "fn": get_files_by_extension,
        "args": [
            lambda job, meta, ctx: meta[LOCATIONS_KEY][SOURCE_DIR],
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
        "when": lambda job, meta, ctx: len(ctx.get("pst_files", [])) > 0,
    },
    {
        "phase": "pre",
        "fn": clear_pst_files,
        "args": [
            lambda job, meta, ctx: ctx,
        ],
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
    },
    {
        "phase": "pre",
        "fn": select_email_folder,
        "args": [
            lambda job, meta, ctx: ctx.get("email_files", []),
        ],
        "result": "selected_folder_emails",
        "when": lambda job, meta, ctx: bool(ctx.get("email_files")),
    },
    {
        "phase": "pre",
        "fn": select_email,
        "args": [
            lambda job, meta, ctx: "Select an email",
            lambda job, meta, ctx: ctx.get("selected_folder_emails", []),
        ],
        "result": "selected_email",
        "when": lambda job, meta, ctx: isinstance(ctx.get("selected_folder_emails"), list) and bool(ctx.get("selected_folder_emails")),
    },
    {
        "phase": "pre",
        "fn": lambda ctx: ctx.update({
            key: None
            for key in ("selected_folder_emails", "selected_email")
            if ctx.get(key) is True
        }),
        "args": [lambda job, meta, ctx: ctx],
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
            lambda job, meta, ctx: ctx.get("summary_rows", []),
            lambda job, meta, ctx: ["Item", "Count"],
            lambda job, meta, ctx: "PST Summary",
        ],
        "result": "summary_ok",
        "when": lambda job, meta, ctx: bool(ctx.get("summary_rows")),
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
        "when": lambda job, meta, ctx: bool(ctx.get("selected_email")),
    },
    {
        "phase": "exec",
        "fn": print_dict_table,
        "args": [
            lambda job, meta, ctx: [
                {"Field": key, "Value": value}
                for key, value in ctx.get("email_details", {}).items()
                if key != "Body"
            ],
            lambda job, meta, ctx: ["Field", "Value"],
            lambda job, meta, ctx: "Email Details",
        ],
        "result": "view_ok",
        "when": lambda job, meta, ctx: bool(ctx.get("email_details")),
    },
    {
        "phase": "exec",
        "fn": print,
        "args": [
            lambda job, meta, ctx: ctx.get("email_details", {}).get("Body", ""),
        ],
        "result": "body_ok",
        "when": lambda job, meta, ctx: bool(ctx.get("email_details")),
    },
]


CONVERT_PST_MBOX_EXEC = [
    {
        "phase": "exec",
        "fn": convert_pst_to_mbox,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][DEST_DIR],
        ],
        "result": "convert_ok",
    },
]


CONVERT_PST_EML_EXEC = [
    {
        "phase": "exec",
        "fn": convert_pst_to_eml,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][DEST_DIR],
        ],
        "result": "convert_ok",
    },
]


EXTRACT_CONTACTS_EXEC = [
    {
        "phase": "exec",
        "fn": extract_pst_contacts,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][DEST_DIR],
        ],
        "result": "extract_ok",
    },
]


EXTRACT_ATTACHMENTS_EXEC = [
    {
        "phase": "exec",
        "fn": extract_pst_attachments,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_pst"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][DEST_DIR],
        ],
        "result": "extract_ok",
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
# STEP GROUPS
# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# PIPELINE STATES
# ---------------------------------------------------------------------

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "VIEW_PST_SUMMARY": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *VIEW_PST_SUMMARY_EXEC,
        ],
        "label": "SUMMARY_COMPLETE",
        "success_key": "summary_ok",
    },
    "LIST_EMAILS": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *LIST_EMAILS_EXEC,
        ],
        "label": "LIST_COMPLETE",
        "success_key": "list_ok",
    },
    "VIEW_EMAIL": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *VIEW_EMAIL_PRE,
            *VIEW_EMAIL_EXEC,
        ],
        "label": "VIEW_COMPLETE",
        "success_key": "view_ok",
    },
    "CONVERT_PST_MBOX": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *CONVERT_PST_MBOX_EXEC,
        ],
        "label": "CONVERT_COMPLETE",
        "success_key": "convert_ok",
    },
    "CONVERT_PST_EML": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *CONVERT_PST_EML_EXEC,
        ],
        "label": "CONVERT_COMPLETE",
        "success_key": "convert_ok",
    },
    "EXTRACT_CONTACTS": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *EXTRACT_CONTACTS_EXEC,
        ],
        "label": "EXTRACT_COMPLETE",
        "success_key": "extract_ok",
    },
    "EXTRACT_ATTACHMENTS": {
        "pipeline": [
            *PST_FILE_SELECTION_PRE,
            *EXTRACT_ATTACHMENTS_EXEC,
        ],
        "label": "EXTRACT_COMPLETE",
        "success_key": "extract_ok",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "SHOW_CONFIG_COMPLETE",
        "success_key": "ok",
    },
}
