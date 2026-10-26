from __future__ import annotations
import json
import zlib
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from modules.router_encryption_utils import (
    parse_line_wrapper,
    parse_technicolor_wrapper,
    rebuild_technicolor_wrapper,
    rebuild_line_wrapper,
    encode_router_payload,
    parse_encrypted_configuration,
    verify_rsa_md5_signature,
    sign_rsa_md5_configuration,
    decrypt_aes_128_cbc_field,
    encrypt_aes_128_cbc_field,
    crypt_aes_256_cbc,
    crypt_aes_256_cbc_fixed_key,
    crypt_technicolor_thenc,
    interpret_password_credentials,
    load_device_key_credentials,
    load_target_device_key_credentials,
)
from getpass import getpass
from modules.display_utils import confirm
from modules.json_utils import load_json
from modules.router_config_utils import (
    extract_xml_configuration,
    validate_tar_gzip_config,
    read_tar_files,
    replace_router_directory,
    extract_tar_archive,
    rebuild_tar_archive,
    validate_edited_fields,
    decode_xml_configuration,
    validate_xml_declaration,
    safe_relative,
    validate_directory,
    parse_key_value_fields,
    key_value_values,
    update_key_value_fields,
    prepare_config_conversion,
    validate_key_value_field_changes,
    xml_field_values,
    view_key_value_values,
    edit_key_value_values,
    update_xml_fields,
    validate_xml_field_changes,
    validate_edited_xml,
)


# ---------------------------------------------------------------------
# FILE CONSTANTS
# ---------------------------------------------------------------------

ENCRYPTED_FILENAME = "config.enc"
DECODED_EXTENSION = ".tar.gz"
MODEL_SPECS_EXTENSION = ".json"
CONFIG_FIELDS_KEY = "config_fields"
CONFIG_FIELDS_FILE_KEY = "file"

# ---------------------------------------------------------------------
# DISPATCHER HANDLERS
# ---------------------------------------------------------------------

ENCRYPTION_HANDLERS = {
    ("aes-256-cbc", "openssl-legacy"): crypt_aes_256_cbc,
    ("aes-256-cbc", "device-key"): crypt_technicolor_thenc,
    ("aes-256-cbc", "fixed-key"): crypt_aes_256_cbc_fixed_key,
}

FIELD_ENCRYPT_HANDLERS = {
    "aes-128-cbc-zero-padded-base64": encrypt_aes_128_cbc_field,
}

FIELD_DECRYPT_HANDLERS = {
    "aes-128-cbc-zero-padded-base64": decrypt_aes_128_cbc_field,
}

CONFIG_VIEW_HANDLERS = {
    "key-value": view_key_value_values,
    "xml": xml_field_values,
}

CONFIG_EDIT_HANDLERS = {
    "key-value": edit_key_value_values,
    "xml": update_xml_fields,
}

WRAPPER_PARSE_HANDLERS = {
    "line-wrapper": parse_line_wrapper,
    "technicolor-thenc": parse_technicolor_wrapper,
    "encrypted-configuration": parse_encrypted_configuration,
}

WRAPPER_REBUILD_HANDLERS = {
    "line-wrapper": rebuild_line_wrapper,
    "technicolor-thenc": rebuild_technicolor_wrapper,
}

# ---------------------------------------------------------------------
# SIGNED CONFIGURATION HELPERS
# ---------------------------------------------------------------------

def decode_signed_configuration(data: bytes, specs: dict) -> bytes:
    """Decompress a signed single-file configuration and verify the complete RSA block."""
    try:
        decompressor = zlib.decompressobj()
        # Bound authenticated output before allocating an arbitrarily large decompressed stream.
        decoded = decompressor.decompress(data, 64 * 1024 * 1024 + 1)
    except zlib.error:
        raise ValueError("Invalid zlib configuration: incorrect key/IV or corrupt backup") from None
    if len(decoded) > 64 * 1024 * 1024 or not decompressor.eof:
        raise ValueError("Truncated or oversized zlib configuration")
    trailing = decompressor.unused_data
    if len(trailing) > 16 or any(trailing):
        raise ValueError("Invalid trailing AES zero padding")
    length = specs["backup_format"]["signature_length"]
    if len(decoded) <= length:
        raise ValueError("Missing signed configuration or RSA signature")
    signed, signature = decoded[:-length], decoded[-length:]
    verify_rsa_md5_signature(signed, signature, specs)
    return decode_xml_configuration(signed, specs)


