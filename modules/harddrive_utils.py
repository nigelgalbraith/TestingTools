#!/usr/bin/env python3
"""
harddrive_utils.py

Hard drive, partition, filesystem, SMART, and storage diagnostic utilities
for Linux live environments.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
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


def _format_bytes(value: int) -> str:
    """Return bytes in human-readable format."""
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PiB"


def _get_physical_drives() -> List[Dict[str, Any]]:
    """Return physical drive information from lsblk."""
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


def _get_drive_tree(device: str) -> List[Dict[str, Any]]:
    """Return one selected drive and all child block devices."""
    result = _run_command(["lsblk", "--json", "--bytes", "--output", "NAME,PATH,TYPE,SIZE,FSTYPE,MOUNTPOINTS,MODEL,LABEL", device])
    if result is None or result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return []
    rows: List[Dict[str, Any]] = []
    stack = list(data.get("blockdevices", []))
    while stack:
        current = stack.pop(0)
        children = current.get("children", [])
        rows.append(current)
        if isinstance(children, list):
            stack[0:0] = children
    return rows


def _get_smart_json(device: str) -> Dict[str, Any]:
    """Return SMART information for one drive in JSON format."""
    result = _run_command(["smartctl", "-a", "-j", device], timeout=30)
    if result is None or not result.stdout:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def _get_mountpoints(block_device: Dict[str, Any]) -> List[str]:
    """Return valid mountpoints from an lsblk record."""
    mountpoints = block_device.get("mountpoints") or []
    if isinstance(mountpoints, str):
        return [mountpoints] if mountpoints else []
    if not isinstance(mountpoints, list):
        return []
    return [str(item) for item in mountpoints if item]


# ---------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------


def get_drive_diagnostic_status() -> List[Dict[str, Any]]:
    """Return Hard Drive Tools readiness."""
    ready = shutil.which("smartctl") is not None and shutil.which("lsblk") is not None
    return [{"harddrive": "Hard drive tools", "ready": ready}]


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


def select_drive(title: str, drives: List[Dict[str, Any]]) -> str | None:
    """Prompt for a physical drive and return its device path."""
    if not drives:
        print("No physical drives detected.")
        return None
    print(f"\n{title}:")
    for index, drive in enumerate(drives, start=1):
        print(f"{index}) {drive.get('Device', '')} - {drive.get('Model', 'Unknown')} - {drive.get('Size', 'Unknown')} - {drive.get('Type', 'Unknown')}")
    try:
        choice = int(input(f"Enter your selection (1-{len(drives)}): ").strip())
    except ValueError:
        return None
    if not 1 <= choice <= len(drives):
        return None
    return str(drives[choice - 1].get("Device") or "") or None


# ---------------------------------------------------------------------
# DISK AND PARTITION OVERVIEW
# ---------------------------------------------------------------------


def get_disk_overview(device: str) -> List[Dict[str, Any]]:
    """Return the selected drive and its partitions."""
    rows: List[Dict[str, Any]] = []
    for block_device in _get_drive_tree(device):
        try:
            size = int(block_device.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        mount = ", ".join(_get_mountpoints(block_device))
        rows.append({"Device": block_device.get("path") or block_device.get("name") or "", "Type": block_device.get("type") or "", "Size": _format_bytes(size), "Filesystem": block_device.get("fstype") or "", "Mount": mount})
    return rows


# ---------------------------------------------------------------------
# FILESYSTEM USAGE
# ---------------------------------------------------------------------


def get_filesystem_usage(device: str, warning_threshold: int | float) -> List[Dict[str, Any]]:
    """Return mounted filesystem usage for the selected drive."""
    rows: List[Dict[str, Any]] = []
    for block_device in _get_drive_tree(device):
        filesystem = str(block_device.get("fstype") or "")
        if not filesystem:
            continue
        for mountpoint in _get_mountpoints(block_device):
            try:
                usage = shutil.disk_usage(mountpoint)
            except OSError:
                continue
            percentage = (usage.used / usage.total) * 100 if usage.total else 0
            status = "WARNING" if percentage >= float(warning_threshold) else "PASS"
            rows.append({"Filesystem": block_device.get("path") or block_device.get("name") or "", "Size": _format_bytes(usage.total), "Used": _format_bytes(usage.used), "Available": _format_bytes(usage.free), "Usage": f"{percentage:.1f}% ({mountpoint})", "Status": status})
    if not rows:
        rows.append({"Filesystem": device, "Size": "", "Used": "", "Available": "", "Usage": "No mounted filesystems", "Status": "INFO"})
    return rows


# ---------------------------------------------------------------------
# WINDOWS INSTALLATION DETECTION
# ---------------------------------------------------------------------


def _is_windows_installation(path: Path) -> bool:
    """Return True when a filesystem appears to contain Windows."""
    return (path / "Windows" / "System32").is_dir()


def detect_windows_installations(device: str) -> List[Dict[str, Any]]:
    """Detect Windows installations on the selected drive."""
    rows: List[Dict[str, Any]] = []
    for block_device in _get_drive_tree(device):
        if block_device.get("type") != "part":
            continue
        filesystem = str(block_device.get("fstype") or "").lower()
        if filesystem not in ("ntfs", "ntfs3"):
            continue
        device_path = str(block_device.get("path") or "")
        if not device_path:
            continue
        mountpoints = _get_mountpoints(block_device)
        existing_mount = mountpoints[0] if mountpoints else None
        detected = False
        display_mount = existing_mount or ""
        if existing_mount:
            detected = _is_windows_installation(Path(existing_mount))
        else:
            temporary_mount = tempfile.mkdtemp(prefix="testingtools_harddrive_")
            mounted = False
            result = _run_command(["mount", "-o", "ro", device_path, temporary_mount], timeout=20)
            if result is not None and result.returncode == 0:
                mounted = True
                detected = _is_windows_installation(Path(temporary_mount))
            if mounted:
                _run_command(["umount", temporary_mount], timeout=20)
            try:
                os.rmdir(temporary_mount)
            except OSError:
                pass
            if detected:
                display_mount = "Read-only scan"
        if detected:
            rows.append({"Device": device_path, "Filesystem": filesystem.upper(), "Windows": "Detected", "Mount": display_mount})
    if not rows:
        rows.append({"Device": device, "Filesystem": "", "Windows": "No Windows installation detected", "Mount": ""})
    return rows


# ---------------------------------------------------------------------
# ENCRYPTION / BITLOCKER
# ---------------------------------------------------------------------


def get_encryption_status(device: str) -> List[Dict[str, Any]]:
    """Return encryption status for the selected drive and its partitions."""
    rows: List[Dict[str, Any]] = []
    for block_device in _get_drive_tree(device):
        filesystem = str(block_device.get("fstype") or "").lower()
        if filesystem in ("bitlocker", "bitlk"):
            encryption = "BitLocker"
            status = "DETECTED"
        elif filesystem in ("crypto_luks", "luks"):
            encryption = "LUKS"
            status = "DETECTED"
        elif filesystem:
            encryption = "None detected"
            status = "CLEAR"
        else:
            encryption = "Unknown"
            status = "UNKNOWN"
        rows.append({"Device": block_device.get("path") or block_device.get("name") or "", "Filesystem": filesystem or "Unknown", "Encryption": encryption, "Status": status})
    return rows


# ---------------------------------------------------------------------
# DRIVE INFORMATION
# ---------------------------------------------------------------------


def get_drive_information(device: str) -> List[Dict[str, Any]]:
    """Return detailed identification information for one drive."""
    data = _get_smart_json(device)
    model = data.get("model_name") or data.get("model_family") or "Unknown"
    serial = data.get("serial_number") or "Unknown"
    firmware = data.get("firmware_version") or "Unknown"
    capacity_data = data.get("user_capacity", {})
    capacity = capacity_data.get("bytes", 0) if isinstance(capacity_data, dict) else 0
    interface = data.get("interface_speed", {})
    if isinstance(interface, dict):
        current = interface.get("current", {})
        interface_name = current.get("string", "Unknown") if isinstance(current, dict) else "Unknown"
    else:
        interface_name = "Unknown"
    return [{"Device": device, "Model": model, "Serial": serial, "Firmware": firmware, "Capacity": _format_bytes(int(capacity)) if capacity else "Unknown", "Interface": interface_name}]


# ---------------------------------------------------------------------
# SMART HEALTH
# ---------------------------------------------------------------------


def get_smart_health(device: str) -> List[Dict[str, Any]]:
    """Return SMART overall health for one drive."""
    data = _get_smart_json(device)
    smart_status = data.get("smart_status", {})
    passed = smart_status.get("passed") if isinstance(smart_status, dict) else None
    if passed is True:
        health = "SMART health passed"
        status = "PASS"
    elif passed is False:
        health = "SMART health failed"
        status = "FAIL"
    else:
        health = "SMART health unavailable"
        status = "UNKNOWN"
    return [{"Device": device, "Health": health, "Status": status}]


# ---------------------------------------------------------------------
# SMART ATTRIBUTES
# ---------------------------------------------------------------------


def get_smart_attributes(device: str) -> List[Dict[str, Any]]:
    """Return SMART attributes for one ATA/SATA drive."""
    rows: List[Dict[str, Any]] = []
    data = _get_smart_json(device)
    table = data.get("ata_smart_attributes", {})
    attributes = table.get("table", []) if isinstance(table, dict) else []
    for attribute in attributes:
        name = attribute.get("name") or "Unknown"
        value = attribute.get("value", "")
        raw_data = attribute.get("raw", {})
        raw_value = raw_data.get("string", "") if isinstance(raw_data, dict) else raw_data
        when_failed = attribute.get("when_failed", "")
        rows.append({"Device": device, "Attribute": name, "Value": value, "Raw": raw_value, "Status": "FAIL" if when_failed else "PASS"})
    if not rows:
        rows.append({"Device": device, "Attribute": "SMART attributes", "Value": "", "Raw": "No ATA SMART attribute table available", "Status": "INFO"})
    return rows


# ---------------------------------------------------------------------
# TEMPERATURE AND WEAR
# ---------------------------------------------------------------------


def get_temperature_wear(device: str, temperature_warning: int | float, wear_warning: int | float) -> List[Dict[str, Any]]:
    """Return temperature and wear information for one drive."""
    data = _get_smart_json(device)
    temperature_data = data.get("temperature", {})
    temperature = temperature_data.get("current") if isinstance(temperature_data, dict) else None
    nvme = data.get("nvme_smart_health_information_log", {})
    percentage_used = nvme.get("percentage_used") if isinstance(nvme, dict) else None
    wear = "Unknown"
    status = "PASS"
    if temperature is not None and float(temperature) >= float(temperature_warning):
        status = "WARNING"
    if percentage_used is not None:
        wear = f"{percentage_used}% used"
        if float(percentage_used) >= float(wear_warning):
            status = "WARNING"
    return [{"Device": device, "Temperature": f"{temperature}°C" if temperature is not None else "Unknown", "Wear": wear, "Status": status}]


# ---------------------------------------------------------------------
# SMART TEST HISTORY
# ---------------------------------------------------------------------


def get_smart_test_history(device: str) -> List[Dict[str, Any]]:
    """Return SMART self-test history for one drive."""
    rows: List[Dict[str, Any]] = []
    data = _get_smart_json(device)
    log = data.get("ata_smart_self_test_log", {})
    standard = log.get("standard", {}) if isinstance(log, dict) else {}
    table = standard.get("table", []) if isinstance(standard, dict) else []
    if not table:
        return [{"Device": device, "Test": "No history", "Result": "No SMART self-tests recorded", "Lifetime Hours": ""}]
    for entry in table:
        test_data = entry.get("type", {})
        status_data = entry.get("status", {})
        test_name = test_data.get("string", "Unknown") if isinstance(test_data, dict) else "Unknown"
        result = status_data.get("string", "Unknown") if isinstance(status_data, dict) else "Unknown"
        rows.append({"Device": device, "Test": test_name, "Result": result, "Lifetime Hours": entry.get("lifetime_hours", "")})
    return rows


# ---------------------------------------------------------------------
# SMART TESTS
# ---------------------------------------------------------------------


def run_short_smart_test(device: str) -> List[Dict[str, Any]]:
    """Start a short SMART self-test on one drive."""
    result = _run_command(["smartctl", "-t", "short", device])
    if result is None:
        message = "Unable to start SMART test"
        status = "FAIL"
    elif result.returncode in (0, 2):
        message = "Short SMART test started"
        status = "STARTED"
    else:
        message = (result.stderr or result.stdout or "SMART test failed").strip()
        status = "FAIL"
    return [{"Device": device, "Result": message, "Status": status}]


def run_long_smart_test(device: str) -> List[Dict[str, Any]]:
    """Start a long SMART self-test on one drive."""
    result = _run_command(["smartctl", "-t", "long", device])
    if result is None:
        message = "Unable to start SMART test"
        status = "FAIL"
    elif result.returncode in (0, 2):
        message = "Long SMART test started"
        status = "STARTED"
    else:
        message = (result.stderr or result.stdout or "SMART test failed").strip()
        status = "FAIL"
    return [{"Device": device, "Result": message, "Status": status}]


# ---------------------------------------------------------------------
# READ BENCHMARK
# ---------------------------------------------------------------------


def run_read_benchmark(device: str, size_mb: int) -> List[Dict[str, Any]]:
    """Run a non-destructive sequential read benchmark on one drive."""
    start = time.monotonic()
    result = _run_command(["dd", f"if={device}", "of=/dev/null", "bs=1M", f"count={size_mb}", "iflag=direct", "status=none"], timeout=120)
    elapsed = time.monotonic() - start
    if result is None or result.returncode != 0 or elapsed <= 0:
        speed = "Unable to benchmark"
        status = "FAIL"
    else:
        speed = f"{size_mb / elapsed:.1f} MB/s"
        status = "PASS"
    return [{"Device": device, "Read Speed": speed, "Status": status}]


# ---------------------------------------------------------------------
# FULL HARD DRIVE DIAGNOSTIC
# ---------------------------------------------------------------------


def get_full_drive_diagnostic(device: str, temperature_warning: int | float, wear_warning: int | float, disk_usage_warning: int | float) -> List[Dict[str, Any]]:
    """Return a diagnostic summary for one selected drive."""
    rows: List[Dict[str, Any]] = []
    health = get_smart_health(device)[0]
    wear = get_temperature_wear(device, temperature_warning, wear_warning)[0]
    filesystems = get_filesystem_usage(device, disk_usage_warning)
    windows = detect_windows_installations(device)
    encryption = get_encryption_status(device)
    filesystem_warning = any(row.get("Status") == "WARNING" for row in filesystems)
    windows_found = any(row.get("Windows") == "Detected" for row in windows)
    encryption_found = any(row.get("Status") == "DETECTED" for row in encryption)
    rows.append({"Device": device, "Check": "SMART Health", "Result": health.get("Health", "Unknown"), "Status": health.get("Status", "UNKNOWN")})
    rows.append({"Device": device, "Check": "Temperature", "Result": wear.get("Temperature", "Unknown"), "Status": wear.get("Status", "UNKNOWN")})
    rows.append({"Device": device, "Check": "Wear", "Result": wear.get("Wear", "Unknown"), "Status": wear.get("Status", "UNKNOWN")})
    rows.append({"Device": device, "Check": "Filesystem Usage", "Result": "High usage detected" if filesystem_warning else "Usage normal or not mounted", "Status": "WARNING" if filesystem_warning else "PASS"})
    rows.append({"Device": device, "Check": "Windows Installation", "Result": "Detected" if windows_found else "Not detected", "Status": "INFO"})
    rows.append({"Device": device, "Check": "Encryption", "Result": "Encryption detected" if encryption_found else "No encryption detected", "Status": "INFO"})
    return rows