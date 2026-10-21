
# TestingTools

TestingTools is a collection of interactive, terminal-based utilities built around a shared `ToolLoader` and a configurable pipeline-style state machine.

The project separates tool-specific operations from common functionality such as configuration loading, validation, dependency checks, file handling, terminal displays, and workflow execution.

## Design Goals

- **Modularity:** Keep individual utilities focused on their own responsibilities.
- **Reusability:** Share common functions rather than duplicating processing logic.
- **Consistency:** Use a common execution framework for menu actions and workflows.
- **Separation of concerns:** Keep utility functions separate from pipeline definitions.
- **Configuration-driven behaviour:** Define settings, paths, validation rules, and supported models through configuration files.
- **Extensibility:** Add new utilities and operations without rewriting the shared loader.

## Available Tools

The following utilities are registered in `ToolLoader.py`:

| Utility | Purpose |
|---|---|
| WiFi | Scan and analyse wireless networks |
| Network | Inspect network interfaces, neighbours, and ports |
| Diagnostic | Inspect system hardware and operating conditions |
| HardDrive | Inspect disks, filesystems, and drive health |
| Data Recovery | Create recovery images and launch recovery tools |
| Windows Inspection | Inspect offline Windows installations |
| File Integrity | Generate, compare, and verify checksums |
| Email | Browse, convert, and extract Outlook PST data |
| Router | Decode, edit, migrate, and encode router configurations |
| Function | Analyse and inspect functions in Python modules |

Each utility has its own constants module, configuration file, and documentation file.

## WiFi Utility

The WiFi utility provides wireless network scanning and analysis.

### Features

- Scan for nearby wireless networks.
- Analyse a selected wireless network.
- Display network information obtained from wireless scanning tools.
- Show configuration help.

### Configuration

**Configuration file:** `config/WiFiConfig.json`

The configuration defines wireless scan settings and patterns used to extract information from scan results.

Configured fields include:

- Scan timeout.
- Network summary columns.
- Regular-expression patterns for wireless information.

### Files

- `constants/WiFiConstants.py`
- `modules/wifi_utils.py`
- `config/WiFiConfig.json`
- `doc/WiFiDoc.json`

### Troubleshooting

Some wireless adapters may report:

```text
Device or resource busy (-16)
```

This can occur when the wireless driver, NetworkManager, or another process is using the interface.

Retrying the scan may resolve the issue.

## Network Utility

The Network utility provides network interface analysis, neighbour discovery, and TCP port scanning.

### Features

- Analyse a selected network interface.
- Display neighbouring devices using network neighbour information.
- Scan selected hosts for open TCP ports.
- Display configuration help.

### Configuration

**Configuration file:** `config/NetworkConfig.json`

The configuration contains:

- General scan timeout.
- TCP ports to scan.
- Connection timeout.
- Worker count for concurrent port scanning.

The default configured TCP ports are:

```text
22, 80, 443, 445, 3389, 5985, 5986
```

These values can be changed through the configuration file.

### Files

- `constants/NetworkConstants.py`
- `modules/network_utils.py`
- `modules/portscan_utils.py`
- `config/NetworkConfig.json`
- `doc/NetworkDoc.json`

## Diagnostic Utility

The Diagnostic utility provides system information and hardware diagnostics.

### Features

- Display a system summary.
- Inspect CPU information.
- Check memory status.
- Read available temperature information.
- Inspect battery health.
- List hardware devices.
- Check system errors.
- Generate a full diagnostic report.
- Display configuration help.

### Configuration

**Configuration file:** `config/DiagnosticConfig.json`

Configurable warning thresholds include:

| Setting | Default |
|---|---|
| `temperature_warning` | 80 |
| `memory_usage_warning` | 90 |

### Files

- `constants/DiagnosticConstants.py`
- `modules/diagnostic_utils.py`
- `config/DiagnosticConfig.json`
- `doc/DiagnosticDoc.json`