def encode_signed_configuration(xml: bytes, specs: dict) -> bytes:
    """Build signed zlib data with AES zero padding, preserving every XML byte."""
    validate_xml_declaration(xml, specs)
    if b"\x00" in xml:
        raise ValueError("XML configuration contains an embedded null byte")
    signed = xml + b"\x00"
    signature = sign_rsa_md5_configuration(signed, specs)
    compressed = zlib.compress(signed + signature, 9)
    padded = compressed + b"\x00" * (16 - len(compressed) % 16)
    if decode_signed_configuration(padded, specs) != xml:
        raise ValueError("Rebuilt signed configuration failed verification")
    return padded

# ---------------------------------------------------------------------
# ROUTER FORMAT HELPERS
# ---------------------------------------------------------------------

def parse_router_wrapper(data: bytes, model_specs: dict) -> dict:
    """Parse the configured backup wrapper using loaded specifications."""
    wrapper_type = model_specs["backup_format"]["type"]

    try:
        handler = WRAPPER_PARSE_HANDLERS[wrapper_type]
    except KeyError:
        raise ValueError(f"Unsupported router wrapper type: {wrapper_type}") from None

    return handler(data, model_specs)


def rebuild_router_wrapper(encoded: bytes, header: bytes, specs: dict) -> bytes:
    """Rebuild the configured backup wrapper using loaded specifications."""
    wrapper_type = specs["backup_format"]["type"]

    if wrapper_type == "encrypted-configuration":
        parse_encrypted_configuration(encoded, specs)
        return encoded

    try:
        handler = WRAPPER_REBUILD_HANDLERS[wrapper_type]
    except KeyError:
        raise ValueError(f"Unsupported router wrapper type: {wrapper_type}") from None

    return handler(encoded, header, specs)


# ---------------------------------------------------------------------
# PRE STEPS
# ---------------------------------------------------------------------

def get_target_router_password(model_specs: dict, template_password: str) -> str | bool:
    if not model_specs.get("password_required", False):
        return ""
    try:
        password = getpass("Enter target router password (Enter to use template password): ")
        return password or template_password
    except (EOFError, KeyboardInterrupt):
        print("\nTarget router password entry cancelled.")
        return False


