#!/usr/bin/env python3
"""
email_utils.py
"""

from __future__ import annotations

import mailbox
import shutil
import subprocess
import tempfile
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any, Dict, List


EMAIL_COLUMN_WIDTHS = {
    "From": 50,
    "Date": 31,
    "Subject": 60,
    "Attachments": 11,
}


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def _natural_email_sort_key(path: str | Path):
    """Return a filename-stem sort key with numeric stems ordered numerically."""
    stem = Path(path).stem
    try:
        return (0, int(stem))
    except ValueError:
        return (1, stem)


def _parse_email_file(email_file: str | Path):
    """Return the parsed email message, or None if parsing fails."""
    try:
        with open(email_file, "rb") as f:
            return BytesParser(policy=policy.default).parse(f)
    except Exception:
        return None


def _run_readpst(args: list[str]) -> subprocess.CompletedProcess:
    """Run readpst with the given arguments."""
    return subprocess.run(
        ["readpst", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _get_pst_output_dir(pst_file: str, dest_dir: str) -> Path:
    """Return the output directory for a PST file."""
    output_dir = Path(dest_dir) / Path(pst_file).stem
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _extract_eml_temp(pst_file: str) -> Path | None:
    """Extract PST contents to temporary EML files."""
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="pst_email_"))
        r = _run_readpst(["-e", "-o", str(temp_dir), pst_file])
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


def clear_pst_files(ctx: dict) -> bool:
    """Remove temporary PST discovery data from context."""
    ctx.pop("pst_files", None)
    return True


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
                msg = _parse_email_file(email_file)
                if msg is None:
                    continue
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


