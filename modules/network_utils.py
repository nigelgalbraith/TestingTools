#!/usr/bin/env python3
"""
network_utils.py
"""


from __future__ import annotations

from typing import List, Dict, Any, Optional
import subprocess
import os


def _run_nmcli(args: List[str]) -> str:
    """Run nmcli and return stdout (best-effort)."""
    r = subprocess.run(
        ["nmcli", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout or ""


def get_interfaces(types: Optional[List[str]] = None) -> List[str]:
    """Return all interface names optionally filtered by type."""
    try:
        out = _run_nmcli(["-t", "-f", "DEVICE,TYPE", "device"])
        wanted = set(t.lower() for t in (types or []))
        interfaces: List[str] = []
        for line in out.strip().splitlines():
            parts = line.split(":")
            if len(parts) != 2:
                continue
            device, dev_type = parts[0].strip(), parts[1].strip().lower()
            if not device:
                continue
            if wanted and dev_type not in wanted:
                continue
            interfaces.append(device)
        return list(dict.fromkeys(interfaces))
    except Exception:
        return []


def get_connected_interfaces(types: Optional[List[str]] = None) -> List[str]:
    """Return only connected interface names optionally filtered by type."""
    try:
        out = _run_nmcli(["-t", "-f", "DEVICE,TYPE,STATE", "device"])
        wanted = set(t.lower() for t in (types or []))
        interfaces: List[str] = []
        for line in out.strip().splitlines():
            parts = line.split(":")
            if len(parts) != 3:
                continue
            device, dev_type, state = parts[0].strip(), parts[1].strip().lower(), parts[2].strip().lower()
            if not device:
                continue
            if wanted and dev_type not in wanted:
                continue
            if state != "connected":
                continue
            interfaces.append(device)
        return list(dict.fromkeys(interfaces))
    except Exception:
        return []

def get_interface_status() -> List[Dict[str, Any]]:
    """Return status rows for each non-loopback interface."""
    rows: List[Dict[str, Any]] = []
    base = "/sys/class/net"
    try:
        ifaces = sorted([n for n in os.listdir(base) if n and n != "lo"])
    except Exception:
        ifaces = []
    for iface in ifaces:
        operstate_path = os.path.join(base, iface, "operstate")
        carrier_path = os.path.join(base, iface, "carrier")
        state = "disconnected"
        try:
            operstate = ""
            carrier = "0"
            if os.path.exists(operstate_path):
                with open(operstate_path, "r", encoding="utf-8") as f:
                    operstate = (f.read() or "").strip().lower()
            if os.path.exists(carrier_path):
                with open(carrier_path, "r", encoding="utf-8") as f:
                    carrier = (f.read() or "").strip()
            if carrier == "1" and operstate in ("up", "unknown"):
                state = "connected"
        except Exception:
            state = "disconnected"
        rows.append({"device": iface, "state": state})
    if not rows:
        rows.append({"device": "No interfaces", "state": "disconnected"})
    return rows


def analyze_interface(interface: str) -> List[Dict[str, Any]]:
    """Return nmcli device show output as rows for print_dict_table."""
    if not interface:
        print("[ERROR] No interface provided.")
        return []
    try:
        r = subprocess.run(["nmcli", "device", "show", interface], capture_output=True, text=True, check=True)
        out = (r.stdout or "").strip()
        if not out:
            print(f"[WARN] No output for interface: {interface}")
            return []
        rows: List[Dict[str, Any]] = []
        for line in out.splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            key = k.strip()
            val = v.strip()
            if key:
                rows.append({"Key": key, "Value": val})
        return rows
    except Exception as e:
        print(f"[ERROR] Failed to analyze interface {interface}: {e}")
        return []

