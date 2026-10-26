#!/usr/bin/env python3
"""
json_utils.py

Helpers for loading JSON config and validating config/job structures.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple, Union


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def load_json(config_path: Union[str, Path, list[Union[str, Path]]]):
    """Load one JSON path or an ordered list of paths without modifying the input."""
    paths = config_path if isinstance(config_path, list) else [config_path]
    results = []
    for path in paths:
        path = os.path.expanduser(path)
        try:
            with open(path) as f:
                results.append(json.load(f))
        except json.JSONDecodeError as exc:
            raise json.JSONDecodeError(f"{path}: {exc.msg}", exc.doc, exc.pos) from exc
        except UnicodeDecodeError as exc:
            raise UnicodeDecodeError(exc.encoding, exc.object, exc.start, exc.end,
                                     f"{path}: {exc.reason}") from exc
    return results if isinstance(config_path, list) else results[0]


def resolve_value(
    data: dict,
    primary_key: str,
    secondary_key: str,
    default_key: str = "default",
    check_file: bool = True,
) -> str | bool:
    """Resolve a nested dictionary value with fallback to `default_key`."""
    value = None
    if primary_key in data and secondary_key in data[primary_key]:
        value = data[primary_key][secondary_key]
    elif default_key in data and secondary_key in data[default_key]:
        value = data[default_key][secondary_key]
    if value is None:
        return False
    if check_file and isinstance(value, str) and not os.path.isfile(value):
        return False
    return value


# ---------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------


def validate_required_fields(
    jobs: Dict[str, Dict[str, Any]],
    required_fields: Dict[str, Union[type, Tuple[type, ...]]],
) -> Dict[str, bool]:
    """Check that each job dict contains required fields of the expected type(s)."""
    results: Dict[str, bool] = {field: True for field in required_fields}
    for job_name, meta in jobs.items():
        if not isinstance(meta, dict):
            for field in required_fields:
                results[field] = False
            continue
        for field, expected_type in required_fields.items():
            types = expected_type if isinstance(expected_type, tuple) else (expected_type,)
            if field not in meta or not isinstance(meta[field], types):
                results[field] = False
    return results


def validate_secondary_subkey(
    jobs_block: Dict[str, Dict[str, Any]],
    subkey: str,
    rules: Dict[str, Any],
) -> Dict[str, bool]:
    """Validate required fields for dict items stored under a list-valued subkey for each job."""
    allow_empty = bool(rules.get("allow_empty", False))
    required = rules.get("required_job_fields", {}) or {}
    results: Dict[str, bool] = {fname: True for fname in required}
    for job_name, meta in jobs_block.items():
        if not isinstance(meta, dict):
            for fname in required:
                results[fname] = False
            continue
        items = meta.get(subkey, [])
        if not isinstance(items, list):
            for fname in required:
                results[fname] = False
            continue
        if not items and not allow_empty:
            for fname in required:
                results[fname] = False
            continue
        for itm in items:
            if not isinstance(itm, dict):
                for fname in required:
                    results[fname] = False
                continue
            for field, expected_type in required.items():
                types_tuple = expected_type if isinstance(expected_type, tuple) else (expected_type,)
                if field not in itm or not isinstance(itm[field], types_tuple):
                    results[field] = False
    return results


def validate_json_schema(data: dict | list[dict], schema_path: Union[str, Path],
                         label: str = "Configuration", report_success: bool = True) -> dict | list[dict]:
    """Validate an external schema and return the original data unchanged.

    Schema paths use load_json's normal relative-path convention.
    """
    from jsonschema import exceptions, validators

    try:
        path = Path(schema_path).expanduser()
        try:
            schema = load_json(path)
            if not isinstance(schema, (dict, bool)):
                raise ValueError("schema must be an object or boolean")
            validator_class = validators.validator_for(schema)
            validator_class.check_schema(schema)
        except exceptions.SchemaError as exc:
            raise ValueError(f"invalid schema {schema_path}: {exc.message}") from None
        except (OSError, ValueError) as exc:
            raise ValueError(f"invalid schema {schema_path}: {exc}") from None
        validator = validator_class(schema)
        configs = data if isinstance(data, list) else [data]
        for index, item in enumerate(configs):
            errors = list(validator.iter_errors(item))
            if errors:
                messages = []
                for error in errors:
                    property_path = (f"$[{index}]" if isinstance(data, list) else "$") + "".join(
                        f"[{part}]" if isinstance(part, int) else f".{part}"
                        for part in error.absolute_path
                    )
                    messages.append(f"{property_path}: {error.message}")
                raise ValueError("; ".join(dict.fromkeys(messages)))
    except (OSError, ValueError, TypeError) as exc:
        message = f"{label}: {exc}"
        print(f"[FAILED] {message}")
        error = ValueError(message)
        # The pipeline records this exception without printing the same error again.
        error.reported = True
        raise error from None
    if report_success:
        print(f"[OK] {label} schema validated successfully.")
    return data
