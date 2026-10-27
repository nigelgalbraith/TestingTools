# ---------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------

from __future__ import annotations

from functools import partial
from getpass import getpass
from pathlib import Path
import os
import shutil
import subprocess
import tarfile
import tempfile

import jsonschema

from modules.display_utils import confirm
from modules.json_utils import load_json
from modules.router_config_utils import (
    normalize_key_value_fields,
    parse_key_value_fields,
    parse_xml_field_selector,
    validate_key_value_field_changes,
    xml_field_values,
    view_key_value_values,
    edit_key_value_values,
    update_xml_fields,
    validate_xml_field_changes,
)
from modules.router_encryption_utils import (
    decrypt_aes_128_cbc_field, encrypt_aes_128_cbc_field,
    crypt_aes_256_cbc, crypt_aes_256_cbc_fixed_key, crypt_technicolor_thenc,
    interpret_password_credentials,
    calculate_payload_checksum, verify_rsa_md5_signature, sign_rsa_md5_configuration,
)
from modules.router_format_utils import (
    validate_xml_declaration,
    validate_directory,
    safe_relative,
    rebuild_tar_archive,
    extract_tar_archive,
    replace_router_directory,
    read_tar_files,
    split_line_wrapper, prepare_line_wrapper,
    parse_technicolor_wrapper, parse_encrypted_configuration,
    rebuild_technicolor_wrapper,
    encode_base64_payload, decode_base64_payload,
    unpack_signed_configuration, pack_signed_configuration, decode_xml_configuration,
)


# ---------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------

DECODED_EXTENSION = ".tar.gz"

ROUTER_FUNCTIONS = {
    "base64": {"decode": decode_base64_payload, "encode": encode_base64_payload},
    "aes-256-cbc": {"decode": crypt_aes_256_cbc, "encode": crypt_aes_256_cbc},
    "fixed-key": {"decode": crypt_aes_256_cbc_fixed_key, "encode": crypt_aes_256_cbc_fixed_key},
    "device-key": {"decode": crypt_technicolor_thenc, "encode": crypt_technicolor_thenc},
    "line-wrapper": {"decode": split_line_wrapper, "encode": prepare_line_wrapper},
    "technicolor-thenc": {"decode": parse_technicolor_wrapper, "encode": rebuild_technicolor_wrapper},
    "encrypted-configuration": {"decode": parse_encrypted_configuration, "encode": parse_encrypted_configuration},
    "tar.gz": {"decode": read_tar_files, "encode": rebuild_tar_archive},
    "signed-zlib": {"decode": unpack_signed_configuration, "encode": pack_signed_configuration},
    "rsa-md5": {"decode": verify_rsa_md5_signature, "encode": sign_rsa_md5_configuration},
    "md5": {"checksum": calculate_payload_checksum},
    "sha256": {"checksum": calculate_payload_checksum},
    "sha512": {"checksum": calculate_payload_checksum},
    "key-value": {"decode": view_key_value_values, "edit": edit_key_value_values},
    "xml": {"decode": xml_field_values, "edit": update_xml_fields},
    "aes-128-cbc-zero-padded-base64": {"decode": decrypt_aes_128_cbc_field, "encode": encrypt_aes_128_cbc_field},
}


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def field_handler(specs: dict, action: str):
    settings = (specs["router_specs"].get("edit") or {}).get("field_encryption")
    if not settings or settings.get("algorithm") is None:
        return None
    return partial(ROUTER_FUNCTIONS[settings["algorithm"]][action],
                   key_hex=settings["key_hex"], iv_hex=settings["iv_hex"])


def parse_line_wrapper(data: bytes, backup_format: dict) -> dict:
    """Verify the wrapper checksum before decoding and validating its Base64 payload."""
    wrapper = ROUTER_FUNCTIONS["line-wrapper"]["decode"](data, backup_format)
    encoded = wrapper["encoded"]
    expected = ROUTER_FUNCTIONS[backup_format["checksum"]]["checksum"](encoded, backup_format["checksum"])
    if wrapper["checksum"] != expected:
        raise ValueError("Backup encrypted payload checksum mismatch")
    encrypted = decode_base64_payload(encoded)
    if encode_base64_payload(encrypted, backup_format) != encoded:
        raise ValueError("Invalid encoded payload line layout")
    return {"header": wrapper["header"], "encoded": encoded,
            "encrypted": encrypted, "checksum": expected}


def rebuild_line_wrapper(encoded: bytes, header: bytes, backup_format: dict) -> bytes:
    """Build and verify a wrapper with its checksum and fresh random prefix."""
    before, after = ROUTER_FUNCTIONS["line-wrapper"]["encode"](encoded, header, backup_format)
    checksum = ROUTER_FUNCTIONS[backup_format["checksum"]]["checksum"](encoded, backup_format["checksum"])
    result = before + checksum + after
    parse_line_wrapper(result, backup_format)
    return result


def parse_router_wrapper(data: bytes, settings: dict) -> dict:
    method = settings.get("wrapper")
    if method == "line-wrapper":
        return parse_line_wrapper(data, settings)
    if method == "technicolor-thenc":
        return ROUTER_FUNCTIONS[method]["decode"](data, settings, settings["hardware"], settings["firmware"])
    if method == "encrypted-configuration":
        return ROUTER_FUNCTIONS[method]["decode"](data)
    if method is None:
        return {"header": b"", "encrypted": data}
    raise ValueError(f"Unsupported router wrapper: {method}")


