
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
```

from `iw scan`.

This is usually a transient driver, supplicant, or NetworkManager contention issue.

The tool still works fine, but a scan may occasionally need to be retried.

A future improvement may add a small busy check or retry backoff before scanning.

---

### NetworkScanner

A network utility that can:

- list network interfaces
- analyze a selected interface
- show connected interfaces
- show ARP neighbors using `ip neigh`
- run a TCP port scan against a selected or manually entered host
- report interface connection status

**Config:** `config/NetworkConfig.json`

**Constants:** `constants/NetworkConstants.py`

**Docs:** `doc/NetworkDoc.json`

---

### Email

An email and Outlook PST utility built around `pst-utils`.

The Email tool can:

- view a PST summary
- list emails contained in a PST
- select and view an individual email
- convert PST files to mbox
- convert PST files to separate EML files
- extract contacts
- extract attachments
- display Email config help

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

### Router

A router configuration utility for decoding, inspecting, editing, and re-encoding router backup files.

The Router tool can:

- select a router model specification
- select an original router configuration backup
- decode an encrypted router backup
- save the decoded archive
- extract the router configuration files
- view configured router settings
- edit supported configuration fields
- rebuild and encrypt an updated backup
- validate the generated backup before saving
- display Router config help

**Config:** `config/RouterConfig.json`

**Constants:** `constants/RouterConstants.py`

**Docs:** `doc/RouterDoc.json`

**Module:** `modules/router_utils.py`

**Model specifications:** `routers/model_specs/`

**Model documentation:** `routers/model_specs/README.md`

#### JSON-driven router support

Router models are configured through JSON rather than separate Python implementations for each model.

Each model specification describes the mechanisms needed to process its backups, including:

- encryption algorithm
- encoded payload format
- salt handling
- password requirements and hashing
- encryption key derivation
- backup headers, checksums, and trailers
- archive format and compression
- configuration file format
- editable configuration keys

For example:

```text
routers/model_specs/
    README.md
    VRV9517.json
```

**Router model names are identifiers, not processing rules.**

The utility selects its processing behavior from the model specification.

If another router uses mechanisms already supported by `router_utils.py`, it should require only another model JSON file.

If a router introduces an unsupported mechanism, a reusable helper must be implemented for that mechanism.

Do not add router-model-specific processing code to ToolLoader.

#### Router directory configuration

The router utility reads its directory locations from `config/RouterConfig.json`.

Current configuration:

```json
{
    "Locations": {
        "model_specs_path": "routers/model_specs",
        "config_path": "~/Documents/Routers/templates",
        "decoded_config_path": "~/Documents/Routers/decoded",
        "edited_config_path": "~/Documents/Routers/edited",
        "updated_config_path": "~/Documents/Routers/updated"
    }
}
```

| Configuration key | Purpose |
|---|---|
| `model_specs_path` | Directory containing router model JSON files |
| `config_path` | Directory containing original router backups |
| `decoded_config_path` | Directory for decoded archives and extracted configurations |
| `edited_config_path` | Directory for edited configurations |
| `updated_config_path` | Directory for newly encoded router backups |

The original router backups are stored outside the project source directory.

Changing these directories should require updating the JSON configuration rather than modifying Python code.

#### Supported backup extensions

Router backup selection currently supports:

```python
CONFIG_EXTENSION = [".cfg", ".bin"]
```

This controls file selection only.

**The extension does not determine the internal backup format.**

A `.bin` file may use a supported format or a completely different encryption and archive structure.

The model JSON determines whether the utility can process its contents.

The shared `get_files_by_extension()` helper supports both individual extensions and lists of extensions.

#### Router workflow

The typical processing sequence is:

```text
Select router model
        |
Select original backup
        |
Decode encrypted backup
        |
Save decoded archive
        |
Extract configuration
        |
View or edit supported settings
        |
Save edited configuration
        |
Rebuild archive
        |
Encrypt and rebuild backup
        |
Validate updated backup
        |
Save updated configuration
```

The generic router functions handle the processing based on the selected model JSON.

ToolLoader only coordinates the pipeline.

#### Router output naming

The original backup extension is retained in the generated filenames and extracted directory names.

For example:

```text
Original backup:
    router.cfg

Decoded archive:
    decoded/router.cfg.tar.gz

Extracted directory:
    decoded/router.cfg/

Edited directory:
    edited/router.cfg/

Updated backup:
    updated/router.cfg
```

For a `.bin` backup:

```text
Original backup:
    router.bin

Decoded archive:
    decoded/router.bin.tar.gz

Extracted directory:
    decoded/router.bin/

Edited directory:
    edited/router.bin/

Updated backup:
    updated/router.bin