def get_pst_email_files(pst_file: str, work_dir: str) -> List[str]:
    """Extract a PST and return contained EML files."""
    try:
        output_path = Path(work_dir)
        if output_path.exists():
            shutil.rmtree(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        r = _run_readpst(["-e", "-o", str(output_path), pst_file])
        if r.returncode != 0:
            return []
        return sorted((str(path) for path in output_path.rglob("*.eml")), key=_natural_email_sort_key)
    except Exception:
        return []


def get_email_details(email_file: str) -> Dict[str, Any]:
    """Return details for an email file."""
    try:
        msg = _parse_email_file(email_file)
        if msg is None:
            return {}
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
        r = _run_readpst(["-o", str(output_dir), str(pst_path)])
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
        r = _run_readpst(["-e", "-o", str(output_dir), pst_file])
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


def browse_pst_emails(pst_file: str, page_size: int = 25) -> bool:
    """Browse PST email summaries using a paginated built-in table."""
    temp_dir = _extract_eml_temp(pst_file)
    if not temp_dir:
        return False
    try:
        email_files = sorted(temp_dir.rglob("*.eml"), key=_natural_email_sort_key)
        if not email_files:
            return False
        page = 0
        total = len(email_files)
        total_pages = (total + page_size - 1) // page_size
        while True:
            start = page * page_size
            end = min(start + page_size, total)
            rows = []
            for email_file in email_files[start:end]:
                try:
                    msg = _parse_email_file(email_file)
                    if msg is None:
                        continue
                    rows.append({
                        "From": str(msg.get("From", "")),
                        "Date": str(msg.get("Date", "")),
                        "Subject": str(msg.get("Subject", "")),
                        "Attachments": str(sum(1 for part in msg.iter_attachments())),
                    })
                except Exception:
                    continue
            headers = ["From", "Date", "Subject", "Attachments"]
            widths = {}
            for header in headers:
                widths[header] = len(header)
            for row in rows:
                for header in headers:
                    value = str(row.get(header, ""))
                    max_width = EMAIL_COLUMN_WIDTHS[header]
                    if len(value) > max_width:
                        value = value[:max_width - 3] + "..."
                        row[header] = value
                    widths[header] = max(widths[header], len(value))
            print(f"\nEMAILS - PAGE {page + 1}/{total_pages}")
            header_line = "  ".join(header.ljust(widths[header]) for header in headers)
            separator = "  ".join("-" * widths[header] for header in headers)
            print(f"  {header_line}")
            print(f"  {separator}")
            for row in rows:
                line = "  ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers)
                print(f"  {line}")
            print(f"\nShowing {start + 1}-{end} of {total} emails")
            if page > 0:
                print("p) Previous page")
            if page < total_pages - 1:
                print("n) Next page")
            print("g) Go to page")
            print("q) Quit")
            choice = input("Choice: ").strip().lower()
            if choice == "q":
                return True
            if choice == "n" and page < total_pages - 1:
                page += 1
                continue
            if choice == "p" and page > 0:
                page -= 1
                continue
            if choice == "g":
                target = input(f"Go to page [1-{total_pages}]: ").strip()
                try:
                    target_page = int(target)
                except ValueError:
                    continue
                if 1 <= target_page <= total_pages:
                    page = target_page - 1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def extract_pst_contacts(pst_file: str, dest_dir: str) -> bool:
    """Extract PST contacts as VCard files."""
    try:
        output_dir = _get_pst_output_dir(pst_file, dest_dir) / "contacts"
        output_dir.mkdir(parents=True, exist_ok=True)
        before = set(output_dir.rglob("*.vcf"))
        r = _run_readpst(["-e", "-t", "c", "-cv", "-o", str(output_dir), pst_file])
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
                msg = _parse_email_file(email_file)
                if msg is None:
                    continue
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


def get_email_folders(email_files: list[str]) -> dict[str, list[str]]:
    """Group email paths by parent folder and sort each folder naturally."""
    folders: dict[str, list[str]] = {}
    for email_file in email_files:
        folder = Path(email_file).parent.name
        folders.setdefault(folder, []).append(email_file)
    for files in folders.values():
        files.sort(key=_natural_email_sort_key)
    return folders


def select_email_folder(email_files: list[str]) -> list[str] | None:
    """Select a folder and return its email paths, or None if cancelled."""
    folders = get_email_folders(email_files)
    if not folders:
        return None
    folder_names = sorted(folders)
    while True:
        print("\nSelect an email folder:")
        for index, folder in enumerate(folder_names, 1):
            print(f"{index}) {folder} ({len(folders[folder])})")
        print(f"{len(folder_names) + 1}) Cancel")
        choice = input("Choice: ").strip()
        try:
            selected = int(choice)
        except ValueError:
            continue
        if selected == len(folder_names) + 1:
            return None
        if 1 <= selected <= len(folder_names):
            return folders[folder_names[selected - 1]]


def select_email(title: str, email_files: list[str], page_size: int = 25) -> str | None:
    """Select an email from a paginated list."""
    if not email_files:
        return None
    page = 0
    total = len(email_files)
    total_pages = (total + page_size - 1) // page_size
    while True:
        start = page * page_size
        end = min(start + page_size, total)
        print(f"\n{title} - Page {page + 1}/{total_pages}")
        print(f"Showing {start + 1}-{end} of {total} emails")
        for index in range(start, end):
            email_path = Path(email_files[index])
            name = email_path.name
            print(f"{index + 1}) {name}")
        if page > 0:
            print("p) Previous page")
        if page < total_pages - 1:
            print("n) Next page")
        print("g) Go to page")
        print("q) Cancel")
        choice = input("Choice: ").strip().lower()
        if choice == "q":
            return None
        if choice == "n" and page < total_pages - 1:
            page += 1
            continue
        if choice == "p" and page > 0:
            page -= 1
            continue
        if choice == "g":
            target = input(f"Go to page [1-{total_pages}]: ").strip()
            try:
                target_page = int(target)
            except ValueError:
                continue
            if 1 <= target_page <= total_pages:
                page = target_page - 1
            continue
        try:
            selected = int(choice)
        except ValueError:
            continue
        if start + 1 <= selected <= end:
            return email_files[selected - 1]
