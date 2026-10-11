from __future__ import annotations
import base64
import binascii
import copy
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from getpass import getpass


# ---------------------------------------------------------------------
# FILE CONSTANTS
# ---------------------------------------------------------------------

ENCRYPTED_FILENAME = "config.enc"
DECODED_EXTENSION = ".tar.gz"
MODEL_SPECS_EXTENSION = ".json"


CONFIG_FIELDS_KEY = "config_fields"
CONFIG_FIELDS_FILE_KEY = "file"
OPENSSL_HEADER = b"Salted__"
SUPPORTED_HASHES = ("md5", "sha256", "sha512")


# ---------------------------------------------------------------------
# GET TARGET ROUTER FACTORY PASSWORD
# ---------------------------------------------------------------------

def get_target_router_password(model_specs: dict) -> str | bool:
    """Prompt for the target router's original factory Wi-Fi password."""
    if not model_specs.get("password_required", False):
        return ""
    try:
        password = getpass("Enter target router factory Wi-Fi password: ")
        if not password:
            print("Target router factory Wi-Fi password is required.")
            return False
        return password
    except (EOFError, KeyboardInterrupt):
        print("\nTarget router password entry cancelled.")
        return False


# ---------------------------------------------------------------------
# GET TEMPLATE PASSWORD
# ---------------------------------------------------------------------

def get_router_template_password(model_specs: dict, password_dir: str) -> str | bool:
    """Select and read a template router's factory password."""
    if not model_specs.get("password_required", False):
        return ""
    directory = Path(password_dir).expanduser()
    if not directory.is_dir():
        print(f"Template password directory not found: {directory}")
        return False
    password_files = sorted(directory.glob("*.txt"))
    if not password_files:
        print("No template router password files found.")
        return False
    print("\nSelect Template Router Password")
    print("--------------------------------")
    for index, path in enumerate(password_files, 1):
        print(f"{index}. {path.name}")
    try:
        choice = input("\nSelect password file (0 to cancel): ").strip()
        if choice == "0":
            return False
        index = int(choice) - 1
        if not 0 <= index < len(password_files):
            print("Invalid selection.")
            return False
        password = password_files[index].read_text(
            encoding="utf-8"
        ).strip()
        if not password:
            print("Selected password file is empty.")
            return False
        return password
    except (ValueError, OSError) as exc:
        print(f"Failed to load template password: {exc}")
        return False
    except (EOFError, KeyboardInterrupt):
        print("\nTemplate password selection cancelled.")
        return False
    
# ---------------------------------------------------------------------
# LOAD ROUTER MODEL SPECS
# ---------------------------------------------------------------------

