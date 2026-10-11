from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
from modules.display_utils import display_config_doc, select_from_list, display_readme
from modules.file_utils import get_directory_status, get_files_by_extension
from modules.router_utils import (
    load_router_model_specs,
    decode_router_config,
    save_router_config,
    extract_router_config,
    view_router_config_fields,
    edit_router_config_fields,
    encode_router_config,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

CONFIG_PATH = "config/RouterConfig.json"
TOOL_TYPE = "Router Configuration"
CONFIG_DOC = "doc/RouterDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

LOCATIONS_KEY = "Locations"
CONFIG_FILE = "config_path"
DECODED_CONFIG_FILE = "decoded_config_path"
EDITED_CONFIG_FILE = "edited_config_path"
UPDATED_CONFIG_FILE = "updated_config_path"
MODEL_SPECS_PATH = "model_specs_path"
TEMPLATE_ROUTER_PASSWORD_PATH = "template_router_password_path"

# ---------------------------------------------------------------------
# MODEL SPECIFICATION KEYS
# ---------------------------------------------------------------------

MODEL_KEY = "model"
FIRMWARE_KEY = "firmware"
HARDWARE_KEY = "hardware"
ENCRYPTION_KEY = "encryption"
ENCODING_KEY = "encoding"
SALTED_KEY = "salted"
PASSWORD_BASE_KEY = "password_base"
PASSWORD_HASH_KEY = "password_hash"
KEY_DERIVATION_KEY = "key_derivation"
CONFIG_FIELDS_KEY = "config_fields"
MODEL_SPECS_README = "model_specs_readme_path"

# ---------------------------------------------------------------------
# FILE EXTENSIONS
# ---------------------------------------------------------------------

CONFIG_EXTENSION = [".cfg", ".bin"]
DECODED_EXTENSION = ".tar.gz"
MODEL_SPECS_EXTENSION = ".json"

DECODED_SUFFIX = "-decoded"
EDITED_SUFFIX = "-edited"
UPDATED_SUFFIX = "-updated"


# ---------------------------------------------------------------------
# VALIDATION CONFIG
# ---------------------------------------------------------------------

VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {LOCATIONS_KEY: dict},
}


# ---------------------------------------------------------------------
# SECONDARY VALIDATION
# ---------------------------------------------------------------------

SECONDARY_VALIDATION: Dict[str, Any] = {
    LOCATIONS_KEY: {
        "required_job_fields": {
            CONFIG_FILE: str,
            DECODED_CONFIG_FILE: str,
            EDITED_CONFIG_FILE: str,
            UPDATED_CONFIG_FILE: str,
            MODEL_SPECS_PATH: str,
            MODEL_SPECS_README: str,
            TEMPLATE_ROUTER_PASSWORD_PATH: str,
        },
        "allow_empty": False,
    },
}


# ---------------------------------------------------------------------
# USER REQUIREMENTS
# ---------------------------------------------------------------------

REQUIRED_USER = "standard"
ACTIVE_LABEL = "CONFIGS PRESENT"
INACTIVE_LABEL = "NO CONFIGS"


# ---------------------------------------------------------------------
# STATUS CHECK CONFIG
# ---------------------------------------------------------------------

STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": get_directory_status,
    "args": [lambda job, meta, ctx: meta[LOCATIONS_KEY][CONFIG_FILE]],
    "id_field": "location",
    "active_rule": {"field": "state", "equals": "data_present"},
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = ["openssl"]


# ---------------------------------------------------------------------
# PLAN CONFIG
# ---------------------------------------------------------------------

PLAN_COLUMN_ORDER = [LOCATIONS_KEY]
OPTIONAL_PLAN_COLUMNS: Dict[str, Any] = {}