```

This prevents backups such as `router.cfg` and `router.bin` from using the same intermediate archive or directory name.

The `.tar.gz` examples reflect the currently supported archive format. Supporting another archive format would require an appropriate reusable handler.

#### Password handling

Some router backups require the device's factory Wi-Fi password for encryption or decryption.

Whether a password is required is controlled by the selected model specification:

```json
"password_required": true
```

When required:

- the password is requested interactively
- input is hidden using `getpass`
- the password is requested once per decode or encode operation
- password processing follows the model JSON
- the password is not stored in the model specification
- the password is not stored in ToolLoader's pipeline context

Password handling belongs inside `router_utils.py`, not the shared ToolLoader.

The View and Edit operations work on extracted configuration data and do not require decrypting the original backup again.

#### Editable router fields

The `config_fields` section in each model JSON specifies the fields available through View and Edit.

Example:

```json
"config_fields": {
    "file": "config/.glbcfg",
    "wifi_2g_ssid": "ARC_WLAN_24G_SSID_0_ESSID",
    "wifi_2g_password": "ARC_WLAN_24G_SSID_0_WPA_Passphrase",
    "wifi_5g_ssid": "ARC_WLAN_5G_SSID_0_ESSID",
    "wifi_5g_password": "ARC_WLAN_5G_SSID_0_WPA_Passphrase"
}
```

The `file` entry identifies the configuration file inside the extracted archive.

The remaining entries map readable field names to the keys used by the router.

Additional supported fields can be exposed by changing the JSON without modifying the Python editor.

#### Backup safety

The router utility keeps the original configuration separate from edited and updated copies.

Important precautions:

- keep an unchanged copy of the original router backup
- avoid overwriting existing output files accidentally
- do not commit real router backups containing private configuration data
- validate the generated backup before attempting a restore
- retain a recovery method before testing modified configurations on a physical device

A successful local decode and re-encode does not guarantee that the router will accept the modified backup.

Full router model specification documentation is available in:

```text
routers/model_specs/README.md
```

---

## How it works

Each tool is defined mainly by a **constants module**.

The constants module describes:

- config path
- config documentation path
- JSON keys
- validation rules
- secondary validation
- required user level
- dependency list
- status function configuration
- plan column configuration
- menu actions
- reusable pre-phase blocks
- reusable exec-phase blocks
- pipeline states

The actual reusable logic lives in modules such as:

```text
modules/
    display_utils.py
    file_utils.py
    network_utils.py
    email_utils.py
    router_utils.py
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

- discovering network interfaces
- discovering ARP neighbors
- finding PST files
- selecting a PST file
- extracting selectable email files
- selecting an individual email
- finding router model specifications
- selecting a router model
- selecting a router backup
- selecting an extracted or edited router configuration

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

Sensitive passwords should not be stored in shared pipeline context.

---

## Exec-phase

The `exec` phase performs the requested operation.

Examples include:

- scanning ports
- analyzing an interface
- displaying network data
- reading PST metadata
- converting PST to mbox
- converting PST to EML
- extracting contacts
- extracting attachments
- decoding router backups
- saving decoded archives
- extracting router configurations
- viewing and editing router fields
- rebuilding and encoding updated router backups

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

- `job` is available for pipeline patterns that require a job object
- `meta` contains the loaded tool configuration
- `ctx` contains results generated by previous pipeline steps

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

- fixed fields
- editable values
- example configuration
- field descriptions

The config help action uses:

```python
display_config_doc
```

to display the documentation directly in the terminal.

For the Router utility, the configuration documentation describes the directory settings in `RouterConfig.json`.

The separate router model specification documentation explains the encryption, archive, backup wrapper, and editable field settings.

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

is not PST-specific or router-specific.

The Email constants layer supplies:

```text
.pst
```

when it needs PST files.

The Router constants layer can supply:

```python
[".cfg", ".bin"]
```

when it needs router backup files.

The same helper accepts either a single extension or a list of extensions.

This means it can be reused for:

```text
.eml
.mbox
.ost
.vcf
.ics
.cfg
.bin
```

or other file types without introducing tool-specific branches into `file_utils.py`.

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

router_utils.py
    load_router_model_specs
    decode_router_config
    save_router_config
    extract_router_config
    view_router_config_fields
    edit_router_config_fields
    encode_router_config
```

Menu and display logic stays in the constants/pipeline layer rather than being embedded inside the reusable utility functions.

Router-specific encryption, password processing, backup parsing, and archive handling remain inside the router module.

ToolLoader does not contain router-specific processing logic.

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
│   ├── EmailConfig.json
│   └── RouterConfig.json
│
├── constants/
│   ├── WiFiConstants.py
│   ├── NetworkConstants.py
│   ├── EmailConstants.py
│   └── RouterConstants.py
│
├── doc/
│   ├── WiFiDoc.json
│   ├── NetworkDoc.json
│   ├── EmailDoc.json
│   └── RouterDoc.json
│
├── modules/
│   ├── display_utils.py
│   ├── file_utils.py
│   ├── network_utils.py
│   ├── email_utils.py
│   ├── router_utils.py
│   └── state_machine_utils.py
│
├── routers/
│   └── model_specs/
│       ├── README.md
│       └── VRV9517.json
│
└── email/
    ├── email_source/
    └── email_dest/
```

The `email/` directory is runtime data and should normally be excluded from Git.

Original router backups and generated router configuration files are stored in the locations configured by `RouterConfig.json`.

The model JSON files and their documentation remain part of the source project.

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

# Router backup files, if stored inside the project
routers/templates/
```

For a repository that contains `TestingTools/` as a subdirectory, corresponding rules can be written relative to the repository root:

```gitignore
TestingTools/email/
TestingTools/recovery/
TestingTools/integrity/
TestingTools/routers/templates/
```

The current router configuration stores original backups at:

```text
~/Documents/Routers/templates
```

This directory is outside the project source tree and normally does not need a repository `.gitignore` entry.

Do not commit real router backup files or generated configurations containing credentials.

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

The Router utility follows the same approach:

```text
RouterConfig.json
        +
RouterConstants.py
        +
Router model JSON
        +
router_utils.py
        +
Shared ToolLoader
```

Router models remain data-driven, while the shared ToolLoader stays independent of individual tools.
