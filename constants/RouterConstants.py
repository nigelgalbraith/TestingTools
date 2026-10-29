
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from modules.state_machine_utils import (
    result_available, 
    meta_available
)
from modules.json_utils import (
    load_json, 
    validate_json_schema
)
from modules.display_utils import (
    display_config_doc, 
    select_from_list, 
    display_readme
)
from modules.file_utils import get_directory_status
from modules.router_utils import (
    decode_router_config,
    save_router_config,
    extract_router_config,
    view_router_config_fields,
    edit_router_config_files,
    encode_router_config_files,
    convert_router_config_fields,
    validate_router_settings,
)


# ---------------------------------------------------------------------
# CONFIG PATHS
# ---------------------------------------------------------------------

ROUTER_SCHEMA_PATH = "schemas/RouterSchema.json"
CONFIG_PATH = "config/RouterConfig.json"
TOOL_TYPE = "Router Configuration"
CONFIG_DOC = "doc/RouterDoc.json"


# ---------------------------------------------------------------------
# JSON KEYS
# ---------------------------------------------------------------------

COMMON_LOCATIONS_KEY = "Common Locations"
ROUTERS_KEY = "Routers"
MODEL_SPECS_README = "model_specs_readme_path"
SPECS_KEY = "specs"
PASSWORD_KEY = "password"
DEVICE_KEY = "device_key"
TEMPLATE_KEY = "template"
DECODED_KEY = "template_decoded"
DECODED_DIR_KEY = "template_decoded_dir"
EDITED_KEY = "template_edited"
EDITED_DIR_KEY = "template_edited_dir"
ENCODED_KEY = "template_encoded"
ORIGINAL_KEY = "original"
MIGRATION_DECODED_KEY = "migration_decoded"
MIGRATION_DECODED_DIR_KEY = "migration_decoded_dir"
MIGRATION_EDITED_KEY = "migration_edited"
MIGRATION_EDITED_DIR_KEY = "migration_edited_dir"
MIGRATION_CONVERTED_KEY = "migration_converted"
MIGRATION_CONVERTED_DIR_KEY = "migration_converted_dir"
MIGRATION_ENCODED_KEY = "migration_encoded"


# ---------------------------------------------------------------------
# VALIDATION CONFIG
# ---------------------------------------------------------------------

VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        COMMON_LOCATIONS_KEY: dict,
        ROUTERS_KEY: dict,
    },
}


# ---------------------------------------------------------------------
# SECONDARY VALIDATION
# ---------------------------------------------------------------------

