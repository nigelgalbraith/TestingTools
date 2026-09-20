#!/usr/bin/env python3
"""
data_recovery_utils.py

Data recovery utilities for Linux live environments.
"""

from __future__ import annotations

import json
import os
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


def _run_interactive(command: List[str]) -> int | None:
    """Run an interactive command in the current terminal."""
    try:
        return subprocess.run(command, check=False).returncode
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _format_bytes(value: int) -> str:
    """Return bytes in human-readable format."""
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PiB"


def _get_physical_drive(device: str) -> str | None:
    """Return the physical parent drive for a block device."""
    if not device.startswith("/dev/"):
        return None
    result = _run_command(["lsblk", "-sno", "PATH,TYPE", device])
    if result is None or result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == "disk":
            return parts[0]
    return None


def _get_destination_drive(destination: Path) -> str | None:
    """Return the physical drive containing the recovery destination."""
    result = _run_command(["findmnt", "-n", "-o", "SOURCE", "-T", str(destination)])
    if result is None or result.returncode != 0:
        return None
    source = result.stdout.strip().split("[", 1)[0]
    if not source.startswith("/dev/"):
        return None
    return _get_physical_drive(source)


def _get_physical_drives() -> List[Dict[str, Any]]:
    """Return detected physical drives."""
    result = _run_command(["lsblk", "--json", "--bytes", "--nodeps", "--output", "NAME,PATH,TYPE,SIZE,MODEL,SERIAL,TRAN,ROTA"])
    if result is None or result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return []
    devices = data.get("blockdevices", [])
    if not isinstance(devices, list):
        return []
    return [device for device in devices if device.get("type") == "disk"]


def _get_recovery_destination(destination: str) -> Path | None:
    """Create and return the configured recovery directory."""
    destination_name = destination.strip()
    if not destination_name:
        return None
    path = (Path.cwd() / destination_name).resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    if not path.is_dir():
        return None
    return path


def _recovery_paths(device: str, destination: Path) -> tuple[Path, Path]:
    """Return image and map file paths for a source drive."""
    drive_name = Path(device).name
    return destination / f"{drive_name}.img", destination / f"{drive_name}.map"


def _same_source_destination(device: str, destination: Path) -> bool:
    """Return True when source and destination use the same physical drive."""
    source_drive = _get_physical_drive(device)
    destination_drive = _get_destination_drive(destination)
    if source_drive is None or destination_drive is None:
        return False
    return source_drive == destination_drive


# ---------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------


def get_recovery_status(destination: str) -> List[Dict[str, Any]]:
    """Return Data Recovery readiness."""
    destination_path = _get_recovery_destination(destination)
    ready = destination_path is not None and destination_path.is_dir()
    return [{"data_recovery": "Data recovery", "ready": ready}]

# ---------------------------------------------------------------------
# DRIVE LIST AND SELECTION
# ---------------------------------------------------------------------


