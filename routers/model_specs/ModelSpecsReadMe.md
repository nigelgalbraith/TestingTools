# Router Model Specifications

All TestingTools router specifications use one common schema, including fixed-key
encryption settings and signature parameters. AutomationTools is unchanged by HG659 support.
`modules/router_utils.py` coordinates workflows, credentials and specification validation.
`modules/router_format_utils.py` implements transport encoding, backup wrappers and archive processing.
`modules/router_config_utils.py` implements configuration parsing, transformations and path checks.
`modules/router_encryption_utils.py` implements encryption and cryptographic checksums.

## Adding a Router Model

Copy `doc/RouterSpecificationTemplate.json`, or an existing model specification, and
populate the settings supported by the exported backup. The template includes every
canonical key and nested object; its null values are placeholders, not a runnable
router configuration. Existing Spark and Vodafone specifications are complete examples.

Every specification must contain the canonical base keys, including all keys inside
`config_fields`, `backup_format`, `checksum`, `prefix`, `trailer`, and `archive`.
Every model and the template include `encryption_settings` and `signature`, with the
same nested keys. Unused leaf values must be JSON `null`; neither object may be omitted.
Do not omit inactive fields: use JSON `null`. Empty strings and the string `"unknown"`
are not placeholders for unknown or non-applicable values.

`ROUTER_SPEC_SCHEMA` in `router_utils.py` defines the types and complete structure.
Schema validation rejects missing keys, unexpected keys, incorrectly typed values, and
booleans used as integers. Mechanism validators then require their applicable values.
Errors identify the invalid JSON path. Every TestingTools model uses the same structure, while mechanisms determine which
values must be populated. AutomationTools retains its existing specifications.

The canonical `config_fields` roles are `file`, `wifi_2g_ssid`, `wifi_2g_password`,
`wifi_5g_ssid`, and `wifi_5g_password`. Set unused mappings to null; a known configuration
format requires `file`. Configuration keys are router-specific values, not Python branches.
A new semantic field would require a coordinated canonical-schema update in both projects
and all specifications, rather than adding a one-off JSON key for one router.

## Existing Mechanisms

`router_utils.py` selects encryption using one complete `ENCRYPTION_HANDLERS`
dictionary keyed by `(encryption, key_derivation)`. Its values are imported callables.
Validation and encryption entry points use the same central dictionaries.
Configuration viewing/editing and protected fields use the adjacent registrations;
other processing uses ordinary `if` / `elif` checks. There are no registration calls, function-name
lookup systems, or router-model branches.

| JSON setting | Supported mechanisms |
|---|---|
| `encryption` + `key_derivation` | `aes-256-cbc` + `openssl-legacy`; `aes-256-cbc` + `device-key` (explicitly unavailable); `aes-256-cbc` + `fixed-key` |
| `encoding` | `base64`, `binary` |
| `backup_format.type` | `line-wrapper`, `technicolor-thenc` (structural parsing only); `encrypted-configuration` |
| `archive.format` + `archive.compression` | `tar` + `gzip`; `single-file` + `zlib` |
| `configuration_format` | `key-value`; `xml` (viewing, targeted attribute editing and signed encoding) |

`encrypt_router_payload` and `decrypt_router_payload` select and call the imported
`crypt_aes_256_cbc`, `crypt_technicolor_thenc` or `crypt_aes_256_cbc_fixed_key` directly. The actual algorithms,
key preparation, credential interpretation and unsupported THENC errors remain in
`router_encryption_utils.py`. Workflow path selection and user interaction stay in `router_utils.py`; archive file processing lives in the format module.

Encoding and wrapper entry points select processing mechanisms from the specification.
Their implementations live in `router_format_utils.py`, independently of the orchestrator. Archive
workflows call `read_tar_files`, `extract_tar_archive`, and `rebuild_tar_archive`;
`tar_gzip_mode` validates the configured format/compression and supplies the mode.
Configuration workflows call `router_config_utils.py` functions `parse_key_value_fields`, `key_value_values`,
`update_key_value_fields`, and `normalize_key_value_fields` directly. Unsupported
formats fail explicitly. Archive safety and editable-field integrity checks remain.