def get_router_template_password(model_specs: dict, password_path: str) -> str | bool:
    """Read the selected router's configured template password file."""
    if not model_specs.get("password_required", False):
        return ""
    try:
        path = Path(password_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Template password file not found: {path}")
        password = interpret_password_credentials(path.read_bytes())
        return password
    except (OSError, ValueError, TypeError) as exc:
        print(f"Failed to load template password: {exc}")
        return False


def load_router_credentials(password_path: str | None, model_specs: dict, password_prompt: str) -> str | bool:
    """Preserve password-file and interactive-password behaviour."""
    if model_specs["key_derivation"] == "device-key":
        return load_device_key_credentials(password_path, model_specs, password_prompt)
    if model_specs["key_derivation"] == "fixed-key":
        return ""
    if password_path is not None:
        return get_router_template_password(model_specs, password_path)
    if not model_specs["password_required"]:
        return ""
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
    if model_specs["key_derivation"] == "device-key":
        return load_target_device_key_credentials(template_credentials, model_specs, password_prompt)
    if model_specs["key_derivation"] == "fixed-key":
        return ""
    if not model_specs["password_required"]:
        return ""
    if password_prompt == "Enter target router password (Enter to use template password): ":
        return get_target_router_password(model_specs, template_credentials)
    try:
        password = getpass(password_prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nDestination router password entry cancelled.")
        return False
    if not password:
        print("Destination router password is required.")
        return False
    return password


# ---------------------------------------------------------------------
# DISPATCHER FUNCTIONS
# ---------------------------------------------------------------------

def read_router_credential(password_path: str, specs: dict) -> str | bytes:
    """Read the selected credential type without treating passwords as device keys."""
    if specs["key_derivation"] == "openssl-legacy":
        if not specs["password_required"]:
            return ""
        if not password_path:
            raise ValueError("Router password file is required by the selected specification")
        return interpret_password_credentials(Path(password_path).expanduser().read_bytes())
    elif specs["key_derivation"] == "device-key":
        return load_device_key_credentials(password_path, specs)
    return ""


def decrypt_router_payload(data: bytes, password: str, model_specs: dict, wrapper: dict | None = None, device_key: bytes | None = None, device_key_path: str | None = None) -> bytes:
    """Decrypt using the encryption method defined in the router specification."""
    mechanism = (model_specs["encryption"], model_specs["key_derivation"])
    if model_specs["key_derivation"] == "device-key" and device_key is None:
        if not device_key_path:
            raise ValueError("THENC device key unavailable: device_key_path is required; an export password is not a device key")
        device_key = Path(device_key_path).expanduser().read_bytes()
        if not device_key:
            raise ValueError("THENC device key file is empty")
    return ENCRYPTION_HANDLERS[mechanism](data, password, model_specs, True, wrapper=wrapper, device_key=device_key)


def encrypt_router_payload(data: bytes, password: str, model_specs: dict, device_key_path: str | None = None) -> bytes:
    """Encrypt using the encryption method defined in the router specification."""
    mechanism = (model_specs["encryption"], model_specs["key_derivation"])
    if model_specs["key_derivation"] == "device-key":
        if not device_key_path:
            raise ValueError("THENC device key unavailable: device_key_path is required; an export password is not a device key")
        device_key = Path(device_key_path).expanduser().read_bytes()
        if not device_key:
            raise ValueError("THENC device key file is empty")
        return ENCRYPTION_HANDLERS[mechanism](data, password, model_specs, False, device_key=device_key)
    return ENCRYPTION_HANDLERS[mechanism](data, password, model_specs, False)


# ---------------------------------------------------------------------
# ROUTER WORKFLOWS
# ---------------------------------------------------------------------

def load_router_model_specs(specs_path: str) -> dict:
    """Load a model dictionary; CHECK and derived-data preparation belong to PRE."""
    path = Path(specs_path).expanduser()
    if path.suffix.lower() != MODEL_SPECS_EXTENSION:
        raise ValueError(f"Router model specifications must be a {MODEL_SPECS_EXTENSION} file")
    specs = load_json(path)
    if not isinstance(specs, dict):
        raise ValueError(f"Router model specifications must be a JSON object: {path}")
    return specs


def read_router_backup(config_path: str) -> bytes | bool:
    """Read an original router configuration backup."""
    try:
        path = Path(config_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Router backup not found: {path}")
        data = path.read_bytes()
        if not data:
            raise ValueError("Router backup is empty")
        print(f"Read router backup: {path}")
        return data
    except (OSError, ValueError, TypeError) as exc:
        print(f"Failed to read router backup: {exc}")
        return False


def decode_router_config(config_path: str, model_specs: dict, password_path: str | None, password_prompt: str = "Enter router password: ", device_key_path: str | None = None) -> bytes | bool:
    """Decode and validate a router backup using its model specifications."""
    wrapper = parse_router_wrapper(Path(config_path).expanduser().read_bytes(), model_specs)
    password = "" if model_specs["key_derivation"] == "device-key" else load_router_credentials(password_path, model_specs, password_prompt)
    if password is False:
        return False
    decoded = decrypt_router_payload(wrapper["encrypted"], password, model_specs, wrapper=wrapper, device_key_path=device_key_path)
    if model_specs["archive"] == {"format": "single-file", "compression": "zlib"}:
        return decode_signed_configuration(decoded, model_specs)
    validate_tar_gzip_config(decoded, model_specs)
    return decoded


def save_router_config(decoded_config: bytes, decoded_config_path: str, model_specs: dict) -> bool:
    """Save the decoded router configuration in its declared format."""
    if not isinstance(decoded_config, bytes) or not decoded_config:
        print("No decoded router configuration available to save.")
        return False
    try:
        path = Path(decoded_config_path).expanduser()
        extension = ".xml" if model_specs["configuration_format"] == "xml" else DECODED_EXTENSION
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
        if model_specs["configuration_format"] == "xml":
            validate_xml_declaration(decoded_config, model_specs)
        else:
            read_tar_files(decoded_config, model_specs)
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
        if model_specs["configuration_format"] == "xml":
            extract_xml_configuration(archive_path, output, model_specs)
        else:
            extract_tar_archive(archive_path, output, model_specs)
        print(f"Extracted router configuration: {output}")
        return str(output)
    except (OSError, ValueError, TypeError, tarfile.TarError) as exc:
        print(f"Failed to extract router configuration: {exc}")
        return False


def view_router_config_fields(config_dir: str, model_specs: dict) -> bool:
    """Display selected router configuration fields."""
    try:
        viewer = CONFIG_VIEW_HANDLERS.get(model_specs["configuration_format"])
        if viewer is None:
            raise ValueError(f'Unsupported configuration_format for viewing: {model_specs["configuration_format"]}')
        config_fields = model_specs["config_fields"]
        directory = Path(config_dir).expanduser()
        validate_directory(directory)
        if not directory.is_dir():
            raise NotADirectoryError(f"Configuration directory not found: {directory}")
        config_file = config_fields[CONFIG_FIELDS_FILE_KEY]
        relative = Path(config_file)
        path = directory / relative
        if not path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        contents = path.read_bytes().decode("utf-8")
        values = viewer(contents, model_specs, FIELD_DECRYPT_HANDLERS.get(model_specs["field_encryption"]["algorithm"]))
        rows = []
        for label, key in config_fields.items():
            if label != CONFIG_FIELDS_FILE_KEY and key is not None:
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


def edit_router_config_fields(config_dir: str, edited_dir: str, model_specs: dict) -> str | bool:
    """Copy and edit selected router configuration fields."""
    try:
        configuration_format = model_specs["configuration_format"]
        editor = CONFIG_EDIT_HANDLERS.get(configuration_format)
        viewer = CONFIG_VIEW_HANDLERS.get(configuration_format)
        if editor is None or viewer is None:
            raise ValueError(f"Unsupported configuration_format for editing: {configuration_format}")
        config_fields = model_specs["config_fields"]
        source = Path(config_dir).expanduser()
        validate_directory(source)
        destination = Path(edited_dir).expanduser()
        if not source.is_dir():
            raise NotADirectoryError(f"Decoded configuration directory not found: {source}")
        if any(path.is_symlink() for path in (destination, *destination.parents)):
            raise ValueError(f"Unsafe edited configuration symlink: {destination}")
        if destination.exists() and not destination.is_dir():
            raise ValueError(f"Edited configuration destination is not a directory: {destination}")
        relative = safe_relative(config_fields[CONFIG_FIELDS_FILE_KEY])
        source_file = source / relative
        if not source_file.is_file() or source_file.is_symlink():
            raise FileNotFoundError(f"Configuration file not found or unsafe: {source_file}")
        original_bytes = source_file.read_bytes()
        original = original_bytes.decode("utf-8")
        changes = {}
        values = viewer(original, model_specs, FIELD_DECRYPT_HANDLERS.get(model_specs["field_encryption"]["algorithm"]))
        if source.resolve() == destination.resolve() or source.resolve() in destination.resolve().parents or destination.resolve() in source.resolve().parents:
            raise ValueError("Edited directory must be separate from the decoded source directory")
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
            return False
        if destination.exists():
            if not confirm(f"Edited configuration already exists: {destination}\nOverwrite? [y/n]: "):
                print("Edited configuration overwrite cancelled.")
                return False
        edited = editor(original, model_specs, changes, FIELD_ENCRYPT_HANDLERS.get(model_specs["field_encryption"]["algorithm"]))
        if configuration_format == "xml":
            validate_xml_field_changes(original, edited, model_specs, changes,
                FIELD_DECRYPT_HANDLERS.get(model_specs["field_encryption"]["algorithm"]),
                FIELD_ENCRYPT_HANDLERS.get(model_specs["field_encryption"]["algorithm"]))
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        staging = Path(tempfile.mkdtemp(dir=destination.parent, prefix=f".{destination.name}."))
        backup = staging / "original"
        prepared = staging / "replacement"
        try:
            shutil.copytree(source, prepared, symlinks=True)
            validate_directory(prepared)
            target = prepared / relative
            if target.is_symlink():
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
                    FIELD_DECRYPT_HANDLERS.get(model_specs["field_encryption"]["algorithm"]),
                    FIELD_ENCRYPT_HANDLERS.get(model_specs["field_encryption"]["algorithm"]))
            else:
                parse_key_value_fields(saved, model_specs)
            if source_file.read_bytes() != original_bytes:
                raise ValueError("Original decoded configuration changed during editing")
            validate_directory(prepared)
            if destination.exists():
                os.replace(destination, backup)
            try:
                os.replace(prepared, destination)
            except BaseException:
                if backup.exists():
                    os.replace(backup, destination)
                raise
            if backup.exists():
                shutil.rmtree(backup)
        finally:
            if backup.exists():
                print(f"Original configuration retained at: {backup}")
                if prepared.exists():
                    shutil.rmtree(prepared)
            else:
                shutil.rmtree(staging)
        print(f"Saved edited router configuration: {destination}")
        return str(destination)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(f"Failed to edit router configuration: {exc}")
        return False


def encode_router_config(
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
        single_file = model_specs["archive"] == {"format": "single-file", "compression": "zlib"}
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
        wrapper = parse_router_wrapper(original.read_bytes(), model_specs)
        template_password = "" if model_specs["key_derivation"] == "device-key" else load_router_credentials(password_path, model_specs, "Enter router password: ")
        if template_password is False:
            return False
        original_archive = decrypt_router_payload(wrapper["encrypted"], template_password, model_specs, wrapper=wrapper, device_key_path=device_key_path)
        if single_file:
            original_archive = decode_signed_configuration(original_archive, model_specs)
            rebuilt_archive, changes = validate_edited_xml(original_archive, directory, model_specs,
                FIELD_DECRYPT_HANDLERS.get(model_specs["field_encryption"]["algorithm"]),
                FIELD_ENCRYPT_HANDLERS.get(model_specs["field_encryption"]["algorithm"]))
            payload = encode_signed_configuration(rebuilt_archive, model_specs)
        else:
            rebuilt_archive, changes = rebuild_tar_archive(original_archive, str(directory), model_specs)
            validate_edited_fields(original_archive, directory, model_specs)
            payload = rebuilt_archive
        target_password = "" if model_specs["key_derivation"] == "device-key" else load_target_router_credentials(template_password, model_specs, password_prompt)
        if target_password is False:
            return False
        encrypted = encrypt_router_payload(payload, target_password, model_specs, device_key_path=device_key_path)
        rebuilt = rebuild_router_wrapper(encode_router_payload(encrypted, model_specs), wrapper["header"], model_specs)
        verified = parse_router_wrapper(rebuilt, model_specs)
        decrypted = decrypt_router_payload(verified["encrypted"], target_password, model_specs, wrapper=verified, device_key_path=device_key_path)
        if single_file:
            decrypted = decode_signed_configuration(decrypted, model_specs)
        if decrypted != rebuilt_archive:
            raise ValueError("Generated backup failed decryption verification")
        if not single_file:
            validate_tar_gzip_config(decrypted, model_specs)
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
                    recovered = decode_router_config(str(prepared), model_specs, password_path, device_key_path=device_key_path)
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
        print("Modified files: " + (", ".join(changes) or "none; original compressed archive retained"))
        print(f"Saved edited router archive: {edited_archive}")
        print(f"Updated router backup: {output}; checksum and local round-trip verified.")
        return str(output)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, tarfile.TarError, EOFError, subprocess.SubprocessError) as exc:
        print(f"Failed to encode router configuration: {exc}")
        return False


def convert_router_config_fields(source_dir: str, destination_dir: str, source_specs: dict, destination_specs: dict) -> str | bool:
    """Transfer matching configured fields into the prepared destination and report skipped fields."""
    try:
        source_reader = CONFIG_VIEW_HANDLERS.get(source_specs["configuration_format"])
        destination_reader = CONFIG_VIEW_HANDLERS.get(destination_specs["configuration_format"])
        editor = CONFIG_EDIT_HANDLERS.get(destination_specs["configuration_format"])
        if source_reader is None or destination_reader is None or editor is None:
            raise ValueError("Unsupported configuration format for source reading or destination editing")
        source_decrypt_handler = FIELD_DECRYPT_HANDLERS.get(source_specs["field_encryption"]["algorithm"])
        destination_decrypt_handler = FIELD_DECRYPT_HANDLERS.get(destination_specs["field_encryption"]["algorithm"])
        destination_encrypt_handler = FIELD_ENCRYPT_HANDLERS.get(destination_specs["field_encryption"]["algorithm"])
        destination, destination_relative, original, source_file, source_bytes, skipped_fields, changes = prepare_config_conversion(
            source_dir, destination_dir, source_specs, destination_specs, source_reader, destination_reader,
            source_decrypt_handler, destination_decrypt_handler)
        print("\nSkipped source fields:")
        print("-" * 50)
        if skipped_fields:
            for label in skipped_fields:
                print(f"{label}: Not defined in destination")
        else:
            print("None")
        if not changes:
            print("\nNo matching configuration changes to transfer.")
            return False
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
            return False
        updates = {label: value for label, previous, value in changes}
        edited = editor(original, destination_specs, updates, destination_encrypt_handler)
        if destination_specs["configuration_format"] == "xml":
            validate_xml_field_changes(original, edited, destination_specs, updates,
                destination_decrypt_handler, destination_encrypt_handler)
        else:
            validate_key_value_field_changes(original, edited, destination_specs, updates)
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        staging = Path(tempfile.mkdtemp(dir=destination.parent, prefix=f".{destination.name}."))
        backup = staging / "original"
        prepared = staging / "replacement"
        try:
            shutil.copytree(destination, prepared, symlinks=True)
            validate_directory(prepared)
            target = prepared / destination_relative
            if target.is_symlink():
                raise ValueError("Unsafe destination configuration file")
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=target.parent, prefix=".config.", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(edited)
            try:
                os.chmod(temp_path, 0o600)
                os.replace(temp_path, target)
            finally:
                temp_path.unlink(missing_ok=True)
            saved = target.read_bytes().decode("utf-8")
            if destination_specs["configuration_format"] == "xml":
                validate_xml_field_changes(original, saved, destination_specs, updates,
                    destination_decrypt_handler, destination_encrypt_handler)
            else:
                validate_key_value_field_changes(original, saved, destination_specs, updates)
            if source_file.read_bytes() != source_bytes:
                raise ValueError("Source configuration changed during conversion")
            if (destination / destination_relative).read_bytes() != original.encode("utf-8"):
                raise ValueError("Prepared destination configuration changed during conversion")
            validate_directory(prepared)
            os.replace(destination, backup)
            try:
                os.replace(prepared, destination)
            except BaseException:
                os.replace(backup, destination)
                raise
            shutil.rmtree(backup)
        finally:
            if backup.exists():
                print(f"Previous destination retained at: {backup}")
                if prepared.exists():
                    shutil.rmtree(prepared)
            else:
                shutil.rmtree(staging)
        print(f"Converted configuration saved: {destination}")
        return str(destination)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(f"Failed to convert router configuration: {exc}")
        return False
