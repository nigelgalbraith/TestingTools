from __future__ import annotations

from typing import Any, Dict

from modules.json_utils import load_json, validate_json_schema
from modules.display_utils import display_config_doc, select_from_list, display_readme
from modules.file_utils import get_directory_status
from modules.router_utils import (
    resolve_router_operations,
    build_encode_operations,
    build_decode_operations,
    build_edit_operations,
    build_view_operations,
    run_router_operations,
    read_router_input,
    prepare_codec_context,
    load_target_router_credentials,
    validate_router_field_mappings,
    validate_decoded_configuration,
    validate_configuration_changes,
    extract_configuration_file,
    extract_router_config,
    display_configuration_values,
    display_router_operations,
    read_configuration_source,
    prepare_configuration_context,
    prompt_router_changes,
    prepare_router_conversion,
    prepare_encode_paths,
    compare_configuration_files,
    prepare_encode_payload,
    verify_encoded_backup,
    save_router_config,
    save_configuration_directory,
    save_encoded_outputs,
    report_encoded_backup,
)

from modules.router_config_utils import (
    xml_field_values,
    view_key_value_values,
    edit_key_value_values,
    update_xml_fields,
    validate_key_value_settings,
    validate_xml_field_settings,
)

from modules.router_encryption_utils import (
    decrypt_aes_128_cbc_field,
    encrypt_aes_128_cbc_field,
    encrypt_aes_256_cbc,
    decrypt_aes_256_cbc,
    encrypt_aes_256_cbc_fixed_key,
    decrypt_aes_256_cbc_fixed_key,
    encrypt_technicolor_thenc,
    decrypt_technicolor_thenc,
    calculate_payload_checksum,
    decode_rsa_md5_configuration,
    encode_rsa_md5_configuration,
    validate_legacy_aes_settings,
    validate_fixed_key_settings,
    validate_device_key_settings,
    validate_rsa_md5_settings,
    validate_rsa_md5_signing_settings,
    validate_field_encryption_settings,
)

from modules.router_format_utils import (
    rebuild_tar_archive,
    read_tar_files,
    split_line_wrapper,
    prepare_line_wrapper,
    parse_technicolor_wrapper,
    parse_encrypted_configuration,
    rebuild_technicolor_wrapper,
    encode_base64_payload,
    decode_base64_payload,
    unpack_signed_configuration,
    pack_signed_configuration,
    validate_signed_configuration_settings,
    validate_tar_configuration,
    validate_xml_declaration,
    extract_tar_archive,
    validate_base64_settings,
    validate_line_wrapper_settings,
    validate_technicolor_settings,
)

ROUTER_FUNCTIONS = {
    "encode": {
        "functions": {
            "tar.gz": rebuild_tar_archive,
            "rsa-md5": encode_rsa_md5_configuration,
            "signed-zlib": pack_signed_configuration,
            "aes-256-cbc": encrypt_aes_256_cbc,
            "fixed-key": encrypt_aes_256_cbc_fixed_key,
            "device-key": encrypt_technicolor_thenc,
            "openssl-legacy": encrypt_aes_256_cbc,
            "base64": encode_base64_payload,
            "line-wrapper": prepare_line_wrapper,
            "technicolor-thenc": rebuild_technicolor_wrapper,
            "encrypted-configuration": parse_encrypted_configuration,
            "aes-128-cbc-zero-padded-base64": encrypt_aes_128_cbc_field,
        },
        "validate": {
            "signed-zlib": validate_signed_configuration_settings,
            "aes-256-cbc": validate_legacy_aes_settings,
            "openssl-legacy": validate_legacy_aes_settings,
            "fixed-key": validate_fixed_key_settings,
            "device-key": validate_device_key_settings,
            "base64": validate_base64_settings,
            "line-wrapper": validate_line_wrapper_settings,
            "technicolor-thenc": validate_technicolor_settings,
            "aes-128-cbc-zero-padded-base64": validate_field_encryption_settings,
            "rsa-md5": validate_rsa_md5_signing_settings,
        },
    },
    "decode": {
        "functions": {
            "line-wrapper": split_line_wrapper,
            "technicolor-thenc": parse_technicolor_wrapper,
            "encrypted-configuration": parse_encrypted_configuration,
            "base64": decode_base64_payload,
            "aes-256-cbc": decrypt_aes_256_cbc,
            "fixed-key": decrypt_aes_256_cbc_fixed_key,
            "device-key": decrypt_technicolor_thenc,
            "openssl-legacy": decrypt_aes_256_cbc,
            "tar.gz": read_tar_files,
            "signed-zlib": unpack_signed_configuration,
            "rsa-md5": decode_rsa_md5_configuration,
            "aes-128-cbc-zero-padded-base64": decrypt_aes_128_cbc_field,
        },
        "validate": {
            "signed-zlib": validate_signed_configuration_settings,
            "aes-256-cbc": validate_legacy_aes_settings,
            "openssl-legacy": validate_legacy_aes_settings,
            "fixed-key": validate_fixed_key_settings,
            "device-key": validate_device_key_settings,
            "base64": validate_base64_settings,
            "line-wrapper": validate_line_wrapper_settings,
            "technicolor-thenc": validate_technicolor_settings,
            "aes-128-cbc-zero-padded-base64": validate_field_encryption_settings,
            "rsa-md5": validate_rsa_md5_settings,
        },
    },
    "extract": {
        "tar.gz": extract_tar_archive,
        "signed-zlib": extract_configuration_file,
    },
    "check": {
        "tar.gz": validate_tar_configuration,
        "signed-zlib": validate_xml_declaration,
    },
    "checksum": {
        "md5": calculate_payload_checksum,
        "sha256": calculate_payload_checksum,
        "sha512": calculate_payload_checksum,
    },
    "edit": {
        "functions": {
            "key-value": edit_key_value_values,
            "xml": update_xml_fields,
        },
        "validate": {
            "key-value": validate_key_value_settings,
            "xml": validate_xml_field_settings,
        },
    },
    "view": {
        "functions": {
            "key-value": view_key_value_values,
            "xml": xml_field_values,
        },
        "validate": {
            "key-value": validate_key_value_settings,
            "xml": validate_xml_field_settings,
        },
    },
}


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
        "args": ['meta.Routers'],
        "result": "router_choices",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": ['Select router', 'router_choices'],
        "when": 'router_choices',
        "result": "selected_router",
    },
]