Hardware information and available diagnostic results depend on the operating system, installed utilities, and permissions.

## HardDrive Utility

The HardDrive utility provides disk inspection, filesystem information, SMART diagnostics, and drive testing.

### Features

- List detected drives.
- Display disk and partition information.
- Inspect filesystem usage.
- Detect Windows installations.
- Check encryption and BitLocker information.
- Display drive information.
- Check SMART health.
- Display SMART attributes.
- Inspect drive temperature and wear.
- Display SMART self-test history.
- Run short SMART tests.
- Run long SMART tests.
- Run read benchmarks.
- Generate a full hard drive diagnostic.
- Display configuration help.

### Configuration

**Configuration file:** `config/HardDriveConfig.json`

| Setting | Default |
|---|---|
| `temperature_warning` | 60 |
| `wear_warning` | 80 |
| `benchmark_size_mb` | 512 |
| `disk_usage_warning` | 90 |

### Files

- `constants/HardDriveConstants.py`
- `modules/harddrive_utils.py`
- `config/HardDriveConfig.json`
- `doc/HardDriveDoc.json`

### Safety

Drive tests and diagnostic commands should be used carefully, particularly on failing storage devices.

A drive that is already experiencing hardware failure may deteriorate further under sustained testing.

For important data, prioritise recovery imaging before performing unnecessary diagnostic workloads.

## Data Recovery Utility

The Data Recovery utility provides disk imaging and access to recovery applications.

### Features

- List available drives.
- Create recovery images.
- Resume recovery imaging.
- Launch TestDisk.
- Launch PhotoRec.
- Restore recovery output permissions.
- Display configuration help.

### Configuration

**Configuration file:** `config/DataRecoveryConfig.json`

The configuration includes:

| Setting | Purpose |
|---|---|
| `destination` | Directory for recovery output |
| `log_destination` | Directory for recovery logs |
| `ddrescue_retries` | Configured recovery retry count |

The default recovery directory is:

```text
~/Documents/TestingToolsData/recovery
```

The default log directory is:

```text
~/Documents/TestingToolsData/recovery/log
```

### Files

- `constants/DataRecoveryConstants.py`
- `modules/data_recovery_utils.py`
- `config/DataRecoveryConfig.json`
- `doc/DataRecoveryDoc.json`

### Recovery Precautions

- Avoid writing recovered data back to the failing source drive.
- Prefer imaging damaged drives before attempting filesystem repairs.
- Verify source and destination devices before starting recovery.
- Preserve recovery logs when resuming interrupted operations.
- Use a separate destination with sufficient available storage.

## Windows Inspection Utility

The Windows Inspection utility examines Windows installations accessible from the Linux environment.

### Features

- Detect Windows installations.
- Display Windows installation information.
- Inspect Windows users.
- Inspect registry hives.
- Display startup entries.
- Inspect services.
- List installed software.
- Display configuration help.

### Configuration

**Configuration file:** `config/WindowsInspectionConfig.json`

The configuration defines a `mount_root` directory used by the inspection workflow.

### Files

- `constants/WindowsInspectionConstants.py`
- `modules/windows_inspection_utils.py`
- `config/WindowsInspectionConfig.json`
- `doc/WindowsInspectionDoc.json`

### Notes

Inspection results depend on the accessibility of the Windows filesystem and the availability of relevant registry and system files.

Encrypted, damaged, or inaccessible installations may not provide complete information.

## File Integrity Utility

The File Integrity utility provides hashing, file comparison, duplicate detection, and checksum manifest operations.

### Features

- Calculate a file hash.
- Verify a file against an expected hash.
- Hash a directory.
- Compare files.
- Find duplicate files.
- Create checksum manifests.
- Verify checksum manifests.
- Restore manifest permissions.
- Display configuration help.

### Configuration

**Configuration file:** `config/FileIntegrityConfig.json`

The default configuration includes:

```json
{
  "general": {
    "algorithm": "sha256",
    "target_dir": "~/Documents/TestingToolsData/integrity/targets",
    "manifest_dir": "~/Documents/TestingToolsData/integrity/manifests"
  }
}
```

### Files

- `constants/FileIntegrityConstants.py`
- `modules/file_integrity_utils.py`
- `config/FileIntegrityConfig.json`
- `doc/FileIntegrityDoc.json`

### Notes

Checksums are useful for detecting file changes and verifying integrity.

A matching checksum provides evidence that the compared content is identical under the selected hashing algorithm. It does not independently establish that a file is safe or trustworthy.

## Email Utility

The Email utility provides Outlook PST browsing, conversion, and extraction using `pst-utils` and Python email-processing functions.

### Features

- View PST summaries.
- List emails in a PST.
- Select and view individual emails.
- Convert PST files to MBOX.
- Convert PST files to separate EML files.
- Extract Outlook contacts as vCards.
- Extract calendar appointments as iCalendar files.
- Extract email attachments.
- Display configuration help.

### Files

- `constants/EmailConstants.py`
- `modules/email_utils.py`
- `config/EmailConfig.json`
- `doc/EmailDoc.json`

### Dependencies

The utility uses `pst-utils`, including the `readpst` command.

On Debian-based systems, the package can be installed with:

```bash
sudo apt install pst-utils
```

### Configuration

**Configuration file:** `config/EmailConfig.json`

```json
{
  "locations": {
    "pst_dir": "~/Documents/TestingToolsData/email/pst",
    "mbox_dir": "~/Documents/TestingToolsData/email/mbox",
    "eml_dir": "~/Documents/TestingToolsData/email/eml",
    "contacts_dir": "~/Documents/TestingToolsData/email/contacts",
    "calendars_dir": "~/Documents/TestingToolsData/email/calendars",
    "attachments_dir": "~/Documents/TestingToolsData/email/attachments",
    "work_dir": "/tmp/toolloader_email_view"
  }
}
```

### Directory Configuration

| Configuration key | Purpose |
|---|---|
| `pst_dir` | Source PST files |
| `mbox_dir` | MBOX conversion output |
| `eml_dir` | EML conversion output |
| `contacts_dir` | Extracted contact files |
| `calendars_dir` | Extracted calendar appointments |
| `attachments_dir` | Extracted email attachments |
| `work_dir` | Temporary PST email-viewing workspace |

### Directory Layout

A typical directory layout is:

```text
email/
├── pst/
│   ├── sample.pst
│   └── unittest.pst
├── mbox/
├── eml/
├── contacts/
├── calendars/
└── attachments/
```

The utility lists PST files from the configured `pst_dir` and prompts the user to select a file.

Each conversion or extraction operation creates a directory named after the selected PST file, without its `.pst` extension.

For example, processing `unittest.pst` may produce:

```text
email/
├── pst/
│   └── unittest.pst
├── mbox/
│   └── unittest/
├── eml/
│   └── unittest/
├── contacts/
│   └── unittest/
├── calendars/
│   └── unittest/
└── attachments/
    └── unittest/
```

Each operation uses its own configured destination directory.

### PST Summaries

The View PST summary operation reads a selected PST and displays summary information about its contents.

### Email Listing and Viewing

The utility supports selecting and viewing emails contained in PST files.

Temporary extracted email data is used during viewing operations.

The `work_dir` configuration provides the designated temporary workspace for the email-viewing workflow.

### MBOX Conversion

The Convert PST to mbox operation converts PST email content into MBOX format.

Output is written beneath the configured `mbox_dir` in a directory named after the selected PST.

### EML Conversion

The Convert PST to EML operation extracts emails into individual EML files.

Output is written beneath the configured `eml_dir` in a directory named after the selected PST.

### Contact Extraction

The Extract contacts operation uses `readpst` with contact filtering and vCard output options.

The command options are:

```text
-e -t c -cv
```

Where:

- `-e` enables separate output files with extensions.
- `-t c` selects contact items.
- `-cv` selects vCard contact output.

