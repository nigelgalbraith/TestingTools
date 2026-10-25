#!/usr/bin/env python3
"""
email_utils.py
"""

from __future__ import annotations

import json
import mailbox
import shutil
import subprocess
import tempfile
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any, Dict, List

from modules.display_utils import confirm, select_from_list
from modules.file_utils import expand_path


# ---------------------------------------------------------------------
# FILE CONSTANTS
# ---------------------------------------------------------------------

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
        text=True,
        check=False,
    )


def _get_pst_output_dir(pst_file: str, dest_dir: str) -> Path | None:
    """Create a PST-named output folder, confirming before overwrite."""
    pst_path = Path(pst_file)
    if not pst_path.is_file():
        print(f"[ERROR] PST file not found: {pst_file}")
        return None
    output_dir = Path(expand_path(dest_dir)) / pst_path.stem
    if output_dir.exists():
        if not output_dir.is_dir():
            print(f"[ERROR] Output path is not a directory: {output_dir}")
            return None
        if not confirm(f"Overwrite existing folder {output_dir}? [y/n]: "):
            print("[INFO] Operation cancelled.")
            return None
        shutil.rmtree(output_dir)
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


def _flatten_extracted_files(output_dir: Path, extension: str) -> int:
    """Move extracted files into the PST output directory and remove empty folders."""
    count = 0
    for source in list(output_dir.rglob("*")):
        if not source.is_file() or source.suffix.lower() != extension.lower():
            continue
        if source.parent != output_dir:
            target = output_dir / source.name
            number = 2
            while target.exists():
                target = output_dir / f"{source.stem}_{number}{source.suffix}"
                number += 1
            shutil.move(str(source), str(target))
        count += 1
    for directory in sorted(
        (p for p in output_dir.rglob("*") if p.is_dir()),
        key=lambda p: len(p.parts),
        reverse=True,
    ):
        if not any(directory.iterdir()):
            directory.rmdir()
    return count


def count_mbox_messages(mbox_file: str) -> int:
    """Return the number of messages in an mbox file."""
    try:
        box = mailbox.mbox(mbox_file)
        return len(box)
    except Exception:
        return 0


def get_email_folders(email_files: list[str]) -> dict[str, list[str]]:
    """Group email paths by parent folder and sort each folder naturally."""
    folders: dict[str, list[str]] = {}
    for email_file in email_files:
        folder = Path(email_file).parent.name
        folders.setdefault(folder, []).append(email_file)
    for files in folders.values():
        files.sort(key=_natural_email_sort_key)
    return folders


# ---------------------------------------------------------------------
# PRE STEPS
# ---------------------------------------------------------------------


def clear_pst_files(ctx: dict) -> bool:
    """Remove temporary PST discovery data from context."""
    ctx.pop("pst_files", None)
    return True


# ---------------------------------------------------------------------
# PST SELECTION AND INFORMATION
# ---------------------------------------------------------------------


def select_pst_files(pst_dir: str) -> str | list[str] | None:
    """Find and select one PST file or all PST files."""
    directory = Path(expand_path(pst_dir))
    pst_files = sorted(str(path) for path in directory.iterdir() if path.is_file() and path.suffix.lower() == ".pst") if directory.is_dir() else []
    if not pst_files:
        print("No PST files available.")
        return None
    return select_from_list("Select a PST file", pst_files, allow_all=True, retry_invalid=True)


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


# ---------------------------------------------------------------------
# PST CONVERSION
# ---------------------------------------------------------------------


def convert_pst_to_mbox(pst_file: str, dest_dir: str) -> bool:
    """Convert a PST file to mbox format using readpst."""
    try:
        pst_path = Path(pst_file)
        if not pst_path.is_file():
            print(f"[ERROR] PST file not found: {pst_file}")
            return False
        output_dir = _get_pst_output_dir(pst_file, dest_dir)
        if output_dir is None:
            return False
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
        output_dir = _get_pst_output_dir(pst_file, dest_dir)
        if output_dir is None:
            return False
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


