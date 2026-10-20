A collection of terminal-based testing utilities built around a shared, reusable ToolLoader and a pipeline-style state machine
The main goals are to:

    Keep tools modular.
    Reuse common functions.
    Maintain predictable execution (pre → plan → confirm → exec).
    Avoid unnecessary tool-specific implementations.
    Keep processing logic separate from shared display, file and pipeline helpers.

What's Included
WiFiScanner

A Wi-Fi utility that can:

    List wireless interfaces.
    Scan for nearby networks.
    Show detailed information for selected networks.
    Display BSS details.
    Report wireless interface status.

Config: config/WiFiConfig.json

Constants: constants/WiFiConstants.py

Docs: doc/WiFiDoc.json

Some wireless adapters can intermittently report Device or resource busy (-16) from iw scan. This is generally a transient driver, supplicant or NetworkManager contention issue. Retrying the scan may resolve it.
NetworkScanner

A network utility that can:

    List network interfaces.
    Analyse a selected interface.
    Show connected interfaces.
    Display ARP neighbours using ip neigh.
    Run TCP port scans against selected or manually entered hosts.
    Report interface connection status.

Config: config/NetworkConfig.json

Constants: constants/NetworkConstants.py

Docs: doc/NetworkDoc.json
Email

An email and Outlook PST utility built around pst-utils.

The Email tool can:

    View a PST summary.
    List emails contained in a PST.
    Select and view individual emails.
    Convert PST files to mbox.
    Convert PST files to separate EML files.
    Extract contacts.
    Extract attachments.
    Display Email configuration help.

The source directory can contain multiple PST files. The tool builds a selection menu before processing the selected file.

Config: config/EmailConfig.json

Constants: constants/EmailConstants.py

Docs: doc/EmailDoc.json
Email Directory Layout

Email source and destination directories are configured by the Email utility.

A typical layout is:
email/
    email_source/
    email_dest/

Each PST receives its own output directory.

For example:
email_source/
    testPST.pst

email_dest/
    testPST/
        mbox/
        eml/
        contacts/
        attachments/

This keeps output from different PST files separate.

Runtime email data may contain private information and should generally be excluded from Git.
Dependencies

The Email utility uses pst-utils, including the readpst command for PST conversion and extraction.
Router

A JSON-driven router configuration utility for decoding, viewing, editing, converting and encoding router backup files. It supports editing backups for the same model and transferring selected settings between different router models.

The Router tool can:

    Select a router entry and load its model specifications.
    Decode reference templates using their configured template password files.
    Decode physical source router backups using a password entered at the prompt.
    Save and extract decoded configuration archives.
    View and edit supported configuration fields.
    Prepare a destination configuration from its model template.
    Transfer matching logical configuration fields between source and destination models.
    Encode the converted configuration using the destination router's password.
    Verify generated backups through local encryption/decryption checks.
    Run the same-model or different-model workflow as a sequence of pipeline steps.
    Display configuration and model specification help.

Config: config/RouterConfig.json

Constants: constants/RouterConstants.py

Docs: doc/RouterDoc.json

Module: modules/router_utils.py
JSON-Driven Router Support

Router entries are configured under Routers in RouterConfig.json. Each entry has its own paths to a model specification, reference template, template password file, physical backup and generated files.

A router is not permanently a source or destination. The menu determines its role for each migration. Router 1 can migrate to Router 2, Router 2 to Router 1, or either can be selected in both roles for testing. More router entries can be added without changing the workflow.

Each model specification describes its backup structure and supported configuration fields, including:

    Router model, firmware and hardware identifiers.
    Encryption and encoded payload format.
    Salt, hashing and key derivation rules.
    Headers, checksums and trailers.
    Archive format and compression.
    Configuration file location and named configuration keys.

The model identifier is not a processing rule. If a new model uses mechanisms already implemented in router_utils.py, support can be added through model JSON and a new router entry. Unsupported formats require appropriate reusable processing support.

Model specification paths are set per router using Routers.<router name>.specs.
Router Directory Configuration

