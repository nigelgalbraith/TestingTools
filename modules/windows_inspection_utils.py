#!/usr/bin/env python3
"""
windows_inspection_utils.py

Offline Windows inspection utilities for Linux live environments.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List


# ---------------------------------------------------------------------
# COMMAND HELPERS
# ---------------------------------------------------------------------


def _run_command(command: List[str], timeout: int = 20) -> subprocess.CompletedProcess | None:
    """Run a command and return the completed process."""
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)
    except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired, OSError):
        return None


def _get_block_devices() -> List[Dict[str, Any]]:
    """Return block devices and filesystem information."""
    result = _run_command(["lsblk", "--json", "--output", "PATH,TYPE,FSTYPE,MOUNTPOINTS,SIZE,LABEL"])
    if result is None or result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return []
    devices = data.get("blockdevices", [])
    return devices if isinstance(devices, list) else []


def _flatten_devices(devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten nested lsblk device output."""
    rows: List[Dict[str, Any]] = []
    for device in devices:
        rows.append(device)
        children = device.get("children")
        if isinstance(children, list):
            rows.extend(_flatten_devices(children))
    return rows


def _mount_device(device: str, mount_root: str) -> Path | None:
    """Mount a Windows partition read-only and return its mount path."""
    mount_path = Path(mount_root) / Path(device).name
    try:
        mount_path.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    result = _run_command(["mount", "-o", "ro", device, str(mount_path)])
    if result is None or result.returncode != 0:
        existing = _run_command(["findmnt", "-n", "-o", "TARGET", device])
        if existing is None or existing.returncode != 0:
            return None
        existing_path = existing.stdout.strip()
        return Path(existing_path) if existing_path else None
    return mount_path


def _is_windows_installation(path: Path) -> bool:
    """Return True when a mounted path looks like Windows."""
    return (path / "Windows" / "System32").is_dir() and (path / "Windows" / "System32" / "config").is_dir()


# ---------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------


def get_windows_status(mount_root: str) -> List[Dict[str, Any]]:
    """Return Offline Windows Inspection readiness."""
    mount_path = Path(mount_root)
    ready = mount_path.exists() and mount_path.is_dir()
    return [{"windows_inspection": "Offline Windows inspection", "ready": ready}]

def check_mount_root(mount_root: str) -> List[Dict[str, Any]]:
    """Check whether the configured mount root exists and is usable."""
    path = Path(mount_root)
    if not path.exists():
        return [{
            "Mount root": str(path),
            "Result": "Configured mount root does not exist",
            "Status": "FAIL",
            "ready": False,
        }]
    if not path.is_dir():
        return [{
            "Mount root": str(path),
            "Result": "Configured mount root is not a directory",
            "Status": "FAIL",
            "ready": False,
        }]
    return [{
        "Mount root": str(path),
        "Result": "Mount root is available",
        "Status": "PASS",
        "ready": True,
    }]

# ---------------------------------------------------------------------
# WINDOWS DETECTION
# ---------------------------------------------------------------------


def detect_windows_installations(mount_root: str) -> List[Dict[str, Any]]:
    """Detect Windows installations on NTFS partitions."""
    rows: List[Dict[str, Any]] = []
    devices = _flatten_devices(_get_block_devices())
    for device in devices:
        if str(device.get("fstype") or "").lower() not in ("ntfs", "ntfs3"):
            continue
        device_path = str(device.get("path") or "")
        if not device_path:
            continue
        mountpoints = device.get("mountpoints") or []
        mounted = next((item for item in mountpoints if item), None)
        mount_path = Path(mounted) if mounted else _mount_device(device_path, mount_root)
        if mount_path is None:
            continue
        if _is_windows_installation(mount_path):
            rows.append({"Device": device_path, "Mount": str(mount_path), "Windows": "Detected"})
    return rows