# ---------------------------------------------------------------------
# PST EXTRACTION
# ---------------------------------------------------------------------


def extract_pst_contacts(pst_file: str, dest_dir: str) -> bool:
    """Extract PST contacts as VCard files."""
    try:
        output_dir = _get_pst_output_dir(pst_file, dest_dir)
        if output_dir is None:
            return False
        r = _run_readpst([
            "-e",
            "-t", "c",
            "-cv",
            "-o", str(output_dir),
            pst_file,
        ])
        if r.returncode != 0:
            print(f"[ERROR] Failed to extract contacts: {pst_file}")
            if r.stderr:
                print(r.stderr.strip())
            return False
        count = _flatten_extracted_files(output_dir, ".vcf")
        if count == 0:
            print("[INFO] No contacts found.")
        else:
            print(f"[INFO] Contacts extracted: {count}")
        print(f"[INFO] Output directory: {output_dir}")
        return True
    except Exception as e:
        print(f"[ERROR] Contact extraction failed: {e}")
        return False


def extract_pst_calendars(pst_file: str, dest_dir: str) -> bool:
    """Extract PST calendar appointments as iCalendar files."""
    try:
        output_dir = _get_pst_output_dir(pst_file, dest_dir)
        if output_dir is None:
            return False
        r = _run_readpst([
            "-e",
            "-t", "a",
            "-o", str(output_dir),
            pst_file,
        ])
        if r.returncode != 0:
            print(f"[ERROR] Failed to extract calendars: {pst_file}")
            if r.stderr:
                print(r.stderr.strip())
            return False
        count = _flatten_extracted_files(output_dir, ".ics")
        if count == 0:
            print("[INFO] No calendar appointments found.")
        else:
            print(f"[INFO] Calendar appointments extracted: {count}")
        print(f"[INFO] Output directory: {output_dir}")
        return True
    except Exception as e:
        print(f"[ERROR] Calendar extraction failed: {e}")
        return False


def extract_pst_attachments(pst_file: str, dest_dir: str) -> bool:
    """Extract attachments from all emails contained in a PST file."""
    if not Path(pst_file).is_file():
        print(f"[ERROR] PST file not found: {pst_file}")
        return False
    temp_dir = _extract_eml_temp(pst_file)
    if not temp_dir:
        print(f"[ERROR] Failed to read PST: {pst_file}")
        return False
    try:
        output_dir = _get_pst_output_dir(pst_file, dest_dir)
        if output_dir is None:
            return False
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


# ---------------------------------------------------------------------
# EMAIL BROWSING
# ---------------------------------------------------------------------


def get_pst_email_files(pst_file: str, work_dir: str) -> List[str]:
    """Extract a PST and return contained EML files."""
    try:
        output_path = Path(expand_path(work_dir))
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


# ---------------------------------------------------------------------
# EMAIL SEARCH
# ---------------------------------------------------------------------


def list_email_search_configs(search_configs: list) -> list | bool:
    """Select one search configuration or all configurations."""
    if not isinstance(search_configs, list) or not search_configs:
        print("No email search configurations available.")
        return False
    selection = select_from_list("Select Email Search Criteria", search_configs, allow_all=True, retry_invalid=True)
    if selection is None:
        return False
    selected = selection if isinstance(selection, list) else [selection]
    return [str(expand_path(config)) for config in selected]