# ---------------------------------------------------------------------
# ACTIONS
# ---------------------------------------------------------------------

ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": "Router Configuration"},
    "Decode Configuration": {
        "verb": "decode",
        "prompt": "Decode router configuration? [y/n]: ",
        "execute_state": "DECODE_CONFIG",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "View Configuration": {
        "verb": "view",
        "prompt": "View decoded router configuration? [y/n]: ",
        "execute_state": "VIEW_CONFIG",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Edit Configuration": {
        "verb": "edit",
        "prompt": "Edit router configuration? [y/n]: ",
        "execute_state": "EDIT_CONFIG",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "View Edited Configuration": {
        "verb": "view_edited",
        "prompt": "View edited router configuration? [y/n]: ",
        "execute_state": "VIEW_EDITED_CONFIG",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Encode Configuration": {
        "verb": "encode",
        "prompt": "Encode edited router configuration? [y/n]: ",
        "execute_state": "ENCODE_CONFIG",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "View Model Specifications Help": {
        "verb": "model_specs_help",
        "prompt": "View model specifications help? [y/n]: ",
        "execute_state": "SHOW_MODEL_SPECS_HELP",
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
# SELECT ROUTER MODEL SPECS PRE
# ---------------------------------------------------------------------

SELECT_ROUTER_MODEL_PRE = [
    {
        "phase": "pre",
        "fn": get_files_by_extension,
        "args": [
            lambda job, meta, ctx: meta[LOCATIONS_KEY][MODEL_SPECS_PATH],
            lambda job, meta, ctx: MODEL_SPECS_EXTENSION,
        ],
        "result": "model_specs_files",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select router model specifications",
            lambda job, meta, ctx: ctx.get("model_specs_files", []),
        ],
        "result": "selected_model_specs",
        "when": lambda job, meta, ctx: bool(ctx.get("model_specs_files")),
    },
]


# ---------------------------------------------------------------------
# SELECT ROUTER CONFIGURATION PRE
# ---------------------------------------------------------------------

SELECT_ROUTER_CONFIG_PRE = [
    {
        "phase": "pre",
        "fn": get_files_by_extension,
        "args": [
            lambda job, meta, ctx: meta[LOCATIONS_KEY][CONFIG_FILE],
            lambda job, meta, ctx: CONFIG_EXTENSION,
        ],
        "result": "config_files",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_model_specs")),
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select a router configuration",
            lambda job, meta, ctx: ctx.get("config_files", []),
        ],
        "result": "selected_config",
        "when": lambda job, meta, ctx: bool(ctx.get("config_files")),
    },
]


# ---------------------------------------------------------------------
# VIEW CONFIGURATION PRE
# ---------------------------------------------------------------------

VIEW_CONFIG_PRE = [
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select a decoded configuration",
            lambda job, meta, ctx: [
                str(path)
                for path in sorted(Path(meta[LOCATIONS_KEY][DECODED_CONFIG_FILE]).expanduser().iterdir())
                if path.is_dir()
            ],
        ],
        "result": "selected_decoded_config",
        "when": lambda job, meta, ctx: (
            Path(meta[LOCATIONS_KEY][DECODED_CONFIG_FILE]).expanduser().is_dir()
            and any(
                path.is_dir()
                for path in Path(meta[LOCATIONS_KEY][DECODED_CONFIG_FILE]).expanduser().iterdir()
            )
        ),
    },
]


# ---------------------------------------------------------------------
# SELECT EDITED CONFIGURATION PRE
# ---------------------------------------------------------------------

SELECT_EDITED_CONFIG_PRE = [
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select an edited configuration",
            lambda job, meta, ctx: [
                str(path)
                for path in sorted(Path(meta[LOCATIONS_KEY][EDITED_CONFIG_FILE]).expanduser().iterdir())
                if path.is_dir()
            ],
        ],
        "result": "selected_edited_config",
        "when": lambda job, meta, ctx: (
            Path(meta[LOCATIONS_KEY][EDITED_CONFIG_FILE]).expanduser().is_dir()
            and any(
                path.is_dir()
                for path in Path(meta[LOCATIONS_KEY][EDITED_CONFIG_FILE]).expanduser().iterdir()
            )
        ),
    },
]


# ---------------------------------------------------------------------
# LOAD ROUTER MODEL SPECS
# ---------------------------------------------------------------------

LOAD_ROUTER_MODEL_SPECS_PRE = [
    {
        "phase": "pre",
        "fn": load_router_model_specs,
        "args": [lambda job, meta, ctx: ctx.get("selected_model_specs")],
        "result": "model_specs",
        "when": lambda job, meta, ctx: bool(ctx.get("selected_model_specs")),
    },
]


# ---------------------------------------------------------------------
# DECODE ROUTER CONFIGURATION
# ---------------------------------------------------------------------

DECODE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": decode_router_config,
        "args": [
            lambda job, meta, ctx: ctx["selected_config"],
            lambda job, meta, ctx: ctx["model_specs"],
            lambda job, meta, ctx: meta[LOCATIONS_KEY][TEMPLATE_ROUTER_PASSWORD_PATH],
        ],
        "result": "decoded_config",
        "when": lambda job, meta, ctx: (
            isinstance(ctx.get("model_specs"), dict)
            and bool(ctx.get("selected_config"))
        ),
    },
]


# ---------------------------------------------------------------------
# SAVE DECODED CONFIGURATION
# ---------------------------------------------------------------------

