
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

The Email utility provides Outlook PST browsing, conversion, extraction, and EML email searching using `pst-utils` and Python email-processing functions.

### Features

- View PST summaries.
- List emails in a PST.
- Select and view individual emails.
- Convert PST files to MBOX.
- Convert PST files to separate EML files.
- Extract Outlook contacts as vCards.
- Extract calendar appointments as iCalendar files.
- Extract email attachments.
- Search EML files using configurable search criteria.
- Run individual or multiple email search configurations.
- Save matching emails to configured results directories.
- View previously saved email search results.
- Display paginated search results and view individual emails.
- Display email search help.
- Display configuration help.

### Files

- `constants/EmailConstants.py`
- `modules/email_utils.py`
- `config/EmailConfig.json`
- `doc/EmailDoc.json`
- `doc/SearchReadMe.md`
- `schemas/EmailSearchSchema.json`

Email search criteria are defined in separate JSON configuration files referenced by `search_configs` in `EmailConfig.json`.

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
    "work_dir": "/tmp/toolloader_email_view",
    "search_readme_path": "doc/SearchReadMe.md"
  },
  "search_configs": [
    "config/InvoiceSearch.json",
    "config/AddressSearch.json",
    "config/ProjectSearch.json"
  ]
}
```

The search configuration paths above illustrate the three available search configurations. Each referenced file contains its own search criteria and source and destination paths.

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
| `search_readme_path` | Email search documentation |
| `search_configs` | List of available email search configuration files |

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
├── attachments/
└── search_results/
```

The `search_results` directory is illustrative. Actual search result locations are defined by `results_location` in each search configuration.

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

These EML files can also be used as input for email searches.

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

### Email Searching

The Search emails operation searches EML files using criteria defined in JSON search configuration files.

Available search configurations are listed under `search_configs` in `EmailConfig.json`.

The user can select an individual search configuration or All Search Configurations.

The PRE pipeline loads all selected files through one `load_json()` call, then validates the resulting configurations through one `validate_json_schema()` call using `EMAIL_SEARCH_SCHEMA_PATH = "schemas/EmailSearchSchema.json"`. The same schema applies to every selected configuration, and all must pass before searches begin. PRE associates each filename with its validated dictionary. Search execution, saved-result loading, and summary display consume this mapping without reopening the configuration files during EXEC.

Each search configuration defines:

| Configuration key | Purpose |
|---|---|
| `search_location` | Directory containing EML files to search |
| `results_location` | Directory where matching EML files are saved |
| `match` | Determines how search criteria are combined |
| `criteria` | Fields and keywords used to identify matching emails |

Search criteria support the following email fields:

- `from` — Sender.
- `to` — Recipient.
- `subject` — Email subject.
- `body` — Email body.

The supported matching modes are:

- **ANY:** An email matches when at least one configured search criterion is satisfied.
- **ALL:** An email matches when all configured search criteria are satisfied.

The search operation reads EML files recursively from `search_location` and copies matching emails to `results_location`.

When multiple configurations are selected, each configuration is processed using its own criteria and output directory.

Search results are displayed in a paginated table.

### Viewing Saved Search Results

The View Search Results operation loads previously saved search results without executing another search.

The user can select an individual search configuration or All Search Configurations.

For each selected configuration, the utility reads the configured `results_location` and loads the saved EML files.

When All Search Configurations is selected, the results are combined into a single paginated table.

The display includes an Email Search Summary showing the selected configurations, match modes, search locations, and criteria.

The results table contains:

| Column | Purpose |
|---|---|
| `No` | Email selection number |
| `Date` | Email date |
| `From` | Email sender |
| `Subject` | Email subject |
| `Matched` | Matching criteria or originating search configuration |

When running a search, the `Matched` column identifies which email fields matched the configured criteria.

When viewing saved results, the `Matched` column identifies the originating search configuration, such as `InvoiceSearch`, `AddressSearch`, or `ProjectSearch`.

