# modules/portscan_utils.py
from __future__ import annotations

import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PortResult:
    """Port scan result for a single TCP port."""
    port: int
    open: bool
    service: str = ""
    note: str = ""


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def _tcp_connect_open(host: str, port: int, timeout: float) -> bool:
    """Return True if TCP connect succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


# ---------------------------------------------------------------------
# NETWORK OPERATIONS
# ---------------------------------------------------------------------


def get_arp_neighbors() -> List[str]:
    """Return a list of neighbor IPs from `ip neigh` (best-effort)."""
    rows = get_arp_neighbor_rows()
    ips: List[str] = []
    for r in rows:
        ip = str(r.get("IP", "")).strip()
        if ip:
            ips.append(ip)
    return list(dict.fromkeys(ips))


def get_arp_neighbor_rows() -> List[Dict[str, Any]]:
    """Return ARP neighbor rows from `ip neigh` for display/table output."""
    try:
        r = subprocess.run(["ip", "neigh"], capture_output=True, text=True, check=True)
    except Exception:
        return []
    out = (r.stdout or "").strip()
    if not out:
        return []
    rows: List[Dict[str, Any]] = []
    for line in out.splitlines():
        parts = line.split()
        if not parts:
            continue
        ip = parts[0].strip()
        if not (ip and "." in ip and ip[0].isdigit()):
            continue
        dev = ""
        lladdr = ""
        if "dev" in parts:
            i = parts.index("dev")
            if i + 1 < len(parts):
                dev = parts[i + 1].strip()
        if "lladdr" in parts:
            i = parts.index("lladdr")
            if i + 1 < len(parts):
                lladdr = parts[i + 1].strip()
        rows.append({"IP": ip, "MAC": lladdr or "?", "Interface": dev or "?"})
    return rows


def prompt_for_target(default: Optional[str] = None) -> Optional[str]:
    """Prompt user for a target IP/hostname."""
    suffix = f" [{default}]" if default else ""
    s = input(f"Enter target IP/hostname{suffix}: ").strip()
    return s or default


def scan_tcp_ports(
    host: str,
    ports: List[int],
    port_info: Dict[str, Dict[str, str]],
    timeout: float,
    workers: int,
) -> List[Dict[str, Any]]:
    """TCP connect scan for a list of ports; returns list of dicts for table display."""
    if not isinstance(port_info, dict):
        raise ValueError("port_scan.port_info must be a dictionary")
    for key, info in port_info.items():
        if not isinstance(key, str) or not key.isascii() or not key.isdigit() or not 1 <= int(key) <= 65535:
            raise ValueError(f"Invalid port_scan.port_info key: {key!r}; expected a numeric port string in 1-65535")
        if not isinstance(info, dict):
            raise ValueError(f"port_scan.port_info.{key} must be a dictionary")
        for field in ("service", "note"):
            if not isinstance(info.get(field), str):
                raise ValueError(f"port_scan.port_info.{key}.{field} must be a string")
    if not host or not ports:
        return []
    ports = sorted(set(int(p) for p in ports if isinstance(p, int) or str(p).isdigit()))
    results: List[PortResult] = []
    with ThreadPoolExecutor(max_workers=max(1, int(workers))) as ex:
        fut_map = {ex.submit(_tcp_connect_open, host, p, timeout): p for p in ports}
        for fut in as_completed(fut_map):
            p = fut_map[fut]
            is_open = False
            try:
                is_open = bool(fut.result())
            except Exception:
                is_open = False
            if is_open:
                info = port_info.get(str(p), {})
                results.append(
                    PortResult(
                        port=p,
                        open=True,
                        service=info.get("service", ""),
                        note=info.get("note", ""),
                    )
                )
    results.sort(key=lambda x: x.port)
    out: List[Dict[str, Any]] = []
    for r in results:
        out.append(
            {
                "Port": r.port,
                "Service": r.service,
                "Note": r.note,
            }
        )
    return out