Extracted `.vcf` files are collected into the PST-named contacts directory.

The utility uses the generic `_flatten_extracted_files()` helper to move vCards from nested directories into the output root.

Duplicate filenames are renamed with numeric suffixes to prevent collisions.

Empty subdirectories are removed.

Not every PST contains Outlook contact records. A successful `readpst` execution does not necessarily mean that contacts were found.

### Calendar Extraction

The Extract calendars operation uses `readpst` to extract appointment records.

The command options are:

```text
-e -t a
```

Where:

- `-e` enables separate output files with extensions.
- `-t a` selects appointment items.

Calendar appointments are exported as iCalendar (`.ics`) files when supported by the PST contents and `readpst`.

The generic `_flatten_extracted_files()` helper moves extracted `.ics` files into the PST-named calendars directory.

Empty subdirectories are removed.

### Attachment Extraction

The Extract attachments operation processes emails from the selected PST and saves extracted attachments.

Output is written beneath the configured `attachments_dir` in a directory named after the PST.

Attachment extraction is handled by Python email-processing logic after obtaining temporary email files from the PST.

### Generic File Flattening

Contact and calendar extraction share the helper:

```python
_flatten_extracted_files(output_dir, extension)
```

The helper:

1. Searches the extraction output recursively.
2. Identifies files matching the requested extension.
3. Moves matching files into the PST-named output directory.
4. Renames files when duplicate filenames exist.
5. Removes empty subdirectories.
6. Returns the number of matching extracted files.

Contacts use:

```python
_flatten_extracted_files(output_dir, ".vcf")
```

Calendars use:

```python
_flatten_extracted_files(output_dir, ".ics")
```

This avoids maintaining separate flattening implementations for each extraction format.

Nonmatching files are not moved or deleted by the helper.

### Overwrite Behaviour

The email utility uses `_get_pst_output_dir()` to prepare conversion and extraction output directories.

If the PST-named output directory already exists, the utility asks for confirmation before deleting and recreating it.

Declining the overwrite prompt cancels the operation and preserves the existing directory.

The utility does not automatically create numbered PST output directories such as `unittest-2`.

### Email Data Privacy

PST files may contain:

- Personal emails.
- Contact details.
- Calendar appointments.
- Attachments.
- Private business information.

Source PST files and extracted output should generally be kept outside public Git repositories.

## Router Utility

The Router utility provides configuration backup processing, editing, encoding, and migration workflows.

Router-specific processing is implemented through reusable functions and JSON model specifications.

### Features

- Decode router configurations.
- View decoded configurations.
- Edit supported configuration fields.
- View edited configurations.
- Encode updated configurations.
- Run the complete same-model modification workflow.
- Decode configurations for migration.
- Edit migration configurations.
- View edited migration configurations.
- Prepare destination configurations.
- Convert migration configurations.
- Encode migration configurations.
- Run the complete different-model migration workflow.
- Display model specification documentation.
- Display configuration help.

### Files

- `constants/RouterConstants.py`
- `modules/router_utils.py`
- `config/RouterConfig.json`
- `doc/RouterDoc.json`
- `routers/model_specs/ModelSpecsReadMe.md`

### Dependencies

The Router utility declares `openssl` as a dependency.

Supported backup formats and processing requirements depend on the selected router model specification.

### Router Configuration

**Configuration file:** `config/RouterConfig.json`

The configuration is organised into two top-level sections:

```json
{
  "Common Locations": {
    "model_specs_readme_path": "routers/model_specs/ModelSpecsReadMe.md"
  },
  "Routers": {
    "Router Model Name": {
      "specs": "routers/model_specs/example-spec.json",
      "password": "~/Documents/TestingToolsData/routers/templatePasswords/example-password.txt",
      "template": "~/Documents/TestingToolsData/routers/templates/example-template.cfg",
      "template_decoded": "~/Documents/TestingToolsData/routers/decoded/example-decoded.tar.gz",
      "template_decoded_dir": "~/Documents/TestingToolsData/routers/decoded/example-decoded",
      "template_edited": "~/Documents/TestingToolsData/routers/edited/example-edited.tar.gz",
      "template_edited_dir": "~/Documents/TestingToolsData/routers/edited/example-edited",
      "template_encoded": "~/Documents/TestingToolsData/routers/encoded/example-encoded.cfg",
      "original": "~/Documents/TestingToolsData/routers/original/example-original.cfg",
      "migration_decoded": "~/Documents/TestingToolsData/routers/migration/decoded/example-decoded.tar.gz",
      "migration_decoded_dir": "~/Documents/TestingToolsData/routers/migration/decoded/example-decoded",
      "migration_edited": "~/Documents/TestingToolsData/routers/migration/edited/example-edited.tar.gz",
      "migration_edited_dir": "~/Documents/TestingToolsData/routers/migration/edited/example-edited",
      "migration_converted": "~/Documents/TestingToolsData/routers/migration/converted/example-converted.tar.gz",
      "migration_converted_dir": "~/Documents/TestingToolsData/routers/migration/converted/example-converted",
      "migration_encoded": "~/Documents/TestingToolsData/routers/migration/encoded/example-encoded.cfg"
    }
  }
}
```

### Router Path Keys

Each router model defines the following configuration keys:

| Key | Purpose |
|---|---|
| `specs` | Router model specification JSON |
| `password` | Template router password file |
| `template` | Original template backup |
| `template_decoded` | Decoded template archive |
| `template_decoded_dir` | Extracted decoded template directory |
| `template_edited` | Edited template archive |
| `template_edited_dir` | Extracted edited template directory |
| `template_encoded` | Encoded template output |
| `original` | Original router configuration path |
| `migration_decoded` | Decoded migration archive |
| `migration_decoded_dir` | Extracted migration directory |
| `migration_edited` | Edited migration archive |
| `migration_edited_dir` | Extracted edited migration directory |
| `migration_converted` | Converted migration archive |
| `migration_converted_dir` | Extracted converted migration directory |
| `migration_encoded` | Encoded migration output |

The configured paths determine where router processing reads and writes files.

### Configured Router Models

The supplied configuration includes entries for:

- Spark SmartModem VRV9517.
- Spark SmartModem VRV951 B.

Each entry references its own model specification and associated paths.

The presence of a model entry does not guarantee compatibility with every firmware or hardware revision.

### JSON-Driven Router Processing

Router specifications define the properties needed to process a supported backup format.

Specification fields include:

- Model.
- Firmware.
- Hardware.
- Encryption.
- Encoding.
- Salt handling.
- Password requirements.
- Password hashing.
- Key derivation.
- Editable configuration fields.

This separates model-specific settings from the shared router processing functions.

New router support may be added through additional model specifications when the required processing mechanisms are already supported.

New encryption, archive, or configuration formats may require changes to `router_utils.py`.

### Router Backup Extensions

Router backup selection supports:

```python
CONFIG_EXTENSION = [".cfg", ".bin"]
```

These extensions control which files can be selected.

They do not determine the internal backup format.

The model specification determines how the selected backup is interpreted.

### Same-Model Router Workflow

The same-model workflow provides operations for:

1. Decoding a configuration.
2. Viewing decoded configuration fields.
3. Editing supported fields.
4. Viewing edited configuration fields.
5. Encoding the updated configuration.

The menu also provides:

```text
Modify Router - Same Model (Run All)
```

This runs the associated same-model workflow through the configured pipeline.

### Different-Model Migration Workflow

The Router utility also contains a separate migration workflow.

The available operations are:

1. Migrate a Config.
2. Edit Migration Config.
3. View Edited Migration Config.
4. Prepare Destination Config.
5. Convert Migration Config.
6. Encode Migration Config.

The menu also provides:

```text
Modify Router - Different Model (Run All)
```

This executes the configured migration workflow.