def load_router_model_specs(specs_path: str) -> dict | bool:
    """Load and validate router model specifications from a JSON file."""
    try:
        path = Path(specs_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Router model specifications not found: {path}")
        if path.suffix.lower() != MODEL_SPECS_EXTENSION:
            raise ValueError(f"Router model specifications must be a {MODEL_SPECS_EXTENSION} file")
        with path.open("r", encoding="utf-8") as file:
            specs = json.load(file)
        validate_model_specs(specs)
        print(f"Loaded router model specifications: {specs['model']}")
        return specs
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Failed to load router model specifications: {exc}")
        return False


# ---------------------------------------------------------------------
# READ ROUTER BACKUP
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# VALIDATE MODEL SPECIFICATIONS
# ---------------------------------------------------------------------

def validate_model_specs(specs: dict) -> None:
    """Reject missing settings and unsupported mechanisms without guessing."""
    types = {"model": str, "firmware": str, "hardware": str, "encryption": str,
             "encoding": str, "salted": bool, "password_required": bool,
             "password_base": str, "password_hash": str, "key_derivation": str,
             "key_derivation_digest": str, "backup_format": dict, "archive": dict,
             "configuration_format": str, "config_fields": dict}
    if not isinstance(specs, dict):
        raise ValueError("Model specifications must be an object")
    for key, kind in types.items():
        if type(specs.get(key)) is not kind:
            raise ValueError(f"Missing or invalid model setting: {key}")
    supported = {"encryption": ("aes-256-cbc",), "encoding": ("base64",),
                 "password_hash": (*SUPPORTED_HASHES, "none"),
                 "key_derivation": ("openssl-legacy",),
                 "key_derivation_digest": SUPPORTED_HASHES,
                 "configuration_format": ("key-value",)}
    for key, values in supported.items():
        if specs[key] not in values:
            raise ValueError(f"Unsupported {key}: {specs[key]}")
    if any(c in specs["password_base"] for c in "\r\n\x00"):
        raise ValueError("Invalid password_base")
    archive_mode(specs, "r")
    fields = specs["config_fields"]
    if len(fields) < 2 or "file" not in fields:
        raise ValueError("config_fields requires file and editable fields")
    for label, key in fields.items():
        if not isinstance(label, str) or not label or not isinstance(key, str) or not key.strip():
            raise ValueError("Invalid config_fields entry")
    safe_relative(fields["file"])
    keys = [key for label, key in fields.items() if label != "file"]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate configured field keys")
    fmt = specs["backup_format"]
    required = {"type": str, "header_lines": int, "preserve_header": bool,
                "payload_line_length": int, "newline": str, "checksum": dict, "trailer": dict}
    for key, kind in required.items():
        if type(fmt.get(key)) is not kind:
            raise ValueError(f"Missing or invalid backup_format.{key}")
    if fmt["type"] != "line-wrapper" or fmt["newline"] != "\n":
        raise ValueError("Unsupported wrapper type or newline")
    if fmt["header_lines"] < 0 or fmt["payload_line_length"] <= 0 or fmt["payload_line_length"] % 4:
        raise ValueError("Invalid wrapper line counts")
    if fmt["header_lines"] and not fmt["preserve_header"]:
        raise ValueError("Header lines require preserve_header")
    checksum = fmt["checksum"]
    if checksum.get("algorithm") not in SUPPORTED_HASHES or checksum.get("scope") != "encoded-payload-with-newlines" or checksum.get("encoding") != "hex-lower":
        raise ValueError("Unsupported checksum algorithm, scope or encoding")
    if type(checksum.get("after_payload_lines")) is not int or checksum["after_payload_lines"] < 0:
        raise ValueError("Invalid checksum location")
    prefix = checksum.get("prefix", {})
    if not isinstance(prefix, dict) or prefix.get("encoding") != "base64" or type(prefix.get("random_bytes")) is not int or prefix["random_bytes"] < 0:
        raise ValueError("Unsupported checksum prefix")
    trailer = fmt["trailer"]
    if not isinstance(trailer.get("character"), str) or len(trailer["character"]) != 1 or not trailer["character"].isascii() or trailer["character"] in "\r\n" or type(trailer.get("repeat")) is not int or trailer["repeat"] < 1:
        raise ValueError("Invalid trailer construction")


# ---------------------------------------------------------------------
# PASSWORD DERIVATION AND ENCRYPTION
# ---------------------------------------------------------------------

def derive_router_passphrase(password: str, model_specs: dict) -> str:
    """Hash the factory password independently of OpenSSL key derivation."""
    if not isinstance(password, str) or (model_specs["password_required"] and not password):
        raise ValueError("Factory Wi-Fi password is required")
    algorithm = model_specs["password_hash"]
    if algorithm == "none":
        hashed = password
    elif algorithm in SUPPORTED_HASHES:
        hashed = hashlib.new(algorithm, password.encode("utf-8")).hexdigest()
    else:
        raise ValueError(f"Unsupported password_hash: {algorithm}")
    passphrase = model_specs["password_base"] + hashed
    if any(c in passphrase for c in "\r\n\x00"):
        raise ValueError("Passphrase contains unsupported control characters")
    return passphrase


def crypt_aes_256_cbc(data: bytes, password: str, model_specs: dict, decrypt: bool) -> bytes:
    """Use explicit OpenSSL legacy derivation; ciphertext never shares stdin."""
    if model_specs["key_derivation"] != "openssl-legacy":
        raise ValueError("Unsupported key_derivation")
    digest = model_specs["key_derivation_digest"]
    if digest not in SUPPORTED_HASHES:
        raise ValueError("Unsupported key_derivation_digest")
    if decrypt and model_specs["salted"] and (not data.startswith(OPENSSL_HEADER) or len(data) < 32):
        raise ValueError("Missing or corrupt OpenSSL salted header")
    passphrase = derive_router_passphrase(password, model_specs)
    with tempfile.TemporaryDirectory() as temp_dir:
        source = Path(temp_dir) / "payload"
        source.write_bytes(data)
        command = ["openssl", "enc", "-aes-256-cbc", "-d" if decrypt else "-e",
                   "-salt" if model_specs["salted"] else "-nosalt", "-md", digest,
                   "-in", str(source), "-pass", "stdin"]
        result = subprocess.run(command, input=passphrase.encode("utf-8") + b"\n",
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise ValueError("OpenSSL failed: incorrect factory password, corrupt payload or unavailable cipher/digest")
    return result.stdout


def decrypt_router_payload(data: bytes, password: str, model_specs: dict) -> bytes:
    """Dispatch decryption by mechanism, never by router identity."""
    if model_specs["encryption"] == "aes-256-cbc":
        return crypt_aes_256_cbc(data, password, model_specs, True)
    raise ValueError(f"Unsupported encryption: {model_specs['encryption']}")


def encrypt_router_payload(data: bytes, password: str, model_specs: dict) -> bytes:
    """Dispatch encryption by mechanism."""
    if model_specs["encryption"] == "aes-256-cbc":
        return crypt_aes_256_cbc(data, password, model_specs, False)
    raise ValueError(f"Unsupported encryption: {model_specs['encryption']}")


# ---------------------------------------------------------------------
# ENCODED PAYLOAD AND BACKUP WRAPPER
# ---------------------------------------------------------------------

def encode_router_payload(data: bytes, specs: dict) -> bytes:
    """Produce Base64 with the configured wrapping and trailing newline."""
    if specs["encoding"] != "base64":
        raise ValueError("Unsupported encoding")
    encoded = base64.b64encode(data)
    width = specs["backup_format"]["payload_line_length"]
    return b"".join(encoded[i:i + width] + b"\n" for i in range(0, len(encoded), width))


def decode_router_payload(data: bytes, specs: dict) -> bytes:
    """Decode the transport separately from encryption and wrapper handling."""
    if specs["encoding"] != "base64":
        raise ValueError("Unsupported encoding")
    return base64.b64decode(data.replace(b"\n", b""), validate=True)


def wrapper_trailer(fmt: dict) -> bytes:
    """Construct the configured final line."""
    return (fmt["trailer"]["character"] * fmt["trailer"]["repeat"] + fmt["newline"]).encode("ascii")


def parse_router_wrapper(data: bytes, model_specs: dict) -> dict:
    """Validate the exact wrapper and checksum before decoding the payload."""
    validate_model_specs(model_specs)
    fmt = model_specs["backup_format"]
    checksum = fmt["checksum"]
    lines = data.splitlines(keepends=True)
    count = fmt["header_lines"]
    position = count + checksum["after_payload_lines"]
    if len(lines) <= position + 1 or lines[-1] != wrapper_trailer(fmt):
        raise ValueError("Invalid backup wrapper or trailer")
    if any(not line.endswith(b"\n") or b"\r" in line for line in lines):
        raise ValueError("Invalid wrapper newline")
    special = lines[position][:-1]
    prefix_size = checksum["prefix"]["random_bytes"]
    prefix_length = 4 * ((prefix_size + 2) // 3)
    prefix = special[:prefix_length]
    if len(base64.b64decode(prefix, validate=True)) != prefix_size:
        raise ValueError("Invalid checksum random prefix")
    encoded = b"".join(lines[count:position] + lines[position + 1:-1])
    expected = hashlib.new(checksum["algorithm"], encoded).hexdigest().encode("ascii")
    if special[prefix_length:] != expected:
        raise ValueError("Backup encrypted payload checksum mismatch")
    encrypted = decode_router_payload(encoded, model_specs)
    if encode_router_payload(encrypted, model_specs) != encoded:
        raise ValueError("Invalid encoded payload line layout")
    return {"header": b"".join(lines[:count]), "encoded": encoded,
            "encrypted": encrypted, "checksum": expected}


def rebuild_router_wrapper(encoded: bytes, header: bytes, specs: dict) -> bytes:
    """Insert a fresh checksum and random prefix into the configured layout."""
    fmt = specs["backup_format"]
    checksum = fmt["checksum"]
    lines = encoded.splitlines(keepends=True)
    position = checksum["after_payload_lines"]
    if len(lines) < position:
        raise ValueError("Payload too short for configured checksum location")
    if len(header.splitlines(keepends=True)) != fmt["header_lines"]:
        raise ValueError("Original header does not match configured layout")
    prefix = base64.b64encode(os.urandom(checksum["prefix"]["random_bytes"]))
    special = prefix + hashlib.new(checksum["algorithm"], encoded).hexdigest().encode("ascii") + b"\n"
    result = header + b"".join(lines[:position]) + special + b"".join(lines[position:]) + wrapper_trailer(fmt)
    parse_router_wrapper(result, specs)
    return result


# ---------------------------------------------------------------------
# ARCHIVE VALIDATION
# ---------------------------------------------------------------------

def safe_relative(name: str) -> Path:
    """Reject absolute paths and traversal."""
    path = Path(name)
    if not name or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe relative path: {name}")
    return path


def archive_mode(specs: dict, operation: str) -> str:
    """Select supported archive and compression mechanisms."""
    if specs["archive"].get("format") != "tar" or specs["archive"].get("compression") != "gzip":
        raise ValueError("Unsupported archive format or compression")
    return operation + ":gz"


def validate_archive(archive: tarfile.TarFile) -> list:
    """Validate all entries before any extraction or edited-file reads."""
    members = archive.getmembers()
    seen = {}
    if not members:
        raise ValueError("Empty archive")
    for member in members:
        path = safe_relative(member.name)
        if not (member.isfile() or member.isdir()) or path in seen or (path == Path('.') and not member.isdir()):
            raise ValueError(f"Unsafe or duplicate archive member: {member.name}")
        seen[path] = member
    for path in seen:
        if any(parent in seen and not seen[parent].isdir() for parent in path.parents):
            raise ValueError(f"Conflicting archive paths: {path}")
    return members


def validate_directory(directory: Path) -> None:
    """Reject symlinks and special files, including symlink ancestors."""
    if any(path.is_symlink() for path in (directory, *directory.parents)):
        raise ValueError("Unsafe directory symlink")
    for path in directory.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"Unsafe configuration entry: {path}")


def decode_router_config(
    config_path: str,
    model_specs: dict,
    password_dir: str
) -> bytes | bool:
    """Decode and validate an original backup using only declared mechanisms."""
    wrapper = parse_router_wrapper(
        Path(config_path).expanduser().read_bytes(),
        model_specs
    )
    password = get_router_template_password(model_specs, password_dir)
    if password is False:
        return False
    decoded = decrypt_router_payload(
        wrapper["encrypted"],
        password,
        model_specs
    )
    with tarfile.open(
        fileobj=io.BytesIO(decoded),
        mode=archive_mode(model_specs, "r")
    ) as archive:
        members = validate_archive(archive)
        configured = Path(model_specs["config_fields"]["file"])
        member = next(
            (m for m in members if Path(m.name) == configured and m.isfile()),
            None
        )
        if member is None:
            raise ValueError("Configured file missing from archive")
        parse_config_fields(
            archive.extractfile(member).read().decode("utf-8"),
            model_specs
        )
    return decoded


# ---------------------------------------------------------------------
# SAVE DECODED CONFIGURATION
# ---------------------------------------------------------------------

def save_router_config(decoded_config: bytes, decoded_config_path: str, model_specs: dict) -> bool:
    """Save the decoded router configuration as a tar.gz archive."""
    if not isinstance(decoded_config, bytes) or not decoded_config:
        print("No decoded router configuration available to save.")
        return False
    try:
        path = Path(decoded_config_path).expanduser()
        if not path.name.endswith(DECODED_EXTENSION):
            raise ValueError(f"Decoded configuration path must end with {DECODED_EXTENSION}")
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"Decoded archive already exists: {path}")
        with tarfile.open(fileobj=io.BytesIO(decoded_config), mode=archive_mode(model_specs, "r")) as archive:
            validate_archive(archive)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            os.chmod(temp_path, 0o600)
            temp_file.write(decoded_config)
        try:
            os.link(temp_path, path)
        finally:
            temp_path.unlink(missing_ok=True)
        print(f"Saved decoded router configuration: {path}")
        return True
    except (OSError, ValueError, TypeError, tarfile.TarError, EOFError) as exc:
        print(f"Failed to save decoded router configuration: {exc}")
        return False


# ---------------------------------------------------------------------
# EXTRACT ROUTER CONFIG
# ---------------------------------------------------------------------

def extract_router_config(archive_path: str, output_dir: str, model_specs: dict) -> str | bool:
    """Safely extract the decoded router configuration."""
    try:
        archive_path = Path(archive_path).expanduser()
        output = Path(output_dir).expanduser()
        if not archive_path.is_file():
            raise FileNotFoundError(f"Decoded archive not found: {archive_path}")
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Extraction directory already exists: {output}")
        with tarfile.open(archive_path, mode=archive_mode(model_specs, "r")) as archive:
            members = validate_archive(archive)
            if not members:
                raise ValueError("Decoded archive is empty")
            for member in members:
                relative = Path(member.name)
                if relative.is_absolute() or ".." in relative.parts or not (member.isfile() or member.isdir()):
                    raise ValueError(f"Unsafe archive member: {member.name}")
            output.mkdir(parents=True, mode=0o700)
            try:
                for member in members:
                    destination = output / member.name
                    if member.isdir():
                        destination.mkdir(parents=True, exist_ok=True, mode=0o700)
                    else:
                        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                        stream = archive.extractfile(member)
                        if stream is None:
                            raise ValueError(f"Cannot extract: {member.name}")
                        with stream, destination.open("xb") as target:
                            shutil.copyfileobj(stream, target)
                        destination.chmod(0o600)
            except Exception:
                shutil.rmtree(output)
                raise
        print(f"Extracted router configuration: {output}")
        return str(output)
    except (OSError, ValueError, TypeError, tarfile.TarError) as exc:
        print(f"Failed to extract router configuration: {exc}")
        return False


# ---------------------------------------------------------------------
# VIEW ROUTER CONFIG FIELDS
# ---------------------------------------------------------------------

def view_router_config_fields(config_dir: str, model_specs: dict) -> bool:
    """Display selected router configuration fields."""
    try:
        config_fields = model_specs["config_fields"]
        directory = Path(config_dir).expanduser()
        validate_directory(directory)
        if not directory.is_dir():
            raise NotADirectoryError(f"Configuration directory not found: {directory}")
        config_file = config_fields[CONFIG_FIELDS_FILE_KEY]
        relative = Path(config_file)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid configuration file path")
        path = directory / relative
        if not path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        contents = path.read_bytes().decode("utf-8")
        lines, fields = parse_config_fields(contents, model_specs)
        values = {key: lines[index].split("=", 1)[1].rstrip("\r\n") for key, index in fields.values()}
        rows = []
        for label, key in config_fields.items():
            if label != CONFIG_FIELDS_FILE_KEY:
                rows.append((label, values[key]))
        width = max(len("Field"), *(len(label) for label, _ in rows))
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
# EDIT ROUTER CONFIG FIELDS
# ---------------------------------------------------------------------

def edit_router_config_fields(config_dir: str, edited_dir: str, model_specs: dict) -> str | bool:
    """Copy and edit selected router configuration fields."""
    from constants.RouterConstants import EDITED_SUFFIX
    try:
        config_fields = model_specs["config_fields"]
        source = Path(config_dir).expanduser()
        validate_directory(source)
        destination = Path(edited_dir).expanduser()
        if not source.is_dir():
            raise NotADirectoryError(f"Decoded configuration directory not found: {source}")
        configuration_name = input("Configuration name (blank for default; letters, numbers, _ or -): ").strip()
        if configuration_name:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", configuration_name):
                raise ValueError("Invalid configuration name: use only letters, numbers, _ or -")
            destination = destination.with_name(f"{configuration_name}{EDITED_SUFFIX}")
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"Edited configuration already exists: {destination}")
        relative = Path(config_fields[CONFIG_FIELDS_FILE_KEY])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid configuration file path")
        source_file = source / relative
        if not source_file.is_file() or source_file.is_symlink():
            raise FileNotFoundError(f"Configuration file not found or unsafe: {source_file}")
        original = source_file.read_bytes().decode("utf-8")
        lines, fields = parse_config_fields(original, model_specs)
        changes = {}
        print(f"\nEditing configuration: {source.name}")
        print("Press Enter to keep the existing value.")
        for label, (key, index) in fields.items():
            current = lines[index].split("=", 1)[1].rstrip("\r\n")
            print(f"\n{label}: {current}")
            updated = input(f"New {label}: ")
            if not updated:
                continue
            if "\n" in updated or "\r" in updated or "\x00" in updated:
                raise ValueError(f"Invalid value for {label}")
            changes[index] = updated
        if not changes:
            print("No changes made.")
        else:
            print("\nChanges:")
            for label, (key, index) in fields.items():
                if index in changes:
                    print(f"{label}: {lines[index].split('=', 1)[1].rstrip()} -> {changes[index]}")
        confirmation = input("\nSave configuration for encoding? [y/n]: ").strip().lower()
        if confirmation not in ("y", "yes"):
            print("Configuration editing cancelled.")
            return False
        for index, value in changes.items():
            line = lines[index]
            prefix = line.split("=", 1)[0]
            newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
            lines[index] = f"{prefix}={value}{newline}"
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copytree(source, destination, symlinks=True)
        try:
            target = destination / relative
            if target.is_symlink():
                raise ValueError(f"Unsafe configuration file: {target}")
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=target.parent, prefix=".config.", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.writelines(lines)
            try:
                os.chmod(temp_path, 0o600)
                os.replace(temp_path, target)
            finally:
                temp_path.unlink(missing_ok=True)
        except Exception:
            shutil.rmtree(destination)
            raise
        print(f"Saved edited router configuration: {destination}")
        return str(destination)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(f"Failed to edit router configuration: {exc}")
        return False

