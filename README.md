
# TestingTools

A collection of terminal-based testing utilities built around a **shared, reusable ToolLoader** and a **pipeline-style state machine**.

The main goals are to:

- Keep tools modular.
- Reuse common functions.
- Maintain predictable execution (`pre → plan → confirm → exec`).
- Avoid unnecessary tool-specific implementations.
- Keep processing logic separate from shared display, file and pipeline helpers.

---

## What's Included

### WiFiScanner

A Wi-Fi utility that can:

- List wireless interfaces.
- Scan for nearby networks.
- Show detailed information for selected networks.
- Display BSS details.
- Report wireless interface status.

**Config:** `config/WiFiConfig.json`

**Constants:** `constants/WiFiConstants.py`

**Docs:** `doc/WiFiDoc.json`

Some wireless adapters can intermittently report `Device or resource busy (-16)` from `iw scan`. This is generally a transient driver, supplicant or NetworkManager contention issue. Retrying the scan may resolve it.

### NetworkScanner

A network utility that can:

- List network interfaces.
- Analyse a selected interface.
- Show connected interfaces.
- Display ARP neighbours using `ip neigh`.
- Run TCP port scans against selected or manually entered hosts.
- Report interface connection status.

**Config:** `config/NetworkConfig.json`

**Constants:** `constants/NetworkConstants.py`

**Docs:** `doc/NetworkDoc.json`

### Email

An email and Outlook PST utility built around `pst-utils`.

The Email tool can:

- View a PST summary.
- List emails contained in a PST.
- Select and view individual emails.
- Convert PST files to mbox.
- Convert PST files to separate EML files.
- Extract contacts.
- Extract attachments.
- Display Email configuration help.

The source directory can contain multiple PST files. The tool builds a selection menu before processing the selected file.

**Config:** `config/EmailConfig.json`

**Constants:** `constants/EmailConstants.py`

**Docs:** `doc/EmailDoc.json`

#### Email Directory Layout

Email source and destination directories are configured by the Email utility.

A typical layout is:

```text
email/
    email_source/
    email_dest/
```

Each PST receives its own output directory.

For example:

```text
email_source/
    testPST.pst

email_dest/
    testPST/
        mbox/
        eml/
        contacts/
        attachments/
```

This keeps output from different PST files separate.

Runtime email data may contain private information and should generally be excluded from Git.

#### Dependencies

The Email utility uses `pst-utils`, including the `readpst` command for PST conversion and extraction.

---

## Router

A router configuration utility for decoding, inspecting, editing and re-encoding router backup files.

The Router tool can:

- Select a router model specification.
- Select an original configuration backup.
- Select the appropriate template router password file.
- Decode encrypted router backups.
- Save decoded archives.
- Extract configuration files.
- View configured router settings.
- Edit supported configuration fields.
- Rebuild configuration archives.
- Encrypt updated backups for target routers.
- Validate generated backups.
- Display configuration and model specification help.

**Config:** `config/RouterConfig.json`

**Constants:** `constants/RouterConstants.py`

**Docs:** `doc/RouterDoc.json`

**Module:** `modules/router_utils.py`

### JSON-Driven Router Support

Router models are configured through JSON rather than separate Python implementations for each model.

Each model specification defines:

- Router model, firmware and hardware.
- Encryption algorithm.
- Encoded payload format.
- Salt handling.
- Password requirements and hashing.
- Encryption key derivation.
- Backup headers, checksums and trailers.
- Archive format and compression.
- Configuration file format.
- Editable configuration keys.

The router model is an identifier, not a processing rule.

If another router uses mechanisms already supported by `router_utils.py`, adding support should require only another model JSON.

If an unsupported mechanism is needed, implement a reusable Python helper rather than adding router-specific logic to ToolLoader.

Model specifications are loaded from `Locations.model_specs_path`.

### Router Directory Configuration

All router locations are defined in `config/RouterConfig.json` under `Locations`.

| Configuration key | Purpose |
|---|---|
| `model_specs_path` | Router model JSON specifications |
| `model_specs_readme_path` | Model specification documentation |
| `template_router_password_path` | Template router password text files |
| `config_path` | Original encrypted router templates |
| `decoded_config_path` | Decoded archives and extracted configurations |
| `edited_config_path` | Edited router configurations |
| `updated_config_path` | Re-encoded router backups |

These paths are configurable. No router data directory is hardcoded into the processing workflow.

Paths can be changed by editing `RouterConfig.json` without modifying the router utility code.

### Supported Backup Extensions

Router backup selection supports:

```python
CONFIG_EXTENSION = [".cfg", ".bin"]
```

This controls file selection only.

**The file extension does not determine the internal backup format.**

A `.bin` file may contain an entirely different encryption or archive structure.

The model JSON determines how the utility processes the selected file.

### Router Workflow

The typical workflow is:

```text
Select Router Model
        |
        v
Select Original Template
        |
        v
Select Template Password File
        |
        v
Decode Configuration
        |
        v
Save Decoded Archive
        |
        v
Extract Configuration
        |
        v
View / Edit Configuration
        |
        v
Save Edited Configuration
        |
        v
Select Original Template
and Template Password File
        |
        v
Enter Target Router Password
        |
        v
Rebuild Archive
        |
        v
Encrypt for Target Router
        |
        v
Verify Generated Backup
        |
        v
Save Updated Configuration
```