Saved results reflect the EML files currently present in the configured results directories. The original search criteria are not reapplied when viewing them.

### Search Result Navigation

Search results are displayed in pages of 25 emails by default.

The following commands are available:

| Command | Action |
|---|---|
| `N` | Display the next page |
| `P` | Display the previous page |
| Number | View the selected email |
| `Q` | Quit the results viewer |

Selecting an email number displays its details and body.

Pressing `N` on the final page displays:

```text
Already on the last page.
```

Pressing `P` on the first page displays:

```text
Already on the first page.
```

Invalid input displays:

```text
Invalid selection.
```

### Email Search Documentation

The View Email Search Help operation displays the search documentation referenced by `locations.search_readme_path`.

The guide explains search configuration settings, supported criteria, matching modes, search execution, and saved-result viewing.

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

Email search output uses the `results_location` defined by each search configuration.

### Email Data Privacy

PST files, EML files, and extracted content may contain:

- Personal emails.
- Contact details.
- Calendar appointments.
- Attachments.
- Private business information.
- Sensitive information contained in saved search results.

Source PST files, extracted output, and saved email search results should generally be kept outside public Git repositories.

## Router Utility

The Router utility provides configuration backup decoding, viewing, editing, encoding, and migration workflows.

Router processing uses a modular, JSON-driven architecture. The main router utility coordinates operations through centralised dispatchers, while specialised utility modules implement reusable processing functions.

Adding a router that uses existing processing mechanisms requires a model specification and router configuration entry.

### Features

- Decode encrypted router configuration backups.
- Extract and view decoded configurations.
- View supported key-value and XML configuration fields.
- Decrypt and display protected Wi-Fi passwords.
- Edit supported configuration fields.
- Encrypt modified protected configuration fields.
- View edited configurations.
- Encode updated configurations.
- Sign and verify supported router backups.
- Verify generated backups through local decoding round trips.
- Run the complete same-model modification workflow.
- Decode configurations for migration.
- Edit migration configurations.
- View edited migration configurations.
- Prepare destination configurations.
- Convert configuration values between supported router models and formats.
- Encode migrated configurations.
- Run the complete different-model migration workflow.
- Display router model specification documentation.
- Display router configuration help.

### Files

- `constants/RouterConstants.py` — router utility constants, dependencies, menu actions, and pipeline configuration.
- `modules/router_utils.py` — main router workflows, backup validation, orchestration, and centralised dispatcher registrations.
- `modules/router_encryption_utils.py` — encryption, decryption, cryptographic hashing, field encryption, RSA signing, and signature verification.
- `modules/router_format_utils.py` — backup wrappers, encoding formats, compression, archive processing, and reconstruction.
- `modules/router_config_utils.py` — configuration field extraction, viewing, editing, replacement, and validation.
- `schemas/RouterSchema.json` — shared router model specification validation rules.
- `config/RouterConfig.json` — configured router models and associated file paths.
- `doc/RouterDoc.json` — router configuration documentation.
- `routers/model_specs/` — router model JSON specifications and the common specification template.
- `routers/model_specs/ModelSpecsReadMe.md` — model specification and extension documentation.

### Dependencies

The Router utility uses:

- `openssl` — OpenSSL-based router backup encryption and decryption.
- `python3-cryptography` — AES encryption and decryption using Python's cryptography library.
- `python3-jsonschema` — shared validation against external JSON Schema files.

Dependencies are declared in `constants/RouterConstants.py`.

The required processing mechanisms depend on the selected router model specification.

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
      "device_key": null,
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

The example illustrates the common path configuration. Actual filenames and extensions depend on the router and its backup format.

Password and device-key paths are used only when required by the selected encryption mechanism. Unused credential paths may be `null`.

Firmware-wide encryption parameters are stored in the router model specification rather than separate credential files.

### Router Path Keys

Each configured router uses the following path keys:

| Key | Purpose |
|---|---|
| `specs` | Router model specification JSON |
| `password` | Template password file, when required |
| `device_key` | Device-specific encryption key file, when required |
| `template` | Original template backup |
| `template_decoded` | Decoded template configuration or archive |
| `template_decoded_dir` | Extracted decoded configuration directory |
| `template_edited` | Edited template configuration or archive |
| `template_edited_dir` | Edited configuration directory |
| `template_encoded` | Encoded template backup |
| `original` | Original router configuration backup |
| `migration_decoded` | Decoded migration configuration or archive |
| `migration_decoded_dir` | Extracted migration directory |
| `migration_edited` | Edited migration configuration or archive |
| `migration_edited_dir` | Edited migration directory |
| `migration_converted` | Converted destination configuration or archive |
| `migration_converted_dir` | Converted destination configuration directory |
| `migration_encoded` | Encoded destination backup |

The configured paths determine where router processing reads and writes files.

### Configured Router Models

The supplied configuration supports the following router models:

| Router | Model | Configuration Format | Encryption Mechanism |
|---|---|---|---|
| Spark SmartModem | VRV9517 | Key-value | AES-256-CBC with OpenSSL legacy key derivation |
| Vodafone Ultra Hub | DGA0130VDF | Technicolor THENC | AES-256-CBC with device-specific key |
| Vodafone Huawei HG659 | HG659 B020 | XML | AES-256-CBC with fixed firmware key |

**Spark SmartModem**

Supports configuration decoding, viewing, editing, encoding, and compatible migration operations.

**Vodafone Ultra Hub**

Uses the Technicolor THENC backup format. Authenticated processing requires device-specific cryptographic material. Complete decoding and encoding remain unavailable without the required device key and signing support.

**Vodafone Huawei HG659**

Supports:

- Fixed-key AES-256-CBC backup decryption and encryption.
- zlib compression and decompression.
- RSA/MD5 signature verification and signing.
- XML configuration extraction, viewing, and editing.
- AES-128-CBC encryption and decryption of protected Wi-Fi password fields.
- Signed backup reconstruction.
- Local backup round-trip verification.
- Compatible cross-format configuration migration.

Compatibility depends on the router's firmware and hardware revision.

### JSON-Driven Router Processing

Every router model uses the same JSON specification structure.

The specification template defines the common keys and nested structure. Fields that do not apply to a particular router are assigned JSON `null`.

Router specifications define:

- Model, firmware, and hardware information.
- Backup encryption and key derivation.
- Encryption keys and IVs.
- Password requirements and hashing.
- Digital signature parameters.
- Field-level encryption settings.
- Backup wrappers and encoding.
- Archive format and compression.
- Configuration format.
- Editable configuration fields and selectors.

All model-specific parameters are supplied through JSON rather than hardcoded into processing functions.

Router configuration preparation follows **LOAD → CHECK → PLAN → EXECUTE**. `load_router_model_specs()` loads the JSON through shared `load_json()`; the configured PRE pipeline calls shared `validate_json_schema()` with `ROUTER_SCHEMA_PATH = "schemas/RouterSchema.json"`, then prepares derived XML selectors. The external schema checks the specification structure, supported mechanisms, and parameter combinations before processing; invalid or unsupported specification values and selector preparation errors prevent execution. Planning follows preparation where enabled by the action. Processing consumes the prepared model dictionary without reloading or repeating schema validation. Backup integrity and security checks, including signatures, archive safety, and local output verification where applicable, remain part of processing.

#### Router Architecture

`router_utils.py` is responsible for the main router workflows, backup validation, and dispatching.

All processing handler registrations are centralised near the top of `router_utils.py`:

```python
ENCRYPTION_HANDLERS
FIELD_ENCRYPT_HANDLERS
FIELD_DECRYPT_HANDLERS
CONFIG_VIEW_HANDLERS
CONFIG_EDIT_HANDLERS
```