# Password and device-key fields are optional; credentials follow the model specification.
SECONDARY_VALIDATION: Dict[str, Any] = {
    COMMON_LOCATIONS_KEY: {
        "required_job_fields": {
            MODEL_SPECS_README: str,
        },
        "allow_empty": False,
    },
    ROUTERS_KEY: {
        "required_job_fields": {
            SPECS_KEY: str,
            TEMPLATE_KEY: str,
            DECODED_KEY: str,
            DECODED_DIR_KEY: str,
            EDITED_KEY: str,
            EDITED_DIR_KEY: str,
            ENCODED_KEY: str,
            ORIGINAL_KEY: str,
            MIGRATION_DECODED_KEY: str,
            MIGRATION_DECODED_DIR_KEY: str,
            MIGRATION_EDITED_KEY: str,
            MIGRATION_EDITED_DIR_KEY: str,
            MIGRATION_CONVERTED_KEY: str,
            MIGRATION_CONVERTED_DIR_KEY: str,
            MIGRATION_ENCODED_KEY: str,
        },
        "dynamic_keys": True,
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
    "args": [
        lambda job, meta, ctx: str(
            Path(
                next(iter(meta[ROUTERS_KEY].values()))[TEMPLATE_KEY]
            ).expanduser().parent
        )
    ],
    "id_field": "location",
    "active_rule": {"field": "state", "equals": "data_present"},
}


# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------

DEPENDENCIES = ["openssl", "python3-cryptography", "python3-jsonschema"]


# ---------------------------------------------------------------------
# PLAN CONFIG
# ---------------------------------------------------------------------

PLAN_COLUMN_ORDER = [ROUTERS_KEY]
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
    "Modify Router - Same Model (Run All)": {
        "verb": "run_all_same_model",
        "prompt": "Run all same-model router operations? [y/n]: ",
        "execute_state": "RUN_ALL_SAME_MODEL",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Migrate a Config": {
        "verb": "migrate_decode",
        "prompt": "Decode router configuration for migration? [y/n]: ",
        "execute_state": "MIGRATION_DECODE_CONFIG",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Edit Migration Config": {
        "verb": "migration_edit",
        "prompt": "Edit decoded migration configuration? [y/n]: ",
        "execute_state": "MIGRATION_EDIT_CONFIG",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "View Edited Migration Config": {
        "verb": "view_migration_edited",
        "prompt": "View edited migration configuration? [y/n]: ",
        "execute_state": "VIEW_MIGRATION_EDITED_CONFIG",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Prepare Destination Config": {
        "verb": "migration_convert_prepare",
        "prompt": "Decode destination configuration for conversion? [y/n]: ",
        "execute_state": "MIGRATION_CONVERT_PREPARE",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Convert Migration Config": {
        "verb": "migration_convert",
        "prompt": "Convert migration configuration? [y/n]: ",
        "execute_state": "MIGRATION_CONVERT_CONFIG",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Encode Migration Config": {
        "verb": "migration_encode",
        "prompt": "Encode converted migration configuration? [y/n]: ",
        "execute_state": "MIGRATION_ENCODE_CONFIG",
        "post_state": "MENU_SELECTION",
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Modify Router - Different Model (Run All)": {
        "verb": "run_all_different_model",
        "prompt": "Run all different-model router operations? [y/n]: ",
        "execute_state": "RUN_ALL_DIFFERENT_MODEL",
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
# SELECT ROUTER PRE
# ---------------------------------------------------------------------

SELECT_ROUTER_PRE = [
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select router",
            lambda job, meta, ctx: list(meta[ROUTERS_KEY]),
        ],
        "result": "selected_router",
        "when": lambda job, meta, ctx: meta_available(
            meta, ROUTERS_KEY, require_nonempty=True
        ),
    },
]


# ---------------------------------------------------------------------
# LOAD ROUTER MODEL SPECS
# ---------------------------------------------------------------------

LOAD_ROUTER_MODEL_SPECS_PRE = [
    {
        "phase": "pre",
        "fn": load_json,
        "args": [
            lambda job, meta, ctx:
                meta[ROUTERS_KEY][ctx["selected_router"]][SPECS_KEY],
        ],
        "result": "model_specs",
        "when": lambda job, meta, ctx: result_available(
            ctx, 'selected_router', require_nonempty=True
        ),
    },
    {
        "phase": "pre",
        "fn": validate_json_schema,
        "args": [
            lambda job, meta, ctx: ctx["model_specs"],
            ROUTER_SCHEMA_PATH,
            "Router model specifications",
        ],
        "result": "model_specs",
        "when": lambda job, meta, ctx: result_available(
            ctx, 'model_specs', require_type=dict
        ),
    },
    {
        "phase": "pre",
        "fn": validate_router_settings,
        "args": [
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "when": lambda job, meta, ctx: result_available(
            ctx, 'model_specs', require_type=dict
        ),
        "result": "validate_router_settings_result",
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
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][TEMPLATE_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]].get(PASSWORD_KEY),
            lambda job, meta, ctx: "Enter router password: ",
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]].get(DEVICE_KEY),
        ],
        "result": "decoded_config",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]


# ---------------------------------------------------------------------
# SAVE AND EXTRACT DECODED CONFIGURATION
# ---------------------------------------------------------------------

SAVE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": save_router_config,
        "args": [
            lambda job, meta, ctx: ctx.get("decoded_config"),
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][DECODED_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "save_ok",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'decoded_config', require_type=bytes)
            and result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]

EXTRACT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": extract_router_config,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][DECODED_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][DECODED_DIR_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "extracted_path",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'save_ok', require_type=bool, require_value=True)
            and result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]


