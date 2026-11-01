#!/usr/bin/env python3
"""
file_utils.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List


# ---------------------------------------------------------------------
# FILE OPERATIONS
# ---------------------------------------------------------------------

def expand_path(path):
    """Expand ~ in filesystem paths."""
    return os.path.expanduser(path)


def get_directory_status(
    directory: str | Dict[str, Any],
    path_key: str | None = None,
) -> List[Dict[str, Any]]:
    """Return directory or file status rows for ToolLoader."""
    rows = []
    if isinstance(directory, dict):
        locations = [
            (name, entry.get(path_key))
            for name, entry in directory.items()
            if isinstance(entry, dict) and path_key
        ]
    else:
        locations = [(directory, directory)]
    for name, location in locations:
        try:
            if not location:
                raise ValueError("Missing path")
            path = Path(expand_path(location))

            if path_key:
                has_files = path.is_file()
            else:
                has_files = path.is_dir() and any(
                    item.is_file() for item in path.iterdir()
                )

            rows.append({
                "location": str(name),
                "state": "data_present" if has_files else "no_data",
            })
        except Exception:
            rows.append({
                "location": str(name),
                "state": "no_data",
            })
    return rows


def get_files_by_extension(directory: str, extension: str | list[str]) -> List[str]:
    """Return files matching one or more extensions."""
    try:
        path = Path(expand_path(directory))
        if not path.is_dir():
            return []
        extensions = [extension] if isinstance(extension, str) else extension
        extensions = {ext.lower() for ext in extensions}
        return sorted(str(item) for item in path.iterdir() if item.is_file() and item.suffix.lower() in extensions)
    except Exception:
        return []