def rebuild_router_wrapper(encoded: bytes, header: bytes, settings: dict) -> bytes:
    method = settings.get("wrapper")
    if method == "line-wrapper":
        return rebuild_line_wrapper(encoded, header, settings)
    if method == "technicolor-thenc":
        return ROUTER_FUNCTIONS[method]["encode"](encoded, header, settings, settings["hardware"], settings["firmware"])
    if method == "encrypted-configuration":
        ROUTER_FUNCTIONS[method]["encode"](encoded)
    elif method is not None:
        raise ValueError(f"Unsupported router wrapper: {method}")
    return encoded


def decode_signed_configuration(data: bytes, backup_format: dict, signature: dict) -> bytes:
    """Verify the decompressed RSA block before interpreting authenticated XML bytes."""
    signed, signature_bytes = ROUTER_FUNCTIONS["signed-zlib"]["decode"](data, backup_format)
    ROUTER_FUNCTIONS["rsa-md5"]["decode"](signed, signature_bytes, backup_format, signature)
    return decode_xml_configuration(signed, backup_format)


def encode_signed_configuration(xml: bytes, backup_format: dict, signature: dict) -> bytes:
    """Sign XML, compress and pad it, then verify the exact recovered bytes."""
    validate_xml_declaration(xml, backup_format)
    if b"\x00" in xml:
        raise ValueError("XML configuration contains an embedded null byte")
    signed = xml + b"\x00"
    signature_bytes = ROUTER_FUNCTIONS["rsa-md5"]["encode"](signed, backup_format, signature)
    padded = ROUTER_FUNCTIONS["signed-zlib"]["encode"](signed, signature_bytes)
    if decode_signed_configuration(padded, backup_format, signature) != xml:
        raise ValueError("Rebuilt signed configuration failed verification")
    return padded


def crypt_router_payload(data: bytes, password: str, settings: dict, action: str, device_key_path: str | None = None) -> bytes:
    """Pass the selected cipher its explicit parameters and credential type."""
    if not settings.get("encryption"):
        return data
    derivation = settings.get("key_derivation")
    decrypt = action == "decode"
    if derivation == "openssl-legacy":
        return ROUTER_FUNCTIONS[settings["encryption"]][action](data, password, decrypt,
            salted=settings["salted"], password_required=settings["password_required"],
            password_base=settings["password_base"], password_hash=settings["password_hash"],
            key_derivation_digest=settings["key_derivation_digest"])
    if derivation == "fixed-key":
        return ROUTER_FUNCTIONS[derivation][action](data, password, decrypt,
            encryption_settings=settings["encryption_settings"])
    if derivation == "device-key":
        if not device_key_path:
            raise ValueError("THENC device key unavailable: device_key_path is required; an export password is not a device key")
        key = Path(device_key_path).expanduser().read_bytes()
        if not key:
            raise ValueError("THENC device key file is empty")
        return ROUTER_FUNCTIONS[derivation][action](data, password, decrypt, device_key=key)
    raise ValueError(f"Unsupported key_derivation: {derivation}")