A router using supported mechanisms requires its JSON specification and configuration
entry/files. A new mechanism requires a substantive implementation and a corresponding
entry in the relevant existing central dictionary. Other mechanisms use explicit
selection branches; do not introduce additional registries or modules.

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
The source configuration is retained. Wi-Fi conversion supports both key-value → XML
and XML → key-value through the existing registered readers and destination editor.

## Optional Device-Key Files

Model entries may include optional `device_key`. Decode and encode append its path
after the existing password/prompt arguments. Migration source decoding uses the source
key; destination preparation and encoding use the destination key.

Device-key models require a configured, nonempty binary key file. Spark ignores these
paths. Loading bytes does not implement or verify Vodafone cryptography. THENC
`CIPHERKEY` and `SIGNATUREKEY` values are read from each backup header and preserved
in wrapper metadata and original header bytes; `cipher_key_id` and `signature_key_id`
are no longer static model specification fields.


## HG659 B020 fixed-key decoding (TestingTools only)

`Vodafone_HG659-spec.json` describes firmware `V100R001C206B020`. The `hardware`
identifier is the HG659 family; a board revision has not been established.
The encryption dispatcher registers `(aes-256-cbc, fixed-key)` with
`crypt_aes_256_cbc_fixed_key`. This generic cipher processes aligned AES blocks in
both directions and reads no Wi-Fi password. It uses `python3-cryptography`, loaded
only when the fixed-key cipher runs; the existing dependency list includes that package.

`encryption_settings.key_hex` (64 hexadecimal characters) and
`encryption_settings.iv_hex` (32 hexadecimal characters) supply the fixed firmware
AES-256-CBC parameters directly from the selected model specification. HG659 uses the
confirmed B020 values, not the newer B026 values. The generic cipher supports future
routers by reading their own specification values. No firmware key or IV is hardcoded
inside Python. HG659 requires no external credential file, `credentials_path`, Wi-Fi
password or `device_key` configuration entry.

The common `signature` object contains `algorithm`, `modulus_hex`, `exponent` and
`private_exponent_hex`. For HG659 these are `rsa-md5`, its public RSA modulus and
exponent 65537, and the private signing exponent from `hg659_configtool_v026.py`.
The reference modulus/public exponent match the already verified backup parameters.
Spark, Ultra Hub and the template include the same object with every leaf null,
and also have null `encryption_settings` leaves. A null private exponent permits
verification-only specifications; encoding requires valid signing parameters.
Device-unique Ultra Hub keys continue to use its existing private `device_key` path;
Spark continues to use its existing password mechanism.

For `encrypted-configuration`, the entire binary file is AES-256-CBC ciphertext.
After decryption, the processor accepts one complete zlib stream followed by up to
16 zero padding bytes (including the full block added by the reference encoder
when compressed data is already aligned). Decompressed data is bounded to 64 MiB. The last
`backup_format.signature_length` bytes contain the RSA signature; all preceding
bytes, including the final null, are signed. The decoder verifies the entire
PKCS#1 v1.5 block, including FF padding and DER MD5 DigestInfo, against the MD5 digest.
The observed B020 signature contains the binary MD5 digest, whose hex representation
matches the lowercase MD5 hexdigest; it does not contain ASCII hexadecimal characters.
Only after verification is the final null removed and the configured XML declaration
checked. Truncation, wrong credentials, bad padding and invalid signatures fail.

Decode returns the authenticated XML bytes. The existing save/extract pipeline writes
an `.xml` file and a `config_fields.file` copy (`config.xml`) in the decoded directory.
The local original has an XML declaration but fails strict XML parsing at line 815.
The decoder warns and preserves the authenticated bytes exactly; it does not repair or silently
sanitize the configuration, and verification does not imply well-formed XML.

The reference private exponent now enables signed XML backup encoding through the
existing Encode Configuration action. Targeted XML field editing is supported; XML
conversion reuses the same generic Wi-Fi field mappings. Existing menu names and pipelines are retained.
Local cryptographic verification does not establish router restore compatibility;
no hardware restore is tested.

RSA/MD5 verification is implemented by `verify_rsa_md5_signature` in the encryption module.
Signed zlib decoding remains in the format module, and authenticated XML-byte handling
is in the configuration module. XML well-formedness remains advisory during HG659 decoding.


