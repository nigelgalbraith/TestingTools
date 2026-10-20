
# TestingTools

TestingTools is a collection of terminal-based utilities built around a shared, reusable `ToolLoader` and a pipeline-style state machine.

The project focuses on modularity, reusable helper functions, predictable execution, and separation of concerns. Tool-specific processing remains in dedicated modules, while shared functionality handles configuration, validation, file operations, display, and pipeline execution.

## Design Goals

- **Modular tools:** Keep each utility focused on its own responsibilities.
- **Reusable helpers:** Share common functionality instead of duplicating implementations.
- **Predictable execution:** Use a consistent pre → plan → confirm → exec workflow where appropriate.
- **Separation of concerns:** Keep processing logic separate from shared display, file, and pipeline helpers.
- **Configuration-driven behaviour:** Define tool behaviour and locations through JSON configuration and constants.
- **Extensibility:** Add new tools and supported formats without unnecessarily modifying `ToolLoader`.

## Available Tools

### WiFiScanner

A wireless network utility that can:

- List wireless interfaces.
- Scan for nearby wireless networks.
- Display detailed information about selected networks.
- Show Basic Service Set (BSS) details.
- Report wireless interface status.

#### Files

- **Config:** `config/WiFiConfig.json`
- **Constants:** `constants/WiFiConstants.py`
- **Documentation:** `doc/WiFiDoc.json`

#### Troubleshooting

Some wireless adapters may intermittently return `Device or resource busy (-16)` when running `iw scan`. This is generally a transient driver, supplicant, or NetworkManager contention issue. Retrying the scan may resolve it.

### NetworkScanner

A network utility that can:

- List network interfaces.
- Analyse a selected interface.
- Show connected interfaces.
- Display ARP neighbours using `ip neigh`.
- Run TCP port scans against selected or manually entered hosts.
- Report interface connection status.

#### Files

- **Config:** `config/NetworkConfig.json`
- **Constants:** `constants/NetworkConstants.py`
- **Documentation:** `doc/NetworkDoc.json`

### Email

An email and Outlook PST utility built around `pst-utils`.

It supports:

- Viewing PST summaries.
- Listing emails contained in a PST.
- Selecting and viewing individual emails.
- Converting PST files to mbox.
- Converting PST files into separate EML files.
- Extracting contacts.
- Extracting attachments.
- Displaying email configuration help.

The source directory can contain multiple PST files. The utility presents a selection menu so the user can choose which file to process.

#### Files

- **Config:** `config/EmailConfig.json`
- **Constants:** `constants/EmailConstants.py`
- **Documentation:** `doc/EmailDoc.json`

#### Email Directory Layout

Source and destination directories are configured through the Email utility.

A typical layout is:

```text
email/
├── email_source/
└── email_dest/
```

Each PST receives its own output directory to keep generated files separate.

For example:

```text
email_source/
└── testPST.pst

email_dest/
└── testPST/
    ├── mbox/
    ├── eml/
    ├── contacts/
    └── attachments/
```

#### Dependencies

The Email utility uses `pst-utils`, including the `readpst` command, for PST conversion and extraction.

Runtime email data may contain private information and should generally be excluded from Git.

### Router

A configuration utility for decoding, inspecting, editing, rebuilding, and re-encoding router backup files.

It supports:

- Selecting a router model specification.
- Selecting an original configuration backup.
- Selecting the appropriate template router password file.
- Decoding encrypted router backups.
- Saving decoded archives.
- Extracting configuration files.
- Viewing and editing supported configuration fields.
- Rebuilding configuration archives.
- Encrypting updated backups for target routers.
- Validating generated backups.
- Displaying configuration and model specification help.

#### Files

- **Config:** `config/RouterConfig.json`
- **Constants:** `constants/RouterConstants.py`
- **Documentation:** `doc/RouterDoc.json`
- **Processing module:** `modules/router_utils.py`

#### JSON-Driven Router Support

Router models are defined through JSON specifications rather than separate Python implementations for each model.

Each model specification can define:

- Router model, firmware, and hardware details.
- Encryption algorithm.
- Encoded payload format.
- Salt handling.
- Password requirements and hashing.
- Encryption key derivation.
- Backup headers, checksums, and trailers.
- Archive format and compression.
- Configuration file format.
- Editable configuration keys.

The router model identifier is used to select the appropriate specification; it does not determine processing logic directly.

If a new router uses mechanisms already supported by `router_utils.py`, adding support should generally require only another model JSON file. If a new mechanism is needed, implement a reusable helper in Python rather than adding router-specific logic to `ToolLoader`.

Model specifications are loaded from `Locations.model_specs_path`.

#### Router Directory Configuration

All router paths are defined in `config/RouterConfig.json` under `Locations`.

| Configuration key | Purpose |
|---|---|
| `model_specs_path` | Router model JSON specifications |
| `model_specs_readme_path` | Model specification documentation |
| `template_router_password_path` | Template router password text files |
| `config_path` | Original encrypted router templates |
| `decoded_config_path` | Decoded archives and extracted configurations |
| `edited_config_path` | Edited router configurations |
| `updated_config_path` | Re-encoded router backups |

These paths are configurable. Router processing does not depend on hardcoded data directories, so locations can be changed through `RouterConfig.json` without modifying the utility code.

#### Supported Backup Extensions

Router backup selection supports the following extensions:

```python
CONFIG_EXTENSION = [".cfg", ".bin"]
```

