#!/usr/bin/env python3
"""
file_integrity_utils.py

File and directory integrity utilities.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List


# ---------------------------------------------------------------------
# HASH HELPERS
# ---------------------------------------------------------------------


def _hash_file(path: Path, algorithm: str) -> str | None:
    """Return the hash of one file."""
    try:
        digest = hashlib.new(algorithm)
        with path.open("rb") as file_handle:
            while True:
                block = file_handle.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
        return digest.hexdigest()
    except (OSError, ValueError):
        return None


def _directory_files(directory: Path) -> List[Path]:
    """Return all files below a directory."""
    try:
        return sorted(path for path in directory.rglob("*") if path.is_file())
    except OSError:
        return []


def _resolve_target(target_dir: str) -> Path:
    """Return the configured target directory."""
    return Path(target_dir).expanduser().resolve()


def _resolve_manifest_dir(manifest_dir: str) -> Path:
    """Return the configured manifest directory."""
    path = Path(manifest_dir).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def _restore_owner(path: Path) -> None:
    """Restore ownership to the user who invoked sudo."""
    uid = os.environ.get("SUDO_UID")
    gid = os.environ.get("SUDO_GID")
    if uid is None or gid is None:
        return
    try:
        os.chown(path, int(uid), int(gid))
    except (OSError, ValueError):
        return


# ---------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------


def get_integrity_status(algorithm: str, target_dir: str, manifest_dir: str) -> List[Dict[str, Any]]:
    """Return File Integrity readiness."""
    try:
        hashlib.new(algorithm)
        algorithm_ready = True
    except ValueError:
        algorithm_ready = False
    target_path = _resolve_target(target_dir)
    target_ready = target_path.exists() and target_path.is_dir()
    manifest_path = _resolve_manifest_dir(manifest_dir)
    try:
        manifest_path.mkdir(parents=True, exist_ok=True)
        manifest_ready = manifest_path.is_dir()
    except OSError:
        manifest_ready = False
    ready = algorithm_ready and target_ready and manifest_ready
    return [{"file_integrity": "File integrity", "ready": ready}]


# ---------------------------------------------------------------------
# FILE SELECTION
# ---------------------------------------------------------------------


def select_file(target_dir: str, title: str) -> str | None:
    """Select a file from the configured target directory."""
    root = _resolve_target(target_dir)
    files = _directory_files(root)
    if not files:
        print(f"No files found in: {root}")
        return None
    print(f"\n{title}:")
    for index, path in enumerate(files, start=1):
        print(f"{index}) {path.relative_to(root)}")
    try:
        choice = int(input(f"Enter your selection (1-{len(files)}): ").strip())
    except ValueError:
        return None
    if not 1 <= choice <= len(files):
        return None
    return str(files[choice - 1])


def prompt_expected_hash(algorithm: str) -> str | None:
    """Prompt for an expected file hash."""
    value = input(f"Enter expected {algorithm.upper()} hash: ").strip().lower()
    return value or None


def prompt_manifest_path(manifest_dir: str) -> str | None:
    """Prompt for a checksum manifest."""
    root = _resolve_manifest_dir(manifest_dir)
    if not root.is_dir():
        print(f"Manifest directory does not exist: {root}")
        return None
    manifests = sorted(root.glob("*.json"))
    if not manifests:
        print(f"No manifest files found in: {root}")
        return None
    print("\nSelect a checksum manifest:")
    for index, manifest in enumerate(manifests, start=1):
        print(f"{index}) {manifest.name}")
    try:
        choice = int(input(f"Enter your selection (1-{len(manifests)}): ").strip())
    except ValueError:
        return None
    if not 1 <= choice <= len(manifests):
        return None
    return str(manifests[choice - 1])


# ---------------------------------------------------------------------
# FILE HASH
# ---------------------------------------------------------------------


def hash_file(file_path: str, algorithm: str) -> List[Dict[str, Any]]:
    """Hash one file."""
    path = Path(file_path)
    digest = _hash_file(path, algorithm)
    if digest is None:
        return [{"File": str(path), "Algorithm": algorithm, "Hash": "ERROR"}]
    return [{"File": str(path), "Algorithm": algorithm, "Hash": digest}]


def verify_file_hash(file_path: str, expected_hash: str, algorithm: str) -> List[Dict[str, Any]]:
    """Verify one file against an expected hash."""
    path = Path(file_path)
    actual = _hash_file(path, algorithm)
    if actual is None:
        return [{"File": str(path), "Expected": expected_hash, "Actual": "ERROR", "Status": "FAIL"}]
    status = "PASS" if actual.lower() == expected_hash.lower() else "FAIL"
    return [{"File": str(path), "Expected": expected_hash.lower(), "Actual": actual.lower(), "Status": status}]


# ---------------------------------------------------------------------
# DIRECTORY HASH
# ---------------------------------------------------------------------


def hash_directory(target_dir: str, algorithm: str) -> List[Dict[str, Any]]:
    """Hash every file below the configured target directory."""
    root = _resolve_target(target_dir)
    rows: List[Dict[str, Any]] = []
    for path in _directory_files(root):
        digest = _hash_file(path, algorithm)
        rows.append({"File": str(path.relative_to(root)), "Hash": digest or "ERROR"})
    return rows


# ---------------------------------------------------------------------
# FILE COMPARISON
# ---------------------------------------------------------------------


def compare_files(first_file: str, second_file: str, algorithm: str) -> List[Dict[str, Any]]:
    """Compare two files by hash."""
    first = Path(first_file)
    second = Path(second_file)
    first_hash = _hash_file(first, algorithm)
    second_hash = _hash_file(second, algorithm)
    if first_hash is None or second_hash is None:
        status = "ERROR"
    elif first_hash == second_hash:
        status = "MATCH"
    else:
        status = "DIFFERENT"
    return [{"File 1": str(first), "File 2": str(second), "Status": status}]


# ---------------------------------------------------------------------
# DUPLICATE FILES
# ---------------------------------------------------------------------


def find_duplicate_files(target_dir: str, algorithm: str) -> List[Dict[str, Any]]:
    """Find duplicate files below the configured target directory."""
    root = _resolve_target(target_dir)
    hashes: Dict[str, List[str]] = {}
    for path in _directory_files(root):
        digest = _hash_file(path, algorithm)
        if digest is None:
            continue
        hashes.setdefault(digest, []).append(str(path.relative_to(root)))
    rows: List[Dict[str, Any]] = []
    for digest, files in sorted(hashes.items()):
        if len(files) < 2:
            continue
        rows.append({"Hash": digest, "Count": len(files), "Files": " | ".join(files)})
    if not rows:
        return [{"Hash": "-", "Count": 0, "Files": "No duplicate files found"}]
    return rows


# ---------------------------------------------------------------------
# MANIFEST CREATION
# ---------------------------------------------------------------------


def create_manifest(target_dir: str, manifest_dir: str, algorithm: str) -> List[Dict[str, Any]]:
    """Create a JSON checksum manifest for the configured target directory."""
    root = _resolve_target(target_dir)
    output_root = _resolve_manifest_dir(manifest_dir)
    try:
        output_root.mkdir(parents=True, exist_ok=True)
    except OSError:
        return [{"Directory": str(root), "Manifest": str(output_root), "Files": 0, "Status": "FAIL"}]
    files: Dict[str, str] = {}
    for path in _directory_files(root):
        digest = _hash_file(path, algorithm)
        if digest is not None:
            files[str(path.relative_to(root))] = digest
    manifest = {
        "algorithm": algorithm,
        "directory": str(root),
        "files": files,
    }
    safe_name = root.name or "root"
    manifest_path = output_root / f"{safe_name}.json"
    try:
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except OSError:
        return [{"Directory": str(root), "Manifest": str(manifest_path), "Files": len(files), "Status": "FAIL"}]
    _restore_owner(output_root)
    _restore_owner(manifest_path)
    return [{"Directory": str(root), "Manifest": str(manifest_path), "Files": len(files), "Status": "PASS"}]


def restore_integrity_permissions(manifest_dir: str) -> List[Dict[str, Any]]:
    """Restore manifest ownership to the user who invoked sudo."""
    path = _resolve_manifest_dir(manifest_dir)
    uid = os.environ.get("SUDO_UID")
    gid = os.environ.get("SUDO_GID")
    if uid is None or gid is None:
        return [{"Destination": str(path), "Result": "Unable to determine sudo user", "Status": "FAIL"}]
    try:
        os.chown(path, int(uid), int(gid))
        for item in path.rglob("*"):
            os.chown(item, int(uid), int(gid))
    except (OSError, ValueError):
        return [{"Destination": str(path), "Result": "Unable to restore manifest permissions", "Status": "FAIL"}]
    return [{"Destination": str(path), "Result": "Manifest permissions restored", "Status": "PASS"}]


# ---------------------------------------------------------------------
# MANIFEST VERIFICATION
# ---------------------------------------------------------------------


def verify_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Verify files against a saved checksum manifest."""
    path = Path(manifest_path)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [{"File": str(path), "Status": "INVALID_MANIFEST"}]
    algorithm = str(manifest.get("algorithm") or "")
    root_value = manifest.get("directory")
    files = manifest.get("files")
    if not algorithm or not isinstance(root_value, str) or not isinstance(files, dict):
        return [{"File": str(path), "Status": "INVALID_MANIFEST"}]
    root = Path(root_value)
    rows: List[Dict[str, Any]] = []
    for relative, expected in sorted(files.items()):
        file_path = root / relative
        if not file_path.is_file():
            rows.append({"File": relative, "Status": "MISSING"})
            continue
        actual = _hash_file(file_path, algorithm)
        if actual is None:
            status = "ERROR"
        elif actual == expected:
            status = "PASS"
        else:
            status = "CHANGED"
        rows.append({"File": relative, "Status": status})
    current_files = {str(item.relative_to(root)) for item in _directory_files(root)} if root.is_dir() else set()
    manifest_files = set(files.keys())
    for relative in sorted(current_files - manifest_files):
        rows.append({"File": relative, "Status": "NEW"})
    return rows