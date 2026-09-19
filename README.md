````markdown
# TestingTools

A small collection of terminal-based testing utilities built around a **shared, reusable ToolLoader** and a **pipeline-style state machine**.

The main goal:

- keep tools modular
- keep logic reusable
- keep execution predictable (`pre → plan → confirm → exec`)
- avoid one-off scripts that turn into spaghetti
- keep tool-specific logic separate from shared display, file, and pipeline helpers

---

## What's included

### WiFiScanner

A Wi-Fi utility that can:

- list wireless interfaces
- scan for nearby networks
- show detailed information for a selected network
- display BSS details
- report wireless interface status

**Config:** `config/WiFiConfig.json`

**Constants:** `constants/WiFiConstants.py`

**Docs:** `doc/WiFiDoc.json`

#### Notes

Some USB Wi-Fi adapters can intermittently return:

```text
Device or resource busy (-16)
````

from `iw scan`.

This is usually a transient driver, supplicant, or NetworkManager contention issue.

The tool still works fine, but a scan may occasionally need to be retried.

A future improvement may add a small busy check or retry backoff before scanning.

---

### NetworkScanner

A network utility that can:

* list network interfaces
* analyze a selected interface
* show connected interfaces
* show ARP neighbors using `ip neigh`
* run a TCP port scan against a selected or manually entered host
* report interface connection status

**Config:** `config/NetworkConfig.json`

**Constants:** `constants/NetworkConstants.py`

**Docs:** `doc/NetworkDoc.json`

---

### Email

An email and Outlook PST utility built around `pst-utils`.

The Email tool can:

* view a PST summary
* list emails contained in a PST
* select and view an individual email
* convert PST files to mbox
* convert PST files to separate EML files
* extract contacts
* extract attachments
* display Email config help

The source directory can contain multiple PST files. The tool builds a selection menu so the required PST can be chosen before the requested action runs.

**Config:** `config/EmailConfig.json`

**Constants:** `constants/EmailConstants.py`

**Docs:** `doc/EmailDoc.json`

#### Email directory layout

Runtime email data is stored outside the tracked source code:

```text
email/
    email_source/
    email_dest/
```

PST files are placed in:

```text
email/email_source/
```

Generated output is written to:

```text
email/email_dest/
```

Each PST gets its own output directory.

For example:

```text
email/email_source/testPST.pst
```

can produce:

```text
email/email_dest/
    testPST/
        mbox/
        eml/
        contacts/
        attachments/
```

This keeps output from separate PST files isolated and easier to manage.

The entire `email/` directory is ignored by Git because it contains runtime, test, converted, and potentially private email data.

#### Dependencies

The Email utility uses:

```text
pst-utils
```

The package provides tools such as `readpst` used by the Email module for PST conversion and extraction.

---

## How it works

Each tool is defined mainly by a **constants module**.

The constants module describes:

* config path
* config documentation path
* JSON keys
* validation rules
* secondary validation
* required user level
* dependency list
* status function configuration
* plan column configuration
* menu actions
* reusable pre-phase blocks
* reusable exec-phase blocks
* pipeline states

The actual reusable logic lives in modules such as:

```text
modules/
    display_utils.py
    file_utils.py
    network_utils.py
    email_utils.py
    state_machine_utils.py
```

The constants files then wire those functions together into tool-specific pipelines.

---

## ToolLoader flow

The shared ToolLoader handles the main execution flow.

Typical startup:

1. load the selected tool constants
2. check dependencies
3. install missing dependencies if required
4. load the tool config
5. validate the config
6. run secondary validation
7. compute the tool status
8. display the action menu
9. run the selected pipeline

A pipeline can contain:

```text
pre
 ↓
plan
 ↓
confirm
 ↓
exec
```

Not every action requires every stage.

For example, a read-only action such as:

```text
List emails
```

may skip the plan and confirmation stages.

A modifying or conversion action such as:

```text
Convert PST to mbox
```

can display a plan and require confirmation before execution.

---

## Pre-phase

The `pre` phase is used for preparation and selection.

Examples include:

* discovering network interfaces
* discovering ARP neighbors
* finding PST files
* selecting a PST file
* extracting selectable email files
* selecting an individual email

A pre-phase step can store its result in the pipeline context:

```python
{
    "phase": "pre",
    "fn": get_files_by_extension,
    "args": [
        lambda job, meta, ctx: meta[LOCATIONS_KEY][SOURCE_DIR],
        lambda job, meta, ctx: ".pst",
    ],
    "result": "pst_files",
}
```

Later steps can access that result through:

```python
ctx.get("pst_files", [])
```

---

## Exec-phase

The `exec` phase performs the requested operation.

Examples include:

* scanning ports
* analyzing an interface
* displaying network data
* reading PST metadata
* converting PST to mbox
* converting PST to EML
* extracting contacts
* extracting attachments

Example:

```python
{
    "phase": "exec",
    "fn": convert_pst_to_mbox,
    "args": [
        lambda job, meta, ctx: ctx.get("selected_pst"),
        lambda job, meta, ctx: meta[LOCATIONS_KEY][DEST_DIR],
    ],
    "result": "convert_ok",
}
```

---

## Shared pipeline context

Pipeline steps use three standard resolver arguments:

```text
job
meta
ctx
```

For ToolLoader pipelines:

* `job` is available for pipeline patterns that require a job object
* `meta` contains the loaded tool configuration
* `ctx` contains results generated by previous pipeline steps

For example:

```python
lambda job, meta, ctx: meta["locations"]["source_dir"]
```

reads from config.

While:

```python
lambda job, meta, ctx: ctx.get("selected_pst")
```

reads a value created by an earlier pipeline step.

---

## Status system

Each tool can provide a status function through `STATUS_FN_CONFIG`.

Example:

```python
STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": get_directory_status,
    "args": [
        lambda job, meta, ctx: meta[LOCATIONS_KEY][SOURCE_DIR],
    ],
    "id_field": "location",
    "active_rule": {"field": "state", "equals": "data_present"},
}
```

The Email tool uses this to determine whether its configured source directory currently contains data.

Example output:

```text
Email Status Summary
--------------------