# ---------------------------------------------------------------------
# SELECT DESTINATION ROUTER PRE
# ---------------------------------------------------------------------

SELECT_DESTINATION_ROUTER_PRE = [
    {
        "phase": "pre",
        "fn": list,
        "args": ['meta.Routers'],
        "result": "destination_router_choices",
    },
    {
        "phase": "pre",
        "fn": select_from_list,
        "args": ['Select destination router', 'destination_router_choices'],
        "when": 'destination_router_choices',
        "result": "destination_router",
    },
]


# ---------------------------------------------------------------------
# LOAD ROUTER MODEL SPECS PRE
# ---------------------------------------------------------------------

LOAD_ROUTER_MODEL_SPECS_PRE = [
    {
        "phase": "pre",
        "fn": load_json,
        "args": ['meta.Routers.$selected_router.specs'],
        "when": 'selected_router',
        "result": "raw_specs",
    },
    {
        "phase": "pre",
        "fn": validate_json_schema,
        "args": ['ctx.raw_specs', ROUTER_SCHEMA_PATH, 'Router model specifications'],
        "when": 'raw_specs',
        "result": "model_specs",
    },
    {
        "phase": "pre",
        "fn": validate_router_field_mappings,
        "args": ['ctx.model_specs'],
        "when": 'model_specs',
        "result": "fields_validated",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['encode']['functions'], 'encode'],
        "when": 'fields_validated',
        "result": "encode_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['encode']['validate'], 'encode'],
        "when": 'fields_validated',
        "result": "encode_validate_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['decode']['functions'], 'decode'],
        "when": 'fields_validated',
        "result": "decode_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['decode']['validate'], 'decode'],
        "when": 'fields_validated',
        "result": "decode_validate_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['edit']['functions'], 'edit'],
        "when": 'fields_validated',
        "result": "edit_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['edit']['validate'], 'edit'],
        "when": 'fields_validated',
        "result": "edit_validate_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['view']['functions'], 'view'],
        "when": 'fields_validated',
        "result": "view_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['view']['validate'], 'view'],
        "when": 'fields_validated',
        "result": "view_validate_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['extract'], 'extract'],
        "when": 'fields_validated',
        "result": "extract_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['check'], 'check'],
        "when": 'fields_validated',
        "result": "check_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.model_specs', ROUTER_FUNCTIONS['checksum'], 'checksum'],
        "when": 'fields_validated',
        "result": "checksum_operations",
    },
    {
        "phase": "pre",
        "fn": build_encode_operations,
        "args": ['ctx.model_specs', 'ctx.encode_operations', 'ctx.encode_validate_operations'],
        "when": 'fields_validated',
        "result": "encode_operations_list",
    },
    {
        "phase": "pre",
        "fn": build_decode_operations,
        "args": ['ctx.model_specs', 'ctx.decode_operations', 'ctx.decode_validate_operations'],
        "when": 'fields_validated',
        "result": "decode_operations_list",
    },
    {
        "phase": "pre",
        "fn": build_edit_operations,
        "args": ['ctx.model_specs', 'ctx.edit_operations', 'ctx.edit_validate_operations'],
        "when": 'fields_validated',
        "result": "edit_operations_list",
    },
    {
        "phase": "pre",
        "fn": build_view_operations,
        "args": ['ctx.model_specs', 'ctx.view_operations', 'ctx.view_validate_operations'],
        "when": 'fields_validated',
        "result": "view_operations_list",
    },
]


# ---------------------------------------------------------------------
# LOAD DESTINATION MODEL SPECS PRE
# ---------------------------------------------------------------------

LOAD_DESTINATION_MODEL_SPECS_PRE = [
    {
        "phase": "pre",
        "fn": load_json,
        "args": ['meta.Routers.$destination_router.specs'],
        "when": 'destination_router',
        "result": "destination_raw_specs",
    },
    {
        "phase": "pre",
        "fn": validate_json_schema,
        "args": ['ctx.destination_raw_specs', ROUTER_SCHEMA_PATH, 'Destination router model specifications'],
        "when": 'destination_raw_specs',
        "result": "destination_specs",
    },
    {
        "phase": "pre",
        "fn": validate_router_field_mappings,
        "args": ['ctx.destination_specs'],
        "when": 'destination_specs',
        "result": "destination_fields_validated",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['encode']['functions'], 'encode'],
        "when": 'destination_fields_validated',
        "result": "destination_encode_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['encode']['validate'], 'encode'],
        "when": 'destination_fields_validated',
        "result": "destination_encode_validate_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['decode']['functions'], 'decode'],
        "when": 'destination_fields_validated',
        "result": "destination_decode_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['decode']['validate'], 'decode'],
        "when": 'destination_fields_validated',
        "result": "destination_decode_validate_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['edit']['functions'], 'edit'],
        "when": 'destination_fields_validated',
        "result": "destination_edit_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['edit']['validate'], 'edit'],
        "when": 'destination_fields_validated',
        "result": "destination_edit_validate_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['view']['functions'], 'view'],
        "when": 'destination_fields_validated',
        "result": "destination_view_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['view']['validate'], 'view'],
        "when": 'destination_fields_validated',
        "result": "destination_view_validate_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['extract'], 'extract'],
        "when": 'destination_fields_validated',
        "result": "destination_extract_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['check'], 'check'],
        "when": 'destination_fields_validated',
        "result": "destination_check_operations",
    },
    {
        "phase": "pre",
        "fn": resolve_router_operations,
        "args": ['ctx.destination_specs', ROUTER_FUNCTIONS['checksum'], 'checksum'],
        "when": 'destination_fields_validated',
        "result": "destination_checksum_operations",
    },
    {
        "phase": "pre",
        "fn": build_encode_operations,
        "args": [
            'ctx.destination_specs',
            'ctx.destination_encode_operations',
            'ctx.destination_encode_validate_operations',
        ],
        "when": 'destination_fields_validated',
        "result": "destination_encode_operations_list",
    },
    {
        "phase": "pre",
        "fn": build_decode_operations,
        "args": [
            'ctx.destination_specs',
            'ctx.destination_decode_operations',
            'ctx.destination_decode_validate_operations',
        ],
        "when": 'destination_fields_validated',
        "result": "destination_decode_operations_list",
    },
    {
        "phase": "pre",
        "fn": build_edit_operations,
        "args": [
            'ctx.destination_specs',
            'ctx.destination_edit_operations',
            'ctx.destination_edit_validate_operations',
        ],
        "when": 'destination_fields_validated',
        "result": "destination_edit_operations_list",
    },
    {
        "phase": "pre",
        "fn": build_view_operations,
        "args": [
            'ctx.destination_specs',
            'ctx.destination_view_operations',
            'ctx.destination_view_validate_operations',
        ],
        "when": 'destination_fields_validated',
        "result": "destination_view_operations_list",
    },
]


