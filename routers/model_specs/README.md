
# Router Model Specifications

Place one JSON file per supported router in `routers/model_specs/`, for example `VRV9517.json`.

The router utility reads each JSON file to determine how to decode, encode, extract, and edit that router's configuration backup.

**Router model names are labels, not processing rules.** The JSON settings determine which functions are used.

Original router backups belong in `routers/templates/`.

## Adding Another Router

1. Obtain an original configuration backup from the router.
2. Identify its encryption, encoding, password derivation, backup structure, archive format, and configuration syntax.
3. Copy an existing model JSON and update its settings.
4. Configure the fields you want to view or edit.
5. Place the JSON in `routers/model_specs/`.
6. Place the original backup in `routers/templates/`.
7. Select the model and backup through ToolLoader.
8. Test decoding, editing, encoding, and restoring.

If the router uses mechanisms the program already supports, **only a new JSON file is required**.

If it uses a new encryption algorithm, backup structure, archive type, or configuration syntax, add a reusable Python helper for that mechanism.

Do not create router-model-specific processing functions.

---

## 1. Router Information

| JSON Field | Description |
|---|---|
| `model` | Router model name |
| `firmware` | Firmware version |
| `hardware` | Hardware revision |

Example:

```json
"model": "VRV9517",
"firmware": "v6.00.17 build06",
"hardware": "R01"
```

These fields identify the router but do not determine which processing functions run.

## 2. Encryption Settings

| JSON Field | Description | Currently Supported |
|---|---|---|
| `encryption` | Encryption algorithm | `aes-256-cbc` |
| `encoding` | Encoding of encrypted data | `base64` |
| `salted` | Whether OpenSSL salt is used | `true`, `false` |
| `key_derivation` | Encryption key/IV derivation mechanism | `openssl-legacy` |
| `key_derivation_digest` | Digest used for key derivation | `md5`, `sha256`, `sha512` |

Example:

```json
"encryption": "aes-256-cbc",
"encoding": "base64",
"salted": true,
"key_derivation": "openssl-legacy",
"key_derivation_digest": "md5"
```

These settings determine how encrypted data is processed.

If another router uses a supported algorithm with different parameters, update its JSON.

If it uses an unsupported algorithm, implement a reusable encryption/decryption helper.

## 3. Password Settings

| JSON Field | Description |
|---|---|
| `password_required` | Whether a password prompt is required |
| `password_base` | String prepended to the processed password |
| `password_hash` | Hash applied to the entered password |

Supported password hashing mechanisms:

- `md5`
- `sha256`
- `sha512`
- `none`

Example:

```json
"password_required": true,
"password_base": "pIVWb7ovezIB0/5n5s4oLg==",
"password_hash": "md5"
```

For the VRV9517, the encryption passphrase is derived using:

```python
passphrase = password_base + hashlib.md5(factory_wifi_password.encode("utf-8")).hexdigest()
```

The resulting passphrase is used with the configured OpenSSL key derivation.

**Important:** `password_hash` and `key_derivation_digest` are separate settings.

- `password_hash` controls how the entered password is processed.
- `key_derivation_digest` controls the digest used to derive the encryption key and IV.

Do not store device-specific factory passwords in the JSON.

The program requests the password interactively when required.

## 4. Backup Format

The `backup_format` section describes how the router's exported backup file is structured.

Example:

```json
"backup_format": {
    "type": "line-wrapper",
    "header_lines": 1,
    "preserve_header": true,
    "payload_line_length": 64,
    "newline": "\n",
    "checksum": {
        "algorithm": "md5",
        "scope": "encoded-payload-with-newlines",
        "encoding": "hex-lower",
        "after_payload_lines": 8,
        "prefix": {
            "encoding": "base64",
            "random_bytes": 24
        }
    },
    "trailer": {
        "character": "=",
        "repeat": 64
    }
}
```

### Backup Format Fields

| JSON Field | Description |
|---|---|
| `type` | Backup wrapper mechanism |
| `header_lines` | Number of header lines before the payload |
| `preserve_header` | Whether to reuse the original header |
| `payload_line_length` | Number of encoded characters per line |
| `newline` | Line ending used by the encoded payload |

Currently supported wrapper type:

- `line-wrapper`

### Checksum Fields

| JSON Field | Description |
|---|---|
| `checksum.algorithm` | Hash algorithm used for the checksum |
| `checksum.scope` | Which bytes are included in the checksum |
| `checksum.encoding` | Representation of the checksum |
| `checksum.after_payload_lines` | Position where the checksum line is inserted |

Current VRV9517 values:

```json
"algorithm": "md5",
"scope": "encoded-payload-with-newlines",
"encoding": "hex-lower",
"after_payload_lines": 8
```

`encoded-payload-with-newlines` means the checksum is calculated over the complete Base64-encoded encrypted payload, including newline characters.

The header, checksum line, and trailer are excluded.

### Checksum Prefix

| JSON Field | Description |
|---|---|
| `prefix.encoding` | Encoding applied to the random prefix |
| `prefix.random_bytes` | Number of random bytes generated |

Example:

```json
"prefix": {
    "encoding": "base64",
    "random_bytes": 24
}
```

This generates 24 random bytes and Base64-encodes them into 32 characters.

### Trailer

| JSON Field | Description |
|---|---|
| `trailer.character` | Character repeated in the trailer |
| `trailer.repeat` | Number of repetitions |

Example:

```json
"trailer": {
    "character": "=",
    "repeat": 64
}
```

