# ---------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------

from __future__ import annotations

from functools import partial
from getpass import getpass
from pathlib import Path
import os
import shutil
import tempfile

from modules.display_utils import confirm
from modules.router_config_utils import normalize_key_value_fields

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def safe_relative(name: str) -> Path:
    """Reject absolute paths and traversal."""
    path = Path(name)
    if not name or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe relative path: {name}")
    return path


def validate_directory(directory: Path) -> None:
    """Reject symlinks and special files, including symlink ancestors."""
    if any(path.is_symlink() for path in (directory, *directory.parents)):
        raise ValueError("Unsafe directory symlink")
    for path in directory.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"Unsafe configuration entry: {path}")


def _handler(functions: dict, name: str | None):
    """Resolve a configured algorithm; skip null values, reject unknown ones."""
    if name is None:
        return None
    handler = functions.get(name)
    if not callable(handler):
        raise ValueError(f"Unsupported router algorithm: {name}")
    return handler


def field_handler(edit: dict, functions: dict):
    """Bind the configured field cipher to its key and IV."""
    settings = edit.get("field_encryption") or {}
    name = settings.get("algorithm")
    if name is None:
        return None
    handler = functions.get(name)
    if not callable(handler):
        raise ValueError(f"Unsupported router algorithm: {name}")
    return partial(handler, **{key: value for key, value in settings.items()
                               if key not in ("algorithm", "fields")})


# ---------------------------------------------------------------------
# ROUTER SPECIFICATIONS
# ---------------------------------------------------------------------

def resolve_router_operations(router_settings, registry, operation):
    """Select registered callables in registry execution order."""
    router = router_settings["router_specs"]
    codec = router.get("codec") or {}
    edit = router.get("edit") or {}
    if operation in ("edit", "view"):
        selected = {edit.get("configuration_format")}
    elif operation == "checksum":
        selected = {codec.get("checksum")}
    elif operation in ("extract", "check"):
        selected = {codec.get("archive")}
    else:
        selected = {
            codec.get("encoding"),
            codec.get("wrapper"),
            codec.get("archive"),
            (codec.get("key_derivation") or codec.get("encryption")) if codec.get("encryption") else None,
            (codec.get("signature") or {}).get("algorithm"),
            (edit.get("field_encryption") or {}).get("algorithm"),
        }
    selected.discard(None)
    return {name: function for name, function in registry.items() if name in selected}


# ---------------------------------------------------------------------
# OPERATION BUILDERS
# ---------------------------------------------------------------------

def build_encode_operations(router_settings, encode_operations, encode_validate_operations):
    """Return selected encode validators and algorithms in execution order."""
    codec = router_settings['router_specs'].get('codec') or {}
    if codec.get('key_derivation') and not codec.get('encryption'):
        raise ValueError('key_derivation requires encryption')
    roles = {name: codec.get(name) for name in ('archive', 'encryption', 'encoding', 'wrapper')}
    roles['encryption'] = (codec.get('key_derivation') or codec.get('encryption')) if codec.get('encryption') else None
    signature = (codec.get('signature') or {}).get('algorithm')
    required = (set(roles.values()) | {signature}) - {None}
    for name in required:
        _handler(encode_operations, name)
    names = [name for name in encode_operations if name in required]
    order = codec.get('encode_order')
    if order:
        active = {role for role, name in roles.items() if name is not None}
        if len(order) != len(set(order)) or not active.issubset(order) or not set(order).issubset(roles):
            raise ValueError('Invalid encode_order')
        names = [roles[role] for role in order if roles[role] is not None]
        if signature:
            names.insert(names.index(roles['archive']) if roles['archive'] in names else 0, signature)
        names = list(dict.fromkeys(names))
    return [function for name, function in encode_validate_operations.items() if name in required] + [encode_operations[name] for name in names]