This setting controls file selection only. A file extension does not determine the backup's internal encryption or archive format.

For example, a `.bin` file may use a completely different structure from another `.bin` file. The selected model JSON determines how the backup is processed.

#### Router Workflow

The typical workflow is:

1. Select the router model.
2. Select the original backup template.
3. Select the corresponding template password file.
4. Decode the configuration.
5. Save the decoded archive.
6. Extract the configuration files.
7. View or edit supported configuration fields.
8. Save the edited configuration.
9. Select the original backup template and its password file again for encoding.
10. Enter the target router's factory Wi-Fi password.
11. Rebuild the configuration archive.
12. Encrypt the backup for the target router.
13. Decrypt the generated backup for local verification.
14. Save the updated configuration.

The generic router functions perform the processing using the selected model specification. `ToolLoader` coordinates the workflow through the shared pipeline.

#### Router Output Naming

The utility uses consistent filename suffixes to distinguish each processing stage.

Given an original backup named `SmartModem_backup.cfg`:

| Stage | Output |
|---|---|
| Original | `SmartModem_backup.cfg` |
| Decoded archive | `SmartModem_backup-decoded.tar.gz` |
| Extracted directory | `SmartModem_backup-decoded/` |
| Edited directory | `OfficeRouter-edited/` |
| Encoded backup | `OfficeRouter-encoded.cfg` |

When editing, the user can enter a new configuration name, such as `OfficeRouter`.

If no name is entered, the original template filename is retained:

```text
SmartModem_backup-edited/
SmartModem_backup-encoded.cfg
```

The original template name is retained during decoding. A new configuration name, when provided, is used for editing and encoding.

The original router backup remains unchanged.

#### Router Password Handling

Some router backups require the factory Wi-Fi password of the physical router for encryption and decryption.

The model specification determines whether a password is required:

```json
"password_required": true
```

The utility uses two distinct passwords.

##### 1. Template Router Password

A master template originates from a physical router. Its password is stored in a plain-text `.txt` file under the directory configured by `Locations.template_router_password_path`.

Each password file contains only the password, without JSON formatting or quotation marks.

During decoding, the utility:

1. Lists the available password files.
2. Prompts the user to select the matching template password.
3. Reads the selected file.
4. Uses the password to decrypt the original backup.

Encoding also requires selecting the appropriate template password file to decrypt the original backup before rebuilding the archive.

The template password is not stored in the model specification JSON.

##### 2. Target Router Password

When creating a configuration for another router, the utility prompts for that router's factory Wi-Fi password using `getpass`, which hides the input.

The password is used to encrypt the updated configuration. The utility then decrypts the generated backup for local verification.

The target password is not stored in the model JSON or shared pipeline context.

Each target router may have a different factory password, even when the router model is identical. Password hashing and key derivation are determined by the selected model specification.

#### Editable Router Fields

The `config_fields` section of each model JSON determines which settings appear in the View and Edit menus.

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

The `file` entry identifies the configuration file inside the extracted archive. The remaining entries map readable field names to the actual configuration keys.

Additional fields can be made editable by adding mappings to the JSON, provided the configuration parser supports their format.

#### Router Model Documentation

The router model specification README explains how to create specifications for additional router models.

Its location is configured through:

```python
Locations.model_specs_readme_path
```

The View Model Specifications Help action displays the configured README in the terminal using the shared `display_readme()` helper.

#### Overwrite Behaviour

TestingTools is interactive. If a generated router output already exists, the utility asks for confirmation before replacing it.

Declining the prompt leaves the existing output unchanged.

This differs from AutomationTools, where generated router outputs are intended to be replaced automatically without an overwrite prompt.

#### Router Backup Safety

The utility preserves the original router backup and creates separate decoded, edited, and updated outputs.

Recommended precautions:

- Keep an unchanged copy of original backups.
- Confirm overwrite prompts carefully when replacing generated files or directories.
- Keep private credentials, password files, and router backups out of public repositories.
- Verify generated backups before restoring them.
- Retain a recovery method for physical routers.
- Confirm hardware revision and firmware compatibility where necessary.

A successful local encryption and decryption round trip does not guarantee that a physical router will accept the generated configuration.

## Architecture

Each tool is primarily defined by its constants module, which connects tool-specific configuration to the shared state-machine framework.

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

### Tool Constants

The constants module supplies the information required to configure and execute a tool, including:

- Configuration and documentation paths.
- JSON keys and validation rules.
- Secondary validation.
- Required user level.
- Dependency definitions.
- Status configuration.
- Plan configuration.
- Menu actions.
- Pre-phase pipelines.
- Execution pipelines.
- Pipeline states.

This keeps tool-specific workflow definitions separate from the shared execution engine.

### Shared Modules

Reusable processing and support functions live in modules such as:

```text
modules/
├── display_utils.py
├── file_utils.py
├── network_utils.py
├── email_utils.py
├── router_utils.py
└── state_machine_utils.py
```

Responsibilities are divided by function:

| Module | Responsibility |
|---|---|
| `display_utils.py` | Shared terminal display and documentation helpers |
| `file_utils.py` | Generic file operations and directory status |
| `network_utils.py` | Network interface, neighbour, and scanning operations |
| `email_utils.py` | PST parsing, conversion, and extraction |
| `router_utils.py` | Router model loading, backup processing, and configuration editing |
| `state_machine_utils.py` | Shared state-machine and pipeline execution helpers |
