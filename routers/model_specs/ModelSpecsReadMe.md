# Router Model Specifications

Router model specifications tell TestingTools how to decode, edit and encode router configuration backups.

Each supported router model requires its own JSON specification.

## Adding a Router Model

1. Export a configuration backup from the router.
2. Copy an existing router model specification JSON.
3. Update the model, firmware, hardware and encryption settings.
4. Set `default_password` to the factory password of the router used to create the master template.
5. Configure the fields you want to view or edit.
6. Save the JSON in the directory defined by `Locations.model_specs_path`.
7. Place the original backup in the directory defined by `Locations.config_path`.
8. Test decoding, editing, encoding and restoring.

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
| `default_password` | Factory password of the master template router |
| `password_base` | Prefix used when deriving the encryption passphrase |
| `password_hash` | Hashing method applied to the router password |
| `key_derivation` | Encryption key and IV derivation method |
| `key_derivation_digest` | Digest used for key derivation |
| `backup_format` | Backup wrapper and checksum structure |
| `archive` | Internal archive format and compression |
| `configuration_format` | Configuration file syntax |
| `config_fields` | Configuration settings available for viewing and editing |

Use an existing model specification as a reference for the full JSON structure.

## Template Passwords

The master template is created from one router of a particular model.

**Decoding**

The program automatically reads `default_password` from the selected model specification and uses it to decrypt the master template.

**Editing**

The decoded configuration can be viewed and modified using the fields defined in `config_fields`.

**Encoding**

The program requests the factory password printed on the target router and uses it to encrypt the modified configuration.

**Verification**

The program verifies the generated configuration using the target router's password.

This allows one master template to be reused for compatible routers of the same model.

## Configuration Locations

Router directories are configured in `config/RouterConfig.json` under `Locations`.

| Configuration Key | Purpose |
|---|---|
| `model_specs_path` | Router model specification JSON files |
| `config_path` | Original router configuration templates |
| `decoded_config_path` | Decoded router configurations |
| `edited_config_path` | Edited router configurations |
| `updated_config_path` | Re-encoded router configurations |

Directory locations are determined by the configuration file, not by fixed paths in the router utility.

To change a directory, update its corresponding value in `RouterConfig.json`.

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
- Ensure the router model, hardware revision and firmware are compatible.
- Different encryption or archive mechanisms may require additional reusable Python helpers.
- Successfully decoding and re-encoding a backup does not guarantee the target router will accept it.
- Test a generated configuration before deploying it to multiple routers.

**New router with supported mechanisms → Create a new model JSON.**

**New unsupported mechanism → Add a reusable Python helper.**