# ---------------------------------------------------------------------
# REBUILD ROUTER ARCHIVE
# ---------------------------------------------------------------------

def rebuild_router_archive(original_archive: bytes, edited_dir: str, model_specs: dict) -> tuple[bytes, list[str]]:
    """Rebuild the original tar.gz archive using edited files."""
    directory = Path(edited_dir).expanduser()
    if not directory.is_dir():
        raise NotADirectoryError(f"Edited configuration directory not found: {directory}")
    validate_directory(directory)
    changes = []
    with tarfile.open(fileobj=io.BytesIO(original_archive), mode=archive_mode(model_specs, "r")) as source:
        members = validate_archive(source)
        expected = {str(Path(m.name)) for m in members if m.isfile()}
        actual = {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()}
        if actual != expected:
            raise ValueError("Edited files do not match the original archive")
        contents = []
        for member in members:
            relative = Path(member.name)
            if relative.is_absolute() or ".." in relative.parts or not (member.isfile() or member.isdir()):
                raise ValueError(f"Unsafe archive member: {member.name}")
            if not member.isfile():
                contents.append(None)
                continue
            stream = source.extractfile(member)
            if stream is None:
                raise ValueError(f"Unreadable archive member: {member.name}")
            with stream:
                original_content = stream.read()
            edited_file = directory / relative
            if not edited_file.is_file() or edited_file.is_symlink():
                raise ValueError(f"Missing or unsafe edited file: {edited_file}")
            edited_content = edited_file.read_bytes()
            if edited_content != original_content:
                changes.append(member.name)
            contents.append(edited_content)
        if not changes:
            return original_archive, changes
        buffer = io.BytesIO()
        archive_format = tarfile.PAX_FORMAT if any(member.pax_headers for member in members) else tarfile.GNU_FORMAT
        with tarfile.open(fileobj=buffer, mode=archive_mode(model_specs, "w"), format=archive_format) as target:
            for member, content in zip(members, contents):
                entry = copy.deepcopy(member)
                entry.pax_headers.pop("size", None)
                if entry.isfile():
                    entry.size = len(content)
                    target.addfile(entry, io.BytesIO(content))
                else:
                    target.addfile(entry)
    return buffer.getvalue(), changes