Email                 Status
-----                 ------
email/email_source    DATA PRESENT
```

---

## Config validation

Each tool can define primary validation:

```python
VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        LOCATIONS_KEY: dict,
    },
}
```

and secondary validation for nested structures:

```python
SECONDARY_VALIDATION: Dict[str, Any] = {
    LOCATIONS_KEY: {
        "required_job_fields": {
            SOURCE_DIR: str,
            DEST_DIR: str,
        },
        "allow_empty": False,
    }
}
```

This allows the loader to validate config structure before any action runs.

---

## Config documentation

Each tool can provide a JSON config documentation file.

Example:

```text
doc/EmailDoc.json
```

These files describe:

* fixed fields
* editable values
* example configuration
* field descriptions

The config help action uses:

```python
display_config_doc
```

to display the documentation directly in the terminal.

---

## Example Email config

```json
{
  "locations": {
    "source_dir": "email/email_source",
    "dest_dir": "email/email_dest"
  }
}
```

---

## Example Email actions

```text
Select an Email operation:
1) View PST summary
2) List emails
3) View email
4) Convert PST to mbox
5) Convert PST to EML
6) Extract contacts
7) Extract attachments
8) Show config help
9) Cancel
```

---

## Generic helper design

Where possible, helper functions are kept generic.

For example:

```python
get_files_by_extension(directory, extension)
```

is not PST-specific.

The Email constants layer supplies:

```text
.pst
```

when it needs PST files.

This means the same helper can later be reused for:

```text
.eml
.mbox
.ost
.vcf
.ics
```

or other file types without changing `file_utils.py`.

Tool-specific operations remain in their own modules.

For example:

```text
file_utils.py
    get_directory_status
    get_files_by_extension

email_utils.py
    get_pst_summary
    get_pst_email_rows
    get_pst_email_files
    get_email_details
    convert_pst_to_mbox
    convert_pst_to_eml
    extract_pst_contacts
    extract_pst_attachments
```

Menu and display logic stays in the constants/pipeline layer rather than being embedded inside the reusable utility functions.

---

## Run

### Interactive selection

From the project directory:

```bash
python3 ToolLoader.py
```

The loader presents the available tools and then runs the selected tool through the shared state machine.

---

## Project structure

A simplified project layout:

```text
TestingTools/
│
├── ToolLoader.py
│
├── config/
│   ├── WiFiConfig.json
│   ├── NetworkConfig.json
│   └── EmailConfig.json
│
├── constants/
│   ├── WiFiConstants.py
│   ├── NetworkConstants.py
│   └── EmailConstants.py
│
├── doc/
│   ├── WiFiDoc.json
│   ├── NetworkDoc.json
│   └── EmailDoc.json
│
├── modules/
│   ├── display_utils.py
│   ├── file_utils.py
│   ├── network_utils.py
│   ├── email_utils.py
│   └── state_machine_utils.py
│
└── email/
    ├── email_source/
    └── email_dest/
```

The `email/` directory is runtime data and should normally be excluded from Git.

---

## Git ignore

Typical ignored files include:

```gitignore
# Python cache
__pycache__/
*.py[cod]
*$py.class

# Optional: virtual environments
venv/
.env/

# Email working data
email/
```

---

## Design philosophy

TestingTools is intentionally built around reusable components rather than independent scripts.

A tool should ideally consist of:

```text
Config
  +
Constants
  +
Reusable module functions
  +
Shared ToolLoader
```

rather than duplicating execution logic for every new utility.

This makes it easier to add future tools while preserving the same:

```text
dependency check
config validation
status
menu
preparation
planning
confirmation
execution
finalisation
```

flow across the project.

```

I also changed the run command to `python3 ToolLoader.py`, since that matches the actual filename shown in your current project traces rather than `tool_loader.py`.
```