def build_decode_operations(router_settings, decode_operations, decode_validate_operations):
    """Return selected decode validators and algorithms in execution order."""
    codec = router_settings['router_specs'].get('codec') or {}
    if codec.get('key_derivation') and not codec.get('encryption'):
        raise ValueError('key_derivation requires encryption')
    roles = {name: codec.get(name) for name in ('wrapper', 'encoding', 'encryption', 'archive')}
    roles['encryption'] = (codec.get('key_derivation') or codec.get('encryption')) if codec.get('encryption') else None
    signature = (codec.get('signature') or {}).get('algorithm')
    required = (set(roles.values()) | {signature}) - {None}
    for name in required:
        _handler(decode_operations, name)
    names = [name for name in decode_operations if name in required]
    order = codec.get('decode_order')
    if order:
        active = {role for role, name in roles.items() if name is not None}
        if len(order) != len(set(order)) or not active.issubset(order) or not set(order).issubset(roles):
            raise ValueError('Invalid decode_order')
        names = [roles[role] for role in order if roles[role] is not None]
        if signature:
            names.insert(names.index(roles['archive']) + 1 if roles['archive'] in names else len(names), signature)
        names = list(dict.fromkeys(names))
    return [function for name, function in decode_validate_operations.items() if name in required] + [decode_operations[name] for name in names]


def build_edit_operations(router_settings, edit_operations, edit_validate_operations):
    """Return the selected format validators followed by its editor."""
    method = (router_settings['router_specs'].get('edit') or {}).get('configuration_format')
    if method is None:
        return []
    editor = _handler(edit_operations, method)
    return [function for name, function in edit_validate_operations.items() if name == method] + [editor]


def build_view_operations(router_settings, view_operations, view_validate_operations):
    """Return the selected format validators followed by its reader."""
    method = (router_settings['router_specs'].get('edit') or {}).get('configuration_format')
    if method is None:
        return []
    viewer = _handler(view_operations, method)
    return [function for name, function in view_validate_operations.items() if name == method] + [viewer]


# ---------------------------------------------------------------------
# OPERATION EXECUTION
# ---------------------------------------------------------------------

def run_router_operations(data, operations, context):
    """Pass each result to the next selected operation; validators retain the input."""
    if not isinstance(operations, list) or not isinstance(context, dict):
        raise ValueError("Router operations and context are required")
    if data is None or (isinstance(data, (bytes, str)) and not data):
        raise ValueError("Router input is empty or unavailable")
    for operation in operations:
        value = operation(data, context=context)
        if value is not None:
            if isinstance(data, bytes) and (not isinstance(value, bytes) or not value):
                raise ValueError(f"Invalid router payload from {operation.__name__}")
            data = value
    return data


# ---------------------------------------------------------------------
# ROUTER INPUT AND CREDENTIALS
# ---------------------------------------------------------------------

def read_router_input(path):
    """Read a backup without accepting an empty or missing payload."""
    source = Path(path).expanduser()
    data = source.read_bytes()
    if not data:
        raise ValueError(f"Router backup is empty: {source}")
    return {"path": source, "data": data}


