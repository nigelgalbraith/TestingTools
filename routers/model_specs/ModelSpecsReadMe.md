# Router Model Specifications

Both projects use the same canonical JSON schema and the same direct mechanism selections.
The only router modules are `modules/router_utils.py` and `modules/router_encryption_utils.py`.

## Adding a Router Model

Copy `doc/RouterSpecificationTemplate.json`, or an existing model specification, and
populate the settings supported by the exported backup. The template includes every
canonical key and nested object; its null values are placeholders, not a runnable
router configuration. Existing Spark and Vodafone specifications are complete examples.

Every specification must contain exactly the canonical keys, including all keys inside
`config_fields`, `backup_format`, `checksum`, `prefix`, `trailer`, and `archive`.
Do not omit inactive fields: use JSON `null`. Empty strings and the string `"unknown"`
are not placeholders for unknown or non-applicable values.

`ROUTER_SPEC_SCHEMA` in `router_utils.py` defines the types and complete structure.
Schema validation rejects missing keys, unexpected keys, incorrectly typed values, and
booleans used as integers. Mechanism validators then require their applicable values.
Errors identify the invalid JSON path. The same model has the same specification values
in both projects, although the configured filenames retain each application's existing names.

The canonical `config_fields` roles are `file`, `wifi_2g_ssid`, `wifi_2g_password`,
`wifi_5g_ssid`, and `wifi_5g_password`. Set unused mappings to null; a known configuration
format requires `file`. Configuration keys are router-specific values, not Python branches.
A new semantic field would require a coordinated canonical-schema update in both projects
and all specifications, rather than adding a one-off JSON key for one router.

## Existing Mechanisms

`router_utils.py` selects encryption using one complete `ENCRYPTION_HANDLERS`
dictionary keyed by `(encryption, key_derivation)`. Its values are imported callables.
Validation and encryption entry points use the same dictionary. Other processing
uses ordinary `if` / `elif` checks. There are no registration calls, function-name
lookup systems, or router-model branches.

| JSON setting | Supported mechanisms |
|---|---|
| `encryption` + `key_derivation` | `aes-256-cbc` + `openssl-legacy`; `aes-256-cbc` + `device-key` (explicitly unavailable) |
| `encoding` | `base64`, `binary` |
| `backup_format.type` | `line-wrapper`, `technicolor-thenc` (structural parsing only) |
| `archive.format` + `archive.compression` | `tar` + `gzip` |
| `configuration_format` | `key-value` |

`encrypt_router_payload` and `decrypt_router_payload` select and call the imported
`crypt_aes_256_cbc` or `crypt_technicolor_thenc` directly. The actual algorithms,
key preparation, credential interpretation and unsupported THENC errors remain in
`router_encryption_utils.py`. File paths and user interaction stay in `router_utils.py`.

Encoding and wrapper entry points select their implementations directly. Archive
workflows call `read_tar_files`, `extract_tar_archive`, and `rebuild_tar_archive`;
`tar_gzip_mode` validates the configured format/compression and supplies the mode.
Configuration workflows call `parse_key_value_fields`, `key_value_values`,
`update_key_value_fields`, and `normalize_key_value_fields` directly. Unsupported
formats fail explicitly. Archive safety and editable-field integrity checks remain.

A router using supported mechanisms requires its JSON specification and configuration
entry/files. A new mechanism requires a substantive implementation and a corresponding
entry in the encryption dictionary. Other new mechanisms use explicit selection branches;
do not introduce additional registries or modules.

## Spark Credentials and Processing

The existing factory Wi-Fi password, passphrase prefix, MD5 password hash, OpenSSL
legacy derivation digest, salt behavior, Base64 layout, checksum, random prefix,
TAR/GZIP archive, and configuration mappings are preserved. Passwords stay in the
existing configured files, separate from model specifications. Login passwords,
Wi-Fi settings being edited, and backup encryption credentials are distinct concepts.

## Vodafone THENC Limitations

Both projects validate the supplied THENC specification and parse the existing header,
16-byte IV, AES block-aligned ciphertext, and configured 20-byte signature boundary.
Parsing establishes structure only; it does not verify the signature or decrypt data.

`password_base`, `password_hash`, `key_derivation_digest`, unknown configuration mappings,
unknown archive settings, and unknown configuration format are null. Non-applicable
line-wrapper fields remain present with null values. The known `salted: false` and
`password_required: false` values and all observed header/key identifiers are preserved.

`CIPHERKEY` and `SIGNATUREKEY` are identifiers, not cryptographic keys. Configured device-key files can now be read as binary. Device-key derivation, signature
verification, signing, and authenticated encryption/rebuilding remain unverified.
Attempting actual cryptographic processing still fails explicitly; even
an explicitly supplied key is rejected until derivation and authentication are verified.
An export-password text file is never read as a binary device key. No router login or
Wi-Fi password is substituted. Archive format and configuration fields remain unknown.

## TestingTools Workflow

`config/RouterConfig.json` stores model entries under `Routers`, with the shared README
path under `Common Locations`. Each model keeps its existing `specs`, `password`,
`template`, decoded/edited/encoded paths, `original`, and migration paths.

The existing actions decode, view, interactively edit, encode, and migrate configurations.
Decode reads the template credential file, or prompts when no path was supplied.
Encode asks for the target router's factory password and verifies the generated backup
by decrypting it locally. Existing overwrite confirmations remain in place.

Migration transfers matching non-null field roles into a prepared destination model,
reports skipped fields and proposed changes, and requires the existing confirmation.
It preserves destination-only settings, unrelated files, whitespace, and line endings.
The source configuration is retained. Cross-syntax migration remains unsupported.

## Optional Device-Key Files

Model entries may include optional `device_key`. Decode and encode append its path
after the existing password/prompt arguments. Migration source decoding uses the source
key; destination preparation and encoding use the destination key.

Device-key models require a configured, nonempty binary key file. Spark ignores these
paths. Loading bytes does not implement or verify Vodafone cryptography. THENC
`CIPHERKEY` and `SIGNATUREKEY` values are read from each backup header and preserved
in wrapper metadata and original header bytes; `cipher_key_id` and `signature_key_id`
are no longer static model specification fields.