The configuration has two top-level sections:

    Common Locations.model_specs_readme_path — path to the model specification help document.
    Routers — a mapping of user-defined router names to their settings and file paths.

Each router entry has these required string fields:
Field	Purpose
specs	Model specification JSON
password	Password file for the reference template
template	Original encrypted reference template
template_decoded	Decoded reference template archive
template_decoded_dir	Extracted reference template directory
template_edited	Rebuilt edited template archive
template_edited_dir	Edited reference template directory
template_encoded	Encoded backup produced by template editing
original	Physical router backup used as a migration source
migration_decoded	Decoded physical source backup archive
migration_decoded_dir	Extracted physical source backup directory
migration_edited	Reserved path for an edited source archive
migration_edited_dir	Edited physical source configuration directory
migration_converted	Prepared/rebuilt destination archive
migration_converted_dir	Destination template directory with converted settings
migration_encoded	Final encrypted destination backup

For example, paths may be configured under ~/Documents/TestingToolsData/routers/. The actual paths come from each router entry, not hardcoded model names. doc/RouterDoc.json contains complete examples for Router 1 and Router 2.
Supported Backup Extensions

Router backups may use .cfg or .bin extensions. The extension alone does not identify the internal backup format. The selected model specification determines how a file is decoded and encoded.
Same-Model Workflow

The same-model workflow uses the selected model's template as its reference:
Select Router
    |
    v
Load Model Specifications
    |
    v
Decode Template (template password file)
    |
    v
Save and Extract Archive
    |
    v
View / Edit Supported Fields
    |
    v
Rebuild and Encode
    |
    v
Enter Target Router Password
    |
    v
Verify and Save template_encoded

The original reference template remains unchanged. The existing encoder can also allow the template password as its output password in the standard template-editing flow, where permitted by the model settings and prompt.
Different-Model Migration Workflow

A source and a destination are selected separately. They may use different model specifications, internal configuration field names, backup formats and passwords.
Select SOURCE Router and Load Source Specifications
    |
    v
Decode Physical Source Backup (SOURCE router password)
    |
    v
Save / Extract migration_decoded
    |
    v
Edit Source Fields in migration_edited_dir
    |
    v
Select DESTINATION Router and Load Destination Specifications
    |
    v
Decode Destination TEMPLATE (destination template password file)
    |
    v
Save / Extract migration_converted
    |
    v
Copy Matching Logical Fields into migration_converted_dir
    |
    v
Confirm Destination Changes
    |
    v
Encode Using DESTINATION Router Password
    |
    v
Verify and Save migration_encoded

Conversion matches the logical field labels in the two model specifications, such as wifi_2g_ssid. The underlying configuration keys can differ between models. Only matching supported fields are transferred; other destination settings are retained from the destination model's template.

The destination is prepared from its reference template, not a backup retrieved from the destination physical router. Consequently, the output retains other template values, including any device-specific values that were not explicitly converted. Check device compatibility before attempting a restore.

The menu also exposes the individual migration stages for testing. The Modify Router - Different Model (Run All) action chains decoding, editing, destination preparation, conversion and encoding.
Router Output Naming

Each router entry explicitly defines its output paths. An example layout is:
routers/
    templates/<router>-template.cfg
    templatePasswords/<router>-password.txt
    decoded/<router>-decoded.tar.gz
    decoded/<router>-decoded/
    edited/<router>-edited.tar.gz
    edited/<router>-edited/
    encoded/<router>-encoded.cfg
    original/<router>-original.cfg
    migration/
        decoded/<router>-decoded.tar.gz
        decoded/<router>-decoded/
        edited/<router>-edited.tar.gz
        edited/<router>-edited/
        converted/<router>-converted.tar.gz
        converted/<router>-converted/
        encoded/<router>-encoded.cfg

The paths are configurable; this layout is illustrative. Source files and reference templates are not intentionally overwritten by normal edit and migration operations. Generated files may be replaced only after an overwrite confirmation.
Password Handling

The model specification controls whether a password is required, for example:
"password_required": true