# ---------------------------------------------------------------------
# ENCODE ROUTER CONFIGURATION
# ---------------------------------------------------------------------

def encode_router_config(
    edited_dir: str,
    original_cfg: str,
    output_dir: str,
    model_specs: dict,
    password_dir: str,
    configuration_name: str
) -> str | bool:
    """Rebuild, encrypt and verify an edited backup without changing its source."""
    from constants.RouterConstants import EDITED_SUFFIX, UPDATED_SUFFIX
    try:
        validate_model_specs(model_specs)
        directory = Path(edited_dir).expanduser()
        original = Path(original_cfg).expanduser()
        if not re.fullmatch(r"[A-Za-z0-9_-]+", configuration_name):
            raise ValueError("Invalid configuration name: use only letters, numbers, _ or -")
        if directory.name != configuration_name + EDITED_SUFFIX:
            raise ValueError(
                "Edited configuration directory does not match configuration name"
            )
        output = Path(output_dir).expanduser() / f"{configuration_name}{UPDATED_SUFFIX}{original.suffix}"
        if output.exists() or output.is_symlink():
            raise FileExistsError(
                f"Updated backup already exists: {output}"
            )
        wrapper = parse_router_wrapper(
            original.read_bytes(),
            model_specs
        )
        # Select the password file belonging to the master template router
        template_password = get_router_template_password(model_specs, password_dir)
        if template_password is False:
            return False
        original_archive = decrypt_router_payload(
            wrapper["encrypted"],
            template_password,
            model_specs
        )
        rebuilt_archive, changes = rebuild_router_archive(
            original_archive,
            str(directory),
            model_specs
        )
        validate_edited_fields(
            original_archive,
            directory,
            model_specs
        )
        # Encrypt for target router using its factory password
        target_password = get_target_router_password(model_specs)
        if target_password is False:
            return False
        encrypted = encrypt_router_payload(
            rebuilt_archive,
            target_password,
            model_specs
        )
        rebuilt = rebuild_router_wrapper(
            encode_router_payload(encrypted, model_specs),
            wrapper["header"],
            model_specs
        )
        # Verify using target router password
        verified = parse_router_wrapper(rebuilt, model_specs)
        decrypted = decrypt_router_payload(
            verified["encrypted"],
            target_password,
            model_specs
        )
        if decrypted != rebuilt_archive:
            raise ValueError(
                "Generated backup failed decryption verification"
            )
        with tarfile.open(
            fileobj=io.BytesIO(decrypted),
            mode=archive_mode(model_specs, "r")
        ) as archive:
            validate_archive(archive)
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
            mode=0o700
        )
        with output.open("xb") as target:
            os.chmod(output, 0o600)
            target.write(rebuilt)
        print(
            "Modified files: " +
            (", ".join(changes) or "none; original compressed archive retained")
        )
        print(
            f"Updated router backup: {output}; "
            "checksum and local round-trip verified."
        )
        return str(output)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        tarfile.TarError,
        EOFError,
        subprocess.SubprocessError
    ) as exc:
        print(f"Failed to encode router configuration: {exc}")
        return False