def load_router_credentials(password_path, codec, password_prompt):
    """Read a required template password or prompt, keeping cancellation distinct."""
    if not codec.get("password_required"):
        return ""
    if password_path:
        try:
            password = Path(password_path).expanduser().read_bytes().decode("utf-8").strip()
        except UnicodeError:
            raise ValueError("Password file must contain UTF-8 text") from None
    else:
        try:
            password = getpass(password_prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nRouter password entry cancelled.")
            return None
    if not password or any(char in password for char in "\r\n\x00"):
        raise ValueError("Router password is required and must not contain control characters")
    return password


def prepare_codec_context(model_specs, password_path, password_prompt, device_key_path, checksum_functions):
    """Load this router's credentials and metadata for its selected operations."""
    router = model_specs["router_specs"]
    codec = router["codec"]
    password = load_router_credentials(password_path, codec, password_prompt)
    if password is None:
        return None
    device_key = None
    if codec.get("device_key_required") or codec.get("key_derivation") == "device-key":
        if not device_key_path:
            raise ValueError("Required router device key path is not configured; an export password is not a device key")
        device_key = Path(device_key_path).expanduser().read_bytes()
        if not device_key:
            raise ValueError("Router device key file is empty")
    return {
        "codec": codec,
        "hardware": router.get("hardware"),
        "firmware": router.get("firmware"),
        "edit": router.get("edit") or {},
        "password": password,
        "device_key": device_key,
        "checksum_functions": checksum_functions,
        "header": b"",
        "check_inputs": True,
    }


def load_target_router_credentials(template_context, password_prompt):
    """Collect a target password using only this router's template credentials."""
    if not isinstance(template_context, dict):
        raise ValueError("Template codec context is required")
    codec = template_context["codec"]
    password = ""
    if codec.get("password_required"):
        try:
            password = getpass(password_prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nDestination router password entry cancelled.")
            return None
        if password_prompt == "Enter target router password (Enter to use template password): ":
            password = password or template_context["password"]
        if not password or any(char in password for char in "\r\n\x00"):
            raise ValueError("Destination router password is required and must not contain control characters")
    return {"password": password, "device_key": template_context.get("device_key")}


# ---------------------------------------------------------------------
# ROUTER VALIDATION
# ---------------------------------------------------------------------

def validate_router_field_mappings(model_specs: dict) -> bool:
    """Validate logical field mappings and their protected-field references."""
    edit = model_specs["router_specs"].get("edit") or {}
    names = [field["name"] for field in model_specs["config_fields"]]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate logical configuration field names")
    field_paths = [field["path"] for field in model_specs["config_fields"] if field["path"] is not None]
    if len(field_paths) != len(set(field_paths)):
        raise ValueError("Duplicate configuration field mappings")
    if field_paths and not edit.get("configuration_format"):
        raise ValueError("Configuration field mappings require an edit section")
    if edit.get("configuration_format"):
        safe_relative(edit["configuration_file"])
    protected = edit.get("field_encryption") or {}
    if protected.get("algorithm") is not None and (not isinstance(protected.get("fields"), list) or not protected["fields"]):
        raise ValueError("Field encryption requires a nonempty declared fields list")
    mapped = {field["name"] for field in model_specs["config_fields"] if field["path"] is not None}
    if any(name not in mapped for name in protected.get("fields") or []):
        raise ValueError("Encrypted field has no configuration mapping")
    return True


def validate_decoded_configuration(data, model_specs, check_functions, checksum_functions,
                                   decoded_context, view_operations):
    """Validate decoded bytes and declared configuration fields before saving."""
    if not isinstance(data, bytes) or not data:
        raise ValueError("No decoded router configuration available to save")
    router = model_specs["router_specs"]
    method = router["codec"].get("archive")
    context = {"codec": router["codec"], "edit": router.get("edit") or {},
               "checksum_functions": checksum_functions}
    if method is not None:
        _handler(check_functions, method)(data, context=context)
    if method == "tar.gz":
        edit = router.get("edit") or {}
        configured = str(safe_relative(edit["configuration_file"]))
        files = decoded_context.get("files") or {}
        if configured not in files:
            raise ValueError("Configured file missing from archive")
        if not view_operations:
            raise ValueError("Configuration reader is unavailable")
        view_operations[-1](files[configured].decode("utf-8"), model_specs)
    return True


def validate_configuration_changes(original: str, edited: str, specs: dict,
                                   viewer, editor, decrypt_handler=None, encrypt_handler=None) -> bool:
    """Permit only declared replacements using the selected format's own editor."""
    if not isinstance(original, str) or not isinstance(edited, str):
        raise ValueError('Original and edited configuration must be text')
    before = viewer(original, specs, decrypt_handler)
    after = viewer(edited, specs, decrypt_handler)
    if before.keys() != after.keys():
        raise ValueError("Edited configuration fields do not match the original")
    changes = {name: value for name, value in after.items() if value != before[name]}
    configuration_format = (specs["router_specs"].get("edit") or {}).get("configuration_format")
    if configuration_format == "key-value":
        permitted = normalize_key_value_fields(original, specs) == normalize_key_value_fields(edited, specs)
    else:
        permitted = editor(original, specs, changes, encrypt_handler) == edited
    if not permitted:
        raise ValueError("Edited configuration differs outside declared editable values")
    return True


# ---------------------------------------------------------------------
# DECODING AND EXTRACTION
# ---------------------------------------------------------------------

def extract_configuration_file(data: bytes, output: Path, configuration_file: str | None = None, *, context=None) -> None:
    """Stage one decoded configuration file, preserving its bytes and permissions."""
    if context is not None:
        configuration_file = context["edit"]["configuration_file"]
    relative = safe_relative(configuration_file)
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=f".{output.name}.") as directory:
        prepared = Path(directory) / "configuration"
        target = prepared / relative
        target.parent.mkdir(parents=True, mode=0o700)
        target.write_bytes(data)
        target.chmod(0o600)
        replace_router_directory(prepared, output)


def extract_router_config(archive_path, output_dir, model_specs, extract_functions, checksum_functions):
    """Confirm and atomically extract a declared format through its registered extractor."""
    archive_path, output = Path(archive_path).expanduser(), Path(output_dir).expanduser()
    if not archive_path.is_file():
        raise FileNotFoundError(f"Decoded archive not found: {archive_path}")
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError(f"Unsafe extraction directory symlink: {output}")
    if output.resolve() == archive_path.resolve() or output.resolve() in archive_path.resolve().parents:
        raise ValueError("Extraction directory must not contain the decoded archive")
    if output.exists():
        if not output.is_dir():
            raise NotADirectoryError(f"Extraction destination is not a directory: {output}")
        if not confirm(f"Extraction directory already exists: {output}\nOverwrite? [y/n]: "):
            print("Extraction overwrite cancelled.")
            return None
    router = model_specs["router_specs"]
    context = {"codec": router["codec"], "edit": router.get("edit") or {},
               "checksum_functions": checksum_functions}
    method = router["codec"].get("archive")
    if method is None:
        raise ValueError("Configuration extraction is not declared for this router")
    _handler(extract_functions, method)(archive_path.read_bytes(), output, context=context)
    validate_directory(output)
    if not (output / safe_relative(context["edit"]["configuration_file"])).is_file():
        raise ValueError("Configured file missing from extracted configuration")
    print(f"Extracted router configuration: {output}")
    return str(output)


# ---------------------------------------------------------------------
# CONFIGURATION VIEWING
# ---------------------------------------------------------------------

def display_configuration_values(values, context, config_fields):
    """Display selected fields using the existing layout."""
    if not isinstance(values, dict):
        raise ValueError('Configuration values must be a mapping')
    rows = [(field['name'], values[field['name']]) for field in config_fields if field['path'] is not None]
    width = max([len('Field'), *(len(label) for label, _ in rows)])
    print(f"\nConfiguration: {context['source'].name} ({context['relative']})")
    print(f"{'Field':<{width}} | Value")
    print(f"{'-' * width}-+------------------------------")
    for label, value in rows:
        print(f'{label:<{width}} | {value}')
    return True


def display_router_operations(operations, label):
    """Display selected callable operations through the existing table formatter."""
    from modules.display_utils import print_dict_table

    rows = [
        {"Step": index, "Function": function.__name__}
        for index, function in enumerate(operations, 1)
    ]
    return print_dict_table(rows, ["Step", "Function"], label)


# ---------------------------------------------------------------------
# CONFIGURATION EDITING
# ---------------------------------------------------------------------

def read_configuration_source(config_dir, edit):
    """Read a safe configuration file and retain its exact source bytes."""
    if not edit or not edit.get("configuration_file"):
        raise ValueError('Configuration format is not established')
    source = Path(config_dir).expanduser()
    validate_directory(source)
    if not source.is_dir():
        raise NotADirectoryError(f'Configuration directory not found: {source}')
    relative = safe_relative(edit['configuration_file'])
    path = source / relative
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f'Configuration file not found or unsafe: {path}')
    original = path.read_bytes()
    return {
        'source': source,
        'relative': relative,
        'original_bytes': original,
        'original': original.decode('utf-8'),
    }