# ---------------------------------------------------------------------
# READ TEMPLATE EXEC
# ---------------------------------------------------------------------

READ_TEMPLATE_EXEC = [
    {
        "phase": "exec",
        "fn": read_router_input,
        "args": ['meta.Routers.$selected_router.template'],
        "when": 'model_specs',
        "result": "router_backup",
    },
]


# ---------------------------------------------------------------------
# READ MIGRATION BACKUP EXEC
# ---------------------------------------------------------------------

READ_MIGRATION_BACKUP_EXEC = [
    {
        "phase": "exec",
        "fn": read_router_input,
        "args": ['meta.Routers.$selected_router.original'],
        "when": 'model_specs',
        "result": "router_backup",
    },
]


# ---------------------------------------------------------------------
# READ DESTINATION TEMPLATE EXEC
# ---------------------------------------------------------------------

READ_DESTINATION_TEMPLATE_EXEC = [
    {
        "phase": "exec",
        "fn": read_router_input,
        "args": ['meta.Routers.$destination_router.template'],
        "when": 'destination_specs',
        "result": "destination_backup",
    },
]


# ---------------------------------------------------------------------
# READ MIGRATION DESTINATION EXEC
# ---------------------------------------------------------------------

READ_MIGRATION_DESTINATION_EXEC = [
    {
        "phase": "exec",
        "fn": read_router_input,
        "args": ['meta.Routers.$destination_router.template'],
        "when": 'migration_source',
        "result": "destination_backup",
    },
]


# ---------------------------------------------------------------------
# DECODE ROUTER CONFIG EXEC
# ---------------------------------------------------------------------

DECODE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_codec_context,
        "args": [
            'ctx.model_specs',
            'meta.Routers.$selected_router.password',
            'Enter router password: ',
            'meta.Routers.$selected_router.device_key',
            'ctx.checksum_operations',
        ],
        "when": 'router_backup',
        "result": "decode_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.router_backup.data', 'ctx.decode_operations_list', 'ctx.decode_context'],
        "when": 'decode_context',
        "result": "decoded_config",
    },
    {
        "phase": "exec",
        "fn": validate_decoded_configuration,
        "args": [
            'ctx.decoded_config',
            'ctx.model_specs',
            'ctx.check_operations',
            'ctx.checksum_operations',
            'ctx.decode_context',
            'ctx.view_operations_list',
        ],
        "when": 'decoded_config',
        "result": "decoded_validated",
    },
    {
        "phase": "exec",
        "fn": save_router_config,
        "args": ['ctx.decoded_config', 'meta.Routers.$selected_router.template_decoded', 'ctx.model_specs'],
        "when": 'decoded_validated',
        "result": "saved_archive",
    },
    {
        "phase": "exec",
        "fn": extract_router_config,
        "args": [
            'ctx.saved_archive',
            'meta.Routers.$selected_router.template_decoded_dir',
            'ctx.model_specs',
            'ctx.extract_operations',
            'ctx.checksum_operations',
        ],
        "when": 'saved_archive',
        "result": "extracted_path",
    },
]


# ---------------------------------------------------------------------
# MIGRATION DECODE ROUTER CONFIG EXEC
# ---------------------------------------------------------------------

MIGRATION_DECODE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_codec_context,
        "args": [
            'ctx.model_specs',
            None,
            'Enter SOURCE router password: ',
            'meta.Routers.$selected_router.device_key',
            'ctx.checksum_operations',
        ],
        "when": 'router_backup',
        "result": "migration_decode_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.router_backup.data', 'ctx.decode_operations_list', 'ctx.migration_decode_context'],
        "when": 'migration_decode_context',
        "result": "migration_decoded_config",
    },
    {
        "phase": "exec",
        "fn": validate_decoded_configuration,
        "args": [
            'ctx.migration_decoded_config',
            'ctx.model_specs',
            'ctx.check_operations',
            'ctx.checksum_operations',
            'ctx.migration_decode_context',
            'ctx.view_operations_list',
        ],
        "when": 'migration_decoded_config',
        "result": "migration_decoded_validated",
    },
    {
        "phase": "exec",
        "fn": save_router_config,
        "args": [
            'ctx.migration_decoded_config',
            'meta.Routers.$selected_router.migration_decoded',
            'ctx.model_specs',
        ],
        "when": 'migration_decoded_validated',
        "result": "migration_saved_archive",
    },
    {
        "phase": "exec",
        "fn": extract_router_config,
        "args": [
            'ctx.migration_saved_archive',
            'meta.Routers.$selected_router.migration_decoded_dir',
            'ctx.model_specs',
            'ctx.extract_operations',
            'ctx.checksum_operations',
        ],
        "when": 'migration_saved_archive',
        "result": "migration_extracted_path",
    },
]


# ---------------------------------------------------------------------
# DESTINATION DECODE ROUTER CONFIG EXEC
# ---------------------------------------------------------------------

DESTINATION_DECODE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_codec_context,
        "args": [
            'ctx.destination_specs',
            'meta.Routers.$destination_router.password',
            'Enter router password: ',
            'meta.Routers.$destination_router.device_key',
            'ctx.destination_checksum_operations',
        ],
        "when": 'destination_backup',
        "result": "destination_decode_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": [
            'ctx.destination_backup.data',
            'ctx.destination_decode_operations_list',
            'ctx.destination_decode_context',
        ],
        "when": 'destination_decode_context',
        "result": "destination_decoded_config",
    },
    {
        "phase": "exec",
        "fn": validate_decoded_configuration,
        "args": [
            'ctx.destination_decoded_config',
            'ctx.destination_specs',
            'ctx.destination_check_operations',
            'ctx.destination_checksum_operations',
            'ctx.destination_decode_context',
            'ctx.destination_view_operations_list',
        ],
        "when": 'destination_decoded_config',
        "result": "destination_decoded_validated",
    },
    {
        "phase": "exec",
        "fn": save_router_config,
        "args": [
            'ctx.destination_decoded_config',
            'meta.Routers.$destination_router.migration_converted',
            'ctx.destination_specs',
        ],
        "when": 'destination_decoded_validated',
        "result": "destination_saved_archive",
    },
    {
        "phase": "exec",
        "fn": extract_router_config,
        "args": [
            'ctx.destination_saved_archive',
            'meta.Routers.$destination_router.migration_converted_dir',
            'ctx.destination_specs',
            'ctx.destination_extract_operations',
            'ctx.destination_checksum_operations',
        ],
        "when": 'destination_saved_archive',
        "result": "destination_extracted_path",
    },
]


