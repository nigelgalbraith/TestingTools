
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
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
        ROUTERS_KEY,
        TEMPLATE_KEY,
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
        "fn": list,
        "args": ["meta.Routers"],
        "result": "router_choices",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": ["Select router", "router_choices"],
        "when": "router_choices",
        "result": "selected_router",
    },
]

# ---------------------------------------------------------------------
# LOAD ROUTER MODEL SPECS
# ---------------------------------------------------------------------

LOAD_ROUTER_MODEL_SPECS_PRE = [
    {
        "phase": "pre",
        "fn": load_json,
        "args": ["meta.Routers.$selected_router.specs"],
        "when": "selected_router",
        "result": "model_specs",
    },
    {
        "phase": "pre",
        "fn": validate_json_schema,
        "args": [
            "model_specs",
            ROUTER_SCHEMA_PATH,
            "Router model specifications",
        ],
        "when": "model_specs",
        "result": "model_specs",
    },
    {
        "phase": "pre",
        "fn": validate_router_settings,
        "args": ["model_specs"],
        "when": "model_specs",
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
            "meta.Routers.$selected_router.template",
            "model_specs",
            "meta.Routers.$selected_router.password",
            "Enter router password: ",
            "meta.Routers.$selected_router.device_key",
        ],
        "when": "model_specs",
        "result": "decoded_config",
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
            "decoded_config",
            "meta.Routers.$selected_router.template_decoded",
            "model_specs",
        ],
        "when": "decoded_config",
        "result": "save_ok",
    },
]

EXTRACT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": extract_router_config,
        "args": [
            "meta.Routers.$selected_router.template_decoded",
            "meta.Routers.$selected_router.template_decoded_dir",
            "model_specs",
        ],
        "when": "save_ok",
        "result": "extracted_path",
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
            "meta.Routers.$selected_router.template_decoded_dir",
            "model_specs",
        ],
        "when": "model_specs",
        "result": "view_ok",
    },
]

EDIT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": edit_router_config_files,
        "args": [
            "meta.Routers.$selected_router.template_decoded_dir",
            "meta.Routers.$selected_router.template_edited_dir",
            "model_specs",
        ],
        "when": "model_specs",
        "result": "edited_path",
    },
]

VIEW_EDITED_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": view_router_config_fields,
        "args": [
            "meta.Routers.$selected_router.template_edited_dir",
            "model_specs",
        ],
        "when": "model_specs",
        "result": "view_edited_ok",
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
            "meta.Routers.$selected_router.template_edited_dir",
            "meta.Routers.$selected_router.template",
            "meta.Routers.$selected_router.template_edited",
            "meta.Routers.$selected_router.template_encoded",
            "model_specs",
            "meta.Routers.$selected_router.password",
            "Enter target router password (Enter to use template password): ",
            "meta.Routers.$selected_router.device_key",
        ],
        "when": "model_specs",
        "result": "encoded_path",
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
            "meta.Routers.$selected_router.original",
            "model_specs",
            None,
            "Enter SOURCE router password: ",
            "meta.Routers.$selected_router.device_key",
        ],
        "when": "model_specs",
        "result": "decoded_config",
    },
]

MIGRATION_SAVE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": save_router_config,
        "args": [
            "decoded_config",
            "meta.Routers.$selected_router.migration_decoded",
            "model_specs",
        ],
        "when": "decoded_config",
        "result": "save_ok",
    },
]

MIGRATION_EXTRACT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": extract_router_config,
        "args": [
            "meta.Routers.$selected_router.migration_decoded",
            "meta.Routers.$selected_router.migration_decoded_dir",
            "model_specs",
        ],
        "when": "save_ok",
        "result": "extracted_path",
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
            "meta.Routers.$selected_router.migration_decoded_dir",
            "meta.Routers.$selected_router.migration_edited_dir",
            "model_specs",
        ],
        "when": "model_specs",
        "result": "edited_path",
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
            "meta.Routers.$destination_router.migration_converted_dir",
            "meta.Routers.$destination_router.template",
            "meta.Routers.$destination_router.migration_converted",
            "meta.Routers.$destination_router.migration_encoded",
            "destination_specs",
            "meta.Routers.$destination_router.password",
            "Enter DESTINATION router password: ",
            "meta.Routers.$destination_router.device_key",
        ],
        "when": "destination_specs",
        "result": "migration_encoded_path",
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
            "meta.Routers.$selected_router.migration_edited_dir",
            "model_specs",
        ],
        "when": "model_specs",
        "result": "view_migration_edited_ok",
    },
]

# ---------------------------------------------------------------------
# SELECT DESTINATION ROUTER
# ---------------------------------------------------------------------

SELECT_DESTINATION_ROUTER_PRE = [
    {
        "phase": "pre",
        "fn": list,
        "args": ["meta.Routers"],
        "result": "destination_router_choices",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": [
            "Select destination router",
            "destination_router_choices",
        ],
        "when": "destination_router_choices",
        "result": "destination_router",
    },
]

LOAD_DESTINATION_MODEL_SPECS_PRE = [
    {
        "phase": "pre",
        "fn": load_json,
        "args": ["meta.Routers.$destination_router.specs"],
        "when": "destination_router",
        "result": "destination_specs",
    },
    {
        "phase": "pre",
        "fn": validate_json_schema,
        "args": [
            "destination_specs",
            ROUTER_SCHEMA_PATH,
            "Destination router model specifications",
        ],
        "when": "destination_specs",
        "result": "destination_specs",
    },
    {
        "phase": "pre",
        "fn": validate_router_settings,
        "args": ["destination_specs"],
        "when": "destination_specs",
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
            "meta.Routers.$destination_router.template",
            "destination_specs",
            "meta.Routers.$destination_router.password",
            "Enter router password: ",
            "meta.Routers.$destination_router.device_key",
        ],
        "when": "destination_specs",
        "result": "converted_decoded_config",
    },
]

MIGRATION_CONVERT_SAVE_EXEC = [
    {
        "phase": "exec",
        "fn": save_router_config,
        "args": [
            "converted_decoded_config",
            "meta.Routers.$destination_router.migration_converted",
            "destination_specs",
        ],
        "when": "converted_decoded_config",
        "result": "converted_save_ok",
    },
]

MIGRATION_CONVERT_EXTRACT_EXEC = [
    {
        "phase": "exec",
        "fn": extract_router_config,
        "args": [
            "meta.Routers.$destination_router.migration_converted",
            "meta.Routers.$destination_router.migration_converted_dir",
            "destination_specs",
        ],
        "when": "converted_save_ok",
        "result": "converted_extracted_path",
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
            "meta.Routers.$selected_router.migration_edited_dir",
            "meta.Routers.$destination_router.migration_converted_dir",
            "model_specs",
            "destination_specs",
        ],
        "when": ["model_specs", "destination_specs"],
        "result": "converted_path",
    },
]

# ---------------------------------------------------------------------
# SHOW MODEL SPECIFICATIONS HELP
# ---------------------------------------------------------------------

SHOW_MODEL_SPECS_HELP_EXEC = [
    {
        "phase": "exec",
        "fn": display_readme,
        "args": ["meta.Common Locations.model_specs_readme_path"],
        "result": "display_readme_result",
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
        "result": "display_config_doc_result",
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