## XML field viewing (TestingTools)

The existing View Configuration operation selects a generic reader from
`CONFIG_VIEW_HANDLERS` using `configuration_format`. Key-value viewing retains its
existing field labels, table layout and validation. XML viewing reads only configured
attributes without requiring the full document to parse as strict XML or rewriting it.

For XML configurations, a non-null `config_fields` mapping has the form
`element|attribute=value|attribute=value|output_attribute`. At least one attribute
condition is required; multiple conditions must all match. Element, condition and
output-attribute names must be valid selector names. Empty components, missing filter
values and repeated filter attributes are rejected. Conditions match attribute values
exactly. The reader accepts single or double quotes and standard XML entity references.
Comment and CDATA contents are excluded from matching.

Each configured field must identify exactly one element with the requested output
attribute; zero matches, multiple matches or a missing attribute fail clearly.
Null mappings are skipped. For a child attribute, use
`element|attribute=value|child_element@output_attribute`. The child search is bounded
to the uniquely selected parent's body, including nested containers; exactly one
matching child is required. HG659 maps the main 2.4GHz and 5GHz SSIDs and passwords,
using both `X_OperatingFrequencyBand` and `X_Is_Guest_Network=0` to exclude guests.
Viewing never saves, updates or normalizes the source file.

Every specification and the template includes the same `field_encryption` object:
`algorithm`, `key_hex`, `iv_hex`, and `fields`. All four are null when unused, as in
Spark and Ultra Hub. HG659 supplies its inner field key and IV as 32-character
hexadecimal strings and lists the two password labels in `fields`. These parameters
are separate from the unchanged AES-256-CBC backup settings.

After XML extraction, the reader applies the registered
`aes-128-cbc-zero-padded-base64` handler only to the listed fields. It strictly decodes
Base64, decrypts with AES-128-CBC, strips trailing zero padding, and decodes UTF-8.
Invalid settings, incomplete ciphertext blocks, embedded zero padding and invalid
UTF-8 fail clearly. SSIDs remain plaintext. The existing View Configuration table
displays the returned values, including decrypted passwords.


## XML field editing (TestingTools)

The existing Edit Configuration action selects `key-value` or `xml` from
`CONFIG_EDIT_HANDLERS`. Key-value edits continue to use the existing parser and
replacement implementation. XML editing reuses the viewer's selector matching to
locate exact attribute-value spans, including bounded child attributes. Each field
must match uniquely; missing, duplicate or overlapping mappings fail before saving.

Only replacement attribute values are written. Both quote styles are supported,
XML special characters are escaped, and unrelated content, whitespace, line endings
and guest-network entries remain byte-identical. The full Huawei document is never
parsed and rewritten. The existing HG659 mappings and common schema are unchanged.

Protected fields use `FIELD_ENCRYPT_HANDLERS` with the existing
`aes-128-cbc-zero-padded-base64` identifier, key, IV and field labels. Replacement
plaintext is encoded as UTF-8, zero padded, encrypted and Base64 encoded; decryption
must recover the supplied value. The decryption algorithm is unchanged. XML password
prompts use ordinary input, and current decrypted values and change summaries are
displayed in plaintext, consistently with the viewer and key-value editor.
Pressing Enter retains the exact stored value, including its original ciphertext.

After confirmation, the editor checks that the edited text equals only the requested
replacements and that re-reading/decryption returns the requested values. These
checks run before staging and again on the staged file. The original decoded file is
checked for changes before publishing the edited directory. Source and destination
directories must be separate; existing overwrite confirmation, staged installation
and rollback handling remain in place.

Saving edited XML does not itself create a router backup. Use the existing Encode
Configuration action to sign, compress and encrypt it. XML migration uses the existing
conversion flow and registered readers/editors.


## Signed single-file configuration encoding (TestingTools)

The existing encoder dispatches on `archive.format`/`archive.compression`: TAR/GZIP
retains its current path, while single-file/zlib validates edited XML against the
authenticated original backup. Only declared field replacements are accepted;
undeclared changes, guest edits, extra files and missing/ambiguous selectors fail.
The existing XML editing and field-encryption implementations are reused unchanged.