# ---------------------------------------------------------------------
# LOAD DECODED SOURCE EXEC
# ---------------------------------------------------------------------

LOAD_DECODED_SOURCE_EXEC = [
    {
        "phase": "exec",
        "fn": read_configuration_source,
        "args": ['meta.Routers.$selected_router.template_decoded_dir', 'ctx.model_specs.router_specs.edit'],
        "when": 'model_specs',
        "result": "edit_source",
    },
]


# ---------------------------------------------------------------------
# LOAD EXTRACTED SOURCE EXEC
# ---------------------------------------------------------------------

LOAD_EXTRACTED_SOURCE_EXEC = [
    {
        "phase": "exec",
        "fn": read_configuration_source,
        "args": ['ctx.extracted_path', 'ctx.model_specs.router_specs.edit'],
        "when": 'extracted_path',
        "result": "edit_source",
    },
]


# ---------------------------------------------------------------------
# LOAD MIGRATION DECODED EXEC
# ---------------------------------------------------------------------

LOAD_MIGRATION_DECODED_EXEC = [
    {
        "phase": "exec",
        "fn": read_configuration_source,
        "args": ['meta.Routers.$selected_router.migration_decoded_dir', 'ctx.model_specs.router_specs.edit'],
        "when": 'model_specs',
        "result": "edit_source",
    },
]


# ---------------------------------------------------------------------
# LOAD MIGRATION EXTRACTED EXEC
# ---------------------------------------------------------------------

LOAD_MIGRATION_EXTRACTED_EXEC = [
    {
        "phase": "exec",
        "fn": read_configuration_source,
        "args": ['ctx.migration_extracted_path', 'ctx.model_specs.router_specs.edit'],
        "when": 'migration_extracted_path',
        "result": "edit_source",
    },
]


# ---------------------------------------------------------------------
# LOAD EDITED SOURCE EXEC
# ---------------------------------------------------------------------

LOAD_EDITED_SOURCE_EXEC = [
    {
        "phase": "exec",
        "fn": read_configuration_source,
        "args": ['meta.Routers.$selected_router.template_edited_dir', 'ctx.model_specs.router_specs.edit'],
        "when": 'model_specs',
        "result": "view_source",
    },
]


# ---------------------------------------------------------------------
# LOAD MIGRATION EDITED EXEC
# ---------------------------------------------------------------------

LOAD_MIGRATION_EDITED_EXEC = [
    {
        "phase": "exec",
        "fn": read_configuration_source,
        "args": ['meta.Routers.$selected_router.migration_edited_dir', 'ctx.model_specs.router_specs.edit'],
        "when": 'model_specs',
        "result": "view_source",
    },
]


# ---------------------------------------------------------------------
# LOAD CONVERSION SOURCE EXEC
# ---------------------------------------------------------------------

LOAD_CONVERSION_SOURCE_EXEC = [
    {
        "phase": "exec",
        "fn": read_configuration_source,
        "args": ['meta.Routers.$selected_router.migration_edited_dir', 'ctx.model_specs.router_specs.edit'],
        "when": 'model_specs',
        "result": "migration_source",
    },
]


# ---------------------------------------------------------------------
# LOAD SAVED CONVERSION SOURCE EXEC
# ---------------------------------------------------------------------

LOAD_SAVED_CONVERSION_SOURCE_EXEC = [
    {
        "phase": "exec",
        "fn": read_configuration_source,
        "args": ['ctx.edited_path', 'ctx.model_specs.router_specs.edit'],
        "when": 'edited_path',
        "result": "migration_source",
    },
]


# ---------------------------------------------------------------------
# LOAD PREPARED DESTINATION EXEC
# ---------------------------------------------------------------------

LOAD_PREPARED_DESTINATION_EXEC = [
    {
        "phase": "exec",
        "fn": read_configuration_source,
        "args": [
            'meta.Routers.$destination_router.migration_converted_dir',
            'ctx.destination_specs.router_specs.edit',
        ],
        "when": 'destination_specs',
        "result": "conversion_destination",
    },
]


# ---------------------------------------------------------------------
# LOAD EXTRACTED DESTINATION EXEC
# ---------------------------------------------------------------------

LOAD_EXTRACTED_DESTINATION_EXEC = [
    {
        "phase": "exec",
        "fn": read_configuration_source,
        "args": ['ctx.destination_extracted_path', 'ctx.destination_specs.router_specs.edit'],
        "when": 'destination_extracted_path',
        "result": "conversion_destination",
    },
]


# ---------------------------------------------------------------------
# VIEW DECODED CONFIG EXEC
# ---------------------------------------------------------------------

VIEW_DECODED_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_configuration_context,
        "args": [
            'ctx.edit_source',
            'ctx.model_specs',
            'ctx.decode_operations',
            'ctx.encode_operations',
            'ctx.view_operations_list',
        ],
        "when": 'edit_source',
        "result": "view_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.view_context.original', 'ctx.view_operations_list', 'ctx.view_context'],
        "when": 'view_context',
        "result": "view_values",
    },
    {
        "phase": "exec",
        "fn": display_configuration_values,
        "args": ['ctx.view_values', 'ctx.view_context', 'ctx.model_specs.config_fields'],
        "when": 'view_context',
        "result": "view_reported",
    },
]


# ---------------------------------------------------------------------
# VIEW EDITED CONFIG EXEC
# ---------------------------------------------------------------------