The workflows distinguish three password roles:

    Template password — read from Routers.<router name>.password; used to decode that model's reference template.
    Source router password — entered securely when decoding the selected physical source backup.
    Destination router password — entered securely when encoding the converted destination configuration.

Physical routers can have different passwords even when they are the same model. A template password must not be assumed to be the physical source or destination password.

Passwords entered interactively use getpass and are not intended to be stored in shared pipeline context. For migration encoding of password-protected models, the destination password is required rather than silently substituting the template password.

The generated backup is decrypted locally using the chosen output password to verify that the encrypted payload round-trips correctly. This does not guarantee that the destination hardware will accept the backup.
Editable and Convertible Router Fields

The config_fields section of each model specification maps shared logical names to model-specific keys. For example:
"config_fields": {
    "file": "config/.glbcfg",
    "wifi_2g_ssid": "ARC_WLAN_24G_SSID_0_ESSID",
    "wifi_2g_password": "ARC_WLAN_24G_SSID_0_WPA_Passphrase",
    "wifi_5g_ssid": "ARC_WLAN_5G_SSID_0_ESSID",
    "wifi_5g_password": "ARC_WLAN_5G_SSID_0_WPA_Passphrase"
}

The file entry identifies the file inside the extracted archive. Other keys name settings presented to the user and used for cross-model matching.

A future model can map wifi_2g_ssid to a different underlying field while retaining that common logical name. Fields without a matching logical name are not automatically copied.
Router Model Documentation

The model specification guide is configured at Common Locations.model_specs_readme_path. Use View Model Specifications Help to display it. doc/RouterDoc.json describes the router configuration keys and provides two example router entries; neither is permanently a source or destination.
Overwrite Behaviour

TestingTools prompts before overwriting generated router archives, directories or encoded outputs. Declining preserves the existing output. This differs from unattended tooling that may be configured to replace generated files automatically.
Backup Safety

    Keep unchanged copies of original physical backups and reference templates.
    Keep passwords and private router backups out of public repositories.
    Verify the selected source and destination model specifications.
    Review converted values before confirming changes.
    Keep a recovery method for physical routers.
    Verify firmware, hardware revision and device-specific settings before restoring a template-derived backup.

Local decoding, encoding and round-trip verification establish internal consistency, not physical-router restore compatibility.
How It Works

Each tool is primarily defined by a constants module.

The constants module supplies:

    Configuration path.
    Documentation path.
    JSON keys.
    Validation rules.
    Secondary validation.
    Required user level.
    Dependencies.
    Status configuration.
    Plan configuration.
    Menu actions.
    Pre-phase pipelines.
    Execution pipelines.
    Pipeline states.

Reusable processing logic lives in modules such as:
modules/
    display_utils.py
    file_utils.py
    network_utils.py
    email_utils.py
    router_utils.py
    state_machine_utils.py

The constants files connect these functions to the shared state-machine framework.
ToolLoader Flow

ToolLoader manages the general execution sequence:

    Load the selected tool constants.
    Check dependencies.
    Install missing dependencies if required.
    Load the tool configuration.
    Validate the configuration.
    Perform secondary validation.
    Compute status.
    Display available actions.
    Execute the selected pipeline.

A pipeline can contain:
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

Not every action requires every stage.

Read-only actions may skip planning and confirmation, while modifying actions can require user confirmation.
Pre-Phase

The pre phase handles preparation and selection.

Examples include:

    Discovering interfaces.
    Discovering ARP neighbours.
    Finding PST files.
    Selecting email files.
    Selecting router model specifications.
    Selecting original router backups.
    Selecting extracted or edited configurations.

A typical pipeline entry:
{
    "phase": "pre",
    "fn": get_files_by_extension,
    "args": [
        lambda job, meta, ctx: meta[LOCATIONS_KEY][SOURCE_DIR],
        lambda job, meta, ctx: ".pst",
    ],
    "result": "pst_files",
}

The result becomes available through:
ctx.get("pst_files", [])
Exec-Phase

The exec phase performs the requested action.

