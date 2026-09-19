#!/usr/bin/env python3
"""
email_utils.py
"""

from __future__ import annotations

from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import List, Dict, Any
import mailbox
import shutil
import subprocess
import tempfile

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def _get_pst_output_dir(pst_file: str, dest_dir: str) -> Path:
    """Return the output directory for a PST file."""
    output_dir = Path(dest_dir) / Path(pst_file).stem
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _extract_eml_temp(pst_file: str) -> Path | None:
    """Extract PST contents to temporary EML files."""
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="pst_email_"))
        r = subprocess.run(
            ["readpst", "-e", "-o", str(temp_dir), pst_file],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
        return temp_dir
    except Exception:
        return None


def _get_email_body(msg) -> str:
    """Return the readable text body from an email message."""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and part.get_content_disposition() != "attachment":
                    return part.get_content()
            return ""
        return msg.get_content()
    except Exception:
        return ""


def count_mbox_messages(mbox_file: str) -> int:
    """Return the number of messages in an mbox file."""
    try:
        box = mailbox.mbox(mbox_file)
        return len(box)
    except Exception:
        return 0

# ---------------------------------------------------------------------
# PST FILE PROCESSING
# ---------------------------------------------------------------------


def get_pst_summary(pst_file: str) -> List[Dict[str, Any]]:
    """Return summary rows for a PST file."""
    temp_dir = _extract_eml_temp(pst_file)
    if not temp_dir:
        return []
    try:
        email_files = list(temp_dir.rglob("*.eml"))
        contact_files = list(temp_dir.rglob("*.vcf"))
        calendar_files = list(temp_dir.rglob("*.ics"))
        attachments = 0
        for email_file in email_files:
            try:
                with open(email_file, "rb") as f:
                    msg = BytesParser(policy=policy.default).parse(f)
                attachments += sum(1 for part in msg.iter_attachments())
            except Exception:
                continue
        return [
            {"Item": "Emails", "Count": len(email_files)},
            {"Item": "Contacts", "Count": len(contact_files)},
            {"Item": "Calendar items", "Count": len(calendar_files)},
            {"Item": "Attachments", "Count": attachments},
        ]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def get_pst_email_rows(pst_file: str) -> List[Dict[str, Any]]:
    """Return email summary rows from a PST file."""
    temp_dir = _extract_eml_temp(pst_file)
    if not temp_dir:
        return []
    try:
        rows: List[Dict[str, Any]] = []
        for email_file in sorted(temp_dir.rglob("*.eml")):
            try:
                with open(email_file, "rb") as f:
                    msg = BytesParser(policy=policy.default).parse(f)
                rows.append({
                    "From": str(msg.get("From", "")),
                    "Date": str(msg.get("Date", "")),
                    "Subject": str(msg.get("Subject", "")),
                    "Attachments": sum(1 for part in msg.iter_attachments()),
                })
            except Exception:
                continue
        return rows
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def get_pst_email_files(pst_file: str, work_dir: str) -> List[str]:
    """Extract a PST and return contained EML files."""
    try:
        output_path = Path(work_dir)
        if output_path.exists():
            shutil.rmtree(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(
            ["readpst", "-e", "-o", str(output_path), pst_file],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            return []
        return sorted(str(path) for path in output_path.rglob("*.eml"))
    except Exception:
        return []


def get_email_details(email_file: str) -> Dict[str, Any]:
    """Return details for an email file."""
    try:
        with open(email_file, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)
        return {
            "From": str(msg.get("From", "")),
            "To": str(msg.get("To", "")),
            "Date": str(msg.get("Date", "")),
            "Subject": str(msg.get("Subject", "")),
            "Body": _get_email_body(msg),
        }
    except Exception:
        return {}


def convert_pst_to_mbox(pst_file: str, dest_dir: str) -> bool:
    """Convert a PST file to mbox format using readpst."""
    try:
        pst_path = Path(pst_file)
        if not pst_path.is_file():
            print(f"[ERROR] PST file not found: {pst_file}")
            return False
        output_dir = _get_pst_output_dir(pst_file, dest_dir) / "mbox"
        output_dir.mkdir(parents=True, exist_ok=True)
        before = set(output_dir.glob("*"))
        r = subprocess.run(
            ["readpst", "-o", str(output_dir), str(pst_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            print(f"[ERROR] Failed to convert: {pst_file}")
            if r.stderr:
                print(r.stderr.strip())
            return False
        after = set(output_dir.glob("*"))
        created = after - before
        total_messages = 0
        for mbox_file in created:
            if not mbox_file.is_file():
                continue
            count = count_mbox_messages(str(mbox_file))
            if count:
                total_messages += count
                print(f"[INFO] {mbox_file.name}: {count} emails")
        print(f"[INFO] Total emails extracted: {total_messages}")
        print(f"[INFO] Output directory: {output_dir}")
        return True
    except Exception as e:
        print(f"[ERROR] PST conversion failed: {e}")
        return False


def convert_pst_to_eml(pst_file: str, dest_dir: str) -> bool:
    """Convert a PST file to separate EML files using readpst."""
    try:
        output_dir = _get_pst_output_dir(pst_file, dest_dir) / "eml"
        output_dir.mkdir(parents=True, exist_ok=True)
        before = set(output_dir.rglob("*.eml"))
        r = subprocess.run(
            ["readpst", "-e", "-o", str(output_dir), pst_file],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            print(f"[ERROR] Failed to convert: {pst_file}")
            if r.stderr:
                print(r.stderr.strip())
            return False
        after = set(output_dir.rglob("*.eml"))
        count = len(after - before)
        print(f"[INFO] Emails extracted: {count}")
        print(f"[INFO] Output directory: {output_dir}")
        return True
    except Exception as e:
        print(f"[ERROR] EML conversion failed: {e}")
        return False


def extract_pst_contacts(pst_file: str, dest_dir: str) -> bool:
    """Extract PST contacts as VCard files."""
    try:
        output_dir = _get_pst_output_dir(pst_file, dest_dir) / "contacts"
        output_dir.mkdir(parents=True, exist_ok=True)
        before = set(output_dir.rglob("*.vcf"))
        r = subprocess.run(
            ["readpst", "-e", "-t", "c", "-cv", "-o", str(output_dir), pst_file],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            print(f"[ERROR] Failed to extract contacts: {pst_file}")
            if r.stderr:
                print(r.stderr.strip())
            return False
        after = set(output_dir.rglob("*.vcf"))
        count = len(after - before)
        if count == 0:
            print("[INFO] No contacts found.")
        else:
            print(f"[INFO] Contacts extracted: {count}")
        print(f"[INFO] Output directory: {output_dir}")
        return True
    except Exception as e:
        print(f"[ERROR] Contact extraction failed: {e}")
        return False


def extract_pst_attachments(pst_file: str, dest_dir: str) -> bool:
    """Extract attachments from all emails contained in a PST file."""
    temp_dir = _extract_eml_temp(pst_file)
    if not temp_dir:
        print(f"[ERROR] Failed to read PST: {pst_file}")
        return False
    try:
        output_dir = _get_pst_output_dir(pst_file, dest_dir) / "attachments"
        output_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for email_file in temp_dir.rglob("*.eml"):
            try:
                with open(email_file, "rb") as f:
                    msg = BytesParser(policy=policy.default).parse(f)
                for part in msg.iter_attachments():
                    filename = part.get_filename() or f"attachment_{count + 1}"
                    if part.get_content_type() == "message/rfc822" and not Path(filename).suffix:
                        filename += ".eml"
                    target = output_dir / filename
                    index = 1
                    while target.exists():
                        target = output_dir / f"{target.stem}_{index}{target.suffix}"
                        index += 1
                    payload = part.get_payload(decode=True)
                    if payload is not None:
                        target.write_bytes(payload)
                    elif part.get_content_type() == "message/rfc822":
                        embedded = part.get_payload()
                        if isinstance(embedded, list) and embedded:
                            target.write_bytes(embedded[0].as_bytes(policy=policy.default))
                        else:
                            continue
                    else:
                        continue
                    count += 1
            except Exception:
                continue
        if count == 0:
            print("[INFO] No attachments found.")
        else:
            print(f"[INFO] Attachments extracted: {count}")
        print(f"[INFO] Output directory: {output_dir}")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)