SAVE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": save_router_config,
        "args": [
            lambda job, meta, ctx: ctx.get("decoded_config"),
            lambda job, meta, ctx: str(
                Path(meta[LOCATIONS_KEY][DECODED_CONFIG_FILE]).expanduser()
                / (Path(ctx["selected_config"]).stem + DECODED_SUFFIX + DECODED_EXTENSION)
            ) if ctx.get("selected_config") else "",
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "save_ok",
        "when": lambda job, meta, ctx: isinstance(ctx.get("decoded_config"), bytes),
    },
]


# ---------------------------------------------------------------------
# EXTRACT DECODED CONFIGURATION
# ---------------------------------------------------------------------

EXTRACT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": extract_router_config,
        "args": [
            lambda job, meta, ctx: str(
                Path(meta[LOCATIONS_KEY][DECODED_CONFIG_FILE]).expanduser()
                / (Path(ctx["selected_config"]).stem + DECODED_SUFFIX + DECODED_EXTENSION)
            ),
            lambda job, meta, ctx: str(
                Path(meta[LOCATIONS_KEY][DECODED_CONFIG_FILE]).expanduser()
                / (Path(ctx["selected_config"]).stem + DECODED_SUFFIX)
            ),
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "extracted_path",
        "when": lambda job, meta, ctx: ctx.get("save_ok") is True,
    },
]


# ---------------------------------------------------------------------
# VIEW ROUTER CONFIGURATION FIELDS
# ---------------------------------------------------------------------

VIEW_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": view_router_config_fields,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_decoded_config"),
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "view_ok",
        "when": lambda job, meta, ctx: (
            bool(ctx.get("selected_decoded_config"))
            and isinstance(ctx.get("model_specs"), dict)
            and isinstance(ctx["model_specs"].get(CONFIG_FIELDS_KEY), dict)
        ),
    },
]


# ---------------------------------------------------------------------
# EDIT ROUTER CONFIGURATION FIELDS
# ---------------------------------------------------------------------

EDIT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": edit_router_config_fields,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_decoded_config"),
            lambda job, meta, ctx: str(
                Path(meta[LOCATIONS_KEY][EDITED_CONFIG_FILE]).expanduser()
                / (Path(ctx["selected_decoded_config"]).name.removesuffix(DECODED_SUFFIX) + EDITED_SUFFIX)
            ),
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "edited_path",
        "when": lambda job, meta, ctx: (
            bool(ctx.get("selected_decoded_config"))
            and isinstance(ctx.get("model_specs"), dict)
            and isinstance(ctx["model_specs"].get(CONFIG_FIELDS_KEY), dict)
        ),
    },
]


# ---------------------------------------------------------------------
# VIEW EDITED ROUTER CONFIGURATION FIELDS
# ---------------------------------------------------------------------

VIEW_EDITED_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": view_router_config_fields,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_edited_config"),
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "view_edited_ok",
        "when": lambda job, meta, ctx: (
            bool(ctx.get("selected_edited_config"))
            and isinstance(ctx.get("model_specs"), dict)
            and isinstance(ctx["model_specs"].get(CONFIG_FIELDS_KEY), dict)
        ),
    },
]


# ---------------------------------------------------------------------
# ENCODE ROUTER CONFIGURATION
# ---------------------------------------------------------------------

ENCODE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": encode_router_config,
        "args": [
            lambda job, meta, ctx: ctx.get("selected_edited_config"),
            lambda job, meta, ctx: ctx.get("selected_config"),
            lambda job, meta, ctx: str(
                Path(meta[LOCATIONS_KEY][UPDATED_CONFIG_FILE]).expanduser()
                / (Path(ctx["selected_config"]).stem + UPDATED_SUFFIX + Path(ctx["selected_config"]).suffix)
            ),
            lambda job, meta, ctx: ctx.get("model_specs"),
            lambda job, meta, ctx: meta[LOCATIONS_KEY][TEMPLATE_ROUTER_PASSWORD_PATH],
        ],
        "result": "encoded_path",
        "when": lambda job, meta, ctx: (
            bool(ctx.get("selected_edited_config"))
            and bool(ctx.get("selected_config"))
            and isinstance(ctx.get("model_specs"), dict)
        ),
    },
]

# ---------------------------------------------------------------------
# SHOW MODEL SPECIFICATIONS HELP
# ---------------------------------------------------------------------

SHOW_MODEL_SPECS_HELP_EXEC = [
    {
        "phase": "exec",
        "fn": display_readme,
        "args": [
            lambda job, meta, ctx: meta[LOCATIONS_KEY][MODEL_SPECS_README],
        ],
        "result": "ok",
    },
]