def search_emails(config_file: str) -> list | bool:
    """Search EML files using JSON criteria and copy matching messages."""
    try:
        if not config_file:
            return False
        with Path(expand_path(config_file)).open("r", encoding="utf-8") as file:
            config = json.load(file)
        search_location = Path(expand_path(config["search_location"])).resolve()
        results_location = Path(expand_path(config["results_location"])).resolve()
        match_mode = config.get("match", "any").lower()
        criteria = config["criteria"]
        if match_mode not in ("any", "all"):
            raise ValueError("Match mode must be 'any' or 'all'")
        if not search_location.is_dir():
            raise ValueError(f"Search directory does not exist: {search_location}")
        if search_location == results_location or search_location in results_location.parents:
            raise ValueError("Results directory must not be inside the search directory")
        if results_location in search_location.parents:
            raise ValueError("Search directory must not be inside the results directory")
        fields = ("from", "to", "subject", "body")
        active_criteria = {}
        for field in fields:
            terms = criteria.get(field, [])
            if not isinstance(terms, list) or any(not isinstance(term, str) for term in terms):
                raise ValueError(f"Invalid search criteria for {field}")
            active_criteria[field] = [term.casefold() for term in terms if term.strip()]
        if not any(active_criteria.values()):
            raise ValueError("No search criteria defined")
        if results_location.exists():
            if not results_location.is_dir():
                raise ValueError(f"Results path is not a directory: {results_location}")
            if not confirm(f"Overwrite existing folder {results_location}? [y/n]: "):
                print("[INFO] Email search cancelled.")
                return False
            shutil.rmtree(results_location)
        results_location.mkdir(parents=True, exist_ok=True)
        results = []
        scanned = 0
        for email_file in sorted(search_location.rglob("*")):
            if not email_file.is_file() or email_file.suffix.lower() != ".eml":
                continue
            scanned += 1
            try:
                message = _parse_email_file(email_file)
                if message is None:
                    print(f"Skipped unreadable email: {email_file}")
                    continue
                values = {
                    "from": str(message.get("From", "")),
                    "to": str(message.get("To", "")),
                    "subject": str(message.get("Subject", "")),
                    "body": _get_email_body(message),
                }
                matched = []
                field_matches = []
                for field, terms in active_criteria.items():
                    if not terms:
                        continue
                    found = any(term in values[field].casefold() for term in terms)
                    field_matches.append(found)
                    if found:
                        matched.append(field.title())
                is_match = any(field_matches) if match_mode == "any" else all(field_matches)
                if not is_match:
                    continue
                relative_path = email_file.relative_to(search_location)
                destination = results_location / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(email_file, destination)
                results.append({
                    "Date": str(message.get("Date", "")),
                    "From": values["from"],
                    "To": values["to"],
                    "Subject": values["subject"],
                    "Matched": ", ".join(matched),
                    "File": str(destination),
                })
            except (OSError, UnicodeError, ValueError, TypeError) as exc:
                print(f"Skipped unreadable email {email_file}: {exc}")
        print(f"\nEmails scanned : {scanned}")
        print(f"Matches found  : {len(results)}")
        print(f"Results saved  : {len(results)}")
        print(f"Results folder : {results_location}")
        return results
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"Email search failed: {exc}")
        return False


def load_email_search_results(config_files: list) -> list | bool:
    """Load saved email results and identify their search configuration."""
    if not isinstance(config_files, list) or not config_files:
        return False
    results = []
    for config_file in config_files:
        try:
            with Path(expand_path(config_file)).open("r", encoding="utf-8") as file:
                config = json.load(file)
            results_dir = Path(expand_path(config["results_location"]))
            if not results_dir.is_dir():
                print(f"No saved search results found: {results_dir}")
                continue
            search_name = Path(config_file).stem
            for email_file in sorted(results_dir.rglob("*")):
                if not email_file.is_file() or email_file.suffix.lower() != ".eml":
                    continue
                details = get_email_details(str(email_file))
                if not details:
                    continue
                results.append({
                    "Date": details.get("Date", ""),
                    "From": details.get("From", ""),
                    "To": details.get("To", ""),
                    "Subject": details.get("Subject", ""),
                    "Matched": search_name,
                    "File": str(email_file),
                })
        except (OSError, ValueError, TypeError, KeyError) as exc:
            print(f"Unable to load search results from {config_file}: {exc}")
    return results