def prepare_configuration_context(source, model_specs, decode_functions, encode_functions,
                                  view_operations, edit_operations=None, destination=None):
    """Bind the loaded configuration to registered field handlers and its format."""
    if not isinstance(source, dict) or not view_operations or (edit_operations is not None and not edit_operations):
        raise ValueError("Configuration source and format operations are required")
    target = Path(destination).expanduser() if destination is not None else None
    if target is not None:
        if any(path.is_symlink() for path in (target, *target.parents)):
            raise ValueError(f"Unsafe edited configuration symlink: {target}")
        if target.exists() and not target.is_dir():
            raise NotADirectoryError(f"Edited configuration destination is not a directory: {target}")
        directory = source["source"].resolve()
        if directory == target.resolve() or directory in target.resolve().parents or target.resolve() in directory.parents:
            raise ValueError("Edited directory must be separate from the decoded source directory")
    edit = model_specs["router_specs"].get("edit") or {}
    return {
        **source,
        "destination": target,
        "specs": model_specs,
        "decrypt_handler": field_handler(edit, decode_functions),
        "encrypt_handler": field_handler(edit, encode_functions),
        "viewer": view_operations[-1],
        "editor": edit_operations[-1] if edit_operations else None,
    }


def prompt_router_changes(values, context):
    """Collect and confirm field edits, including unchanged configurations."""
    if not isinstance(values, dict) or not isinstance(context, dict):
        raise ValueError("Configuration values are unavailable")
    source, destination = context["source"], context["destination"]
    configuration_format = context["specs"]["router_specs"]["edit"]["configuration_format"]
    changes = {}
    print(f"\nEditing configuration: {source.name}")
    print("Press Enter to keep the existing value.")
    try:
        for label, current in values.items():
            print(f"\n{label}: {current}")
            updated = input(f"New {label}: ")
            if not updated:
                continue
            if any(char in updated for char in "\r\n\x00"):
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
        if destination.exists() and not confirm(f"Edited configuration already exists: {destination}\nOverwrite? [y/n]: "):
            print("Edited configuration overwrite cancelled.")
            return None
    except (EOFError, KeyboardInterrupt):
        print("\nConfiguration editing cancelled.")
        return None
    return {**context, "changes": changes}