# ---------------------------------------------------------------------
# CONFIGURATION PARSER AND ORIGINAL MATCHING
# ---------------------------------------------------------------------

def parse_config_fields(contents: str, specs: dict) -> tuple[list, dict]:
    """Select the generic parser and require unique configured keys."""
    if specs["configuration_format"] != "key-value":
        raise ValueError("Unsupported configuration_format")
    lines = contents.splitlines(keepends=True)
    indices = {}
    for index, line in enumerate(lines):
        if "=" in line and not line.lstrip().startswith(("#", ";")):
            key = line.split("=", 1)[0].strip()
            if key in indices:
                raise ValueError(f"Duplicate configuration key: {key}")
            indices[key] = index
    fields = {}
    for label, key in specs["config_fields"].items():
        if label == "file":
            continue
        if key not in indices:
            raise ValueError(f"Missing configuration field: {label} ({key})")
        fields[label] = (key, indices[key])
    return lines, fields


def validate_edited_fields(original_archive: bytes, directory: Path, specs: dict) -> None:
    """Match every original byte except values explicitly declared editable."""
    config_path = safe_relative(specs["config_fields"]["file"])
    found = False
    with tarfile.open(fileobj=io.BytesIO(original_archive), mode=archive_mode(specs, "r")) as archive:
        for member in validate_archive(archive):
            if not member.isfile():
                continue
            original = archive.extractfile(member).read()
            edited = (directory / member.name).read_bytes()
            if Path(member.name) != config_path:
                if original != edited:
                    raise ValueError(f"Original mismatch in uneditable file: {member.name}")
                continue
            found = True
            before, fields = parse_config_fields(original.decode("utf-8"), specs)
            after, edited_fields = parse_config_fields(edited.decode("utf-8"), specs)
            for label, (_, index) in fields.items():
                other = edited_fields[label][1]
                for lines, position in ((before, index), (after, other)):
                    line = lines[position]
                    newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
                    lines[position] = line.split("=", 1)[0] + "=" + newline
            if before != after:
                raise ValueError("Edited configuration differs outside declared editable values")
    if not found:
        raise ValueError("Configured file missing from original archive")
