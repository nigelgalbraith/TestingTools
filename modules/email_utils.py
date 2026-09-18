#!/usr/bin/env python3
"""
email_utils.py
"""

from __future__ import annotations

import mailbox
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def count_mbox_messages(mbox_file: str) -> int:
    """Return the number of messages in an mbox file."""
    try:
        box = mailbox.mbox(mbox_file)
        return len(box)
    except Exception:
        return 0

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def convert_pst_to_mbox(pst_file: str, dest_dir: str) -> bool:
    """Convert a PST file to mbox format using readpst."""
    try:
        pst_path = Path(pst_file)
        dest_path = Path(dest_dir)
        if not pst_path.is_file():
            print(f"[ERROR] PST file not found: {pst_file}")
            return False
        dest_path.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(
            ["readpst", "-o", str(dest_path), str(pst_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            print(f"[ERROR] Failed to convert: {pst_file}")
            if r.stderr:
                print(r.stderr.strip())
            return False
        mbox_files = list(dest_path.glob("*.mbox"))
        total_messages = 0
        for mbox_file in mbox_files:
            count = count_mbox_messages(str(mbox_file))
            total_messages += count
            print(f"[INFO] {mbox_file.name}: {count} emails")
        print(f"[INFO] Total emails extracted: {total_messages}")
        return True
    except Exception as e:
        print(f"[ERROR] PST conversion failed: {e}")
        return False