# ---------------------------------------------------------------------
# CONVERSION AND MIGRATION
# ---------------------------------------------------------------------

def prepare_router_conversion(source_values, destination_values, source_context, destination_context):
    """Compare fields and confirm the same conversion report before changing files."""
    if not isinstance(source_values, dict) or not isinstance(destination_values, dict):
        raise ValueError("Source and destination configuration values are unavailable")
    source, destination = source_context["source"].resolve(), destination_context["source"].resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Source and destination directories must be separate")
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
    return {**destination_context, "destination": destination_context["source"],
            "changes": updates,
            "conversion_source": (source_context["source"] / source_context["relative"],
                                  source_context["original_bytes"])}


# ---------------------------------------------------------------------
# ENCODING AND VERIFICATION
# ---------------------------------------------------------------------

def prepare_encode_paths(edited_dir, original_cfg, edited_archive_path, output_path, model_specs):
    """Validate and confirm the two encoding destinations before collecting credentials."""
    directory, original, edited_archive, output = (
        Path(value).expanduser() for value in (edited_dir, original_cfg, edited_archive_path, output_path))
    extension = model_specs["router_specs"]["codec"]["decoded_extension"]
    if not edited_archive.name.endswith(extension):
        raise ValueError(f"Edited archive path must end with {extension}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Edited configuration directory not found: {directory}")
    validate_directory(directory)
    if edited_archive.resolve() == output.resolve() or (edited_archive.exists() and output.exists() and edited_archive.samefile(output)):
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
            return None
    return {"directory": directory, "original": original, "edited_archive": edited_archive, "output": output}


def compare_configuration_files(directory, files, edit):
    """Compare the edited directory with the original and protect uneditable files."""
    if files is None:
        raise ValueError('Selected decoder does not declare editable configuration files')
    actual = {str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file()}
    if actual != set(files):
        raise ValueError('Edited files do not match the original configuration')
    configured = str(safe_relative(edit['configuration_file']))
    if configured not in files:
        raise ValueError('Configured file missing from original backup')
    changes = []
    configuration = None
    for name, original_data in files.items():
        edited_data = (directory / safe_relative(name)).read_bytes()
        if name == configured:
            configuration = edited_data
        elif original_data != edited_data:
            raise ValueError(f'Original mismatch in uneditable file: {name}')
        if original_data != edited_data:
            changes.append(name)
    return {
        'changes': changes,
        'original': files[configured].decode('utf-8'),
        'edited': configuration.decode('utf-8'),
        'data': configuration,
    }


def prepare_encode_payload(original_archive, original_context, comparison, credentials, signing, directory):
    """Construct encoding metadata and payload from validated configuration inputs."""
    data = comparison['data'] if original_context.get('configuration_payload') else original_archive
    return {
        **original_context,
        **credentials,
        'signing': signing,
        'edited_dir': str(directory),
        'changes': comparison['changes'],
        'data': data,
        'expected': data,
        'configuration_payload': bool(original_context.get('configuration_payload')),
    }


def verify_encoded_backup(actual, expected):
    """Require byte-identical round-trip recovery before saving."""
    if actual != expected:
        raise ValueError('Generated backup failed decryption verification')
    return True


# ---------------------------------------------------------------------
# FILE AND DIRECTORY SAVING
# ---------------------------------------------------------------------