`sign_rsa_md5_configuration` builds the complete PKCS#1 v1.5 MD5 DigestInfo block,
uses the specification's private exponent and modulus, and verifies its generated
signature through the existing generic verifier. No signing parameters are stored
in Python or in an external credential file.

`encode_signed_configuration` preserves the edited XML bytes, appends one NUL,
signs that exact sequence, appends the signature, compresses with zlib level 9 and
adds 1–16 zero bytes to reach an AES block boundary, matching the reference encoder.
The orchestrator then calls the existing fixed-key encryption dispatcher and emits
a binary `.conf`. The configured edited intermediate ends in `.xml`.

Before publishing either output, the encoder checks signature verification, AES
and zlib decoding, exact recovered XML and a separate staged-file pass through the
existing decode workflow. The original backup and edited source file are preserved.
The existing overwrite prompts, two-output staging, restricted file permissions
and rollback handling apply. No router upload or restoration is attempted, and
successful local round trips do not prove that firmware will accept a restore.


## Central registrations and processing callbacks

All five handler dictionaries are together under `DISPATCHER HANDLERS` at the top
of `modules/router_utils.py`: `ENCRYPTION_HANDLERS`, `FIELD_ENCRYPT_HANDLERS`,
`FIELD_DECRYPT_HANDLERS`, `CONFIG_VIEW_HANDLERS` and `CONFIG_EDIT_HANDLERS`.
Implementations remain in their specialised encryption, configuration and format
modules, which do not import the orchestrator or contain handler registrations.

The orchestrator selects field callbacks from `field_encryption.algorithm` and
passes them explicitly. `xml_field_values` and the key-value view adapter accept
an optional `decrypt_handler`; `update_xml_fields` and the key-value edit adapter
accept an optional `encrypt_handler`. `validate_xml_field_changes` and
`validate_edited_xml` accept both. Protected fields require the selected callbacks;
there is no hidden registry or fallback in configuration processing. The key-value
adapters accept the same optional arguments without changing their parsing/editing.
Public router workflow signatures are unchanged, and either dependency import order
works without circular imports.

To add a mechanism, implement it in its specialised utility, register it once in
`router_utils.py`, and select it through the common specification. No model-name
checks, new loaders, credential files or separate workflows are needed.


## Cross-format Wi-Fi migration (TestingTools)

The existing migration actions support Spark key-value configurations and HG659 XML
in either direction. No menu operations, states, pipeline definitions or staging paths
change. Source editing, plaintext displays, destination confirmation and password
prompts retain their existing behaviour.

`prepare_config_conversion` extends the former key-value preparation helper. The
orchestrator selects both readers from `CONFIG_VIEW_HANDLERS` and supplies each
source/destination decryption callback. Preparation reads readable values, intersects
non-null configured labels and reports skipped source roles. Only the four common
Wi-Fi roles are declared in the schema; unrelated hardware, WAN and authentication
settings are not transferred. Unsupported readers/editors and missing/ambiguous
configured fields fail clearly before modifying the prepared destination.

`convert_router_config_fields` displays the existing change summary and confirmation,
then calls the destination's `CONFIG_EDIT_HANDLERS` entry with its selected field
encryption callback. XML replacements therefore encrypt source plaintext passwords;
XML source passwords are decrypted before insertion into key-value destinations.
XML attribute escaping and all byte-preserving replacement rules remain unchanged.

Before installation, `validate_xml_field_changes` or
`validate_key_value_field_changes` verifies that only the requested configured fields
changed. Staged bytes are validated again; the source and original prepared destination
are checked for concurrent changes. Unrelated destination bytes, guest entries and
other files are preserved, and the existing directory replacement/rollback is reused.
Cancellation and no-change conversions retain their existing return behaviour.

Prepare Destination Config and Encode Migration Config keep their existing roles.
The same encoder validates against the destination's original backup, rebuilds
TAR/GZIP or signed XML as appropriate and verifies the generated backup by decoding.
Synthetic tests exercise both directions through the existing migration decode,
edit, prepare, convert and encode steps. Source and destination backups remain
unchanged. Local verification does not establish acceptance by physical hardware.