Processing implementations remain in specialised utility modules:

- `router_encryption_utils.py` — cryptographic algorithms and signing.
- `router_format_utils.py` — backup encoding, decoding, wrappers, and compression.
- `router_config_utils.py` — configuration field reading, editing, and validation.

Dispatchers select functions using specification values, not router model names.

The main workflow coordinates the registered functions without containing manufacturer-specific processing implementations.

#### Adding Another Router

To add support for another router:

1. Copy the common router specification template.
2. Populate the model-specific parameters.
3. Set unused specification values to `null`.
4. Add the router and its file paths to `config/RouterConfig.json`.
5. Reuse existing registered encryption, format, and configuration-processing mechanisms.
6. If a required mechanism is not supported, implement a generic processing function in the appropriate utility module and register it centrally in `router_utils.py`.
7. Validate the specification and test the supported workflows.

Routers using existing processing mechanisms do not require changes to the main router workflow.

New field names must be added to the common specification schema, template, and every model specification, using `null` where unused.

### Router Backup Extensions

Router backup selection supports the configured extensions:

```python
CONFIG_EXTENSION = [".cfg", ".bin", ".conf"]
```

Common formats include:

- `.cfg` — router configuration backups.
- `.bin` — binary encrypted backups.
- `.conf` — encrypted configuration backups, including Huawei HG659.

The file extension does not determine how a backup is processed.

The router model specification defines its encryption, wrapper, compression, archive format, and configuration format.

Decoded outputs may be TAR/GZIP archives or single-file XML configurations.

### Same-Model Router Workflow

The same-model workflow provides operations for:

1. Decoding a router configuration.
2. Extracting and viewing supported configuration fields.
3. Editing supported configuration fields.
4. Viewing the edited configuration.
5. Encoding the updated configuration.

The menu also provides:

```text
Modify Router - Same Model (Run All)
```

This runs the associated same-model workflow through the configured pipeline.

The workflow uses the same orchestration regardless of router model. Its dispatchers select the processing implementations required by the model specification.

Encoded backups are verified through the supported local decoding and integrity checks before being reported as successfully generated.

### Different-Model Migration Workflow

The Router utility provides a separate workflow for transferring compatible configuration values between router models.

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

This executes the configured migration pipeline.

#### Cross-Format Configuration Conversion

The conversion workflow supports transferring compatible Wi-Fi settings between Spark SmartModem key-value configurations and Huawei HG659 XML configurations.

Supported directions include:

- Spark SmartModem → Huawei HG659.
- Huawei HG659 → Spark SmartModem.

Conversion reuses the existing configuration View and Edit handlers.

The source router provides the readable configuration values. The destination router's existing configuration is used as the base.

Only supported mapped fields are transferred, including:

- 2.4 GHz Wi-Fi SSID.
- 2.4 GHz Wi-Fi password.
- 5 GHz Wi-Fi SSID.
- 5 GHz Wi-Fi password.

Protected fields are encrypted using the destination router's registered field-encryption mechanism.

Unrelated destination configuration, guest networks, and device-specific settings are preserved.

The converted configuration is encoded using the destination model's own backup format and encryption mechanism.

Generated backups are verified locally by decoding them and checking the recovered configuration.

### Router Password Handling

Router backup authentication depends on the selected encryption mechanism.

The supported approaches include:

- Password-based key derivation.
- Device-specific encryption keys.
- Firmware-wide fixed encryption keys.

Password files are used only when the selected router requires them.

Device-specific keys may be supplied through the existing configured key paths.

Firmware-wide encryption parameters, including keys, IVs, and signature parameters, are stored directly in the router model specification JSON.

Some router configurations also protect individual password fields.

For example, the HG659 uses AES-128-CBC encryption for stored Wi-Fi password values. The configuration-processing functions use the registered field-encryption handlers to display and update these values correctly.