The generic router functions perform the processing using the selected model specification.

ToolLoader coordinates the pipeline.

### Router Output Naming

The utility uses consistent filename suffixes for the different configuration stages.

Given an original backup named `SmartModem_backup.cfg`:

```text
Original:
    SmartModem_backup.cfg

Decoded archive:
    SmartModem_backup-decoded.tar.gz

Extracted directory:
    SmartModem_backup-decoded/

Edited directory:
    OfficeRouter-edited/

Encoded backup:
    OfficeRouter-encoded.cfg
```

When editing, the user can enter a new configuration name, such as `OfficeRouter`.

If no name is entered, the original template filename is used:

```text
Edited directory:
    SmartModem_backup-edited/

Encoded backup:
    SmartModem_backup-encoded.cfg
```

The original template name is retained during decoding. The new configuration name is used for editing and encoding.

The original router backup remains unchanged.

### Password Handling

Some router backups require the factory Wi-Fi password of the physical router for encryption and decryption.

The model specification determines whether a password is required:

```json
"password_required": true
```

The utility uses two distinct passwords.

#### Template Router Password

A master template originates from one physical router.

The password belonging to that router is stored in a plain-text `.txt` file in the directory configured by `Locations.template_router_password_path`.

Each password file contains only the password, without JSON formatting or quotation marks.

During decoding:

1. The utility lists available password files.
2. The user selects the corresponding template password.
3. The program reads the selected text file.
4. The password is used to decrypt the master template.

Encoding also uses a selected template password file to decrypt the original backup before rebuilding the archive.

The template password is not stored in the model specification JSON.

#### Target Router Password

When creating a new configuration for another router:

1. The program prompts for the target router's factory Wi-Fi password.
2. Input is hidden using `getpass`.
3. The edited configuration is encrypted using that password.
4. The generated backup is decrypted again for local verification.

The target password is not stored in the model JSON or shared pipeline context.

Each target router may have a different factory password even when the model is identical.

Password hashing and key derivation are determined by the selected model specification.

### Editable Router Fields

The `config_fields` section in each router model JSON determines which settings appear in the View and Edit menus.

For example:

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

Other entries map readable field names to the actual configuration keys.

Additional fields can be made editable by adding their mappings to the JSON, provided the parser supports their format.

### Router Model Documentation

The router model specification README explains how to create specifications for additional router models.

Its path is defined by:

`Locations.model_specs_readme_path`

The **View Model Specifications Help** action displays the configured README in the terminal using the generic `display_readme()` helper.

### Overwrite Behaviour

TestingTools is interactive: when a generated router output already exists, the Router utility asks for confirmation before replacing it. Declining leaves the existing output unchanged. This differs from AutomationTools, where generated router outputs are intended to be replaced automatically without an overwrite prompt.

### Backup Safety

The utility preserves the original router backup and creates separate decoded, edited and updated outputs.

Recommended precautions:

- Keep an unchanged copy of original backups.
- Confirm before overwriting existing generated output files or directories in the interactive TestingTools Router utility.
- Keep private credentials and router backups out of public repositories.
- Verify generated backups before restoring them.
- Retain a recovery method for physical routers.
- Match compatible hardware revisions and firmware where necessary.

**A successful local encryption and decryption round trip does not guarantee that a physical router will accept a generated configuration.**

---

## How It Works

Each tool is primarily defined by a constants module.

The constants module supplies:

- Configuration path.
- Documentation path.
- JSON keys.
- Validation rules.
- Secondary validation.
- Required user level.
- Dependencies.
- Status configuration.
- Plan configuration.
- Menu actions.
- Pre-phase pipelines.
- Execution pipelines.
- Pipeline states.

Reusable processing logic lives in modules such as:

```text
modules/
    display_utils.py
    file_utils.py
    network_utils.py
    email_utils.py
    router_utils.py
    state_machine_utils.py
```

The constants files connect these functions to the shared state-machine framework.

---

## ToolLoader Flow

ToolLoader manages the general execution sequence:

1. Load the selected tool constants.
2. Check dependencies.
3. Install missing dependencies if required.
4. Load the tool configuration.
5. Validate the configuration.
6. Perform secondary validation.
7. Compute status.
8. Display available actions.
9. Execute the selected pipeline.

A pipeline can contain:

```text
pre
 |
 v
plan
 |
 v
confirm
 |
 v
exec
```

Not every action requires every stage.

Read-only actions may skip planning and confirmation, while modifying actions can require user confirmation.

### Pre-Phase

The `pre` phase handles preparation and selection.

Examples include:

- Discovering interfaces.
- Discovering ARP neighbours.
- Finding PST files.
- Selecting email files.
- Selecting router model specifications.
- Selecting original router backups.
- Selecting extracted or edited configurations.

A typical pipeline entry:

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

The result becomes available through:

```python
ctx.get("pst_files", [])
```

### Exec-Phase