Migration requires compatible source and destination model specifications and supported conversion logic.

### Router Password Handling

Router backup processing may require a password depending on the selected model specification.

Template password files are configured per router model using the `password` key.

These files are separate from the router model JSON.

Router password handling, hashing, and key derivation are controlled by the processing logic and selected model specification.

Password files and router backups should not be committed to public repositories.

### Editable Router Fields

The `config_fields` section of a model specification maps readable field names to configuration keys.

For example:

```json
{
  "config_fields": {
    "file": "config/.glbcfg",
    "wifi_2g_ssid": "ARC_WLAN_24G_SSID_0_ESSID",
    "wifi_2g_password": "ARC_WLAN_24G_SSID_0_WPA_Passphrase",
    "wifi_5g_ssid": "ARC_WLAN_5G_SSID_0_ESSID",
    "wifi_5g_password": "ARC_WLAN_5G_SSID_0_WPA_Passphrase"
  }
}
```

The `file` entry identifies the configuration file to process.

The other entries map editable field names to keys in that configuration.

Only fields supported by the configuration parser and selected specification can be edited.

### Router Model Documentation

The model specification guide is stored at:

```text
routers/model_specs/ModelSpecsReadMe.md
```

Its location is configured by:

```text
Common Locations.model_specs_readme_path
```

The Router utility provides a menu option for displaying this documentation.

### Router Output Safety

Router processing uses separate paths for templates, decoded files, edited files, migration files, and encoded outputs.

Recommended precautions:

- Preserve original router backups.
- Keep router passwords private.
- Check firmware and hardware compatibility.
- Confirm source and destination models before migration.
- Inspect generated configuration values before applying them.
- Keep a recovery method available for physical routers.

Successful local processing does not guarantee that a physical router will accept a generated backup.

## Function Utility

The Function utility provides inspection and analysis of functions in Python modules.

### Features

- Analyse functions.
- Show functions.
- Display configuration help.

### Configuration

**Configuration file:** `config/FunctionsConfig.json`

The configuration defines:

- Python modules to inspect.
- The module directory.
- Directories used by the analysis workflow.

The configured module list includes reusable utilities such as:

- `email_utils.py`
- `file_utils.py`
- `display_utils.py`
- `network_utils.py`
- `function_utils.py`
- `router_utils.py` may be inspected when added to the configured module list.

The actual list is controlled by `FunctionsConfig.json`.

### Files

- `constants/FunctionConstants.py`
- `modules/function_utils.py`
- `config/FunctionsConfig.json`
- `doc/FunctionDoc.json`

## Architecture

TestingTools uses a shared loader and tool-specific constants to define execution behaviour.

The general structure is:

```text
JSON Configuration
        |
Tool Constants
        |
Pipeline Definitions
        |
Shared ToolLoader
        |
Reusable Module Functions
```

### ToolLoader

`ToolLoader.py` is the shared execution entry point.

It registers available utilities and loads their corresponding constants modules.

Its responsibilities include coordinating:

- Utility selection.
- Configuration loading.
- Validation.
- Dependency checks.
- Menu actions.
- Pipeline execution.
- State transitions.
- Execution results.

Tool-specific operations are implemented in their respective modules rather than directly inside `ToolLoader`.

### Tool Constants

Each utility has a constants module under `constants/`.

These modules define the integration between configuration data and the shared execution framework.

Typical definitions include:

- Configuration path.
- Documentation path.
- JSON keys.
- Primary validation.
- Secondary validation.
- Required user level.
- Dependency list.
- Status checks.
- Menu actions.
- Pre-phase operations.
- Execution-phase operations.
- Pipeline states.

The exact definitions vary by utility.

### Pipeline Execution

Utilities use configured pipeline states to execute operations.

Depending on the action, a workflow may involve:

```text
Select Action
     |
Pre-Execution
     |
Prepare Plan
     |
Confirmation
     |
Execution
     |
Result
     |
Return to Menu
```