Examples include:

    Scanning ports.
    Reading PST metadata.
    Converting PST files.
    Extracting email attachments.
    Decrypting router backups.
    Saving and extracting router archives.
    Viewing and editing configuration fields.
    Rebuilding and encrypting router backups.

Example:
{
    "phase": "exec",
    "fn": convert_pst_to_mbox,
    "args": [
        lambda job, meta, ctx: ctx.get("selected_pst"),
        lambda job, meta, ctx: meta[LOCATIONS_KEY][DEST_DIR],
    ],
    "result": "convert_ok",
}
Shared Pipeline Context

Pipeline resolver functions use three arguments:
job
meta
ctx

    job provides the current job where required.
    meta contains the loaded tool configuration.
    ctx contains results from earlier pipeline steps.

For example:
lambda job, meta, ctx: meta[LOCATIONS_KEY][SOURCE_DIR]

reads a configured location.

Whereas:
lambda job, meta, ctx: ctx.get("selected_pst")

reads a previously selected value.

Sensitive passwords should remain inside the relevant utility functions rather than being stored in the shared pipeline context.
Status System

Each tool can provide a status function through STATUS_FN_CONFIG.

Example:
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

ToolLoader uses this to display whether the configured location contains data.
Configuration Validation

Each tool can define primary validation rules:
VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        LOCATIONS_KEY: dict,
    },
}

Secondary validation can check nested configuration values:
SECONDARY_VALIDATION: Dict[str, Any] = {
    LOCATIONS_KEY: {
        "required_job_fields": {
            SOURCE_DIR: str,
            DEST_DIR: str,
        },
        "allow_empty": False,
    },
}

This verifies configuration structure before actions execute.
Configuration Documentation

Each tool can provide a JSON documentation file.

For example:
doc/EmailDoc.json

Documentation can describe:

    Required fields.
    Editable values.
    Example configurations.
    Field descriptions.

The shared display_config_doc() helper displays configuration documentation in the terminal.

The Router utility additionally uses display_readme() to display the model specification guide from its configured location.
Example Email Configuration
{
    "locations": {
        "source_dir": "email/email_source",
        "dest_dir": "email/email_dest"
    }
}
Example Email Actions
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
Generic Helper Design

Where possible, helper functions are generic.

For example:
get_files_by_extension(directory, extension)

This function is not tied to PST or router files.

Email can use:
".pst"

Router can use:
[".cfg", ".bin"]

The same helper accepts a single extension or a collection of extensions.

Reusable file operations remain in file_utils.py.

Tool-specific functions remain in their relevant modules.

For example:
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
    convert_router_config_fields

ToolLoader does not need router-specific encryption, email parsing or network scanning logic.
Running TestingTools

From the project directory:
python3 ToolLoader.py

The loader displays available tools and executes the selected utility through the shared state machine.
Project Structure

A simplified source-code structure:
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
    ├── router_utils.py
    └── state_machine_utils.py

Router models, documentation, password files and generated configurations are located using the paths in RouterConfig.json.

They do not need to reside in fixed source-code directories.
Git Ignore

Typical ignored files include:
# Python cache
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
.env/

Runtime files, passwords and private configurations stored inside the repository should also be ignored using paths that match their actual locations.

Files stored outside the repository are not tracked by that repository.

Avoid committing actual router credentials, private backups or generated configurations unless publication is intentional.
Design Philosophy

TestingTools uses reusable components rather than independent scripts for every operation.

A typical tool consists of:
Configuration
      +
Constants
      +
Reusable Module Functions
      +
Shared ToolLoader

This maintains a common workflow for:

    Dependency checks.
    Configuration validation.
    Status display.
    Menu selection.
    Preparation.
    Planning.
    Confirmation.
    Execution.
    Finalisation.

The Router utility follows the same architecture:
RouterConfig.json
        +
RouterConstants.py
        +
Router Model JSON
        +
router_utils.py
        +
Shared ToolLoader

Router models remain data-driven, configuration locations remain configurable, and ToolLoader remains independent of the processing details of individual tools.