def display_email_search_results(results: list, config_files: str | list | None = None, page_size: int = 25) -> bool:
    """Display search configuration details and paginated email results."""
    if not isinstance(results, list) or page_size < 1:
        return False
    configs = [config_files] if isinstance(config_files, str) else (config_files or [])
    print("\nEmail Search Summary")
    print("-" * 70)
    for config_file in configs:
        try:
            with Path(expand_path(config_file)).open("r", encoding="utf-8") as file:
                config = json.load(file)
            print(f"Configuration : {Path(config_file).name}")
            print(f"Match Mode    : {config.get('match', 'any').upper()}")
            print(f"Search Folder : {config.get('search_location', '')}")
            print("Search Criteria:")
            for field, terms in config.get("criteria", {}).items():
                if terms:
                    print(f"  {field.title():<10}: {', '.join(terms)}")
            print("-" * 70)
        except (OSError, ValueError, TypeError) as exc:
            print(f"Unable to display config {config_file}: {exc}")
    print(f"Total Matches : {len(results)}")
    print("-" * 70)
    if not results:
        print("\nNo matching emails found.")
        return True
    page = 0
    total_pages = (len(results) + page_size - 1) // page_size
    while True:
        start = page * page_size
        end = min(start + page_size, len(results))
        print(f"\nEmail Search Results (Page {page + 1} of {total_pages})")
        print("-" * 110)
        print(f"{'No':<5} {'Date':<20} {'From':<28} {'Subject':<35} {'Matched'}")
        print("-" * 110)
        for index in range(start, end):
            item = results[index]
            print(f"{index + 1:<5} {item['Date'][:19]:<20} {item['From'][:27]:<28} {item['Subject'][:34]:<35} {item['Matched']}")
        print("-" * 110)
        print("[N] Next  [P] Previous  [Number] View Email  [Q] Quit")
        selection = input("\nSelection: ").strip().lower()
        if selection == "q":
            return True
        if selection == "n":
            if page < total_pages - 1:
                page += 1
            else:
                print("Already on the last page.")
        elif selection == "p":
            if page > 0:
                page -= 1
            else:
                print("Already on the first page.")
        elif selection.isdigit() and 1 <= int(selection) <= len(results):
            item = results[int(selection) - 1]
            details = get_email_details(item["File"])
            if not details:
                print(f"[ERROR] Unable to read email: {item['File']}")
                input("\nPress Enter to return to results...")
                continue
            print("\nEmail Details")
            print("-" * 70)
            for field in ("From", "To", "Date", "Subject"):
                print(f"{field:<8}: {details.get(field, '')}")
            print(f"Matched : {item['Matched']}")
            print(f"Saved   : {item['File']}")
            print("-" * 70)
            print(details.get("Body", ""))
            input("\nPress Enter to return to results...")
        else:
            print("Invalid selection.")


# ---------------------------------------------------------------------
# BATCH RUNNERS
# ---------------------------------------------------------------------


def run_pst_files(pst_files: str | list[str], dest_dir: str, operation) -> bool:
    """Run a conversion or extraction operation on selected PST files."""
    if not pst_files:
        return False
    if isinstance(pst_files, str):
        return operation(pst_files, dest_dir)
    successful = 0
    for index, pst_file in enumerate(pst_files, 1):
        print(f"\nProcessing {index}/{len(pst_files)}: {Path(pst_file).name}")
        if operation(pst_file, dest_dir):
            successful += 1
    print(f"\nCompleted: {successful}/{len(pst_files)} PST files")
    return successful == len(pst_files)


def run_email_searches(config_files: str | list) -> list | bool:
    """Run one or multiple email searches."""
    if not config_files:
        return False
    if isinstance(config_files, str):
        return search_emails(config_files)
    if not isinstance(config_files, list):
        return False
    results = []
    for config_file in config_files:
        print(f"\nRunning email search: {Path(config_file).name}")
        search_results = search_emails(config_file)
        if search_results is False:
            print(f"[ERROR] Search failed: {Path(config_file).name}")
            continue
        results.extend(search_results)
    return results