# ---------------------------------------------------------------------
# SHOW CONFIG DOC
# ---------------------------------------------------------------------

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
    "DECODE_CONFIG": {
        "pipeline": [
            {"phase": "pre", "fn": lambda: False, "args": [], "result": "extracted_path"},
            {"phase": "exec", "fn": lambda: False, "args": [], "result": "extracted_path"},
            *SELECT_ROUTER_MODEL_PRE,
            *SELECT_ROUTER_CONFIG_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DECODE_ROUTER_CONFIG_EXEC,
            *SAVE_ROUTER_CONFIG_EXEC,
            *EXTRACT_ROUTER_CONFIG_EXEC,
            {"phase": "pre", "fn": lambda ready: ready,
             "args": [lambda job, meta, ctx: isinstance(ctx.get("model_specs"), dict) and bool(ctx.get("selected_config"))],
             "result": "extracted_path"},
        ],
        "label": "DECODE_CONFIG_COMPLETE",
        "success_key": "extracted_path",
    },
    "VIEW_CONFIG": {
        "pipeline": [
            {"phase": "pre", "fn": lambda: False, "args": [], "result": "view_ok"},
            {"phase": "exec", "fn": lambda: False, "args": [], "result": "view_ok"},
            *SELECT_ROUTER_MODEL_PRE,
            *VIEW_CONFIG_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *VIEW_ROUTER_CONFIG_EXEC,
            {"phase": "pre", "fn": lambda ready: ready,
             "args": [lambda job, meta, ctx: isinstance(ctx.get("model_specs"), dict) and bool(ctx.get("selected_decoded_config"))],
             "result": "view_ok"},
        ],
        "label": "VIEW_CONFIG_COMPLETE",
        "success_key": "view_ok",
    },
    "EDIT_CONFIG": {
        "pipeline": [
            {"phase": "pre", "fn": lambda: False, "args": [], "result": "edited_path"},
            {"phase": "exec", "fn": lambda: False, "args": [], "result": "edited_path"},
            *SELECT_ROUTER_MODEL_PRE,
            *VIEW_CONFIG_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *EDIT_ROUTER_CONFIG_EXEC,
            {"phase": "pre", "fn": lambda ready: ready,
             "args": [lambda job, meta, ctx: isinstance(ctx.get("model_specs"), dict) and bool(ctx.get("selected_decoded_config"))],
             "result": "edited_path"},
        ],
        "label": "EDIT_CONFIG_COMPLETE",
        "success_key": "edited_path",
    },
    "VIEW_EDITED_CONFIG": {
        "pipeline": [
            {"phase": "pre", "fn": lambda: False, "args": [], "result": "view_edited_ok"},
            {"phase": "exec", "fn": lambda: False, "args": [], "result": "view_edited_ok"},
            *SELECT_ROUTER_MODEL_PRE,
            *SELECT_EDITED_CONFIG_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *VIEW_EDITED_ROUTER_CONFIG_EXEC,
            {"phase": "pre", "fn": lambda ready: ready,
             "args": [lambda job, meta, ctx: isinstance(ctx.get("model_specs"), dict) and bool(ctx.get("selected_edited_config"))],
             "result": "view_edited_ok"},
        ],
        "label": "VIEW_EDITED_CONFIG_COMPLETE",
        "success_key": "view_edited_ok",
    },
    "ENCODE_CONFIG": {
        "pipeline": [
            {"phase": "pre", "fn": lambda: False, "args": [], "result": "encoded_path"},
            {"phase": "exec", "fn": lambda: False, "args": [], "result": "encoded_path"},
            *SELECT_ROUTER_MODEL_PRE,
            *SELECT_EDITED_CONFIG_PRE,
            *SELECT_ROUTER_CONFIG_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *ENCODE_ROUTER_CONFIG_EXEC,
            {"phase": "pre", "fn": lambda ready: ready,
             "args": [lambda job, meta, ctx: isinstance(ctx.get("model_specs"), dict) and bool(ctx.get("selected_edited_config")) and bool(ctx.get("selected_config"))],
             "result": "encoded_path"},
        ],
        "label": "ENCODE_CONFIG_COMPLETE",
        "success_key": "encoded_path",
    },
    "SHOW_MODEL_SPECS_HELP": {
        "pipeline": [*SHOW_MODEL_SPECS_HELP_EXEC],
        "label": "SHOW_MODEL_SPECS_HELP_COMPLETE",
        "success_key": "ok",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [*SHOW_CONFIG_DOC_EXEC],
        "label": "SHOW_CONFIG_DOC_COMPLETE",
        "success_key": "ok",
    },
}