VIEW_EDITED_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_configuration_context,
        "args": [
            'ctx.view_source',
            'ctx.model_specs',
            'ctx.decode_operations',
            'ctx.encode_operations',
            'ctx.view_operations_list',
        ],
        "when": 'view_source',
        "result": "view_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.view_context.original', 'ctx.view_operations_list', 'ctx.view_context'],
        "when": 'view_context',
        "result": "view_values",
    },
    {
        "phase": "exec",
        "fn": display_configuration_values,
        "args": ['ctx.view_values', 'ctx.view_context', 'ctx.model_specs.config_fields'],
        "when": 'view_context',
        "result": "view_reported",
    },
]


# ---------------------------------------------------------------------
# EDIT ROUTER CONFIG EXEC
# ---------------------------------------------------------------------

EDIT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_configuration_context,
        "args": [
            'ctx.edit_source',
            'ctx.model_specs',
            'ctx.decode_operations',
            'ctx.encode_operations',
            'ctx.view_operations_list',
            'ctx.edit_operations_list',
            'meta.Routers.$selected_router.template_edited_dir',
        ],
        "when": 'edit_source',
        "result": "edit_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.edit_context.original', 'ctx.view_operations_list', 'ctx.edit_context'],
        "when": 'edit_context',
        "result": "edit_values",
    },
    {
        "phase": "exec",
        "fn": prompt_router_changes,
        "args": ['ctx.edit_values', 'ctx.edit_context'],
        "when": 'edit_context',
        "result": "changes_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.changes_context.original', 'ctx.edit_operations_list', 'ctx.changes_context'],
        "when": 'changes_context',
        "result": "edited_text",
    },
    {
        "phase": "exec",
        "fn": save_configuration_directory,
        "args": ['ctx.changes_context', 'ctx.edited_text'],
        "when": 'edited_text',
        "result": "edited_path",
    },
]


# ---------------------------------------------------------------------
# MIGRATION EDIT ROUTER CONFIG EXEC
# ---------------------------------------------------------------------

MIGRATION_EDIT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_configuration_context,
        "args": [
            'ctx.edit_source',
            'ctx.model_specs',
            'ctx.decode_operations',
            'ctx.encode_operations',
            'ctx.view_operations_list',
            'ctx.edit_operations_list',
            'meta.Routers.$selected_router.migration_edited_dir',
        ],
        "when": 'edit_source',
        "result": "edit_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.edit_context.original', 'ctx.view_operations_list', 'ctx.edit_context'],
        "when": 'edit_context',
        "result": "edit_values",
    },
    {
        "phase": "exec",
        "fn": prompt_router_changes,
        "args": ['ctx.edit_values', 'ctx.edit_context'],
        "when": 'edit_context',
        "result": "changes_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.changes_context.original', 'ctx.edit_operations_list', 'ctx.changes_context'],
        "when": 'changes_context',
        "result": "edited_text",
    },
    {
        "phase": "exec",
        "fn": save_configuration_directory,
        "args": ['ctx.changes_context', 'ctx.edited_text'],
        "when": 'edited_text',
        "result": "edited_path",
    },
]


# ---------------------------------------------------------------------
# CONVERT ROUTER CONFIG EXEC
# ---------------------------------------------------------------------

CONVERT_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_configuration_context,
        "args": [
            'ctx.migration_source',
            'ctx.model_specs',
            'ctx.decode_operations',
            'ctx.encode_operations',
            'ctx.view_operations_list',
        ],
        "when": ['migration_source', 'conversion_destination'],
        "result": "source_view_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.source_view_context.original', 'ctx.view_operations_list', 'ctx.source_view_context'],
        "when": 'source_view_context',
        "result": "source_values",
    },
    {
        "phase": "exec",
        "fn": prepare_configuration_context,
        "args": [
            'ctx.conversion_destination',
            'ctx.destination_specs',
            'ctx.destination_decode_operations',
            'ctx.destination_encode_operations',
            'ctx.destination_view_operations_list',
            'ctx.destination_edit_operations_list',
        ],
        "when": ['migration_source', 'conversion_destination'],
        "result": "conversion_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": [
            'ctx.conversion_context.original',
            'ctx.destination_view_operations_list',
            'ctx.conversion_context',
        ],
        "when": 'conversion_context',
        "result": "destination_values",
    },
    {
        "phase": "exec",
        "fn": prepare_router_conversion,
        "args": [
            'ctx.source_values',
            'ctx.destination_values',
            'ctx.source_view_context',
            'ctx.conversion_context',
        ],
        "when": ['source_view_context', 'conversion_context'],
        "result": "conversion_changes",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": [
            'ctx.conversion_changes.original',
            'ctx.destination_edit_operations_list',
            'ctx.conversion_changes',
        ],
        "when": 'conversion_changes',
        "result": "converted_text",
    },
    {
        "phase": "exec",
        "fn": save_configuration_directory,
        "args": ['ctx.conversion_changes', 'ctx.converted_text'],
        "when": 'converted_text',
        "result": "converted_path",
    },
]


# ---------------------------------------------------------------------
# PREPARE ENCODE PATHS EXEC
# ---------------------------------------------------------------------

PREPARE_ENCODE_PATHS_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_encode_paths,
        "args": [
            'meta.Routers.$selected_router.template_edited_dir',
            'meta.Routers.$selected_router.template',
            'meta.Routers.$selected_router.template_edited',
            'meta.Routers.$selected_router.template_encoded',
            'ctx.model_specs',
        ],
        "when": 'model_specs',
        "result": "encode_paths",
    },
]


# ---------------------------------------------------------------------
# PREPARE SAVED ENCODE PATHS EXEC
# ---------------------------------------------------------------------

PREPARE_SAVED_ENCODE_PATHS_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_encode_paths,
        "args": [
            'ctx.edited_path',
            'meta.Routers.$selected_router.template',
            'meta.Routers.$selected_router.template_edited',
            'meta.Routers.$selected_router.template_encoded',
            'ctx.model_specs',
        ],
        "when": 'edited_path',
        "result": "encode_paths",
    },
]


# ---------------------------------------------------------------------
# PREPARE MIGRATION ENCODE PATHS EXEC
# ---------------------------------------------------------------------

PREPARE_MIGRATION_ENCODE_PATHS_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_encode_paths,
        "args": [
            'meta.Routers.$destination_router.migration_converted_dir',
            'meta.Routers.$destination_router.template',
            'meta.Routers.$destination_router.migration_converted',
            'meta.Routers.$destination_router.migration_encoded',
            'ctx.destination_specs',
        ],
        "when": 'destination_specs',
        "result": "encode_paths",
    },
]


