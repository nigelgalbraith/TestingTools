
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

The Router utility provides interactive decoding, viewing, editing, encoding, and migration of supported router configuration backups.

Router model specifications determine the processing operations. The application pipelines manage operation order, user selections, validation, confirmation, and file handling.

### Features

- Decode and extract router configuration backups.
- View supported key-value and XML configuration settings.
- Edit supported configuration fields.
- View edited configuration values.
- Encode and verify router backups.
- Modify configurations for the same router model.
- Migrate compatible settings between different router models.
- Prepare and convert destination configurations.
- Display router specifications and configuration help.

Processing capabilities depend on the selected router's format, available credentials, and supported algorithms.

### Files

| File | Purpose |
|---|---|
| `constants/RouterConstants.py` | Router menus, function registry, dependencies, and pipelines |
| `modules/router_utils.py` | Operation builders, dispatcher, validation, credential handling, and file operations |
| `modules/router_encryption_utils.py` | Encryption, decryption, signatures, and checksums |
| `modules/router_format_utils.py` | Backup wrappers, encoding, compression, and archives |
| `modules/router_config_utils.py` | Configuration viewing, editing, and field validation |
| `schemas/RouterSchema.json` | Router specification schema |
| `config/RouterConfig.json` | Router models and configured paths |
| `doc/RouterDoc.json` | Router configuration help |
| `doc/RouterSpecificationTemplate.json` | Router specification template |
| `routers/model_specs/` | Router model specifications |
| `routers/model_specs/ModelSpecsReadMe.md` | Specification documentation |

### Dependencies

The Router utility declares the following dependencies:

- `openssl`
- `python3-cryptography`
- `python3-jsonschema`

The required processing methods depend on the selected router specification.

### Router Configuration

Router models and file paths are defined in `config/RouterConfig.json`.

The configuration contains two top-level sections:

- `Common Locations` — Shared documentation paths.
- `Routers` — Router models, credentials, backups, and output paths.

Each router entry supports these paths:

| Key | Purpose |
|---|---|
| `specs` | Router model specification JSON |
| `password` | Password file, when required |
| `device_key` | Binary device-key file, when required |
| `template` | Template router backup |
| `template_decoded` | Decoded template output |
| `template_decoded_dir` | Extracted template directory |
| `template_edited` | Edited template output |
| `template_edited_dir` | Edited template directory |
| `template_encoded` | Encoded template backup |
| `original` | Original configuration for migration |
| `migration_decoded` | Decoded migration output |
| `migration_decoded_dir` | Extracted migration directory |
| `migration_edited` | Edited migration output |
| `migration_edited_dir` | Edited migration directory |
| `migration_converted` | Converted destination configuration |
| `migration_converted_dir` | Converted destination directory |
| `migration_encoded` | Encoded destination backup |

Unused credential paths may be omitted or set to `null`, depending on the configuration.

Output extensions depend on the router format.

### Router Menu

The Router Configuration menu provides:

1. Decode Configuration
2. View Configuration
3. Edit Configuration
4. View Edited Configuration
5. Encode Configuration
6. Modify Router - Same Model (Run All)
7. Migrate a Config
8. Edit Migration Config
9. View Edited Migration Config
10. Prepare Destination Config
11. Convert Migration Config
12. Encode Migration Config
13. Modify Router - Different Model (Run All)
14. View Model Specifications Help
15. Show config help
16. Cancel

Each action selects the required router and prepares the applicable processing operations.

### Router Architecture

Router processing uses the model specifications and function registry to select reusable operations.

`constants/RouterConstants.py` defines `ROUTER_FUNCTIONS`, with registered functions for:

- Encoding and decoding.
- Encode and decode validation.
- Configuration extraction.
- Format checking.
- Checksums.
- Configuration editing and validation.
- Configuration viewing and validation.

`modules/router_utils.py` provides the operation resolution, builders, and dispatcher:

```python
resolve_router_operations()
build_encode_operations()
build_decode_operations()
build_edit_operations()
build_view_operations()
run_router_operations()
```

The builders prepare operations in the order required by the router specification, with applicable validators.

`run_router_operations()` executes the ordered transformations, passing each operation's result to the next.

The declarative pipelines in `RouterConstants.py` coordinate preparation, validation, processing, viewing, editing, saving, and confirmation. Individual functions perform their assigned operations and return their results.

The selected action displays the relevant processing operations before execution.