def _validate_router_codec(router: dict, codec: dict, edit: dict) -> None:
    """Validate selected implementations, codec requirements and operation ordering."""
    derivation = codec.get("key_derivation")
    cipher = "aes-256-cbc" if derivation == "openssl-legacy" else derivation
    selected = [(codec.get("encoding"), ("decode", "encode")),
                (cipher, ("decode", "encode")),
                (codec.get("wrapper"), ("decode", "encode")),
                (codec.get("archive"), ("decode", "encode")),
                (codec.get("checksum"), ("checksum",)),
                ((codec.get("signature") or {}).get("algorithm"), ("decode", "encode")),
                (edit.get("configuration_format"), ("decode", "edit")),
                ((edit.get("field_encryption") or {}).get("algorithm"), ("decode", "encode"))]
    for method, actions in selected:
        if method is not None:
            for action in actions:
                if not callable(ROUTER_FUNCTIONS.get(method, {}).get(action)):
                    raise ValueError(f"Unsupported {action} method: {method}")
    required = []
    if codec.get("encryption"):
        required.append("key_derivation")
    elif derivation:
        raise ValueError("key_derivation requires encryption")
    if derivation == "openssl-legacy":
        required += ["password_base", "password_hash", "salted", "password_required", "key_derivation_digest"]
        if codec.get("wrapper") != "line-wrapper":
            raise ValueError("OpenSSL legacy backups require a line-wrapper")
    elif derivation == "fixed-key":
        required.append("encryption_settings")
        if any((codec.get("encryption_settings") or {}).get(name) is None for name in ("key_hex", "iv_hex")):
            raise ValueError("Fixed-key encryption requires encryption_settings.key_hex and encryption_settings.iv_hex")
        if codec.get("wrapper") != "encrypted-configuration":
            raise ValueError("Fixed-key backups require encrypted-configuration")
    elif derivation == "device-key":
        if codec.get("wrapper") != "technicolor-thenc":
            raise ValueError("Device-key backups require technicolor-thenc")
    wrapper = codec.get("wrapper")
    if codec.get("encoding") == "base64":
        required.append("payload_line_length")
    if wrapper == "line-wrapper":
        required += ["header_lines", "preserve_header", "payload_line_length", "newline", "checksum",
                     "checksum_after_payload_lines", "checksum_prefix_bytes", "trailer_character", "trailer_repeat"]
        if codec.get("encoding") != "base64" or edit.get("configuration_format") != "key-value":
            raise ValueError("Line wrappers require Base64 and key-value configuration")
        if (codec.get("header_lines") or 0) > 0 and not codec.get("preserve_header"):
            raise ValueError("A nonempty wrapper header must be preserved")
    elif wrapper == "technicolor-thenc":
        required += ["header_lines", "iv_length", "signature_length", "preamble", "backup_version", "header_terminator"]
        if codec.get("header_lines") != 9 or codec.get("iv_length") != 16:
            raise ValueError("THENC requires nine header lines and a 16-byte IV")
        if not router.get("hardware") or not router.get("firmware"):
            raise ValueError("THENC requires hardware and firmware identifiers")
        if edit or codec.get("archive"):
            raise ValueError("THENC configuration editing and archives are not established")
    elif wrapper == "encrypted-configuration":
        if derivation != "fixed-key" or edit.get("configuration_format") != "xml":
            raise ValueError("Encrypted configurations require fixed-key AES and XML configuration")
    if wrapper in ("technicolor-thenc", "encrypted-configuration") and codec.get("encoding"):
        raise ValueError("Binary wrappers do not use transport encoding")
    if codec.get("archive") == "signed-zlib":
        required += ["signature", "signature_length", "preamble"]
        if any((codec.get("signature") or {}).get(name) is None for name in ("algorithm", "modulus_hex", "exponent")):
            raise ValueError("Signed zlib requires signature.algorithm, signature.modulus_hex and signature.exponent")
        if edit.get("configuration_format") != "xml" or wrapper != "encrypted-configuration":
            raise ValueError("Signed zlib requires XML and encrypted-configuration")
        if not (codec.get("preamble") or "").startswith("<?xml"):
            raise ValueError("Signed configurations require an XML preamble")
    if edit.get("configuration_format") == "key-value" and codec.get("archive") != "tar.gz":
        raise ValueError("Key-value configuration requires a tar.gz archive")
    if edit.get("configuration_format") == "xml" and codec.get("archive") != "signed-zlib":
        raise ValueError("XML configuration requires a signed-zlib archive")
    for name in required:
        if codec.get(name) is None:
            raise ValueError(f"Required codec parameter {name} is missing or null")
    for action, default in (("decode", ("wrapper", "encoding", "encryption", "archive")),
                            ("encode", ("archive", "encryption", "encoding", "wrapper"))):
        order = codec.get(f"{action}_order") or default
        for step in default:
            if codec.get(step) and step not in order:
                raise ValueError(f"{action}_order is missing the active {step} operation")


def _validate_router_fields(router: dict, config_fields: list, codec: dict, edit: dict) -> None:
    """Validate logical mappings, protected fields and encoding-only settings."""
    names = [field["name"] for field in config_fields]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate logical configuration field names")
    mapped = set()
    for field in config_fields:
        if field["path"] is None:
            continue
        mapped.add(field["name"])
        if edit.get("configuration_format") == "xml":
            parse_xml_field_selector(field["path"], field["name"])
        elif edit.get("configuration_format") == "key-value":
            if not field["path"].strip() or any(char in field["path"] for char in "=\r\n\x00"):
                raise ValueError(f"Invalid configuration key: {field['name']}")
        else:
            raise ValueError("Configuration field mappings require an edit section")
    fields = edit.get("field_encryption") or {}
    if edit.get("configuration_format") and edit.get("configuration_file") is None:
        raise ValueError("Configuration editing requires configuration_file")
    if fields.get("algorithm") and any(fields.get(name) is None for name in ("key_hex", "iv_hex", "fields")):
        raise ValueError("Field encryption requires key_hex, iv_hex and fields")
    if fields.get("algorithm") and edit.get("configuration_format") != "xml":
        raise ValueError("Protected fields require XML configuration")
    for name in fields.get("fields") or []:
        if name not in mapped:
            raise ValueError(f"Encrypted field has no configuration mapping: {name}")
    if router.get("encode") and codec.get("archive") != "signed-zlib":
        raise ValueError("Private signing settings require a signed-zlib archive")


def validate_router_settings(specs: dict) -> None:
    """Check required method settings, compatible formats and logical field mappings."""
    router = specs["router_specs"]
    codec = router["codec"]
    edit = router.get("edit") or {}
    _validate_router_codec(router, codec, edit)
    _validate_router_fields(router, specs["config_fields"], codec, edit)


def validate_tar_gzip_config(decoded: bytes, model_specs: dict) -> None:
    """Validate TAR/GZIP contents and the declared key-value configuration."""
    files = ROUTER_FUNCTIONS["tar.gz"]["decode"](decoded)
    configured = str(Path(model_specs["router_specs"]["edit"]["configuration_file"]))
    if configured not in files:
        raise ValueError("Configured file missing from archive")
    parse_key_value_fields(files[configured].decode("utf-8"), model_specs)


def validate_edited_fields(original_archive: bytes, directory: Path, specs: dict) -> None:
    """Match every original byte except values explicitly declared editable."""
    config_path = Path(specs["router_specs"]["edit"]["configuration_file"])
    found = False
    files = read_tar_files(original_archive)
    for name, original in files.items():
        edited = (directory / safe_relative(name)).read_bytes()
        if Path(name) != config_path:
            if original != edited:
                raise ValueError(f"Original mismatch in uneditable file: {name}")
            continue
        found = True
        if normalize_key_value_fields(original.decode("utf-8"), specs) != normalize_key_value_fields(edited.decode("utf-8"), specs):
            raise ValueError("Edited configuration differs outside declared editable values")
    if not found:
        raise ValueError("Configured file missing from original archive")


