"""WiFi utilities - interface status, scanning, and network selection."""

import subprocess
import re
from typing import List, Dict, Any

from modules.system_utils import run_cmd

# ============================================================
# HELPERS
# ============================================================

def build_network_choices(
    networks: List[Dict[str, Any]],
    columns: List[Dict[str, Any]],
) -> List[str]:
    """Build readable menu choices for scanned networks using config columns."""
    choices: List[str] = []
    for n in networks or []:
        row: List[str] = []
        for col in columns or []:
            key = col.get("key")
            value = n.get(key)
            if value in (None, "", []):
                value = "<Hidden>" if key == "ssid" else "?"
            row.append(str(value))
        choices.append(" | ".join(row))
    return choices


def select_network_from_scan(
    networks: List[Dict[str, Any]],
    choice: str,
    columns: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Return the network dict matching the chosen display string."""
    if not networks or not choice:
        return {}
    choices = build_network_choices(networks, columns)
    try:
        idx = choices.index(choice)
    except ValueError:
        return {}
    return networks[idx] if 0 <= idx < len(networks) else {}


# ============================================================
# INTERFACE DISCOVERY
# ============================================================

def get_wireless_interfaces(timeout: int) -> List[str]:
    """Get list of available wireless interfaces."""
    print("\n[INFO] Detecting wireless interfaces...")
    interfaces: List[str] = []
    try:
        result = subprocess.run(
            ["iw", "dev"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "Interface" in line:
                    iface = line.split()[-1].strip()
                    if iface:
                        interfaces.append(iface)
    except Exception as e:
        print(f"[WARN] iw dev failed: {e}")
    if not interfaces:
        print("[INFO] Falling back to ip link detection...")
        try:
            result = subprocess.run(
                ["ip", "link", "show"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
            for line in result.stdout.split("\n"):
                if "wlan" in line or "wlx" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        iface = parts[1].strip()
                        if iface and iface not in interfaces:
                            interfaces.append(iface)
        except Exception as e:
            print(f"[WARN] ip link failed: {e}")
    print(f"[INFO] Interfaces found: {interfaces}")
    return interfaces


def check_wifi_status() -> List[Dict[str, Any]]:
    """Return status rows for each wireless adapter."""
    interfaces=get_wireless_interfaces(timeout=5)
    rows: List[Dict[str, Any]]=[]
    for iface in interfaces:
        try:
            result=subprocess.run(["iw","dev",iface,"link"],capture_output=True,text=True,timeout=3)
            connected="Connected to" in (result.stdout or "")
            rows.append({"device":iface,"state":"connected" if connected else "disconnected"})
        except Exception:
            rows.append({"device":iface,"state":"disconnected"})
    if not rows:
        rows.append({"device":"No WiFi adapters","state":"disconnected"})
    return rows


# ============================================================
# SCANNING
# ============================================================

def scan_networks(
    interface: str,
    timeout: int,
    columns: List[Dict[str, Any]],
    mode: str = "managed"
) -> List[Dict[str, Any]]:
    """Scan WiFi networks using JSON-defined extraction patterns."""
    if not interface:
        print("[ERROR] No interface provided for scan.")
        return []
    run_cmd(["ip", "link", "set", interface, "up"])
    print(f"\n[INFO] Scanning on {interface} (timeout={timeout}s)...")
    result = subprocess.run(
        ["iw", "dev", interface, "scan"],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        err = (result.stderr or "").strip()
        out = (result.stdout or "").strip()
        print(f"[ERROR] iw scan failed (rc={result.returncode})")
        if err:
            print(err)
        elif out:
            print(out)
        return []
    networks: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if line.startswith("BSS "):
            if current:
                networks.append(current)
                current = {}
        for col in columns or []:
            pattern = col.get("pattern")
            key = col.get("key")
            if not pattern or not key:
                continue
            match = re.search(pattern, line)
            if match:
                if match.lastindex:   
                    value = match.group(1)
                else:                 
                    value = match.group(0)
                try:
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass
                current[key] = value
    if current:
        networks.append(current)
    print(f"[INFO] Scan complete: {len(networks)} networks found.")
    return networks


def show_network_details(interface: str, network: Dict[str, Any], timeout: int = 8) -> bool:
    """Print raw iw scan block for the selected network (by BSSID)."""
    bssid = str((network or {}).get("bssid") or "").strip()
    if not interface or not bssid:
        print("[ERROR] Missing interface or BSSID.")
        return False
    try:
        result = subprocess.run(
            ["iw", "dev", interface, "scan"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
    except Exception as e:
        print(f"[ERROR] iw scan failed: {e}")
        return False
    lines = result.stdout.splitlines()
    in_block = False
    printed = False
    print("\n=== NETWORK DETAILS ===")
    for line in lines:
        s = line.rstrip()
        if s.strip().startswith("BSS "):
            if printed and in_block:
                break
            in_block = bssid.lower() in s.lower()
        if in_block:
            print(s)
            printed = True
    print()
    return printed