Some actions bypass plan preparation or confirmation.

These behaviours are controlled by the action definitions rather than being mandatory for every operation.

### Shared Modules

Reusable functionality is organised under `modules/`.

Important modules include:

| Module | Responsibility |
|---|---|
| `data_recovery_utils.py` | Recovery imaging and recovery-tool operations |
| `diagnostic_utils.py` | System diagnostics |
| `display_utils.py` | Terminal displays, prompts, and documentation |
| `email_utils.py` | PST browsing, conversion, and extraction |
| `file_integrity_utils.py` | Hashing and integrity verification |
| `file_utils.py` | Shared file and directory operations |
| `function_utils.py` | Python function inspection |
| `harddrive_utils.py` | Drive information and SMART operations |
| `json_utils.py` | JSON-related helpers |
| `network_utils.py` | Network inspection |
| `package_utils.py` | Package and dependency helpers |
| `portscan_utils.py` | Port scanning |
| `router_utils.py` | Router configuration processing |
| `state_machine_utils.py` | Shared pipeline and state-machine helpers |
| `system_utils.py` | System-level support functions |
| `wifi_utils.py` | Wireless network operations |
| `windows_inspection_utils.py` | Windows installation inspection |

### Project Structure

The main project layout is:

```text
TestingTools/
├── ToolLoader.py
├── README.md
├── config/
│   ├── DataRecoveryConfig.json
│   ├── DiagnosticConfig.json
│   ├── EmailConfig.json
│   ├── FileIntegrityConfig.json
│   ├── FunctionsConfig.json
│   ├── HardDriveConfig.json
│   ├── NetworkConfig.json
│   ├── RouterConfig.json
│   ├── WiFiConfig.json
│   └── WindowsInspectionConfig.json
├── constants/
│   ├── DataRecoveryConstants.py
│   ├── DiagnosticConstants.py
│   ├── EmailConstants.py
│   ├── FileIntegrityConstants.py
│   ├── FunctionConstants.py
│   ├── HardDriveConstants.py
│   ├── NetworkConstants.py
│   ├── RouterConstants.py
│   ├── WiFiConstants.py
│   └── WindowsInspectionConstants.py
├── doc/
├── modules/
└── routers/
    └── model_specs/
```

### Configuration and Documentation

Each utility generally uses:

```text
config/<Tool>Config.json
constants/<Tool>Constants.py
doc/<Tool>Doc.json
```

The Function utility uses `FunctionsConfig.json` with `FunctionConstants.py`.

The Router utility additionally uses JSON model specifications stored under `routers/model_specs/`.

### Dependencies and Permissions

Different utilities require different system commands and permissions.

Examples include:

- `pst-utils` for PST processing.
- `openssl` for supported router configuration operations.
- Wireless and networking utilities for scanning.
- Drive and SMART tools for storage diagnostics.
- Recovery tools for disk imaging and file recovery.
- Filesystem access for Windows inspection.

Some operations may require elevated permissions.

Dependency declarations are defined in the corresponding constants modules.

### Data Storage and Privacy

TestingTools separates configuration and processing code from generated runtime data.

Runtime data may contain sensitive information such as:

- PST email archives.
- Extracted contacts and attachments.
- Router passwords and configuration backups.
- Recovery images.
- Filesystem inspection results.
- Checksum manifests.

Private runtime data should generally be stored outside public repositories.

The configured paths can be adjusted to suit the local environment.

## Extending TestingTools

To add a new utility:

1. Create a processing module under `modules/`.
2. Create a constants module under `constants/`.
3. Create a JSON configuration under `config/`.
4. Create the corresponding documentation JSON under `doc/`.
5. Define validation rules, dependencies, actions, and pipeline states.
6. Register the utility in `ToolLoader.py`.
7. Test the operations and state transitions.
8. Update this README.

Where possible, new functionality should use existing shared helpers.

Tool-specific logic should remain outside the shared loader unless a genuinely shared framework change is required.
