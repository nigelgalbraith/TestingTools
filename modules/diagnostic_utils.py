#!/usr/bin/env python3
"""
diagnostic_utils.py

Read-only system diagnostics for Linux live environments.
"""

from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, List


# ---------------------------------------------------------------------
# COMMAND HELPERS
# ---------------------------------------------------------------------


def _run_command(command: List[str], timeout: int = 15) -> subprocess.CompletedProcess | None:
    """Run a command and return the result."""
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired, OSError):
        return None


def _read_text(path: str | Path) -> str:
    """Read text from a file and return an empty string on failure."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except (OSError, PermissionError):
        return ""


def _format_bytes(value: int) -> str:
    """Return bytes in a human-readable format."""
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PiB"


# ---------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------


def get_diagnostic_status() -> List[Dict[str, Any]]:
    """Return Diagnostic utility readiness."""
    ready = os.name == "posix" and Path("/proc").exists() and Path("/sys").exists()
    return [
        {
            "diagnostic": "System diagnostics",
            "ready": ready,
        }
    ]


# ---------------------------------------------------------------------
# SYSTEM SUMMARY
# ---------------------------------------------------------------------


def get_system_summary() -> List[Dict[str, Any]]:
    """Return basic system information."""
    os_name = platform.system()
    os_release = Path("/etc/os-release")
    if os_release.is_file():
        for line in _read_text(os_release).splitlines():
            if line.startswith("PRETTY_NAME="):
                os_name = line.split("=", 1)[1].strip().strip('"')
                break
    boot_mode = "UEFI" if Path("/sys/firmware/efi").exists() else "Legacy BIOS"
    return [
        {
            "Key": "Hostname",
            "Value": socket.gethostname(),
        },
        {
            "Key": "Operating System",
            "Value": os_name,
        },
        {
            "Key": "Kernel",
            "Value": platform.release(),
        },
        {
            "Key": "Architecture",
            "Value": platform.machine(),
        },
        {
            "Key": "Boot Mode",
            "Value": boot_mode,
        },
        {
            "Key": "User",
            "Value": "root" if os.geteuid() == 0 else "standard user",
        },
    ]


# ---------------------------------------------------------------------
# CPU
# ---------------------------------------------------------------------


def get_cpu_info() -> List[Dict[str, Any]]:
    """Return CPU information."""
    result = _run_command(["lscpu"])
    if result is None or result.returncode != 0:
        return [
            {
                "Key": "CPU",
                "Value": platform.processor() or "Unknown",
            }
        ]
    values: Dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    fields = [
        ("Model name", "Model"),
        ("Architecture", "Architecture"),
        ("CPU(s)", "Logical CPUs"),
        ("Core(s) per socket", "Cores per Socket"),
        ("Socket(s)", "Sockets"),
        ("Thread(s) per core", "Threads per Core"),
        ("Virtualization", "Virtualization"),
    ]
    return [
        {
            "Key": display_name,
            "Value": values[source_name],
        }
        for source_name, display_name in fields
        if source_name in values
    ]


# ---------------------------------------------------------------------
# MEMORY
# ---------------------------------------------------------------------


def get_memory_status(warning_threshold: int | float) -> List[Dict[str, Any]]:
    """Return physical memory usage."""
    values: Dict[str, int] = {}
    for line in _read_text("/proc/meminfo").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parts = value.strip().split()
        if not parts:
            continue
        try:
            values[key] = int(parts[0]) * 1024
        except ValueError:
            continue
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", 0)
    if total <= 0:
        return [
            {
                "Metric": "Memory",
                "Value": "Unable to determine",
                "Status": "UNKNOWN",
            }
        ]
    used = total - available
    percentage = (used / total) * 100
    status = "WARNING" if percentage >= float(warning_threshold) else "PASS"
    return [
        {
            "Metric": "Total RAM",
            "Value": _format_bytes(total),
            "Status": "PASS",
        },
        {
            "Metric": "Used RAM",
            "Value": f"{_format_bytes(used)} ({percentage:.1f}%)",
            "Status": status,
        },
        {
            "Metric": "Available RAM",
            "Value": _format_bytes(available),
            "Status": "PASS",
        },
    ]


# ---------------------------------------------------------------------
# TEMPERATURES
# ---------------------------------------------------------------------


def get_temperature_status(warning_threshold: int | float) -> List[Dict[str, Any]]:
    """Return temperatures from Linux thermal zones."""
    rows: List[Dict[str, Any]] = []
    thermal_path = Path("/sys/class/thermal")
    if not thermal_path.is_dir():
        return [
            {
                "Sensor": "System",
                "Temperature": "No sensors detected",
                "Status": "UNKNOWN",
            }
        ]
    for zone in sorted(thermal_path.glob("thermal_zone*")):
        raw_temperature = _read_text(zone / "temp")
        if not raw_temperature:
            continue
        try:
            temperature = float(raw_temperature)
        except ValueError:
            continue
        if temperature > 1000:
            temperature /= 1000
        sensor = _read_text(zone / "type") or zone.name
        status = "WARNING" if temperature >= float(warning_threshold) else "PASS"
        rows.append(
            {
                "Sensor": sensor,
                "Temperature": f"{temperature:.1f}°C",
                "Status": status,
            }
        )
    if not rows:
        rows.append(
            {
                "Sensor": "System",
                "Temperature": "No sensors detected",
                "Status": "UNKNOWN",
            }
        )
    return rows


# ---------------------------------------------------------------------
# BATTERY
# ---------------------------------------------------------------------


def get_battery_health() -> List[Dict[str, Any]]:
    """Return basic battery information."""
    power_path = Path("/sys/class/power_supply")
    if not power_path.is_dir():
        return [
            {
                "Key": "Battery",
                "Value": "No battery detected",
            }
        ]
    batteries = [
        item
        for item in power_path.iterdir()
        if _read_text(item / "type").lower() == "battery"
    ]
    if not batteries:
        return [
            {
                "Key": "Battery",
                "Value": "No battery detected",
            }
        ]
    rows: List[Dict[str, Any]] = []
    for battery in batteries:
        model = _read_text(battery / "model_name") or "Unknown"
        manufacturer = _read_text(battery / "manufacturer")
        charge = _read_text(battery / "capacity")
        status = _read_text(battery / "status")
        rows.append(
            {
                "Key": f"{battery.name} Model",
                "Value": f"{manufacturer} {model}".strip(),
            }
        )
        if charge:
            rows.append(
                {
                    "Key": f"{battery.name} Charge",
                    "Value": f"{charge}%",
                }
            )
        if status:
            rows.append(
                {
                    "Key": f"{battery.name} Status",
                    "Value": status,
                }
            )
    return rows


# ---------------------------------------------------------------------
# HARDWARE
# ---------------------------------------------------------------------


def get_hardware_devices() -> List[Dict[str, Any]]:
    """Return detected PCI and USB devices."""
    rows: List[Dict[str, Any]] = []
    if shutil.which("lspci"):
        result = _run_command(["lspci"])
        if result is not None and result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    rows.append(
                        {
                            "Type": "PCI",
                            "Device": line.strip(),
                        }
                    )
    if shutil.which("lsusb"):
        result = _run_command(["lsusb"])
        if result is not None and result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    rows.append(
                        {
                            "Type": "USB",
                            "Device": line.strip(),
                        }
                    )
    if not rows:
        rows.append(
            {
                "Type": "Hardware",
                "Device": "No hardware information available",
            }
        )
    return rows


# ---------------------------------------------------------------------
# SYSTEM ERRORS
# ---------------------------------------------------------------------


def get_system_errors() -> List[Dict[str, Any]]:
    """Return important kernel errors from the live environment."""
    result = _run_command(
        [
            "dmesg",
            "--level=err,crit,alert,emerg",
        ]
    )
    if result is None or result.returncode != 0:
        return [
            {
                "Source": "Kernel",
                "Message": "Unable to read kernel messages",
                "Status": "UNKNOWN",
            }
        ]
    messages = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]
    if not messages:
        return [
            {
                "Source": "Kernel",
                "Message": "No critical kernel errors detected",
                "Status": "PASS",
            }
        ]
    return [
        {
            "Source": "Kernel",
            "Message": message,
            "Status": "ERROR",
        }
        for message in messages[-50:]
    ]


# ---------------------------------------------------------------------
# FULL REPORT
# ---------------------------------------------------------------------


def get_full_diagnostic_report(
    temperature_warning: int | float,
    memory_usage_warning: int | float,
) -> List[Dict[str, Any]]:
    """Return a concise overall system diagnostic report."""
    rows: List[Dict[str, Any]] = []
    memory = get_memory_status(memory_usage_warning)
    temperatures = get_temperature_status(temperature_warning)
    errors = get_system_errors()
    memory_warning = any(row.get("Status") == "WARNING" for row in memory)
    temperature_warning_found = any(
        row.get("Status") == "WARNING"
        for row in temperatures
    )
    errors_found = any(row.get("Status") == "ERROR" for row in errors)
    rows.append(
        {
            "Check": "System",
            "Result": f"{platform.machine()} / {platform.release()}",
            "Status": "PASS",
        }
    )
    rows.append(
        {
            "Check": "Memory",
            "Result": "High usage detected" if memory_warning else "Usage normal",
            "Status": "WARNING" if memory_warning else "PASS",
        }
    )
    rows.append(
        {
            "Check": "Temperature",
            "Result": (
                "High temperature detected"
                if temperature_warning_found
                else "Temperatures normal"
            ),
            "Status": "WARNING" if temperature_warning_found else "PASS",
        }
    )
    rows.append(
        {
            "Check": "Kernel Errors",
            "Result": "Errors detected" if errors_found else "No critical errors",
            "Status": "WARNING" if errors_found else "PASS",
        }
    )
    return rows