def get_drive_list() -> List[Dict[str, Any]]:
    """Return detected physical drives."""
    rows: List[Dict[str, Any]] = []
    for device in _get_physical_drives():
        try:
            size = int(device.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        rotational = device.get("rota")
        interface = str(device.get("tran") or "")
        if interface == "nvme":
            drive_type = "NVMe"
        elif rotational == 1:
            drive_type = "HDD"
        elif rotational == 0:
            drive_type = "SSD"
        else:
            drive_type = "Unknown"
        rows.append({"Device": device.get("path") or device.get("name") or "", "Model": device.get("model") or "Unknown", "Size": _format_bytes(size), "Type": drive_type, "Interface": interface or "Unknown"})
    return rows


def select_drive(title: str, drives: List[Dict[str, Any]], destination: str) -> str | None:
    """Prompt for a source drive excluding the recovery destination drive."""
    destination_path = _get_recovery_destination(destination)
    if destination_path is None:
        print("Unable to create recovery destination.")
        return None
    destination_drive = _get_destination_drive(destination_path)
    if destination_drive is None:
        print("Unable to determine the physical drive containing the recovery destination.")
        return None
    available_drives = [drive for drive in drives if str(drive.get("Device") or "") != destination_drive]
    if not available_drives:
        print("No valid recovery source drives detected.")
        return None
    print(f"\nRecovery destination: {destination_path}")
    print(f"Destination drive excluded: {destination_drive}")
    print(f"\n{title}:")
    for index, drive in enumerate(available_drives, start=1):
        print(f"{index}) {drive.get('Device', '')} - {drive.get('Model', 'Unknown')} - {drive.get('Size', 'Unknown')} - {drive.get('Type', 'Unknown')}")
    try:
        choice = int(input(f"Enter your selection (1-{len(available_drives)}): ").strip())
    except ValueError:
        return None
    if not 1 <= choice <= len(available_drives):
        return None
    return str(available_drives[choice - 1].get("Device") or "") or None


# ---------------------------------------------------------------------
# PERMISSIONS
# ---------------------------------------------------------------------


def restore_recovery_permissions(destination: str) -> List[Dict[str, Any]]:
    """Restore recovery directory ownership to the user who invoked sudo."""
    destination_path = _get_recovery_destination(destination)
    if destination_path is None:
        return [{"Destination": destination, "Result": "Unable to access recovery destination", "Status": "FAIL"}]
    uid = os.environ.get("SUDO_UID")
    gid = os.environ.get("SUDO_GID")
    if uid is None or gid is None:
        return [{"Destination": str(destination_path), "Result": "Unable to determine sudo user", "Status": "FAIL"}]
    try:
        uid_value = int(uid)
        gid_value = int(gid)
        os.chown(destination_path, uid_value, gid_value)
        for item in destination_path.rglob("*"):
            os.chown(item, uid_value, gid_value)
    except (OSError, ValueError):
        return [{"Destination": str(destination_path), "Result": "Unable to restore recovery permissions", "Status": "FAIL"}]
    return [{"Destination": str(destination_path), "Result": "Recovery permissions restored", "Status": "PASS"}]


# ---------------------------------------------------------------------
# DDRESCUE
# ---------------------------------------------------------------------


def run_ddrescue_image(device: str, destination: str, retries: int, resume: bool) -> List[Dict[str, Any]]:
    """Create or resume a ddrescue image of one source drive."""
    destination_path = _get_recovery_destination(destination)
    if destination_path is None:
        return [{"Source": device, "Image": "", "Map": "", "Result": "Unable to create recovery destination", "Status": "FAIL"}]
    if _same_source_destination(device, destination_path):
        return [{"Source": device, "Image": "", "Map": "", "Result": "Source and recovery destination are on the same physical drive", "Status": "FAIL"}]
    image_path, map_path = _recovery_paths(device, destination_path)
    if resume and not map_path.exists():
        return [{"Source": device, "Image": str(image_path), "Map": str(map_path), "Result": "Map file does not exist", "Status": "FAIL"}]
    if not resume and image_path.exists():
        return [{"Source": device, "Image": str(image_path), "Map": str(map_path), "Result": "Image already exists", "Status": "FAIL"}]
    print(f"\nSource: {device}")
    print(f"Image:  {image_path}")
    print(f"Map:    {map_path}\n")
    first_pass = _run_interactive(["ddrescue", "-f", "-n", device, str(image_path), str(map_path)])
    if first_pass is None or first_pass != 0:
        return [{"Source": device, "Image": str(image_path), "Map": str(map_path), "Result": "Initial ddrescue pass failed", "Status": "FAIL"}]
    retry_pass = _run_interactive(["ddrescue", "-d", "-f", f"-r{retries}", device, str(image_path), str(map_path)])
    if retry_pass is None or retry_pass != 0:
        return [{"Source": device, "Image": str(image_path), "Map": str(map_path), "Result": "Recovery completed with read errors or retry failure", "Status": "WARNING"}]
    return [{"Source": device, "Image": str(image_path), "Map": str(map_path), "Result": "Recovery image completed", "Status": "PASS"}]


# ---------------------------------------------------------------------
# TESTDISK
# ---------------------------------------------------------------------


def run_testdisk(device: str, log_destination: str) -> List[Dict[str, Any]]:
    """Launch TestDisk interactively for one source drive."""
    log_path = (Path.cwd() / log_destination).resolve()
    try:
        log_path.mkdir(parents=True, exist_ok=True)
    except OSError:
        return [{"Device": device, "Result": "Unable to create TestDisk log directory", "Status": "FAIL"}]
    print("\nTestDisk is interactive.")
    print(f"Log directory: {log_path}")
    try:
        result = subprocess.run(["testdisk", "/log", device], cwd=log_path, check=False).returncode
    except (FileNotFoundError, PermissionError, OSError):
        return [{"Device": device, "Result": "Unable to launch TestDisk", "Status": "FAIL"}]
    if result != 0:
        return [{"Device": device, "Result": f"TestDisk exited with status {result}", "Status": "WARNING"}]
    return [{"Device": device, "Result": "TestDisk session completed", "Status": "PASS"}]


# ---------------------------------------------------------------------
# PHOTOREC
# ---------------------------------------------------------------------


def run_photorec(device: str, destination: str) -> List[Dict[str, Any]]:
    """Launch PhotoRec interactively for one source drive."""
    destination_path = _get_recovery_destination(destination)
    if destination_path is None:
        return [{"Device": device, "Destination": destination, "Result": "Unable to create recovery destination", "Status": "FAIL"}]
    if _same_source_destination(device, destination_path):
        return [{"Device": device, "Destination": str(destination_path), "Result": "Source and recovery destination are on the same physical drive", "Status": "FAIL"}]
    print(f"\nSource drive: {device}")
    print(f"Recovered files: {destination_path}")
    print("PhotoRec is interactive. Select the required partition and file types in its menu.\n")
    result = _run_interactive(["photorec", "/d", str(destination_path), device])
    if result is None:
        return [{"Device": device, "Destination": str(destination_path), "Result": "Unable to launch PhotoRec", "Status": "FAIL"}]
    if result != 0:
        return [{"Device": device, "Destination": str(destination_path), "Result": f"PhotoRec exited with status {result}", "Status": "WARNING"}]
    return [{"Device": device, "Destination": str(destination_path), "Result": "PhotoRec session completed", "Status": "PASS"}]