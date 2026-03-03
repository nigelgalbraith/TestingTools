# modules/portscan_utils.py
from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import socket
import subprocess


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


def _tcp_connect_open(host: str, port: int, timeout: float) -> bool:
    """Return True if TCP connect succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _service_lookup(port: int) -> str:
    """Return a simple service guess for common ports."""
    common = {
        21: "ftp",
        22: "ssh",
        23: "telnet",
        25: "smtp",
        53: "dns",
        80: "http",
        110: "pop3",
        139: "netbios",
        143: "imap",
        443: "https",
        445: "smb",
        3389: "rdp",
        5985: "winrm",
        5986: "winrm-ssl",
        3306: "mysql",
        5432: "postgres",
        6379: "redis",
        8080: "http-alt",
    }
    return common.get(port, "")


def _risk_note(port: int) -> str:
    """Return a blunt, practical note for a few high-signal ports."""
    notes = {
        23: "Telnet is plaintext. Avoid.",
        445: "SMB exposure. Watch lateral movement.",
        3389: "RDP exposed. Bruteforce target.",
        5985: "WinRM exposed. Admin surface.",
        5986: "WinRM SSL exposed. Admin surface.",
        6379: "Redis exposed. Often misconfigured.",
    }
    return notes.get(port, "")


# ---------------------------------------------------------------------
# MAIN OPS
# ---------------------------------------------------------------------

def scan_tcp_ports(
    host: str,
    ports: List[int],
    timeout: float = 0.5,
    workers: int = 200,
) -> List[Dict[str, Any]]:
    """TCP connect scan for a list of ports; returns list of dicts for table display."""
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
                results.append(
                    PortResult(
                        port=p,
                        open=True,
                        service=_service_lookup(p),
                        note=_risk_note(p),
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