### Supported Router Models

| Router | Model | Backup Format | Configuration Format |
|---|---|---|---|
| Spark SmartModem | VRV9517 | Legacy OpenSSL AES-256-CBC, Base64, TAR/GZIP | Key-value |
| Vodafone Ultra Hub | DGA0130VDF | Technicolor THENC, device-key specification | Not established |
| Vodafone Huawei HG659 | HG659 | Fixed-key AES-256-CBC, signed zlib | XML |

**Spark SmartModem VRV9517**

Supports decoding, extraction, viewing, editing, encoding, and local backup verification.

**Vodafone Huawei HG659**

Supports fixed-key AES-256-CBC processing, RSA/MD5 signing and verification, XML configuration operations, and supported protected Wi-Fi password fields.

**Vodafone Ultra Hub DGA0130VDF**

Supports THENC format parsing and relevant validation. Complete THENC encryption, decryption, signing, and authentication are not implemented. The required device-key derivation and cryptographic processing must be supported before complete backup modification is available.

Router compatibility depends on the hardware and firmware revision.

### Router Backup Extensions

Configured input and output extensions include:

- `.cfg` — Spark SmartModem backups.
- `.conf` — Vodafone Huawei HG659 backups.
- `.bin` — Vodafone Ultra Hub backups.
- `.tar.gz` — Decoded Spark configuration archives.
- `.xml` — Decoded HG659 configurations.

The selected specification and configured paths determine the expected format.

### Same-Model Workflow

The same-model workflow uses one router model's specification for decoding and encoding.

The processing sequence is:

1. Select the router.
2. Load and validate its model specification.
3. Resolve and build the applicable operations.
4. Decode the router backup.
5. Extract and validate the configuration.
6. View and edit supported fields.
7. Save the edited configuration.
8. Rebuild and encode the backup.
9. Verify the generated backup where supported.

Individual menu actions can use existing saved inputs. Run All performs the configured sequence.

### Different-Model Migration

The migration workflow transfers compatible configuration settings from one router model to another.

The source router specification controls source decoding and field extraction.

The destination router specification controls destination decoding, editing, conversion, and encoding.

The workflow provides separate actions to:

- Decode the migration source.
- Edit migration values.
- View edited migration values.
- Prepare the destination configuration.
- Convert compatible fields into the destination format.
- Encode the destination backup.

**Modify Router - Different Model (Run All)** combines the applicable migration stages.

Only supported logical fields can be transferred. Fields without established destination mappings cannot be converted automatically.

A migration requires valid source and destination backups and any necessary credentials.

### Router Credentials

Password and device-key file paths are configured in `RouterConfig.json`.

Credential requirements are declared by the model specification:

- `password_required` — Password credential requirement.
- `device_key_required` — Binary device-key requirement.

Password-based encryption, fixed-key encryption, and device-key encryption use different preparation mechanisms.

Missing required credentials prevent the corresponding operation from completing.

Credentials should remain outside public repositories.

### Editable Fields

The model specification's `config_fields` list maps logical field names to actual configuration keys or XML selectors.

The supplied models include mappings for:

- `wifi_2g_ssid`
- `wifi_2g_password`
- `wifi_5g_ssid`
- `wifi_5g_password`

Only fields with supported mappings and configuration formats can be edited.

Protected fields are decrypted or encrypted by the registered field-processing functions where supported.

### Router Output Safety

Router workflows validate inputs and use safe file operations when creating or replacing generated outputs.

Supported protections include archive extraction checks, configuration validation, staged writes, and rollback when an operation fails.

Interactive actions request confirmation before overwriting applicable existing outputs.

Failed or cancelled combined workflow stages must not be treated as successful prerequisites for later operations.

Preserve an unchanged copy of the original router backup.

Successful local processing or cryptographic verification does not guarantee that physical router firmware will accept a generated backup.

### Router Model Specifications

Router specifications are stored in `routers/model_specs/` and validated against `schemas/RouterSchema.json`.

AutomationTools and TestingTools use the same specification structure.

For specification fields, operation ordering, supported algorithms, and instructions for adding router models, see:

`routers/model_specs/ModelSpecsReadMe.md`

### Testing

Run the router regression tests with:

```bash
python3 -m unittest discover -s tests -v
```

The tests cover supported workflows using synthetic backups and temporary directories. Physical-router restore compatibility requires separate verification.

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