# ---------------------------------------------------------------------
# PREPARE CONVERTED ENCODE PATHS EXEC
# ---------------------------------------------------------------------

PREPARE_CONVERTED_ENCODE_PATHS_EXEC = [
    {
        "phase": "exec",
        "fn": prepare_encode_paths,
        "args": [
            'ctx.converted_path',
            'meta.Routers.$destination_router.template',
            'meta.Routers.$destination_router.migration_converted',
            'meta.Routers.$destination_router.migration_encoded',
            'ctx.destination_specs',
        ],
        "when": 'converted_path',
        "result": "encode_paths",
    },
]


# ---------------------------------------------------------------------
# ENCODE ROUTER CONFIG EXEC
# ---------------------------------------------------------------------

ENCODE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": read_router_input,
        "args": ['ctx.encode_paths.original'],
        "when": 'encode_paths',
        "result": "encode_original",
    },
    {
        "phase": "exec",
        "fn": prepare_codec_context,
        "args": [
            'ctx.model_specs',
            'meta.Routers.$selected_router.password',
            'Enter router password: ',
            'meta.Routers.$selected_router.device_key',
            'ctx.checksum_operations',
        ],
        "when": 'encode_original',
        "result": "encode_original_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.encode_original.data', 'ctx.decode_operations_list', 'ctx.encode_original_context'],
        "when": 'encode_original_context',
        "result": "encode_original_archive",
    },
    {
        "phase": "exec",
        "fn": compare_configuration_files,
        "args": [
            'ctx.encode_paths.directory',
            'ctx.encode_original_context.files',
            'ctx.model_specs.router_specs.edit',
        ],
        "when": 'encode_original_archive',
        "result": "encode_comparison",
    },
    {
        "phase": "exec",
        "fn": prepare_configuration_context,
        "args": [
            'ctx.encode_comparison',
            'ctx.model_specs',
            'ctx.decode_operations',
            'ctx.encode_operations',
            'ctx.view_operations_list',
            'ctx.edit_operations_list',
        ],
        "when": 'encode_comparison',
        "result": "encode_field_context",
    },
    {
        "phase": "exec",
        "fn": validate_configuration_changes,
        "args": [
            'ctx.encode_comparison.original',
            'ctx.encode_comparison.edited',
            'ctx.model_specs',
            'ctx.encode_field_context.viewer',
            'ctx.encode_field_context.editor',
            'ctx.encode_field_context.decrypt_handler',
            'ctx.encode_field_context.encrypt_handler',
        ],
        "when": 'encode_field_context',
        "result": "encode_changes_validated",
    },
    {
        "phase": "exec",
        "fn": load_target_router_credentials,
        "args": [
            'ctx.encode_original_context',
            'Enter target router password (Enter to use template password): ',
        ],
        "when": 'encode_changes_validated',
        "result": "target_credentials",
    },
    {
        "phase": "exec",
        "fn": prepare_encode_payload,
        "args": [
            'ctx.encode_original_archive',
            'ctx.encode_original_context',
            'ctx.encode_comparison',
            'ctx.target_credentials',
            'ctx.model_specs.router_specs.encode',
            'ctx.encode_paths.directory',
        ],
        "when": ['encode_changes_validated', 'target_credentials'],
        "result": "encode_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.encode_context.data', 'ctx.encode_operations_list', 'ctx.encode_context'],
        "when": 'encode_context',
        "result": "encoded_backup",
    },
    {
        "phase": "exec",
        "fn": dict,
        "args": ['ctx.encode_context'],
        "when": 'encoded_backup',
        "result": "verification_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.encoded_backup', 'ctx.decode_operations_list', 'ctx.verification_context'],
        "when": 'verification_context',
        "result": "recovered_config",
    },
    {
        "phase": "exec",
        "fn": verify_encoded_backup,
        "args": ['ctx.recovered_config', 'ctx.encode_context.expected'],
        "when": 'recovered_config',
        "result": "encoded_verified",
    },
    {
        "phase": "exec",
        "fn": validate_decoded_configuration,
        "args": [
            'ctx.recovered_config',
            'ctx.model_specs',
            'ctx.check_operations',
            'ctx.checksum_operations',
            'ctx.verification_context',
            'ctx.view_operations_list',
        ],
        "when": 'encoded_verified',
        "result": "recovered_validated",
    },
    {
        "phase": "exec",
        "fn": save_encoded_outputs,
        "args": ['ctx.encode_paths', 'ctx.encoded_backup', 'ctx.recovered_config', 'ctx.encode_context'],
        "when": 'recovered_validated',
        "result": "encoded_path",
    },
    {
        "phase": "exec",
        "fn": report_encoded_backup,
        "args": ['ctx.encoded_path', 'ctx.encode_paths', 'ctx.encode_context'],
        "when": 'encoded_path',
        "result": "encoded_reported",
    },
]


# ---------------------------------------------------------------------
# MIGRATION ENCODE ROUTER CONFIG EXEC
# ---------------------------------------------------------------------

