#!/usr/bin/env python3
"""
file_utils.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List


def expand_path(path):
    """Expand ~ in filesystem paths."""
    return os.path.expanduser(path)


def get_directory_status(directory: str) -> List[Dict[str, Any]]:
    """Return directory status rows for ToolLoader."""
    try:
        path = Path(expand_path(directory))
        has_files = path.is_dir() and any(item.is_file() for item in path.iterdir())
        return [{
            "location": directory,
            "state": "data_present" if has_files else "no_data",
        }]
    except Exception:
        return [{
            "location": directory,
            "state": "no_data",
        }]


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