The `exec` phase performs the requested action.

Examples include:

- Scanning ports.
- Reading PST metadata.
- Converting PST files.
- Extracting email attachments.
- Decrypting router backups.
- Saving and extracting router archives.
- Viewing and editing configuration fields.
- Rebuilding and encrypting router backups.

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

## Shared Pipeline Context

Pipeline resolver functions use three arguments:

```text
job
meta
ctx
```

- `job` provides the current job where required.
- `meta` contains the loaded tool configuration.
- `ctx` contains results from earlier pipeline steps.

For example:

```python
lambda job, meta, ctx: meta[LOCATIONS_KEY][SOURCE_DIR]
```

reads a configured location.

Whereas:

```python
lambda job, meta, ctx: ctx.get("selected_pst")
```

reads a previously selected value.

Sensitive passwords should remain inside the relevant utility functions rather than being stored in the shared pipeline context.

---

## Status System

Each tool can provide a status function through `STATUS_FN_CONFIG`.

Example:

```python
STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": get_directory_status,
    "args": [
        lambda job, meta, ctx: meta[LOCATIONS_KEY][SOURCE_DIR],
    ],
    "id_field": "location",
    "active_rule": {
        "field": "state",
        "equals": "data_present"
    },
}
```

ToolLoader uses this to display whether the configured location contains data.

---

## Configuration Validation

Each tool can define primary validation rules:

```python
VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        LOCATIONS_KEY: dict,
    },
}
```

Secondary validation can check nested configuration values:

```python
SECONDARY_VALIDATION: Dict[str, Any] = {
    LOCATIONS_KEY: {
        "required_job_fields": {
            SOURCE_DIR: str,
            DEST_DIR: str,
        },
        "allow_empty": False,
    },
}
```

This verifies configuration structure before actions execute.

---

## Configuration Documentation

Each tool can provide a JSON documentation file.

For example:

```text
doc/EmailDoc.json
```

Documentation can describe:

- Required fields.
- Editable values.
- Example configurations.
- Field descriptions.

The shared `display_config_doc()` helper displays configuration documentation in the terminal.

The Router utility additionally uses `display_readme()` to display the model specification guide from its configured location.

---

## Example Email Configuration

```json
{
    "locations": {
        "source_dir": "email/email_source",
        "dest_dir": "email/email_dest"
    }
}
```

## Example Email Actions

```text
Select an Email operation:

1. View PST summary
2. List emails
3. View email
4. Convert PST to mbox
5. Convert PST to EML
6. Extract contacts
7. Extract attachments
8. Show config help
9. Cancel
```

---

## Generic Helper Design

Where possible, helper functions are generic.

For example:

```python
get_files_by_extension(directory, extension)
```

This function is not tied to PST or router files.

Email can use:

```python
".pst"
```

Router can use:

```python
[".cfg", ".bin"]
```

The same helper accepts a single extension or a collection of extensions.

Reusable file operations remain in `file_utils.py`.

Tool-specific functions remain in their relevant modules.

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

ToolLoader does not need router-specific encryption, email parsing or network scanning logic.

---

## Running TestingTools

From the project directory:

```bash
python3 ToolLoader.py
```

The loader displays available tools and executes the selected utility through the shared state machine.

---

## Project Structure

A simplified source-code structure:

```text
TestingTools/
├── ToolLoader.py
├── config/
│   ├── WiFiConfig.json
│   ├── NetworkConfig.json
│   ├── EmailConfig.json
│   └── RouterConfig.json
├── constants/
│   ├── WiFiConstants.py
│   ├── NetworkConstants.py
│   ├── EmailConstants.py
│   └── RouterConstants.py
├── doc/
│   ├── WiFiDoc.json
│   ├── NetworkDoc.json
│   ├── EmailDoc.json
│   └── RouterDoc.json
└── modules/
    ├── display_utils.py
    ├── file_utils.py
    ├── network_utils.py
    ├── email_utils.py
    └── state_machine_utils.py
```

Router models, documentation, password files and generated configurations are located using the paths in `RouterConfig.json`.

They do not need to reside in fixed source-code directories.

---

## Git Ignore

Typical ignored files include:

```gitignore
# Python cache
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
.env/
```

Runtime files, passwords and private configurations stored inside the repository should also be ignored using paths that match their actual locations.

Files stored outside the repository are not tracked by that repository.

Avoid committing actual router credentials, private backups or generated configurations unless publication is intentional.

---

## Design Philosophy

TestingTools uses reusable components rather than independent scripts for every operation.

A typical tool consists of:

```text
Configuration
      +
Constants
      +
Reusable Module Functions
      +
Shared ToolLoader
```

This maintains a common workflow for:

- Dependency checks.
- Configuration validation.
- Status display.
- Menu selection.
- Preparation.
- Planning.
- Confirmation.
- Execution.
- Finalisation.

The Router utility follows the same architecture:

```text
RouterConfig.json
        +
RouterConstants.py
        +
Router Model JSON
        +
router_utils.py
        +
Shared ToolLoader
```

Router models remain data-driven, configuration locations remain configurable, and ToolLoader remains independent of the processing details of individual tools.