MIGRATION_ENCODE_ROUTER_CONFIG_EXEC = [
    {
        "phase": "exec",
        "fn": read_router_input,
        "args": ['ctx.encode_paths.original'],
        "when": 'encode_paths',
        "result": "encode_original",
    },
    {
        "phase": "exec",
        "fn": prepare_codec_context,
        "args": [
            'ctx.destination_specs',
            'meta.Routers.$destination_router.password',
            'Enter router password: ',
            'meta.Routers.$destination_router.device_key',
            'ctx.destination_checksum_operations',
        ],
        "when": 'encode_original',
        "result": "encode_original_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": [
            'ctx.encode_original.data',
            'ctx.destination_decode_operations_list',
            'ctx.encode_original_context',
        ],
        "when": 'encode_original_context',
        "result": "encode_original_archive",
    },
    {
        "phase": "exec",
        "fn": compare_configuration_files,
        "args": [
            'ctx.encode_paths.directory',
            'ctx.encode_original_context.files',
            'ctx.destination_specs.router_specs.edit',
        ],
        "when": 'encode_original_archive',
        "result": "encode_comparison",
    },
    {
        "phase": "exec",
        "fn": prepare_configuration_context,
        "args": [
            'ctx.encode_comparison',
            'ctx.destination_specs',
            'ctx.destination_decode_operations',
            'ctx.destination_encode_operations',
            'ctx.destination_view_operations_list',
            'ctx.destination_edit_operations_list',
        ],
        "when": 'encode_comparison',
        "result": "encode_field_context",
    },
    {
        "phase": "exec",
        "fn": validate_configuration_changes,
        "args": [
            'ctx.encode_comparison.original',
            'ctx.encode_comparison.edited',
            'ctx.destination_specs',
            'ctx.encode_field_context.viewer',
            'ctx.encode_field_context.editor',
            'ctx.encode_field_context.decrypt_handler',
            'ctx.encode_field_context.encrypt_handler',
        ],
        "when": 'encode_field_context',
        "result": "encode_changes_validated",
    },
    {
        "phase": "exec",
        "fn": load_target_router_credentials,
        "args": ['ctx.encode_original_context', 'Enter DESTINATION router password: '],
        "when": 'encode_changes_validated',
        "result": "target_credentials",
    },
    {
        "phase": "exec",
        "fn": prepare_encode_payload,
        "args": [
            'ctx.encode_original_archive',
            'ctx.encode_original_context',
            'ctx.encode_comparison',
            'ctx.target_credentials',
            'ctx.destination_specs.router_specs.encode',
            'ctx.encode_paths.directory',
        ],
        "when": ['encode_changes_validated', 'target_credentials'],
        "result": "encode_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.encode_context.data', 'ctx.destination_encode_operations_list', 'ctx.encode_context'],
        "when": 'encode_context',
        "result": "encoded_backup",
    },
    {
        "phase": "exec",
        "fn": dict,
        "args": ['ctx.encode_context'],
        "when": 'encoded_backup',
        "result": "verification_context",
    },
    {
        "phase": "exec",
        "fn": run_router_operations,
        "args": ['ctx.encoded_backup', 'ctx.destination_decode_operations_list', 'ctx.verification_context'],
        "when": 'verification_context',
        "result": "recovered_config",
    },
    {
        "phase": "exec",
        "fn": verify_encoded_backup,
        "args": ['ctx.recovered_config', 'ctx.encode_context.expected'],
        "when": 'recovered_config',
        "result": "encoded_verified",
    },
    {
        "phase": "exec",
        "fn": validate_decoded_configuration,
        "args": [
            'ctx.recovered_config',
            'ctx.destination_specs',
            'ctx.destination_check_operations',
            'ctx.destination_checksum_operations',
            'ctx.verification_context',
            'ctx.destination_view_operations_list',
        ],
        "when": 'encoded_verified',
        "result": "recovered_validated",
    },
    {
        "phase": "exec",
        "fn": save_encoded_outputs,
        "args": ['ctx.encode_paths', 'ctx.encoded_backup', 'ctx.recovered_config', 'ctx.encode_context'],
        "when": 'recovered_validated',
        "result": "encoded_path",
    },
    {
        "phase": "exec",
        "fn": report_encoded_backup,
        "args": ['ctx.encoded_path', 'ctx.encode_paths', 'ctx.encode_context'],
        "when": 'encoded_path',
        "result": "encoded_reported",
    },
]


# ---------------------------------------------------------------------
# SHOW MODEL SPECS HELP EXEC
# ---------------------------------------------------------------------

SHOW_MODEL_SPECS_HELP_EXEC = [
    {
        "phase": "exec",
        "fn": display_readme,
        "args": ['meta.Common Locations.model_specs_readme_path'],
        "result": "display_readme_result",
    },
]


# ---------------------------------------------------------------------
# SHOW CONFIG DOC EXEC
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
# ACTION OPERATION DISPLAYS
# ---------------------------------------------------------------------

DISPLAY_ENCODE_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["encode_operations_list", "Encode Operations"],
        "when": "encode_operations_list",
        "result": "encode_operations_displayed",
    },
]


DISPLAY_DECODE_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["decode_operations_list", "Decode Operations"],
        "when": "decode_operations_list",
        "result": "decode_operations_displayed",
    },
]


DISPLAY_EDIT_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["edit_operations_list", "Edit Operations"],
        "when": "edit_operations_list",
        "result": "edit_operations_displayed",
    },
]


DISPLAY_VIEW_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["view_operations_list", "View Operations"],
        "when": "view_operations_list",
        "result": "view_operations_displayed",
    },
]


DISPLAY_SOURCE_DECODE_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["decode_operations_list", "Source Decode Operations"],
        "when": "decode_operations_list",
        "result": "source_decode_operations_displayed",
    },
]


DISPLAY_SOURCE_EDIT_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["edit_operations_list", "Source Edit Operations"],
        "when": "edit_operations_list",
        "result": "source_edit_operations_displayed",
    },
]


DISPLAY_SOURCE_VIEW_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["view_operations_list", "Source View Operations"],
        "when": "view_operations_list",
        "result": "source_view_operations_displayed",
    },
]


DISPLAY_DESTINATION_ENCODE_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["destination_encode_operations_list", "Destination Encode Operations"],
        "when": "destination_encode_operations_list",
        "result": "destination_encode_operations_displayed",
    },
]


DISPLAY_DESTINATION_DECODE_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["destination_decode_operations_list", "Destination Decode Operations"],
        "when": "destination_decode_operations_list",
        "result": "destination_decode_operations_displayed",
    },
]


DISPLAY_DESTINATION_EDIT_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["destination_edit_operations_list", "Destination Edit Operations"],
        "when": "destination_edit_operations_list",
        "result": "destination_edit_operations_displayed",
    },
]