Actual router passwords, device-specific secrets, and router backups should be kept out of public repositories.

### Editable Router Fields

The `config_fields` section of each router specification maps common field names to their locations in the router's configuration.

The supported Wi-Fi fields are:

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

This example represents a key-value configuration.

For XML configurations, the same field names use selectors to identify XML elements and attributes.

For example:

```json
{
  "config_fields": {
    "file": "config.xml",
    "wifi_2g_ssid": "WLANConfigurationInstance|X_OperatingFrequencyBand=2.4GHz|X_Is_Guest_Network=0|SSID",
    "wifi_2g_password": "WLANConfigurationInstance|X_OperatingFrequencyBand=2.4GHz|X_Is_Guest_Network=0|PreSharedKeyInstance@KeyPassphrase",
    "wifi_5g_ssid": "WLANConfigurationInstance|X_OperatingFrequencyBand=5GHz|X_Is_Guest_Network=0|SSID",
    "wifi_5g_password": "WLANConfigurationInstance|X_OperatingFrequencyBand=5GHz|X_Is_Guest_Network=0|PreSharedKeyInstance@KeyPassphrase"
  }
}
```

The XML selectors identify the intended Wi-Fi network and attribute, excluding guest-network entries.

The existing configuration-processing utilities support both formats through registered handlers.

Editing uses targeted field replacement rather than rewriting unrelated configuration content.

Protected password fields are decrypted for viewing and encrypted when modified, according to the model specification.

Adding another editable value generally requires updating its field mapping in the router specification, provided the field name and processing mechanism are already supported.

### Router Model Documentation

The router model specification guide is stored at:

```text
routers/model_specs/ModelSpecsReadMe.md
```

Its location is configured using:

```text
Common Locations.model_specs_readme_path
```

The Router utility provides a menu option for displaying this documentation.

The guide describes the common model specification structure, supported processing mechanisms, configuration field mappings, and how to add router models.

### Router Output Safety

Router processing maintains separate locations for:

- Original router backups.
- Template configurations.
- Decoded configurations.
- Edited configurations.
- Migration configurations.
- Converted configurations.
- Encoded backups.

Processing includes appropriate validation, preservation of unrelated configuration content, and local verification of generated outputs.

Recommended precautions:

- Preserve original router backups.
- Keep device-specific credentials and actual Wi-Fi passwords private.
- Check router firmware and hardware compatibility.
- Confirm source and destination models before migration.
- Review edited and converted configuration values.
- Keep a recovery method available before restoring a configuration to physical hardware.

**Successful local processing and cryptographic verification do not guarantee that physical router firmware will accept a generated backup.**

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

PRE stops at the first exception. The loader records the failing step and error, reports missing files clearly, and returns to the menu when PRE fails instead of proceeding to execution. Exceptions from conditions and argument resolution are handled as step failures too. A truthy `success_key` cannot override recorded errors: success requires no recorded errors and, when present, a truthy success result. EXEC records exceptions and continues with later eligible steps; it does not apply PRE's stop-on-exception behaviour.

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

The shared `modules/json_utils.py` provides `load_json()` for one file path or an ordered list of file paths, and `validate_json_schema()` for one configuration dictionary or a list of dictionaries. Validation rules come from external JSON Schema files whose paths are passed explicitly by constants. The validator checks the schema, applies the same schema to each supplied configuration, and returns the original data unchanged on success. Configured PRE steps retain loaded and validated configurations in the execution context for later use without unnecessary reloading or schema validation.

`load_json()` propagates file errors and includes the file path in JSON and text decoding errors. Schema validation prints `[OK] <label> schema validated successfully.` by default. Invalid schemas or configurations print `[FAILED] <label>: ...` and raise `ValueError`; configuration errors identify property paths such as `$.field` or `$[0].field`. Validation stops at the first invalid configuration, reporting its schema errors. The pipeline records an already reported validation error without printing it again.

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