# ---------------------------------------------------------------------
# VIEW / EDIT ROUTER CONFIGURATION
# ---------------------------------------------------------------------

VIEW_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": view_router_config_fields,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][DECODED_DIR_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "view_ok",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]

EDIT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": edit_router_config_files,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][DECODED_DIR_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][EDITED_DIR_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "edited_path",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]

VIEW_EDITED_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": view_router_config_fields,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][EDITED_DIR_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "view_edited_ok",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]


# ---------------------------------------------------------------------
# ENCODE ROUTER CONFIGURATION
# ---------------------------------------------------------------------

ENCODE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": encode_router_config_files,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][EDITED_DIR_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][TEMPLATE_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][EDITED_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][ENCODED_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]].get(PASSWORD_KEY),
            lambda job, meta, ctx: "Enter target router password (Enter to use template password): ",
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]].get(DEVICE_KEY),
        ],
        "result": "encoded_path",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]


# ---------------------------------------------------------------------
# DECODE MIGRATION CONFIGURATION
# ---------------------------------------------------------------------

MIGRATION_DECODE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": decode_router_config,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][ORIGINAL_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
            None,
            lambda job, meta, ctx: "Enter SOURCE router password: ",
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]].get(DEVICE_KEY),
        ],
        "result": "decoded_config",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]

MIGRATION_SAVE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": save_router_config,
        "args": [
            lambda job, meta, ctx: ctx.get("decoded_config"),
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][MIGRATION_DECODED_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "save_ok",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'decoded_config', require_type=bytes)
            and result_available(ctx, 'model_specs', 'selected_router')
        ),
    },
]

MIGRATION_EXTRACT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": extract_router_config,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][MIGRATION_DECODED_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][MIGRATION_DECODED_DIR_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "extracted_path",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'save_ok', require_type=bool, require_value=True)
            and result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]


# ---------------------------------------------------------------------
# EDIT MIGRATION CONFIGURATION
# ---------------------------------------------------------------------

MIGRATION_EDIT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": edit_router_config_files,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][MIGRATION_DECODED_DIR_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][MIGRATION_EDITED_DIR_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "edited_path",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]


# ---------------------------------------------------------------------
# ENCODE MIGRATION CONFIGURATION
# ---------------------------------------------------------------------

MIGRATION_ENCODE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": encode_router_config_files,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]][MIGRATION_CONVERTED_DIR_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]][TEMPLATE_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]][MIGRATION_CONVERTED_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]][MIGRATION_ENCODED_KEY],
            lambda job, meta, ctx: ctx["destination_specs"],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]].get(PASSWORD_KEY),
            lambda job, meta, ctx: "Enter DESTINATION router password: ",
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]].get(DEVICE_KEY),
        ],
        "result": "migration_encoded_path",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'destination_specs', require_type=dict)
            and result_available(ctx, 'destination_router')
        ),
    },
]


# ---------------------------------------------------------------------
# VIEW EDITED MIGRATION CONFIGURATION
# ---------------------------------------------------------------------

MIGRATION_VIEW_EDITED_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": view_router_config_fields,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][MIGRATION_EDITED_DIR_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
        ],
        "result": "view_migration_edited_ok",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'model_specs', require_type=dict)
            and result_available(ctx, 'selected_router')
        ),
    },
]


# ---------------------------------------------------------------------
# SELECT DESTINATION ROUTER
# ---------------------------------------------------------------------

SELECT_DESTINATION_ROUTER_PRE = [
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            lambda job, meta, ctx: "Select destination router",
            lambda job, meta, ctx: list(meta[ROUTERS_KEY]),
        ],
        "result": "destination_router",
        "when": lambda job, meta, ctx: meta_available(
            meta, ROUTERS_KEY, require_nonempty=True
        ),
    },
]