def validate_edited_xml(original: bytes, directory: Path, specs: dict, decrypt_handler=None, encrypt_handler=None) -> tuple[bytes, list[str]]:
    """Permit only configured XML field edits relative to the authenticated original."""
    if not directory.is_dir():
        raise NotADirectoryError(f"Edited configuration directory not found: {directory}")
    validate_directory(directory)
    relative = Path(specs["router_specs"]["edit"]["configuration_file"])
    actual = {path.relative_to(directory) for path in directory.rglob("*") if path.is_file()}
    if actual != {relative}:
        raise ValueError("Edited files do not match the original single-file configuration")
    edited = (directory / relative).read_bytes()
    validate_xml_declaration(edited, specs["router_specs"]["codec"])
    before = xml_field_values(original.decode("utf-8"), specs, decrypt_handler)
    after = xml_field_values(edited.decode("utf-8"), specs, decrypt_handler)
    changes = {label: value for label, value in after.items() if value != before[label]}
    validate_xml_field_changes(original.decode("utf-8"), edited.decode("utf-8"), specs, changes, decrypt_handler, encrypt_handler)
    return edited, [str(relative)] if edited != original else []


def extract_xml_configuration(archive_path: Path, output: Path, model_specs: dict) -> None:
    """Stage the preserved XML bytes as a single configuration file and replace the destination."""
    decoded = archive_path.read_bytes()
    validate_xml_declaration(decoded, model_specs["router_specs"]["codec"])
    relative = Path(model_specs["router_specs"]["edit"]["configuration_file"])
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=f".{output.name}.") as directory:
        prepared = Path(directory) / "configuration"
        target = prepared / relative
        target.parent.mkdir(parents=True, mode=0o700)
        target.write_bytes(decoded)
        target.chmod(0o600)
        replace_router_directory(prepared, output)


def _prompt_router_changes(source: Path, destination: Path, configuration_format: str, values: dict) -> dict | None:
    """Collect and confirm edits, retaining the existing prompts and cancellation."""
    changes = {}
    print(f"\nEditing configuration: {source.name}")
    print("Press Enter to keep the existing value.")
    for label, current in values.items():
        print(f"\n{label}: {current}")
        updated = input(f"New {label}: ")
        if not updated:
            continue
        if "\n" in updated or "\r" in updated or "\x00" in updated:
            raise ValueError(f"Invalid value for {label}")
        changes[label] = updated
    if not changes:
        print("No changes made.")
    else:
        print("\nChanges:")
        for label, current in values.items():
            if label in changes:
                print(f"{label}: {current} -> {changes[label]}")
    prompt = "\nSave edited configuration? [y/n]: " if configuration_format == "xml" else "\nSave configuration for encoding? [y/n]: "
    if not confirm(prompt):
        print("Configuration editing cancelled.")
        return None
    if destination.exists():
        if not confirm(f"Edited configuration already exists: {destination}\nOverwrite? [y/n]: "):
            print("Edited configuration overwrite cancelled.")
            return None
    return changes


def _confirm_router_conversion(source_values: dict, destination_values: dict) -> dict | None:
    """Compare fields and confirm the same conversion report before changing files."""
    skipped_fields = sorted(source_values.keys() - destination_values.keys())
    changes = []
    for label in sorted(source_values.keys() & destination_values.keys()):
        value = source_values[label]
        previous = destination_values[label]
        if value == previous:
            continue
        if any(char in value for char in ("\r", "\n", "\x00")):
            raise ValueError(f"Invalid configuration value for {label}")
        changes.append((label, previous, value))
    print("\nSkipped source fields:")
    print("-" * 50)
    if skipped_fields:
        for label in skipped_fields:
            print(f"{label}: Not defined in destination")
    else:
        print("None")
    if not changes:
        print("\nNo matching configuration changes to transfer.")
        return None
    print("\nProposed destination changes:")
    print("-" * 50)
    for label, previous, value in changes:
        print(f"{label}: {previous} -> {value}")
    print("\nConversion summary:")
    print("-" * 50)
    print(f"Fields to update : {len(changes)}")
    print(f"Fields skipped   : {len(skipped_fields)}")
    if not confirm("\nApply these changes to the prepared destination? [y/n]: "):
        print("Conversion cancelled.")
        return None
    updates = {label: value for label, previous, value in changes}
    return updates