DISPLAY_DESTINATION_VIEW_OPERATIONS_PRE = [
    {
        "phase": "pre",
        "fn": display_router_operations,
        "args": ["destination_view_operations_list", "Destination View Operations"],
        "when": "destination_view_operations_list",
        "result": "destination_view_operations_displayed",
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
            *DISPLAY_DECODE_OPERATIONS_PRE,
            *READ_TEMPLATE_EXEC,
            *DECODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "DECODE_CONFIG_COMPLETE",
    },
    "VIEW_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DISPLAY_VIEW_OPERATIONS_PRE,
            *LOAD_DECODED_SOURCE_EXEC,
            *VIEW_DECODED_CONFIG_EXEC,
        ],
        "label": "VIEW_CONFIG_COMPLETE",
    },
    "EDIT_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DISPLAY_EDIT_OPERATIONS_PRE,
            *LOAD_DECODED_SOURCE_EXEC,
            *EDIT_ROUTER_CONFIG_EXEC,
        ],
        "label": "EDIT_CONFIG_COMPLETE",
    },
    "VIEW_EDITED_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DISPLAY_VIEW_OPERATIONS_PRE,
            *LOAD_EDITED_SOURCE_EXEC,
            *VIEW_EDITED_CONFIG_EXEC,
        ],
        "label": "VIEW_EDITED_CONFIG_COMPLETE",
    },
    "ENCODE_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DISPLAY_ENCODE_OPERATIONS_PRE,
            *PREPARE_ENCODE_PATHS_EXEC,
            *ENCODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "ENCODE_CONFIG_COMPLETE",
    },
    "RUN_ALL_SAME_MODEL": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DISPLAY_DECODE_OPERATIONS_PRE,
            *DISPLAY_EDIT_OPERATIONS_PRE,
            *DISPLAY_ENCODE_OPERATIONS_PRE,
            *READ_TEMPLATE_EXEC,
            *DECODE_ROUTER_CONFIG_EXEC,
            *LOAD_EXTRACTED_SOURCE_EXEC,
            *EDIT_ROUTER_CONFIG_EXEC,
            *PREPARE_SAVED_ENCODE_PATHS_EXEC,
            *ENCODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "RUN_ALL_SAME_MODEL_COMPLETE",
    },
    "MIGRATION_DECODE_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DISPLAY_SOURCE_DECODE_OPERATIONS_PRE,
            *READ_MIGRATION_BACKUP_EXEC,
            *MIGRATION_DECODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "MIGRATION_DECODE_CONFIG_COMPLETE",
    },
    "MIGRATION_EDIT_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DISPLAY_SOURCE_EDIT_OPERATIONS_PRE,
            *LOAD_MIGRATION_DECODED_EXEC,
            *MIGRATION_EDIT_ROUTER_CONFIG_EXEC,
        ],
        "label": "MIGRATION_EDIT_CONFIG_COMPLETE",
    },
    "VIEW_MIGRATION_EDITED_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *DISPLAY_SOURCE_VIEW_OPERATIONS_PRE,
            *LOAD_MIGRATION_EDITED_EXEC,
            *VIEW_EDITED_CONFIG_EXEC,
        ],
        "label": "VIEW_MIGRATION_EDITED_CONFIG_COMPLETE",
    },
    "MIGRATION_CONVERT_PREPARE": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *SELECT_DESTINATION_ROUTER_PRE,
            *LOAD_DESTINATION_MODEL_SPECS_PRE,
            *DISPLAY_DESTINATION_DECODE_OPERATIONS_PRE,
            *READ_DESTINATION_TEMPLATE_EXEC,
            *DESTINATION_DECODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "MIGRATION_CONVERT_PREPARE_COMPLETE",
    },
    "MIGRATION_CONVERT_CONFIG": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *SELECT_DESTINATION_ROUTER_PRE,
            *LOAD_DESTINATION_MODEL_SPECS_PRE,
            *DISPLAY_SOURCE_VIEW_OPERATIONS_PRE,
            *DISPLAY_DESTINATION_VIEW_OPERATIONS_PRE,
            *DISPLAY_DESTINATION_EDIT_OPERATIONS_PRE,
            *LOAD_CONVERSION_SOURCE_EXEC,
            *LOAD_PREPARED_DESTINATION_EXEC,
            *CONVERT_ROUTER_CONFIG_EXEC,
        ],
        "label": "MIGRATION_CONVERT_CONFIG_COMPLETE",
    },
    "MIGRATION_ENCODE_CONFIG": {
        "pipeline": [
            *SELECT_DESTINATION_ROUTER_PRE,
            *LOAD_DESTINATION_MODEL_SPECS_PRE,
            *DISPLAY_DESTINATION_ENCODE_OPERATIONS_PRE,
            *PREPARE_MIGRATION_ENCODE_PATHS_EXEC,
            *MIGRATION_ENCODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "MIGRATION_ENCODE_CONFIG_COMPLETE",
    },
    "RUN_ALL_DIFFERENT_MODEL": {
        "pipeline": [
            *SELECT_ROUTER_PRE,
            *LOAD_ROUTER_MODEL_SPECS_PRE,
            *SELECT_DESTINATION_ROUTER_PRE,
            *LOAD_DESTINATION_MODEL_SPECS_PRE,
            *DISPLAY_SOURCE_DECODE_OPERATIONS_PRE,
            *DISPLAY_SOURCE_EDIT_OPERATIONS_PRE,
            *DISPLAY_SOURCE_VIEW_OPERATIONS_PRE,
            *DISPLAY_DESTINATION_DECODE_OPERATIONS_PRE,
            *DISPLAY_DESTINATION_VIEW_OPERATIONS_PRE,
            *DISPLAY_DESTINATION_EDIT_OPERATIONS_PRE,
            *DISPLAY_DESTINATION_ENCODE_OPERATIONS_PRE,
            *READ_MIGRATION_BACKUP_EXEC,
            *MIGRATION_DECODE_ROUTER_CONFIG_EXEC,
            *LOAD_MIGRATION_EXTRACTED_EXEC,
            *MIGRATION_EDIT_ROUTER_CONFIG_EXEC,
            *LOAD_SAVED_CONVERSION_SOURCE_EXEC,
            *READ_MIGRATION_DESTINATION_EXEC,
            *DESTINATION_DECODE_ROUTER_CONFIG_EXEC,
            *LOAD_EXTRACTED_DESTINATION_EXEC,
            *CONVERT_ROUTER_CONFIG_EXEC,
            *PREPARE_CONVERTED_ENCODE_PATHS_EXEC,
            *MIGRATION_ENCODE_ROUTER_CONFIG_EXEC,
        ],
        "label": "RUN_ALL_DIFFERENT_MODEL_COMPLETE",
    },
    "SHOW_MODEL_SPECS_HELP": {
        "pipeline": [
            *SHOW_MODEL_SPECS_HELP_EXEC,
        ],
        "label": "SHOW_MODEL_SPECS_HELP_COMPLETE",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": [
            *SHOW_CONFIG_DOC_EXEC,
        ],
        "label": "SHOW_CONFIG_DOC_COMPLETE",
    },
}
