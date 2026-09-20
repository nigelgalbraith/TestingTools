#!/usr/bin/env python3
"""
file_utils.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def get_directory_status(directory: str) -> List[Dict[str, Any]]:
    """Return directory status rows for ToolLoader."""
    try:
        path = Path(directory)
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


def get_files_by_extension(directory: str, extension: str) -> List[str]:
    """Return files in a directory matching the supplied extension."""
    try:
        path = Path(directory)
        if not path.is_dir():
            return []
        return sorted(
            str(item)
            for item in path.iterdir()
            if item.is_file() and item.suffix.lower() == extension.lower()
        )
    except Exception:
        return []