def _save_configuration_directory(
    source: Path,
    destination: Path,
    relative: Path,
    original_bytes: bytes,
    edited: str,
    model_specs: dict,
    changes: dict,
    *,
    conversion_source: tuple[Path, bytes] | None = None,
) -> None:
    """Stage, verify and install edited files while checking the original snapshots."""
    configuration_format = (model_specs["router_specs"].get("edit") or {}).get("configuration_format")
    original = original_bytes.decode("utf-8")
    source_file = source / relative
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staging = Path(tempfile.mkdtemp(dir=destination.parent, prefix=f".{destination.name}."))
    prepared = staging / "replacement"
    try:
        shutil.copytree(source, prepared, symlinks=True)
        validate_directory(prepared)
        target = prepared / relative
        if target.is_symlink():
            if conversion_source is not None:
                raise ValueError("Unsafe destination configuration file")
            raise ValueError(f"Unsafe configuration file: {target}")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=target.parent, prefix=".config.", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(edited)
        try:
            os.chmod(temp_path, 0o600)
            os.replace(temp_path, target)
        finally:
            temp_path.unlink(missing_ok=True)
        saved = target.read_bytes().decode("utf-8")
        if configuration_format == "xml":
            validate_xml_field_changes(original, saved, model_specs, changes,
                field_handler(model_specs, "decode"),
                field_handler(model_specs, "encode"))
        elif conversion_source is not None:
            validate_key_value_field_changes(original, saved, model_specs, changes)
        else:
            parse_key_value_fields(saved, model_specs)
        if conversion_source is not None:
            path, snapshot = conversion_source
            if path.read_bytes() != snapshot:
                raise ValueError("Source configuration changed during conversion")
            if source_file.read_bytes() != original_bytes:
                raise ValueError("Prepared destination configuration changed during conversion")
        elif source_file.read_bytes() != original_bytes:
            raise ValueError("Original decoded configuration changed during editing")
        validate_directory(prepared)
        replace_router_directory(prepared, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _save_encoded_outputs(
    edited_archive: Path,
    output: Path,
    rebuilt_archive: bytes,
    rebuilt: bytes,
    single_file: bool,
    model_specs: dict,
    device_key_path: str | None,
    target_password: str,
) -> None:
    """Publish both encoded outputs with the existing staging, verification and rollback."""
    edited_archive.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staged = []
    backups = {}
    replaced = []
    try:
        for path, data in ((edited_archive, rebuilt_archive), (output, rebuilt)):
            staging = Path(tempfile.mkdtemp(dir=path.parent, prefix=f".{path.name}."))
            staged.append((path, staging))
            prepared = staging / "replacement"
            with prepared.open("xb") as temp_file:
                os.chmod(prepared, 0o600)
                temp_file.write(data)
            if prepared.read_bytes() != data:
                raise ValueError(f"Generated output failed write verification: {path}")
            if single_file and path == output:
                recovered = decode_router_config(str(prepared), model_specs, device_key_path=device_key_path, password=target_password)
                if recovered != rebuilt_archive:
                    raise ValueError("Generated backup failed independent decode verification")
        try:
            for path, staging in staged:
                if path.exists():
                    backup = staging / "original"
                    os.replace(path, backup)
                    backups[path] = backup
                os.replace(staging / "replacement", path)
                replaced.append(path)
        except BaseException:
            for path, staging in reversed(staged):
                try:
                    if path in backups:
                        os.replace(backups[path], path)
                        del backups[path]
                    elif path in replaced:
                        path.unlink()
                except OSError as exc:
                    print(f"Failed to restore output {path}: {exc}")
            raise
        for path, backup in list(backups.items()):
            backup.unlink()
            del backups[path]
    finally:
        for path, staging in staged:
            if path in backups:
                print(f"Original output retained at: {backups[path]}")
                (staging / "replacement").unlink(missing_ok=True)
            else:
                shutil.rmtree(staging)


# ---------------------------------------------------------------------
# ROUTER SPECIFICATIONS
# ---------------------------------------------------------------------


def load_router_model_specs(specs_path: str, schema_path: str) -> dict:
    """Validate a common specification and the settings required by its selected methods."""
    specs = load_json(Path(specs_path).expanduser())
    jsonschema.validate(specs, load_json(Path(schema_path).expanduser()))
    validate_router_settings(specs)
    return specs


# ---------------------------------------------------------------------
# ROUTER CREDENTIALS
# ---------------------------------------------------------------------


def load_router_credentials(password_path: str | None, model_specs: dict, password_prompt: str) -> str | bool:
    """Preserve password-file and interactive-password behaviour."""
    if model_specs.get("key_derivation") == "device-key":
        raise ValueError("THENC device key credentials are not established; an export password is not a device key")
    if model_specs.get("key_derivation") == "fixed-key":
        return ""
    if not model_specs.get("password_required", False):
        return ""
    if password_path is not None:
        try:
            return interpret_password_credentials(Path(password_path).expanduser().read_bytes())
        except (OSError, ValueError, TypeError) as exc:
            print(f"Failed to load template password: {exc}")
            return False
    try:
        password = getpass(password_prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nRouter password entry cancelled.")
        return False
    if not password:
        print("Router password is required.")
        return False
    return password


def load_target_router_credentials(template_credentials, model_specs: dict, password_prompt: str):
    """Preserve the existing destination password prompts and cancellation."""
    if model_specs.get("key_derivation") == "device-key":
        raise ValueError("THENC destination key handling and signature signing are not established")
    if model_specs.get("key_derivation") == "fixed-key":
        return ""
    if not model_specs.get("password_required", False):
        return ""
    try:
        password = getpass(password_prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nDestination router password entry cancelled.")
        return False
    if password_prompt == "Enter target router password (Enter to use template password): ":
        return password or template_credentials
    if not password:
        print("Destination router password is required.")
        return False
    return password


# ---------------------------------------------------------------------
# ROUTER DECODING
# ---------------------------------------------------------------------


def decode_router_config(config_path: str | bytes, model_specs: dict, password_path: str | None = None, password_prompt: str = "Enter router password: ", device_key_path: str | None = None, *, password: str | None = None) -> bytes | bool:
    """Decode bytes or an application backup path in the specified order."""
    settings = {**model_specs["router_specs"]["codec"],
                "hardware": model_specs["router_specs"].get("hardware"),
                "firmware": model_specs["router_specs"].get("firmware")}
    data = config_path if isinstance(config_path, bytes) else Path(config_path).expanduser().read_bytes()
    if password is None:
        password = "" if not settings.get("encryption") or settings.get("key_derivation") == "device-key" else load_router_credentials(password_path, settings, password_prompt)
    if password is False:
        return False
    for operation in (settings.get("decode_order") or ("wrapper", "encoding", "encryption", "archive")):
        if operation == "wrapper":
            wrapper = parse_router_wrapper(data, settings)
            data = wrapper["encoded" if settings.get("wrapper") == "line-wrapper" else "encrypted"]
        elif operation == "encoding" and settings.get("encoding"):
            data = ROUTER_FUNCTIONS[settings["encoding"]]["decode"](data)
        elif operation == "encryption":
            data = crypt_router_payload(data, password, settings, "decode", device_key_path)
        elif operation == "archive":
            if settings.get("archive") == "tar.gz":
                validate_tar_gzip_config(data, model_specs)
            elif settings.get("archive") == "signed-zlib":
                data = decode_signed_configuration(data, settings, settings["signature"])
    return data


# ---------------------------------------------------------------------
# CONFIGURATION SAVING
# ---------------------------------------------------------------------


def save_router_config(decoded_config: bytes, decoded_config_path: str, model_specs: dict) -> bool:
    """Save the decoded router configuration in its declared format."""
    if not isinstance(decoded_config, bytes) or not decoded_config:
        print("No decoded router configuration available to save.")
        return False
    try:
        path = Path(decoded_config_path).expanduser()
        extension = ".xml" if (model_specs["router_specs"].get("edit") or {}).get("configuration_format") == "xml" else DECODED_EXTENSION
        if not path.name.endswith(extension):
            raise ValueError(f"Decoded configuration path must end with {extension}")
        if path.is_symlink():
            raise ValueError(f"Unsafe decoded archive symlink: {path}")
        if path.exists():
            if not path.is_file():
                raise ValueError(f"Decoded archive destination is not a file: {path}")
            if not confirm(f"Decoded archive already exists: {path}\nOverwrite? [y/n]: "):
                print("Decoded archive overwrite cancelled.")
                return False
        if (model_specs["router_specs"].get("edit") or {}).get("configuration_format") == "xml":
            validate_xml_declaration(decoded_config, model_specs["router_specs"]["codec"])
        else:
            read_tar_files(decoded_config)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            os.chmod(temp_path, 0o600)
            temp_file.write(decoded_config)
        try:
            os.replace(temp_path, path)
        finally:
            temp_path.unlink(missing_ok=True)
        print(f"Saved decoded router configuration: {path}")
        return True
    except (OSError, ValueError, TypeError, tarfile.TarError, EOFError) as exc:
        print(f"Failed to save decoded router configuration: {exc}")
        return False


# ---------------------------------------------------------------------
# CONFIGURATION EXTRACTION
# ---------------------------------------------------------------------


def extract_router_config(archive_path: str, output_dir: str, model_specs: dict) -> str | bool:
    """Safely extract the decoded router configuration."""
    try:
        archive_path = Path(archive_path).expanduser()
        output = Path(output_dir).expanduser()
        if not archive_path.is_file():
            raise FileNotFoundError(f"Decoded archive not found: {archive_path}")
        if any(path.is_symlink() for path in (output, *output.parents)):
            raise ValueError(f"Unsafe extraction directory symlink: {output}")
        if output.exists():
            if not output.is_dir():
                raise ValueError(f"Extraction destination is not a directory: {output}")
            if not confirm(f"Extraction directory already exists: {output}\nOverwrite? [y/n]: "):
                print("Extraction overwrite cancelled.")
                return False
        if (model_specs["router_specs"].get("edit") or {}).get("configuration_format") == "xml":
            extract_xml_configuration(archive_path, output, model_specs)
        else:
            extract_tar_archive(archive_path, output)
        print(f"Extracted router configuration: {output}")
        return str(output)
    except (OSError, ValueError, TypeError, tarfile.TarError) as exc:
        print(f"Failed to extract router configuration: {exc}")
        return False


# ---------------------------------------------------------------------
# CONFIGURATION VIEWING
# ---------------------------------------------------------------------


def view_router_config_fields(config_dir: str, model_specs: dict) -> bool:
    """Display selected router configuration fields."""
    try:
        viewer = ROUTER_FUNCTIONS.get((model_specs["router_specs"].get("edit") or {}).get("configuration_format"), {}).get("decode")
        if viewer is None:
            raise ValueError(f'Unsupported configuration_format for viewing: {(model_specs["router_specs"].get("edit") or {}).get("configuration_format")}')
        config_fields = model_specs["config_fields"]
        directory = Path(config_dir).expanduser()
        validate_directory(directory)
        if not directory.is_dir():
            raise NotADirectoryError(f"Configuration directory not found: {directory}")
        config_file = model_specs["router_specs"]["edit"]["configuration_file"]
        relative = Path(config_file)
        path = directory / relative
        if not path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        contents = path.read_bytes().decode("utf-8")
        values = viewer(contents, model_specs, field_handler(model_specs, "decode"))
        rows = []
        for field in config_fields:
            label, key = field["name"], field["path"]
            if key is not None:
                rows.append((label, values[label]))
        width = max([len("Field"), *(len(label) for label, _ in rows)])
        print(f"\nConfiguration: {directory.name} ({config_file})")
        print(f"{'Field':<{width}} | Value")
        print(f"{'-' * width}-+------------------------------")
        for label, value in rows:
            print(f"{label:<{width}} | {value}")
        return True
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Failed to view router configuration fields: {exc}")
        return False


# ---------------------------------------------------------------------
# CONFIGURATION EDITING
# ---------------------------------------------------------------------


def edit_router_config_fields(config: str, changes: dict, specs: dict) -> str:
    """Apply logical field changes through the selected configuration implementation."""
    method = (specs["router_specs"].get("edit") or {}).get("configuration_format")
    if method is None:
        raise ValueError("Configuration editing is unavailable for this specification")
    return ROUTER_FUNCTIONS[method]["edit"](config, specs, changes, field_handler(specs, "encode"))


def edit_router_config_files(config_dir: str, edited_dir: str, model_specs: dict) -> str | bool:
    """Copy and edit selected router configuration fields."""
    try:
        configuration_format = (model_specs["router_specs"].get("edit") or {}).get("configuration_format")
        editor = ROUTER_FUNCTIONS.get(configuration_format, {}).get("edit")
        viewer = ROUTER_FUNCTIONS.get(configuration_format, {}).get("decode")
        if editor is None or viewer is None:
            raise ValueError(f"Unsupported configuration_format for editing: {configuration_format}")
        source = Path(config_dir).expanduser()
        validate_directory(source)
        destination = Path(edited_dir).expanduser()
        if not source.is_dir():
            raise NotADirectoryError(f"Decoded configuration directory not found: {source}")
        if any(path.is_symlink() for path in (destination, *destination.parents)):
            raise ValueError(f"Unsafe edited configuration symlink: {destination}")
        if destination.exists() and not destination.is_dir():
            raise ValueError(f"Edited configuration destination is not a directory: {destination}")
        relative = safe_relative(model_specs["router_specs"]["edit"]["configuration_file"])
        source_file = source / relative
        if not source_file.is_file() or source_file.is_symlink():
            raise FileNotFoundError(f"Configuration file not found or unsafe: {source_file}")
        original_bytes = source_file.read_bytes()
        original = original_bytes.decode("utf-8")
        values = viewer(original, model_specs, field_handler(model_specs, "decode"))
        if source.resolve() == destination.resolve() or source.resolve() in destination.resolve().parents or destination.resolve() in source.resolve().parents:
            raise ValueError("Edited directory must be separate from the decoded source directory")
        changes = _prompt_router_changes(source, destination, configuration_format, values)
        if changes is None:
            return False
        edited = editor(original, model_specs, changes, field_handler(model_specs, "encode"))
        if configuration_format == "xml":
            validate_xml_field_changes(original, edited, model_specs, changes,
                field_handler(model_specs, "decode"),
                field_handler(model_specs, "encode"))
        _save_configuration_directory(source, destination, relative, original_bytes, edited, model_specs, changes)
        print(f"Saved edited router configuration: {destination}")
        return str(destination)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(f"Failed to edit router configuration: {exc}")
        return False


# ---------------------------------------------------------------------
# ROUTER ENCODING
# ---------------------------------------------------------------------


def encode_router_config(data: bytes, specs: dict, password: str = "", header: bytes = b"", device_key_path: str | None = None) -> bytes:
    """Encode prepared configuration bytes in the independent encode order."""
    settings = {**specs["router_specs"]["codec"],
                "hardware": specs["router_specs"].get("hardware"),
                "firmware": specs["router_specs"].get("firmware")}
    for operation in (settings.get("encode_order") or ("archive", "encryption", "encoding", "wrapper")):
        if operation == "archive" and settings.get("archive") == "signed-zlib":
            signature = {**settings["signature"], **(specs["router_specs"].get("encode") or {})}
            signature.setdefault("private_exponent_hex", None)
            data = encode_signed_configuration(data, settings, signature)
        elif operation == "encryption":
            data = crypt_router_payload(data, password, settings, "encode", device_key_path)
        elif operation == "encoding" and settings.get("encoding"):
            data = ROUTER_FUNCTIONS[settings["encoding"]]["encode"](data, settings)
        elif operation == "wrapper":
            data = rebuild_router_wrapper(data, header, settings)
    return data


def encode_router_config_files(
    edited_dir: str,
    original_cfg: str,
    edited_archive_path: str,
    output_path: str,
    model_specs: dict,
    password_path: str,
    password_prompt: str = "Enter target router password (Enter to use template password): ",
    device_key_path: str | None = None,
) -> str | bool:
    """Rebuild, encrypt and verify an edited backup without changing its source."""
    try:
        directory = Path(edited_dir).expanduser()
        original = Path(original_cfg).expanduser()
        edited_archive = Path(edited_archive_path).expanduser()
        output = Path(output_path).expanduser()
        single_file = model_specs["router_specs"]["codec"].get("archive") == "signed-zlib"
        extension = ".xml" if single_file else DECODED_EXTENSION
        if not edited_archive.name.endswith(extension):
            raise ValueError("Edited archive path has an invalid extension")
        if edited_archive.resolve() == output.resolve():
            raise ValueError("Output destinations must be different files")
        for path in (edited_archive, output):
            if path.resolve().is_relative_to(directory.resolve()):
                raise ValueError("Output destinations must not overwrite the edited configuration directory")
            if path.resolve() == original.resolve() or (path.exists() and original.exists() and path.samefile(original)):
                raise ValueError("Output destinations must not overwrite the original backup")
            if any(parent.is_symlink() for parent in (path, *path.parents)):
                raise ValueError(f"Unsafe output symlink: {path}")
            if path.exists() and not path.is_file():
                raise ValueError(f"Output destination is not a file: {path}")
        existing = [path for path in (edited_archive, output) if path.exists()]
        if existing:
            print("\nExisting output files:")
            for path in existing:
                print(f"  {path}")
            if not confirm("Overwrite existing output files? [y/n]: "):
                print("Encoding overwrite cancelled.")
                return False
        codec = {**model_specs["router_specs"]["codec"],
                           "hardware": model_specs["router_specs"].get("hardware"),
                           "firmware": model_specs["router_specs"].get("firmware")}
        wrapper = parse_router_wrapper(original.read_bytes(), codec)
        template_password = "" if codec.get("key_derivation") == "device-key" else load_router_credentials(password_path, codec, "Enter router password: ")
        if template_password is False:
            return False
        original_archive = decode_router_config(original.read_bytes(), model_specs, device_key_path=device_key_path, password=template_password)
        if single_file:
            rebuilt_archive, changes = validate_edited_xml(original_archive, directory, model_specs,
                field_handler(model_specs, "decode"),
                field_handler(model_specs, "encode"))
        else:
            rebuilt_archive, changes = ROUTER_FUNCTIONS[codec["archive"]]["encode"](original_archive, str(directory))
            validate_edited_fields(original_archive, directory, model_specs)
        target_password = "" if codec.get("key_derivation") == "device-key" else load_target_router_credentials(template_password, codec, password_prompt)
        if target_password is False:
            return False
        rebuilt = encode_router_config(rebuilt_archive, model_specs, target_password, wrapper["header"], device_key_path)
        decrypted = decode_router_config(rebuilt, model_specs, device_key_path=device_key_path, password=target_password)
        if decrypted != rebuilt_archive:
            raise ValueError("Generated backup failed decryption verification")
        if not single_file:
            validate_tar_gzip_config(decrypted, model_specs)
        _save_encoded_outputs(edited_archive, output, rebuilt_archive, rebuilt, single_file,
                              model_specs, device_key_path, target_password)
        print("Modified files: " + (", ".join(changes) or "none; original compressed archive retained"))
        print(f"Saved edited router archive: {edited_archive}")
        print(f"Updated router backup: {output}; checksum and local round-trip verified.")
        return str(output)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, tarfile.TarError, EOFError, subprocess.SubprocessError) as exc:
        print(f"Failed to encode router configuration: {exc}")
        return False


# ---------------------------------------------------------------------
# CONFIGURATION CONVERSION
# ---------------------------------------------------------------------


def convert_router_config_fields(source_dir: str, destination_dir: str, source_specs: dict, destination_specs: dict) -> str | bool:
    """Transfer matching configured fields into the prepared destination and report skipped fields."""
    try:
        source_reader = ROUTER_FUNCTIONS.get((source_specs["router_specs"].get("edit") or {}).get("configuration_format"), {}).get("decode")
        destination_reader = ROUTER_FUNCTIONS.get((destination_specs["router_specs"].get("edit") or {}).get("configuration_format"), {}).get("decode")
        editor = ROUTER_FUNCTIONS.get((destination_specs["router_specs"].get("edit") or {}).get("configuration_format"), {}).get("edit")
        if source_reader is None or destination_reader is None or editor is None:
            raise ValueError("Unsupported configuration format for source reading or destination editing")
        source_decrypt_handler = field_handler(source_specs, "decode")
        destination_decrypt_handler = field_handler(destination_specs, "decode")
        destination_encrypt_handler = field_handler(destination_specs, "encode")
        source = Path(source_dir).expanduser()
        destination = Path(destination_dir).expanduser()
        validate_directory(source)
        validate_directory(destination)
        if not source.is_dir() or not destination.is_dir():
            raise ValueError("Source or prepared destination directory is missing")
        if source.resolve() == destination.resolve() or source.resolve() in destination.resolve().parents or destination.resolve() in source.resolve().parents:
            raise ValueError("Source and destination directories must be separate")
        source_relative = Path(source_specs["router_specs"]["edit"]["configuration_file"])
        destination_relative = Path(destination_specs["router_specs"]["edit"]["configuration_file"])
        source_file = source / source_relative
        destination_file = destination / destination_relative
        if not source_file.is_file() or not destination_file.is_file() or source_file.is_symlink() or destination_file.is_symlink():
            raise ValueError("Missing or unsafe router configuration file")
        source_bytes = source_file.read_bytes()
        original = destination_file.read_bytes().decode("utf-8")
        source_values = source_reader(source_bytes.decode("utf-8"), source_specs, source_decrypt_handler)
        destination_values = destination_reader(original, destination_specs, destination_decrypt_handler)
        updates = _confirm_router_conversion(source_values, destination_values)
        if updates is None:
            return False
        edited = editor(original, destination_specs, updates, destination_encrypt_handler)
        if (destination_specs["router_specs"].get("edit") or {}).get("configuration_format") == "xml":
            validate_xml_field_changes(original, edited, destination_specs, updates,
                destination_decrypt_handler, destination_encrypt_handler)
        else:
            validate_key_value_field_changes(original, edited, destination_specs, updates)
        _save_configuration_directory(destination, destination, destination_relative, original.encode("utf-8"),
                                      edited, destination_specs, updates, conversion_source=(source_file, source_bytes))
        print(f"Converted configuration saved: {destination}")
        return str(destination)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(f"Failed to convert router configuration: {exc}")
        return False