This produces a final line containing 64 equals signs.

**Note:** The current wrapper handler supports the configured line-based structure. An unrelated proprietary binary format requires another reusable handler.

## 5. Archive Format

The `archive` section describes what is contained inside the decrypted payload.

Example:

```json
"archive": {
    "format": "tar",
    "compression": "gzip"
}
```

| JSON Field | Description | Currently Supported |
|---|---|---|
| `archive.format` | Archive type | `tar` |
| `archive.compression` | Compression method | `gzip` |

This configuration describes a `.tar.gz` archive.

Another router using ZIP or a proprietary archive format would require an additional reusable archive handler.

## 6. Configuration File Format

The `configuration_format` field determines how the router's configuration settings are parsed.

Example:

```json
"configuration_format": "key-value"
```

Currently supported:

- `key-value` — UTF-8 files using `KEY=VALUE` entries

Example configuration contents:

```text
LAN_IP=192.168.1.1
DHCP_START=192.168.1.100
DHCP_END=192.168.1.200
```

A router using XML, JSON, or a binary configuration structure would require a suitable reusable parser/editor.

## 7. Editable Configuration Fields

The `config_fields` section defines which settings appear in the View and Edit menus.

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

### Field Rules

`file` specifies the configuration file location relative to the extracted archive.

Every other entry maps a display label to the actual configuration key.

For example:

```json
"wifi_2g_ssid": "ARC_WLAN_24G_SSID_0_ESSID"
```

The left side is the label displayed by the program.

The right side is the exact key found in the configuration file.

### Adding More Fields

To add DHCP settings, extend `config_fields`:

```json
"config_fields": {
    "file": "config/.glbcfg",
    "wifi_2g_ssid": "ARC_WLAN_24G_SSID_0_ESSID",
    "dhcp_start": "ACTUAL_DHCP_START_KEY",
    "dhcp_end": "ACTUAL_DHCP_END_KEY"
}
```

Replace the placeholder DHCP keys with the actual keys found in the extracted configuration.

The editor will automatically display and allow changes to those fields.

No Python changes are needed when adding fields to an already-supported configuration format.

### Editing Behaviour

1. The program reads the configured fields.
2. The current value is displayed.
3. Enter a replacement value.
4. Press Enter to keep the existing value.
5. Review the proposed changes.
6. Confirm before saving.

The original decoded configuration is preserved.

## 8. Complete VRV9517 Example

This example describes the known VRV9517 mechanisms. It is not a universal specification.

```json
{
    "model": "VRV9517",
    "firmware": "v6.00.17 build06",
    "hardware": "R01",
    "encryption": "aes-256-cbc",
    "encoding": "base64",
    "salted": true,
    "password_base": "pIVWb7ovezIB0/5n5s4oLg==",
    "password_hash": "md5",
    "key_derivation": "openssl-legacy",
    "password_required": true,
    "key_derivation_digest": "md5",
    "backup_format": {
        "type": "line-wrapper",
        "header_lines": 1,
        "preserve_header": true,
        "payload_line_length": 64,
        "newline": "\n",
        "checksum": {
            "algorithm": "md5",
            "scope": "encoded-payload-with-newlines",
            "encoding": "hex-lower",
            "after_payload_lines": 8,
            "prefix": {
                "encoding": "base64",
                "random_bytes": 24
            }
        },
        "trailer": {
            "character": "=",
            "repeat": 64
        }
    },
    "archive": {
        "format": "tar",
        "compression": "gzip"
    },
    "configuration_format": "key-value",
    "config_fields": {
        "file": "config/.glbcfg",
        "wifi_2g_ssid": "ARC_WLAN_24G_SSID_0_ESSID",
        "wifi_2g_password": "ARC_WLAN_24G_SSID_0_WPA_Passphrase",
        "wifi_5g_ssid": "ARC_WLAN_5G_SSID_0_ESSID",
        "wifi_5g_password": "ARC_WLAN_5G_SSID_0_WPA_Passphrase"
    }
}
```

## 9. When Python Changes Are Required

| New Router Requirement | JSON Only? |
|---|---|
| Different model or firmware | Yes |
| Different factory password | Yes — enter it when prompted |
| Different configuration field names | Yes |
| Different supported encryption parameters | Yes |
| Different supported backup wrapper settings | Yes |
| New encryption algorithm | No — add a reusable encryption helper |
| New proprietary binary wrapper | No — add a reusable wrapper helper |
| ZIP archive instead of tar.gz | No — add a ZIP archive handler |
| XML configuration instead of key-value | No — add an XML parser/editor |
| `.bin` extension with an otherwise supported internal format | Possibly — file selection must also support `.bin` |

**A file extension does not determine the backup format.**

A `.bin` file could contain AES-encrypted data, compressed archives, or a proprietary binary structure.

The program must support the mechanisms contained inside that file.

## 10. Validation and Testing

When adding another router:

- Always keep an unchanged copy of the original backup.
- Use the correct password if the specifications require one.
- Verify the backup format before editing.
- Test decoding and archive extraction.
- Edit a small number of configuration fields.
- Re-encode and verify the result.
- Confirm the generated backup can be decoded locally.
- Test restoring it only when you have an appropriate recovery method.

**Local round-trip verification does not guarantee the physical router will accept the backup.**

The purpose of this design is to make adding routers straightforward:

**New router with supported mechanisms → new JSON file.**

**New mechanism → new reusable Python helper.**

No router-model-specific processing logic should be necessary.