def select_windows_installation(installations: List[Dict[str, Any]]) -> str | None:
    """Prompt for a detected Windows installation."""
    if not installations:
        print("No Windows installations detected.")
        return None
    print("\nSelect a Windows installation:")
    for index, installation in enumerate(installations, start=1):
        print(f"{index}) {installation.get('Device', '')} - {installation.get('Mount', '')}")
    try:
        choice = int(input(f"Enter your selection (1-{len(installations)}): ").strip())
    except ValueError:
        return None
    if not 1 <= choice <= len(installations):
        return None
    return str(installations[choice - 1].get("Mount") or "") or None


# ---------------------------------------------------------------------
# WINDOWS INFORMATION
# ---------------------------------------------------------------------


def get_windows_info(windows_root: str) -> List[Dict[str, Any]]:
    """Return basic information about an offline Windows installation."""
    root = Path(windows_root)
    system32 = root / "Windows" / "System32"
    rows = [
        {"Field": "Windows root", "Value": str(root)},
        {"Field": "System32", "Value": str(system32)},
        {"Field": "Registry path", "Value": str(system32 / "config")},
        {"Field": "Users path", "Value": str(root / "Users")},
    ]
    return rows


# ---------------------------------------------------------------------
# WINDOWS USERS
# ---------------------------------------------------------------------


def get_windows_users(windows_root: str) -> List[Dict[str, Any]]:
    """Return user profile directories from an offline Windows installation."""
    users_path = Path(windows_root) / "Users"
    if not users_path.is_dir():
        return []
    ignored = {"All Users", "Default", "Default User", "Public", "desktop.ini"}
    rows: List[Dict[str, Any]] = []
    for item in sorted(users_path.iterdir()):
        if not item.is_dir() or item.name in ignored:
            continue
        rows.append({"User": item.name, "Profile": str(item)})
    return rows


# ---------------------------------------------------------------------
# REGISTRY HIVES
# ---------------------------------------------------------------------


def inspect_registry_hives(windows_root: str) -> List[Dict[str, Any]]:
    """List standard offline Windows registry hives."""
    config_path = Path(windows_root) / "Windows" / "System32" / "config"
    hives = ["SYSTEM", "SOFTWARE", "SAM", "SECURITY", "DEFAULT"]
    rows: List[Dict[str, Any]] = []
    for hive in hives:
        path = config_path / hive
        rows.append({"Hive": hive, "Path": str(path), "Status": "FOUND" if path.is_file() else "MISSING"})
    return rows


# ---------------------------------------------------------------------
# STARTUP ENTRIES
# ---------------------------------------------------------------------


def inspect_startup_entries(windows_root: str) -> List[Dict[str, Any]]:
    """List startup-folder entries from an offline Windows installation."""
    root = Path(windows_root)
    rows: List[Dict[str, Any]] = []
    common = root / "ProgramData" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    if common.is_dir():
        for item in sorted(common.iterdir()):
            rows.append({"Location": "All Users", "Entry": item.name})
    users_path = root / "Users"
    if users_path.is_dir():
        for user in users_path.iterdir():
            startup = user / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            if not startup.is_dir():
                continue
            for item in sorted(startup.iterdir()):
                rows.append({"Location": user.name, "Entry": item.name})
    return rows


# ---------------------------------------------------------------------
# SERVICES
# ---------------------------------------------------------------------


def inspect_services(windows_root: str) -> List[Dict[str, Any]]:
    """Return service inspection availability for an offline Windows installation."""
    system_hive = Path(windows_root) / "Windows" / "System32" / "config" / "SYSTEM"
    if not system_hive.is_file():
        return [{"Service": "SYSTEM registry hive", "Status": "MISSING"}]
    return [{"Service": "SYSTEM registry hive", "Status": "AVAILABLE"}]


# ---------------------------------------------------------------------
# INSTALLED SOFTWARE
# ---------------------------------------------------------------------


def get_installed_software(windows_root: str) -> List[Dict[str, Any]]:
    """Return installed-software registry availability."""
    software_hive = Path(windows_root) / "Windows" / "System32" / "config" / "SOFTWARE"
    if not software_hive.is_file():
        return [{"Name": "SOFTWARE registry hive", "Version": "MISSING"}]
    return [{"Name": "SOFTWARE registry hive", "Version": "AVAILABLE"}]