def replace_router_directory(staged: Path, destination: Path) -> None:
    """Install a prepared directory, restoring the old one if installation fails."""
    if any(path.is_symlink() for path in (destination, *destination.parents)):
        raise ValueError(f"Unsafe destination symlink: {destination}")
    if not destination.exists():
        os.replace(staged, destination)
        return
    if not destination.is_dir():
        raise NotADirectoryError(f"Expected output directory: {destination}")
    backup_dir = Path(tempfile.mkdtemp(dir=destination.parent, prefix=f".{destination.name}.backup."))
    backup = backup_dir / "original"
    installed = False
    try:
        os.replace(destination, backup)
        try:
            os.replace(staged, destination)
            installed = True
        except BaseException:
            os.replace(backup, destination)
            raise
    finally:
        if installed or not backup.exists():
            shutil.rmtree(backup_dir)
        else:
            print(f"Original configuration retained at: {backup}")



def save_router_config(decoded_config, decoded_config_path, model_specs):
    """Confirm and atomically save validated decoded bytes with private permissions."""
    if not isinstance(decoded_config, bytes) or not decoded_config:
        raise ValueError("No decoded router configuration available to save")
    path = Path(decoded_config_path).expanduser()
    extension = model_specs["router_specs"]["codec"]["decoded_extension"]
    if not path.name.endswith(extension):
        raise ValueError(f"Decoded configuration path must end with {extension}")
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError(f"Unsafe decoded archive symlink: {path}")
    if path.exists():
        if not path.is_file():
            raise ValueError(f"Decoded archive destination is not a file: {path}")
        if not confirm(f"Decoded archive already exists: {path}\nOverwrite? [y/n]: "):
            print("Decoded archive overwrite cancelled.")
            return None
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as target:
            temp_path = Path(target.name)
            os.chmod(temp_path, 0o600)
            target.write(decoded_config)
        if temp_path.read_bytes() != decoded_config:
            raise ValueError("Decoded configuration failed write verification")
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    print(f"Saved decoded router configuration: {path}")
    return str(path)


def save_configuration_directory(context, edited):
    """Stage and verify edits, checking source snapshots before atomic replacement."""
    if not isinstance(edited, str):
        raise ValueError("Edited configuration text is unavailable")
    source, destination, relative = context["source"], context["destination"], context["relative"]
    validate_directory(source)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staging = Path(tempfile.mkdtemp(dir=destination.parent, prefix=f".{destination.name}."))
    prepared = staging / "replacement"
    try:
        shutil.copytree(source, prepared, symlinks=True)
        validate_directory(prepared)
        target = prepared / relative
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=target.parent, prefix=".config.", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(edited)
            os.chmod(temp_path, 0o600)
            os.replace(temp_path, target)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        saved = target.read_bytes().decode("utf-8")
        expected = context["editor"](context["original"], context["specs"], context["changes"], context["encrypt_handler"])
        if saved != expected:
            raise ValueError("Saved configuration differs outside the requested field replacements")
        before = context["viewer"](context["original"], context["specs"], context["decrypt_handler"])
        after = context["viewer"](saved, context["specs"], context["decrypt_handler"])
        configuration_format = context["specs"]["router_specs"]["edit"]["configuration_format"]
        if configuration_format == "xml" and after != {**before, **context["changes"]}:
            raise ValueError("Saved configuration field verification failed")
        conversion_source = context.get("conversion_source")
        if conversion_source is not None:
            path, snapshot = conversion_source
            if path.read_bytes() != snapshot:
                raise ValueError("Source configuration changed during conversion")
        if (source / relative).read_bytes() != context["original_bytes"]:
            raise ValueError("Original configuration changed during editing or conversion")
        validate_directory(prepared)
        replace_router_directory(prepared, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    label = "Converted configuration saved" if context.get("conversion_source") else "Saved edited router configuration"
    print(f"{label}: {destination}")
    return str(destination)


def save_encoded_outputs(paths, rebuilt, recovered, context):
    """Publish both encoded outputs with the existing staging, verification and rollback."""
    if not isinstance(rebuilt, bytes) or not rebuilt or recovered != context["expected"]:
        raise ValueError("Verified encoded output is unavailable")
    edited_archive, output = paths["edited_archive"], paths["output"]
    rebuilt_archive = context["expected"]
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
    return str(output)


# ---------------------------------------------------------------------
# REPORTING
# ---------------------------------------------------------------------

def report_encoded_backup(output, paths, context):
    """Report only the successfully published encoded outputs."""
    print("Modified files: " + (", ".join(context["changes"]) or "none; original compressed archive retained"))
    print(f"Saved edited router archive: {paths['edited_archive']}")
    print(f"Updated router backup: {output}; checksum and local round-trip verified.")
    return output