LOAD_DESTINATION_MODEL_SPECS_PRE = [
    {
        "phase": "pre",
        "fn": load_json,
        "args": [
            lambda job, meta, ctx:
                meta[ROUTERS_KEY][ctx["destination_router"]][SPECS_KEY],
        ],
        "result": "destination_specs",
        "when": lambda job, meta, ctx: result_available(
            ctx, 'destination_router', require_nonempty=True
        ),
    },
    {
        "phase": "pre",
        "fn": validate_json_schema,
        "args": [
            lambda job, meta, ctx: ctx["destination_specs"],
            ROUTER_SCHEMA_PATH,
            "Destination router model specifications",
        ],
        "result": "destination_specs",
        "when": lambda job, meta, ctx: result_available(
            ctx, 'destination_specs', require_type=dict
        ),
    },
    {
        "phase": "pre",
        "fn": validate_router_settings,
        "args": [
            lambda job, meta, ctx: ctx["destination_specs"],
        ],
        "when": lambda job, meta, ctx: result_available(
            ctx, 'destination_specs', require_type=dict
        ),
        "result": "validate_router_settings_result",
    },
]


# ---------------------------------------------------------------------
# DECODE DESTINATION CONFIGURATION FOR CONVERSION
# ---------------------------------------------------------------------

MIGRATION_CONVERT_DECODE_EXEC = [
    {
        "phase": "exec",
        "fn": decode_router_config,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]][TEMPLATE_KEY],
            lambda job, meta, ctx: ctx["destination_specs"],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]].get(PASSWORD_KEY),
            lambda job, meta, ctx: "Enter router password: ",
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]].get(DEVICE_KEY),
        ],
        "result": "converted_decoded_config",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'destination_specs', require_type=dict)
            and result_available(ctx, 'destination_router')
        ),
    },
]

MIGRATION_CONVERT_SAVE_EXEC = [
    {
        "phase": "exec",
        "fn": save_router_config,
        "args": [
            lambda job, meta, ctx: ctx.get("converted_decoded_config"),
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]][MIGRATION_CONVERTED_KEY],
            lambda job, meta, ctx: ctx["destination_specs"],
        ],
        "result": "converted_save_ok",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'converted_decoded_config', require_type=bytes)
            and result_available(ctx, 'destination_specs', 'destination_router')
        ),
    },
]

MIGRATION_CONVERT_EXTRACT_EXEC = [
    {
        "phase": "exec",
        "fn": extract_router_config,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]][MIGRATION_CONVERTED_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]][MIGRATION_CONVERTED_DIR_KEY],
            lambda job, meta, ctx: ctx["destination_specs"],
        ],
        "result": "converted_extracted_path",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'converted_save_ok', require_type=bool, require_value=True)
            and result_available(ctx, 'destination_specs', require_type=dict)
            and result_available(ctx, 'destination_router')
        ),
    },
]


# ---------------------------------------------------------------------
# CONVERT MIGRATION CONFIGURATION
# ---------------------------------------------------------------------

MIGRATION_CONVERT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": convert_router_config_fields,
        "args": [
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["selected_router"]][MIGRATION_EDITED_DIR_KEY],
            lambda job, meta, ctx: meta[ROUTERS_KEY][ctx["destination_router"]][MIGRATION_CONVERTED_DIR_KEY],
            lambda job, meta, ctx: ctx["model_specs"],
            lambda job, meta, ctx: ctx["destination_specs"],
        ],
        "result": "converted_path",
        "when": lambda job, meta, ctx: (
            result_available(ctx, 'model_specs', 'destination_specs', require_type=dict)
            and result_available(ctx, 'selected_router', 'destination_router')
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
            lambda job, meta, ctx:
                meta[COMMON_LOCATIONS_KEY][MODEL_SPECS_README],
        ],
        "result": 'display_readme_result',
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
        "result": 'display_config_doc_result',
    },
]


# ---------------------------------------------------------------------
# PIPELINE STATES
# ---------------------------------------------------------------------

PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "DECODE_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DECODE_ROUTER_CONFIG_EXEC,
            *SAVE_ROUTER_CONFIG_EXEC,
            *EXTRACT_ROUTER_CONFIG_EXEC,
        ],
        "label": "DECODE_CONFIG_COMPLETE",
    },
    "VIEW_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *VIEW_ROUTER_CONFIG_EXEC,
        ],
        "label": "VIEW_CONFIG_COMPLETE",
    },
    "EDIT_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *EDIT_ROUTER_CONFIG_EXEC,
        ],
        "label": "EDIT_CONFIG_COMPLETE",
    },
    "VIEW_EDITED_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *VIEW_EDITED_ROUTER_CONFIG_EXEC,
        ],
        "label": "VIEW_EDITED_CONFIG_COMPLETE",
    },
    "ENCODE_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *ENCODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "ENCODE_CONFIG_COMPLETE",
    },
    "RUN_ALL_SAME_MODEL": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DECODE_ROUTER_CONFIG_EXEC,
            *SAVE_ROUTER_CONFIG_EXEC,
            *EXTRACT_ROUTER_CONFIG_EXEC,
            *EDIT_ROUTER_CONFIG_EXEC,
            *ENCODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "RUN_ALL_SAME_MODEL_COMPLETE",
    },
    "MIGRATION_DECODE_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *MIGRATION_DECODE_ROUTER_CONFIG_EXEC,
            *MIGRATION_SAVE_ROUTER_CONFIG_EXEC,
            *MIGRATION_EXTRACT_ROUTER_CONFIG_EXEC,
        ],
        "label": "MIGRATION_DECODE_CONFIG_COMPLETE",
    },
    "MIGRATION_EDIT_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *MIGRATION_EDIT_ROUTER_CONFIG_EXEC,
        ],
        "label": "MIGRATION_EDIT_CONFIG_COMPLETE",
    },
    "VIEW_MIGRATION_EDITED_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *MIGRATION_VIEW_EDITED_ROUTER_CONFIG_EXEC,
        ],
        "label": "VIEW_MIGRATION_EDITED_CONFIG_COMPLETE",
    },
    "MIGRATION_CONVERT_PREPARE": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *SELECT_DESTINATION_ROUTER_PRE,
            *LOAD_DESTINATION_MODEL_SPECS_PRE,
            *MIGRATION_CONVERT_DECODE_EXEC,
            *MIGRATION_CONVERT_SAVE_EXEC,
            *MIGRATION_CONVERT_EXTRACT_EXEC,
        ],
        "label": "MIGRATION_CONVERT_PREPARE_COMPLETE",
    },
    "MIGRATION_CONVERT_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *SELECT_DESTINATION_ROUTER_PRE,
            *LOAD_DESTINATION_MODEL_SPECS_PRE,
            *MIGRATION_CONVERT_ROUTER_CONFIG_EXEC,
        ],
        "label": "MIGRATION_CONVERT_CONFIG_COMPLETE",
    },
    "MIGRATION_ENCODE_CONFIG": {
        "pipeline": [
            *SELECT_DESTINATION_ROUTER_PRE,
            *LOAD_DESTINATION_MODEL_SPECS_PRE,
            *MIGRATION_ENCODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "MIGRATION_ENCODE_CONFIG_COMPLETE",
    },
    "RUN_ALL_DIFFERENT_MODEL": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *MIGRATION_DECODE_ROUTER_CONFIG_EXEC,
            *MIGRATION_SAVE_ROUTER_CONFIG_EXEC,
            *MIGRATION_EXTRACT_ROUTER_CONFIG_EXEC,
            *MIGRATION_EDIT_ROUTER_CONFIG_EXEC,
            *SELECT_DESTINATION_ROUTER_PRE,
            *LOAD_DESTINATION_MODEL_SPECS_PRE,
            *MIGRATION_CONVERT_DECODE_EXEC,
            *MIGRATION_CONVERT_SAVE_EXEC,
            *MIGRATION_CONVERT_EXTRACT_EXEC,
            *MIGRATION_CONVERT_ROUTER_CONFIG_EXEC,
            *MIGRATION_ENCODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "RUN_ALL_DIFFERENT_MODEL_COMPLETE",
    },
    "SHOW_MODEL_SPECS_HELP": {
        "pipeline": [*SHOW_MODEL_SPECS_HELP_EXEC],
        "label": "SHOW_MODEL_SPECS_HELP_COMPLETE",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [*SHOW_CONFIG_DOC_EXEC],
        "label": "SHOW_CONFIG_DOC_COMPLETE",
    },
}
