# Router Model Specifications

Router model specifications tell TestingTools how to decode, edit and encode router configuration backups.

Each supported router model requires its own JSON specification.

## Adding a Router Model

1. Export a configuration backup from the router.
2. Copy an existing router model specification JSON.
3. Update the model, firmware, hardware and encryption settings.
4. Create a `.txt` file containing the factory password of the router used to create the master template.
5. Save the password file in the directory defined by `Locations.template_router_password_path`.
6. Configure the fields you want to view or edit.
7. Save the model JSON in the directory defined by `Locations.model_specs_path`.
8. Place the original backup in the directory defined by `Locations.config_path`.
9. Test decoding, editing, encoding and restoring.

## Model Specification Settings

| Setting | Description |
|---|---|
| `model` | Router model name |
| `firmware` | Firmware version |
| `hardware` | Hardware revision |
| `encryption` | Encryption algorithm |
| `encoding` | Encrypted data encoding |
| `salted` | Whether OpenSSL salt is used |
| `password_required` | Whether the encryption mechanism requires a password |
| `password_base` | Prefix used when deriving the encryption passphrase |
| `password_hash` | Hashing method applied to the router password |
| `key_derivation` | Encryption key and IV derivation method |
| `key_derivation_digest` | Digest used for key derivation |
| `backup_format` | Backup wrapper and checksum structure |
| `archive` | Internal archive format and compression |
| `configuration_format` | Configuration file syntax |
| `config_fields` | Configuration settings available for viewing and editing |

Use an existing model specification as a reference for the complete JSON structure.

## Template Router Passwords

The master template is created from one physical router of a particular model.

Its factory password is stored separately from the model specification in a plain-text `.txt` file.

For example:

**Filename:** `VRV9517.txt`

```text
FACTORY_PASSWORD_OF_TEMPLATE_ROUTER
```

The file contains only the password, without quotation marks or JSON formatting.

Password files are stored in the directory specified by `Locations.template_router_password_path`.

### Decoding

1. Select the router model specification.
2. Select the original configuration template.
3. Select the `.txt` file containing that template router's factory password.
4. The program reads the selected password and decrypts the template.

### Editing

The decoded configuration can be viewed and modified using the fields defined in `config_fields`.

### Encoding

1. Select the edited configuration.
2. Select the corresponding original template and its password file.
3. The program decrypts the original template.
4. Enter the factory Wi-Fi password printed on the target router.
5. The program rebuilds and encrypts the configuration using the target router's password.

### Verification

The program decrypts the generated backup using the target router's password to verify the encryption process.

This allows one master template to be reused for compatible routers of the same model, each with its own factory password.

## Configuration Locations

Router file locations are configured in `config/RouterConfig.json` under `Locations`.

| Configuration Key | Purpose |
|---|---|
| `model_specs_path` | Router model specification JSON files |
| `model_specs_readme_path` | Router model specification documentation |
| `template_router_password_path` | Template router factory password text files |
| `config_path` | Original router configuration templates |
| `decoded_config_path` | Decoded router configurations |
| `edited_config_path` | Edited router configurations |
| `updated_config_path` | Re-encoded router configurations |

All directory and file locations are determined by the configuration file rather than fixed paths in the router utility.

To change a location, update its corresponding value in `RouterConfig.json`.

## Router Configuration Filenames

TestingTools uses consistent suffixes to identify the different stages.

For example:

```text
Original template:
    SmartModem_backup.cfg

Decoded archive:
    SmartModem_backup-decoded.tar.gz

Extracted configuration:
    SmartModem_backup-decoded/

Edited configuration:
    SmartModem_backup-edited/

Updated configuration:
    SmartModem_backup-updated.cfg
```

The same naming convention applies to `.bin` backups, with the original extension preserved in the updated backup.

The original configuration is never overwritten.

## Adding Configuration Fields

The `config_fields` section determines which router settings are available in the View and Edit menus.

Each entry maps a display name to the corresponding key in the router's configuration file.

For example:

```json
"config_fields": {
    "file": "config/.glbcfg",
    "wifi_2g_ssid": "ARC_WLAN_24G_SSID_0_ESSID",
    "wifi_2g_password": "ARC_WLAN_24G_SSID_0_WPA_Passphrase"
}
```

The `file` entry identifies the configuration file inside the decoded archive.

Additional fields can be added by mapping their actual configuration keys.

## Important Notes

- Keep an unchanged copy of the original router backup.
- Each template password file must match the physical router used to create that template.
- Template passwords are stored separately from model specifications.
- Target router passwords are entered interactively and are not saved by the utility.
- Ensure the router model, hardware revision and firmware are compatible.
- Different encryption or archive mechanisms may require additional reusable Python helpers.
- Successfully decoding and re-encoding a backup does not guarantee the target router will accept it.
- Test a generated configuration before deploying it to multiple routers.

**New router with supported mechanisms → Create a new model JSON and template password file.**

**New unsupported mechanism → Add a reusable Python helper.**
