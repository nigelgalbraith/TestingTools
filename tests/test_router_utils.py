import copy
import contextlib
import inspect
import io
import tempfile
import subprocess
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from modules import router_utils as router
from modules import router_encryption_utils as encryption

ROOT = Path(__file__).resolve().parents[1]
DATA = Path.home() / 'Documents/TestingToolsData/routers'


def specs(name):
    path = ROOT / 'routers/model_specs' / name
    return json.loads(path.read_text())


def thenc_specs():
    result = specs('Vodafone_UltraHub_DGA0130VDF-spec.json')
    # Synthetic layout only: these lengths are NOT verified for the supplied backup.
    result['backup_format'].update(iv_length=16, signature_length=32)
    return result


def thenc_backup(spec):
    fmt = spec['backup_format']
    header = ('PREAMBLE=THENC\nBACKUPVERSION=1.00\nBOARDMNEMONIC=VANT-9\n'
              'PRODUCTNAME=MediaAccess\nSERIALNUMBER=test\nMAC=00:00:00:00:00:00\n'
              'BUILDVERSION=17.4.b.0380-test\n'
              'CIPHERKEY=test-cipher-id\nSIGNATUREKEY=test-signature-id\n\n').encode()
    return header + bytes(range(16)) + b'\x00\xff\n\r' * 16 + b's' * 32


class RouterTests(unittest.TestCase):
    def test_spark_regression(self):
        # Golden ciphertext digest captured from the original implementation.
        for name in ('Spark_SmartModem_VRV9517-spec.json',):
            with self.subTest(name=name):
                spec = specs(name)
                router.validate_model_specs(spec)
                plain = bytes(range(256)) * 4
                for salted in (False, True):
                    current = copy.deepcopy(spec)
                    current['salted'] = salted
                    encrypted = router.encrypt_router_payload(plain, 'test-password', current)
                    self.assertEqual(router.decrypt_router_payload(encrypted, 'test-password', current), plain)
                    if not salted:
                        self.assertEqual(hashlib.sha256(encrypted).hexdigest(),
                                         'aa7a511a17e39f5fc4ed3b8b70d0a272f5a8fd0a1ad61f1ca100ec5ebc1cf465')
                encoded = router.encode_router_payload(encrypted, spec)
                with patch.object(router.os, 'urandom', return_value=b'x' * 24):
                    rebuilt = router.rebuild_router_wrapper(encoded, b'header\n', spec)
                    lines = encoded.splitlines(keepends=True)
                    import base64
                    checksum = base64.b64encode(b'x' * 24) + hashlib.md5(encoded).hexdigest().encode() + b'\n'
                    self.assertEqual(rebuilt, b'header\n' + b''.join(lines[:8]) + checksum + b''.join(lines[8:]) + b'=' * 64 + b'\n')
                parsed = router.parse_router_wrapper(rebuilt, spec)
                self.assertEqual(parsed['encrypted'], encrypted)
                self.assertEqual(parsed['header'], b'header\n')

    def test_supplied_spark(self):
        path = DATA / 'templates/Spark_SmartModem_VRV9517-template.cfg'
        password_path = DATA / 'templatePasswords/Spark_SmartModem_VRV9517-password.txt'
        if not path.exists() or not password_path.exists():
            self.skipTest('Local Spark fixture/password unavailable')
        before = hashlib.sha256(path.read_bytes()).digest()
        for name in ('Spark_SmartModem_VRV9517-spec.json',):
            spec = specs(name)
            parsed = router.parse_router_wrapper(path.read_bytes(), spec)
            rebuilt = router.rebuild_router_wrapper(parsed['encoded'], parsed['header'], spec)
            self.assertEqual(router.parse_router_wrapper(rebuilt, spec)['encrypted'], parsed['encrypted'])
            decoded = router.decode_router_config(str(path), spec, str(password_path))
            self.assertIsInstance(decoded, bytes)
            self.assertEqual(router.decrypt_router_payload(router.encrypt_router_payload(decoded, password_path.read_text().strip(), spec), password_path.read_text().strip(), spec), decoded)
        self.assertEqual(before, hashlib.sha256(path.read_bytes()).digest())

    def test_binary_and_base64(self):
        data = bytes(range(256))
        for spec in (thenc_specs(), specs('Spark_SmartModem_VRV9517-spec.json')):
            self.assertEqual(router.decode_router_payload(router.encode_router_payload(data, spec), spec), data)
        self.assertEqual(router.encode_router_payload(data, thenc_specs()), data)

    def test_thenc_parse_and_dispatch(self):
        spec = thenc_specs()
        data = thenc_backup(spec)
        parsed = router.parse_router_wrapper(data, spec)
        self.assertEqual(parsed['iv'], bytes(range(16)))
        self.assertEqual(parsed['encrypted'], b'\x00\xff\n\r' * 16)
        self.assertEqual(parsed['signature'], b's' * 32)
        self.assertEqual(parsed['header'] + parsed['encoded'], data)
        with patch.object(router, 'parse_technicolor_wrapper', wraps=router.parse_technicolor_wrapper) as helper:
            router.parse_router_wrapper(data, spec)
            helper.assert_called_once_with(data, spec)
        spark = specs('Spark_SmartModem_VRV9517-spec.json')
        with patch.object(router, 'rebuild_line_wrapper', return_value=b'rebuilt') as helper:
            self.assertEqual(router.rebuild_router_wrapper(b'', b'', spark), b'rebuilt')
            helper.assert_called_once()

    def test_invalid_thenc(self):
        spec = thenc_specs()
        data = thenc_backup(spec)
        malformed = [b'', data[:20], data[:-1], data + b'x',
                     data.replace(b'THENC', b'WRONG', 1),
                     data.replace(b'VANT-9', b'VANT-8', 1),
                     data.replace(b'BACKUPVERSION=1.00', b'BACKUPVERSION=2.00'),
                     data.replace(b'BUILDVERSION=17.4', b'BUILDVERSION=18.4'),
                     data.replace(b'CIPHERKEY=test-cipher-id', b'CIPHERKEY='),
                     data.replace(b'SIGNATUREKEY=test-signature-id', b'SIGNATUREKEY='),
                     data.partition(b'\n\n')[0] + b'\n\n' + b'x' * 48]
        for value in malformed:
            with self.subTest(length=len(value)), self.assertRaises(ValueError):
                router.parse_router_wrapper(value, spec)

    def test_incomplete_specifications(self):
        supplied = specs('Vodafone_UltraHub_DGA0130VDF-spec.json')
        del supplied['backup_format']['signature_length']
        with self.assertRaisesRegex(ValueError, 'signature_length'):
            router.validate_model_specs(supplied)
        for key in ('signature_length', 'preamble', 'header_terminator'):
            spec = thenc_specs()
            del spec['backup_format'][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                router.parse_router_wrapper(thenc_backup(thenc_specs()), spec)
        with patch.object(router, 'parse_technicolor_wrapper') as helper:
            with self.assertRaises(ValueError):
                router.parse_router_wrapper(b'', supplied)
            helper.assert_not_called()

    def test_device_key_unavailable(self):
        spec = thenc_specs()
        with patch.dict(router.ENCRYPTION_HANDLERS, {('aes-256-cbc', 'openssl-legacy'): unittest.mock.Mock()}):
            legacy = router.ENCRYPTION_HANDLERS[('aes-256-cbc', 'openssl-legacy')]
            for operation in (router.encrypt_router_payload, router.decrypt_router_payload):
                with self.assertRaisesRegex(ValueError, 'device key unavailable.*device_key_path'):
                    operation(b'ciphertext', '', spec)
            legacy.assert_not_called()
        with self.assertRaisesRegex(ValueError, 'signature signing'):
            router.rebuild_router_wrapper(b'ciphertext', b'header', spec)

    def test_supplied_vodafone_wrapper_and_missing_key(self):
        path = DATA / 'templates/Vodafone_Ultra_Hub-template.bin'
        if not path.exists():
            self.skipTest('Local Vodafone fixture unavailable')
        data = path.read_bytes()
        before = hashlib.sha256(data).digest()
        self.assertTrue(data.startswith(b'PREAMBLE=THENC\n'))
        spec = specs('Vodafone_UltraHub_DGA0130VDF-spec.json')
        router.validate_model_specs(spec)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(router.load_router_model_specs(str(ROOT / 'routers/model_specs/Vodafone_UltraHub_DGA0130VDF-spec.json')), spec)
        parsed = router.parse_router_wrapper(data, spec)
        self.assertEqual(parsed['header'] + parsed['iv'] + parsed['encrypted'] + parsed['signature'], data)
        self.assertEqual(len(parsed['iv']), 16)
        self.assertEqual(len(parsed['signature']), 20)
        self.assertEqual(len(parsed['encrypted']) % 16, 0)
        with self.assertRaisesRegex(ValueError, 'device key unavailable'):
            router.decode_router_config(str(path), spec, str(DATA / 'templatePasswords/Vodafone_Ultra_Hub-password.txt'))
        self.assertEqual(before, hashlib.sha256(path.read_bytes()).digest())

    def test_credentials_are_selected_by_mechanism(self):
        spark = specs('Spark_SmartModem_VRV9517-spec.json')
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'password.txt'
            path.write_text('p' * 64)
            self.assertEqual(router.load_router_credentials(str(path), spark, 'Password: '), 'p' * 64)
            for contents in (b'p' * 64, bytes(range(64)), b'export-password'):
                path.write_bytes(contents)
                with patch.object(Path, 'read_bytes', side_effect=AssertionError('Password must not be read as a key')):
                    with self.assertRaisesRegex(ValueError, 'export password is not a device key'):
                        router.load_router_credentials(str(path), thenc_specs(), 'Password: ')
        with patch.object(router, 'getpass', return_value='interactive'):
            self.assertEqual(router.load_router_credentials(None, spark, 'Password: '), 'interactive')
        for response in ('', KeyboardInterrupt()):
            with patch.object(router, 'getpass', **({'side_effect': response} if isinstance(response, BaseException) else {'return_value': response})):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertIs(router.load_router_credentials(None, spark, 'Password: '), False)
        spark['password_required'] = False
        self.assertEqual(router.load_router_credentials(None, spark, 'Password: '), '')

    def test_unverified_device_key_never_invokes_openssl(self):
        with patch.object(router.subprocess, 'run') as command:
            with self.assertRaisesRegex(ValueError, 'signature verification are not established'):
                router.decrypt_router_payload(b'x' * 16, '', thenc_specs(), wrapper={}, device_key=b'k' * 64)
            command.assert_not_called()

    def test_target_credentials_dispatch_and_password_compatibility(self):
        spark = specs('Spark_SmartModem_VRV9517-spec.json')
        default_prompt = 'Enter target router password (Enter to use template password): '
        with patch.object(router, 'get_target_router_password', return_value='template') as prompt:
            self.assertEqual(router.load_target_router_credentials('template', spark, default_prompt), 'template')
            prompt.assert_called_once_with(spark, 'template')
        with patch.object(router, 'getpass', return_value='destination') as prompt:
            self.assertEqual(router.load_target_router_credentials('template', spark, 'Custom: '), 'destination')
            prompt.assert_called_once_with('Custom: ')
        for response in ('', EOFError(), KeyboardInterrupt()):
            options = {'side_effect': response} if isinstance(response, BaseException) else {'return_value': response}
            with patch.object(router, 'getpass', **options), contextlib.redirect_stdout(io.StringIO()):
                self.assertIs(router.load_target_router_credentials('template', spark, 'Custom: '), False)
        spark['password_required'] = False
        with patch.object(router, 'getpass') as prompt:
            self.assertEqual(router.load_target_router_credentials('template', spark, default_prompt), '')
            prompt.assert_not_called()
        with patch.object(router, 'getpass') as prompt:
            with self.assertRaisesRegex(ValueError, 'destination device key unavailable'):
                router.load_target_router_credentials('export-password', thenc_specs(), default_prompt)
            prompt.assert_not_called()
        credential = object()
        helper = unittest.mock.Mock(return_value=credential)
        with patch.object(router, 'load_target_device_key_credentials', helper):
            self.assertIs(router.load_target_router_credentials(credential, thenc_specs(), default_prompt), credential)
            helper.assert_called_once_with(credential, thenc_specs(), default_prompt)

    def test_encode_passes_wrapper_context_to_decryption(self):
        spec = specs('Spark_SmartModem_VRV9517-spec.json')
        original_wrapper = {'encrypted': b'original', 'header': b'header', 'iv': b'original-iv'}
        verified_wrapper = {'encrypted': b'updated', 'header': b'header', 'iv': b'updated-iv'}
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            directory = Path(temporary)
            original = directory / 'original.cfg'
            original.write_bytes(b'original backup')
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(router, 'parse_router_wrapper', side_effect=[original_wrapper, verified_wrapper]))
                stack.enter_context(patch.object(router, 'load_router_credentials', return_value='source'))
                stack.enter_context(patch.object(router, 'load_target_router_credentials', return_value='target'))
                decrypt = stack.enter_context(patch.object(router, 'decrypt_router_payload', side_effect=[b'archive', b'rebuilt archive']))
                stack.enter_context(patch.object(router, 'rebuild_tar_archive', return_value=(b'rebuilt archive', [])))
                stack.enter_context(patch.object(router, 'validate_edited_fields'))
                stack.enter_context(patch.object(router, 'encrypt_router_payload', return_value=b'ciphertext'))
                stack.enter_context(patch.object(router, 'rebuild_router_wrapper', return_value=b'new backup'))
                stack.enter_context(patch.object(router, 'validate_tar_gzip_config'))
                output = directory / 'output.cfg'
                self.assertEqual(router.encode_router_config(str(directory / 'edited'), str(original), str(directory / 'edited.tar.gz'), str(output), spec, 'password.txt'), str(output))
                self.assertEqual(decrypt.call_args_list, [unittest.mock.call(b'original', 'source', spec, wrapper=original_wrapper, device_key_path=None), unittest.mock.call(b'updated', 'target', spec, wrapper=verified_wrapper, device_key_path=None)])
                self.assertEqual(original.read_bytes(), b'original backup')

    def test_unsupported_combinations_and_draft_operations(self):
        for key, value in (('encoding', 'binary'), ('key_derivation', 'device-key'),
                           ('configuration_format', 'unknown'), ('encryption', 'invented')):
            spec = specs('Spark_SmartModem_VRV9517-spec.json')
            spec[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                router.validate_model_specs(spec)
        with self.assertRaisesRegex(ValueError, 'Unsupported archive'):
            router.tar_gzip_mode(thenc_specs(), 'r')
        with self.assertRaisesRegex(ValueError, 'Unsupported configuration'):
            router.parse_key_value_fields('x=y', thenc_specs())
        for field, value in (('iv_length', 0), ('iv_length', True), ('signature_length', 0), ('signature_length', True)):
            spec = thenc_specs()
            spec['backup_format'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                router.validate_model_specs(spec)

    def test_supported_mechanisms_do_not_depend_on_router_identity(self):
        spec = specs('Spark_SmartModem_VRV9517-spec.json')
        spec.update(model='another-router', firmware='another-firmware', hardware='another-hardware')
        router.validate_model_specs(spec)
        plain = bytes(range(256)) * 4
        encrypted = router.encrypt_router_payload(plain, 'credential', spec)
        self.assertEqual(router.decrypt_router_payload(encrypted, 'credential', spec), plain)
        backup = router.rebuild_router_wrapper(router.encode_router_payload(encrypted, spec), b'header\n', spec)
        self.assertEqual(router.parse_router_wrapper(backup, spec)['encrypted'], encrypted)

    def test_spark_full_encode_and_original_preservation(self):
        source = DATA / 'templates/Spark_SmartModem_VRV9517-template.cfg'
        password = DATA / 'templatePasswords/Spark_SmartModem_VRV9517-password.txt'
        if not source.exists() or not password.exists():
            self.skipTest('Local Spark fixtures unavailable')
        original_data = source.read_bytes()
        for name in ('Spark_SmartModem_VRV9517-spec.json',):
            spec = specs(name)
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
                directory = Path(temporary)
                original = directory / 'original.cfg'
                original.write_bytes(original_data)
                decoded = router.decode_router_config(str(original), spec, str(password), 'Enter router password: ', str(directory / 'unused-key.bin'))
                archive = directory / 'decoded.tar.gz'
                edited = directory / 'edited'
                self.assertTrue(router.save_router_config(decoded, str(archive), spec))
                self.assertEqual(router.extract_router_config(str(archive), str(edited), spec), str(edited))
                # Update a real editable value to exercise archive rebuilding and validation.
                config_file = edited / spec['config_fields']['file']
                lines, fields = router.parse_key_value_fields(config_file.read_text(), spec)
                index = next(iter(fields.values()))[1]
                lines[index] = lines[index].split('=', 1)[0] + '=RegressionSSID\n'
                config_file.write_text(''.join(lines))
                output = directory / 'encoded.cfg'
                rebuilt_archive = directory / 'edited.tar.gz'
                with patch.object(router, 'get_target_router_password', side_effect=lambda spec, template: template):
                    self.assertEqual(router.encode_router_config(str(edited), str(original), str(rebuilt_archive), str(output), spec, str(password), 'Enter target router password (Enter to use template password): ', str(directory / 'unused-key.bin')), str(output))
                self.assertEqual(router.decode_router_config(str(output), spec, str(password)), rebuilt_archive.read_bytes())
                self.assertEqual(original.read_bytes(), original_data)
                self.assertIs(router.encode_router_config(str(edited), str(original), str(rebuilt_archive), str(original), spec, str(password)), False)
                self.assertEqual(original.read_bytes(), original_data)
        self.assertEqual(source.read_bytes(), original_data)

    def test_conversion_preserves_source_and_destination_only_fields(self):
        source_specs = specs('Spark_SmartModem_VRV9517-spec.json')
        destination_specs = copy.deepcopy(source_specs)
        source_specs['config_fields']['wifi_5g_password'] = None
        destination_specs['model'] = 'another-model-using-existing-mechanisms'
        destination_specs['config_fields']['file'] = 'different/settings.conf'
        destination_specs['config_fields']['wifi_2g_password'] = None
        for label, key in destination_specs['config_fields'].items():
            if label != 'file' and key is not None:
                destination_specs['config_fields'][label] = 'DEST_' + key
        router.validate_model_specs(source_specs)
        router.validate_model_specs(destination_specs)
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            source, destination = Path(temporary) / 'source', Path(temporary) / 'destination'
            source_file = source / source_specs['config_fields']['file']
            destination_file = destination / destination_specs['config_fields']['file']
            source_file.parent.mkdir(parents=True)
            destination_file.parent.mkdir(parents=True)
            source_content = ''.join(f'{key}=source-{label}\r\n' for label, key in source_specs['config_fields'].items() if label != 'file' and key is not None).encode()
            destination_content = ''.join(f'{key}=old-{label}\r\n' for label, key in destination_specs['config_fields'].items() if label != 'file' and key is not None).encode() + b'LOCKED=keep\r\n'
            source_file.write_bytes(source_content)
            destination_file.write_bytes(destination_content)
            (destination / 'untouched').write_bytes(b'keep')
            with patch.object(router, 'confirm', return_value=False):
                self.assertIs(router.convert_router_config_fields(str(source), str(destination), source_specs, destination_specs), False)
            self.assertEqual(destination_file.read_bytes(), destination_content)
            with patch.object(router, 'confirm', return_value=True):
                self.assertEqual(router.convert_router_config_fields(str(source), str(destination), source_specs, destination_specs), str(destination))
            contents = destination_file.read_bytes()
            self.assertIn(b'=source-wifi_2g_ssid\r\n', contents)
            self.assertIn(b'=source-wifi_5g_ssid\r\n', contents)
            self.assertIn(b'=old-wifi_5g_password\r\n', contents)
            self.assertIn(b'LOCKED=keep\r\n', contents)
            self.assertEqual((destination / 'untouched').read_bytes(), b'keep')
            self.assertEqual(source_file.read_bytes(), source_content)

    def test_optional_device_key_pipeline_arguments_preserve_prompts_and_migration_roles(self):
        import inspect
        from constants import RouterConstants as constants
        config = json.loads((ROOT / 'config/RouterConfig.json').read_text())
        source = copy.deepcopy(config['Routers']['Vodafone_Ultra_Hub'])
        destination = copy.deepcopy(source)
        source['device_key'], destination['device_key'] = 'source-key.bin', 'destination-key.bin'
        meta = {'Routers': {'source': source, 'destination': destination}}
        ctx = {'selected_router': 'source', 'destination_router': 'destination',
               'model_specs': thenc_specs(), 'destination_specs': thenc_specs()}
        self.assertEqual(constants.DEVICE_KEY, 'device_key')
        self.assertNotIn(constants.DEVICE_KEY, constants.SECONDARY_VALIDATION['Routers']['required_job_fields'])
        cases = ((constants.DECODE_ROUTER_CONFIG_EXEC, 'source-key.bin', 'Enter router password: '),
                 (constants.MIGRATION_DECODE_ROUTER_CONFIG_EXEC, 'source-key.bin', 'Enter SOURCE router password: '),
                 (constants.MIGRATION_CONVERT_DECODE_EXEC, 'destination-key.bin', 'Enter router password: '),
                 (constants.ENCODE_ROUTER_CONFIG_EXEC, 'source-key.bin', 'Enter target router password (Enter to use template password): '),
                 (constants.RUN_ALL_ENCODE_ROUTER_CONFIG_EXEC, 'source-key.bin', 'Enter target router password (Enter to use template password): '),
                 (constants.MIGRATION_ENCODE_ROUTER_CONFIG_EXEC, 'destination-key.bin', 'Enter DESTINATION router password: '),
                 (constants.RUN_ALL_MIGRATION_ENCODE_ROUTER_CONFIG_EXEC, 'destination-key.bin', 'Enter DESTINATION router password: '))
        for pipeline, key_path, prompt in cases:
            step = pipeline[0]
            values = [value('job', meta, ctx) if callable(value) else value for value in step['args']]
            bound = inspect.signature(step['fn']).bind(*values)
            self.assertEqual(bound.arguments['device_key_path'], key_path)
            self.assertEqual(bound.arguments['password_prompt'], prompt)
            if step['fn'] is router.decode_router_config and pipeline is constants.MIGRATION_DECODE_ROUTER_CONFIG_EXEC:
                self.assertIsNone(bound.arguments['password_path'])
            else:
                selected = destination if key_path == 'destination-key.bin' else source
                self.assertEqual(bound.arguments['password_path'], selected['password'])
        source.pop('device_key')
        values = [value('job', meta, ctx) for value in constants.DECODE_ROUTER_CONFIG_EXEC[0]['args']]
        self.assertIsNone(inspect.signature(router.decode_router_config).bind(*values).arguments['device_key_path'])

    def test_public_signatures_and_crypto_compatibility(self):
        expected = {
            'get_target_router_password': ['model_specs', 'template_password'],
            'get_router_template_password': ['model_specs', 'password_path'],
            'load_router_model_specs': ['specs_path'],
            'read_router_backup': ['config_path'],
            'validate_model_specs': ['specs'],
            'validate_line_wrapper_specs': ['specs'],
            'validate_technicolor_specs': ['specs'],
            'decrypt_router_payload': ['data', 'password', 'model_specs', 'wrapper', 'device_key'],
            'encrypt_router_payload': ['data', 'password', 'model_specs'],
            'load_router_credentials': ['password_path', 'model_specs', 'password_prompt'],
            'load_target_router_credentials': ['template_credentials', 'model_specs', 'password_prompt'],
            'encode_router_payload': ['data', 'specs'],
            'decode_router_payload': ['data', 'specs'],
            'encode_base64_payload': ['data', 'specs'],
            'decode_base64_payload': ['data', 'specs'],
            'wrapper_trailer': ['fmt'],
            'parse_router_wrapper': ['data', 'model_specs'],
            'parse_line_wrapper': ['data', 'model_specs'],
            'parse_technicolor_wrapper': ['data', 'model_specs'],
            'rebuild_router_wrapper': ['encoded', 'header', 'specs'],
            'rebuild_technicolor_wrapper': ['encoded', 'header', 'specs'],
            'rebuild_line_wrapper': ['encoded', 'header', 'specs'],
            'safe_relative': ['name'],
            'tar_gzip_mode': ['specs', 'operation'],
            'validate_archive': ['archive'],
            'validate_directory': ['directory'],
            'decode_router_config': ['config_path', 'model_specs', 'password_path', 'password_prompt'],
            'validate_tar_gzip_config': ['decoded', 'model_specs'],
            'save_router_config': ['decoded_config', 'decoded_config_path', 'model_specs'],
            'extract_router_config': ['archive_path', 'output_dir', 'model_specs'],
            'convert_router_config_fields': ['source_dir', 'destination_dir', 'source_specs', 'destination_specs'],
            'view_router_config_fields': ['config_dir', 'model_specs'],
            'edit_router_config_fields': ['config_dir', 'edited_dir', 'model_specs'],
            'encode_router_config': ['edited_dir', 'original_cfg', 'edited_archive_path', 'output_path', 'model_specs', 'password_path', 'password_prompt'],
            'parse_key_value_fields': ['contents', 'specs'],
            'validate_edited_fields': ['original_archive', 'directory', 'specs'],
            'validate_key_value_specs': ['specs'],
        }
        for name, parameters in expected.items():
            with self.subTest(function=name):
                self.assertTrue(callable(getattr(router, name, None)))
                actual = list(inspect.signature(getattr(router, name)).parameters)
                self.assertEqual(actual[:len(parameters)], parameters)
        self.assertEqual(len(inspect.signature(router.decrypt_router_payload).parameters), 6)

class RouterArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.spark = json.loads(next((ROOT / 'routers/model_specs').glob('Spark*.json')).read_text())
        self.vodafone = json.loads((ROOT / 'routers/model_specs/Vodafone_UltraHub_DGA0130VDF-spec.json').read_text())

    def schema_paths(self, schema=None, prefix=()):
        for key, kind in (router.ROUTER_SPEC_SCHEMA if schema is None else schema).items():
            path = prefix + (key,)
            yield path, kind
            if isinstance(kind, dict):
                yield from self.schema_paths(kind, path)

    def parent_at(self, data, path):
        for key in path[:-1]:
            data = data[key]
        return data

    def test_every_schema_key_is_required_and_type_checked(self):
        for original in (self.spark, self.vodafone):
            for path, kind in self.schema_paths():
                label = '.'.join(path)
                with self.subTest(model=original['model'], key=label, mutation='missing'):
                    current = copy.deepcopy(original)
                    del self.parent_at(current, path)[path[-1]]
                    with self.assertRaisesRegex(ValueError, label):
                        router.validate_model_specs(current)
                with self.subTest(model=original['model'], key=label, mutation='type'):
                    current = copy.deepcopy(original)
                    self.parent_at(current, path)[path[-1]] = []
                    with self.assertRaisesRegex(ValueError, label):
                        router.validate_model_specs(current)
                if kind is int:
                    current = copy.deepcopy(original)
                    self.parent_at(current, path)[path[-1]] = True
                    with self.subTest(model=original['model'], key=label, mutation='bool'), self.assertRaisesRegex(ValueError, label):
                        router.validate_model_specs(current)

    def test_unexpected_keys_in_every_object_are_rejected(self):
        objects = [()] + [path for path, kind in self.schema_paths() if isinstance(kind, dict)]
        for original in (self.spark, self.vodafone):
            for path in objects:
                current = copy.deepcopy(original)
                target = current
                for key in path:
                    target = target[key]
                target['misspelled'] = None
                label = '.'.join(path + ('misspelled',))
                with self.subTest(model=original['model'], key=label), self.assertRaisesRegex(ValueError, label):
                    router.validate_model_specs(current)

    def test_null_applicability_and_required_values(self):
        router.validate_model_specs(self.spark)
        router.validate_model_specs(self.vodafone)
        paths = [('salted',), ('password_required',), ('password_base',), ('password_hash',), ('key_derivation_digest',),
                 ('backup_format', 'header_lines'), ('backup_format', 'preserve_header'),
                 ('backup_format', 'payload_line_length'), ('backup_format', 'newline'),
                 ('backup_format', 'checksum', 'algorithm'), ('backup_format', 'checksum', 'scope'),
                 ('backup_format', 'checksum', 'encoding'), ('backup_format', 'checksum', 'after_payload_lines'),
                 ('backup_format', 'checksum', 'prefix', 'encoding'), ('backup_format', 'checksum', 'prefix', 'random_bytes'),
                 ('backup_format', 'trailer', 'character'), ('backup_format', 'trailer', 'repeat'),
                 ('archive', 'compression'), ('config_fields', 'file')]
        for path in paths:
            current = copy.deepcopy(self.spark)
            self.parent_at(current, path)[path[-1]] = None
            with self.subTest(key='.'.join(path)), self.assertRaisesRegex(ValueError, '.'.join(path)):
                router.validate_model_specs(current)
        for key in ('iv_length', 'signature_length', 'preamble', 'backup_version', 'header_terminator'):
            current = copy.deepcopy(self.vodafone)
            current['backup_format'][key] = None
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'backup_format.' + key):
                router.validate_model_specs(current)
        for key in self.spark['config_fields']:
            if key != 'file':
                self.spark['config_fields'][key] = None
        router.validate_model_specs(self.spark)
        self.assertEqual(router.parse_key_value_fields('LOCKED=value\n', self.spark)[1], {})
        for field in ('password_base', 'password_hash', 'key_derivation_digest'):
            self.assertIsNone(self.vodafone[field])
        self.assertTrue(all(value is None for value in self.vodafone['config_fields'].values()))

    def test_specs_schema_and_crypto_match_across_projects(self):
        import ast
        other_name = 'AutomationTools' if ROOT.name == 'TestingTools' else 'TestingTools'
        other = ROOT.parent / other_name
        other_specs = {data['model']: data for path in (other / 'routers/model_specs').glob('*.json')
                       for data in [json.loads(path.read_text())]}
        for current in (self.spark, self.vodafone):
            self.assertEqual(current, other_specs[current['model']])
        template = json.loads((ROOT / 'doc/RouterSpecificationTemplate.json').read_text())
        router.validate_spec_schema(template)
        self.assertEqual(template, json.loads((other / 'doc/RouterSpecificationTemplate.json').read_text()))
        def definitions(path):
            tree = ast.parse(path.read_text())
            return {node.targets[0].id if isinstance(node, ast.Assign) else node.name: ast.dump(node)
                    for node in tree.body if isinstance(node, ast.FunctionDef) or
                    isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'ROUTER_SPEC_SCHEMA'}
        current = definitions(ROOT / 'modules/router_utils.py')
        peer = definitions(other / 'modules/router_utils.py')
        for name in ('ROUTER_SPEC_SCHEMA', 'validate_model_specs', 'decrypt_router_payload', 'encrypt_router_payload',
                     'encode_router_payload', 'decode_router_payload', 'parse_router_wrapper', 'rebuild_router_wrapper',
                     'tar_gzip_mode', 'read_tar_files', 'extract_tar_archive', 'rebuild_tar_archive', 'parse_key_value_fields'):
            self.assertEqual(current[name], peer[name], name)
        self.assertEqual((ROOT / 'modules/router_encryption_utils.py').read_text(), (other / 'modules/router_encryption_utils.py').read_text())

    def test_thenc_parsing_and_explicit_crypto_failure(self):
        spec = copy.deepcopy(self.vodafone)
        fmt = spec['backup_format']
        header = ('PREAMBLE=THENC\nBACKUPVERSION=1.00\nBOARDMNEMONIC=VANT-9\n'
                  'PRODUCTNAME=MediaAccess\nSERIALNUMBER=test\nMAC=00:00:00:00:00:00\n'
                  'BUILDVERSION=17.4.b.0380-test\n'
                  'CIPHERKEY=test-cipher-id\nSIGNATUREKEY=test-signature-id\n\n').encode()
        data = header + bytes(range(16)) + b'ciphertext-block' * 4 + b's' * fmt['signature_length']
        wrapper = router.parse_router_wrapper(data, spec)
        self.assertEqual(wrapper['header'] + wrapper['iv'] + wrapper['encrypted'] + wrapper['signature'], data)
        self.assertEqual(wrapper['iv'], bytes(range(16)))
        self.assertEqual(wrapper['signature'], b's' * fmt['signature_length'])
        with patch.object(router.subprocess, 'run') as command:
            with self.assertRaisesRegex(ValueError, 'device key unavailable.*export password is not a device key'):
                router.decrypt_router_payload(wrapper['encrypted'], 'export-password', spec, wrapper=wrapper)
            with self.assertRaisesRegex(ValueError, 'signature verification are not established'):
                router.decrypt_router_payload(wrapper['encrypted'], '', spec, wrapper=wrapper, device_key=b'k' * 32)
            with self.assertRaisesRegex(ValueError, 'device key unavailable.*device_key_path'):
                router.encrypt_router_payload(b'plain', '', spec)
            command.assert_not_called()
        for malformed in (data[:-1], data.replace(b'VANT-9', b'VANT-8'), data.replace(b'THENC', b'WRONG')):
            with self.assertRaises(ValueError):
                router.parse_router_wrapper(malformed, spec)
        with tempfile.TemporaryDirectory() as temporary:
            password = Path(temporary) / 'export-password.txt'
            password.write_text('export-password')
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('Must not read a text password as a key')):
                with self.assertRaisesRegex(ValueError, 'export password is not a device key'):
                    router.read_router_credential(str(password), spec)

    def test_null_mappings_can_be_viewed(self):
        current = copy.deepcopy(self.spark)
        current['config_fields'] = {key: value if key == 'file' else None for key, value in current['config_fields'].items()}
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            path = Path(temporary) / current['config_fields']['file']
            path.parent.mkdir(parents=True)
            path.write_text('LOCKED=keep\n')
            self.assertTrue(router.view_router_config_fields(temporary, current))

    def test_archive_replacement_restores_destination_on_interruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination, staged = Path(temporary) / 'destination', Path(temporary) / 'staged'
            destination.mkdir()
            staged.mkdir()
            (destination / 'old').write_bytes(b'original')
            (staged / 'new').write_bytes(b'replacement')
            replace = router.os.replace
            def interrupt(source, target):
                if Path(source) == staged:
                    raise KeyboardInterrupt()
                return replace(source, target)
            with patch.object(router.os, 'replace', side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
                router.replace_router_directory(staged, destination)
            self.assertEqual((destination / 'old').read_bytes(), b'original')
            self.assertTrue((staged / 'new').exists())

    def test_encryption_selection_calls_imported_implementation_directly(self):
        self.assertIs(router.crypt_aes_256_cbc, encryption.crypt_aes_256_cbc)
        self.assertIs(router.crypt_technicolor_thenc, encryption.crypt_technicolor_thenc)
        self.assertEqual(router.ENCRYPTION_HANDLERS, {('aes-256-cbc', 'openssl-legacy'): encryption.crypt_aes_256_cbc, ('aes-256-cbc', 'device-key'): encryption.crypt_technicolor_thenc})
        helper = unittest.mock.Mock(wraps=encryption.crypt_aes_256_cbc)
        with patch.dict(router.ENCRYPTION_HANDLERS, {('aes-256-cbc', 'openssl-legacy'): helper}):
            encrypted = router.encrypt_router_payload(b'direct implementation', 'password', self.spark)
            self.assertEqual(router.decrypt_router_payload(encrypted, 'password', self.spark), b'direct implementation')
        self.assertEqual(helper.call_count, 2)
        self.assertEqual(helper.call_args_list[0], unittest.mock.call(b'direct implementation', 'password', self.spark, False))
        self.assertEqual(helper.call_args_list[1], unittest.mock.call(encrypted, 'password', self.spark, True, wrapper=None, device_key=None))
        wrapper = {'iv': b'context'}
        helper = unittest.mock.Mock(side_effect=ValueError('test failure'))
        with patch.dict(router.ENCRYPTION_HANDLERS, {('aes-256-cbc', 'device-key'): helper}):
            with self.assertRaisesRegex(ValueError, 'test failure'):
                router.decrypt_router_payload(b'cipher', '', self.vodafone, wrapper=wrapper, device_key=b'key')
            helper.assert_called_once_with(b'cipher', '', self.vodafone, True, wrapper=wrapper, device_key=b'key')

    def test_unsupported_encryption_pairs_fail_before_crypto(self):
        for cipher, derivation in (('unsupported-cipher', 'openssl-legacy'), ('aes-256-cbc', 'unsupported-derivation')):
            current = copy.deepcopy(self.spark)
            current.update(encryption=cipher, key_derivation=derivation)
            for operation in (router.encrypt_router_payload, router.decrypt_router_payload):
                with self.subTest(cipher=cipher, derivation=derivation, operation=operation.__name__):
                    with patch.object(encryption.subprocess, 'run') as command, self.assertRaisesRegex(ValueError, 'Unsupported encryption mechanism:'):
                        operation(b'data', 'password', current)
                    command.assert_not_called()
                    with patch.object(router, 'validate_model_specs'), self.assertRaisesRegex(ValueError, 'Unsupported encryption mechanism:'):
                        operation(b'data', 'password', current)

    def test_module_layout_has_no_encryption_forwarding_functions(self):
        import ast
        forbidden = {'mechanism_handler', 'archive_handler', 'archive_mode', 'rebuild_router_archive', 'configuration_handler', 'parse_config_fields', 'decrypt_openssl_legacy_payload', 'encrypt_openssl_legacy_payload', 'decrypt_device_key_payload',
                     'decrypt_password_payload', 'encrypt_password_payload'}
        module_files = {path.name for path in (ROOT / 'modules').glob('router*.py')}
        self.assertEqual(module_files, {'router_utils.py', 'router_encryption_utils.py'})
        for filename in module_files:
            path = ROOT / 'modules' / filename
            source = path.read_text()
            tree = ast.parse(source)
            definitions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
            self.assertFalse(forbidden & definitions.keys())
            if filename == 'router_utils.py':
                self.assertNotIn('crypt_aes_256_cbc', definitions)
                self.assertNotIn('globals()', source)
                self.assertEqual({node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id.endswith('_HANDLERS')}, {'ENCRYPTION_HANDLERS'})
                self.assertNotIn('binary_payload', source)
                self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'update' for node in ast.walk(tree)))
            lines = source.splitlines()
            previous = None
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    self.assertTrue(all(line.strip() for line in lines[node.lineno-1:node.end_lineno]), node.name)
                    if previous is not None:
                        gap = lines[previous.end_lineno:node.lineno-1]
                        if not any(line.strip() for line in gap):
                            self.assertEqual(len(gap), 2, node.name)
                    previous = node

    def test_binary_transport_returns_original_object(self):
        data = bytes(range(256))
        for value in (data, b''):
            self.assertIs(router.encode_router_payload(value, self.vodafone), value)
            self.assertIs(router.decode_router_payload(value, self.vodafone), value)
        self.assertFalse(hasattr(router, 'binary_payload'))

    def test_device_key_files_are_binary_and_crypto_remains_unavailable(self):
        key = bytes(range(32)) + b'\xff\x00\n'
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'key.bin'
            path.write_bytes(key)
            helper = unittest.mock.Mock(side_effect=ValueError('crypto unavailable'))
            wrapper = {'iv': b'context'}
            with patch.dict(router.ENCRYPTION_HANDLERS, {('aes-256-cbc', 'device-key'): helper}):
                with self.assertRaisesRegex(ValueError, 'crypto unavailable'):
                    router.decrypt_router_payload(b'cipher', '', self.vodafone, wrapper=wrapper, device_key_path=str(path))
                helper.assert_called_once_with(b'cipher', '', self.vodafone, True, wrapper=wrapper, device_key=key)
                helper.reset_mock()
                with self.assertRaisesRegex(ValueError, 'crypto unavailable'):
                    router.encrypt_router_payload(b'plain', '', self.vodafone, str(path))
                helper.assert_called_once_with(b'plain', '', self.vodafone, False, device_key=key)
            with patch.object(encryption.subprocess, 'run') as command:
                with self.assertRaisesRegex(ValueError, 'derivation and signature verification are not established'):
                    router.decrypt_router_payload(b'cipher', '', self.vodafone, device_key_path=str(path))
                with self.assertRaisesRegex(ValueError, 'signature signing are not established'):
                    router.encrypt_router_payload(b'plain', '', self.vodafone, str(path))
                command.assert_not_called()

    def test_device_key_paths_are_required_only_for_device_key_mechanisms(self):
        with tempfile.TemporaryDirectory() as temporary:
            empty = Path(temporary) / 'empty.bin'
            empty.write_bytes(b'')
            for operation in (router.decrypt_router_payload, router.encrypt_router_payload):
                for path in (None, ''):
                    with self.subTest(operation=operation.__name__, path=path), self.assertRaisesRegex(ValueError, 'device_key_path is required'):
                        operation(b'data', '', self.vodafone, device_key_path=path)
                with self.assertRaisesRegex(ValueError, 'device key file is empty'):
                    operation(b'data', '', self.vodafone, device_key_path=str(empty))
                with self.assertRaises(FileNotFoundError):
                    operation(b'data', '', self.vodafone, device_key_path=str(empty.parent / 'missing.bin'))
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('Spark must not read a device key')):
                encrypted = router.encrypt_router_payload(b'Spark without a key', 'password', self.spark, str(empty))
                self.assertEqual(router.decrypt_router_payload(encrypted, 'password', self.spark, device_key_path='missing.bin'), b'Spark without a key')

    def test_thenc_identifiers_come_from_each_header_and_decode_receives_key(self):
        fmt = self.vodafone['backup_format']
        header = ('PREAMBLE=THENC\nBACKUPVERSION=1.00\nBOARDMNEMONIC=VANT-9\n'
                  'PRODUCTNAME=MediaAccess\nSERIALNUMBER=test\nMAC=00:00:00:00:00:00\n'
                  'BUILDVERSION=17.4.b.0380-test\nCIPHERKEY=dynamic-cipher\nSIGNATUREKEY=dynamic-signature\n\n').encode()
        backup = header + bytes(range(16)) + b'x' * 32 + b's' * fmt['signature_length']
        wrapper = router.parse_router_wrapper(backup, self.vodafone)
        self.assertEqual(wrapper['cipher_key_id'], 'dynamic-cipher')
        self.assertEqual(wrapper['signature_key_id'], 'dynamic-signature')
        self.assertEqual(wrapper['header'], header)
        for field in ('CIPHERKEY', 'SIGNATUREKEY'):
            changed = backup.replace((field + '=dynamic-').encode(), (field + '=different-').encode())
            self.assertEqual(router.parse_router_wrapper(changed, self.vodafone)['header'], changed.partition(b'\n\n')[0] + b'\n\n')
        for field in ('CIPHERKEY=dynamic-cipher', 'SIGNATUREKEY=dynamic-signature'):
            malformed = backup.replace(field.encode(), (field.split('=')[0] + '=').encode())
            with self.assertRaisesRegex(ValueError, 'Invalid THENC header field'):
                router.parse_router_wrapper(malformed, self.vodafone)
        with tempfile.TemporaryDirectory() as temporary:
            source, key_path = Path(temporary) / 'backup.bin', Path(temporary) / 'key.bin'
            source.write_bytes(backup)
            key_path.write_bytes(b'\xff\x00binary-key')
            with self.assertRaisesRegex(ValueError, 'signature verification are not established'):
                if ROOT.name == 'TestingTools':
                    router.decode_router_config(str(source), self.vodafone, 'not-a-key.txt', 'Existing prompt: ', str(key_path))
                else:
                    router.decode_router_config(str(source), self.vodafone, 'not-a-key.txt', str(key_path))
            self.assertEqual(source.read_bytes(), backup)

    def test_static_specs_and_templates_have_no_thenc_key_identifiers(self):
        self.assertNotIn('cipher_key_id', router.ROUTER_SPEC_SCHEMA['backup_format'])
        self.assertNotIn('signature_key_id', router.ROUTER_SPEC_SCHEMA['backup_format'])
        for spec in (self.spark, self.vodafone, json.loads((ROOT / 'doc/RouterSpecificationTemplate.json').read_text())):
            self.assertNotIn('cipher_key_id', spec['backup_format'])
            self.assertNotIn('signature_key_id', spec['backup_format'])

    def test_router_modules_import_in_either_order(self):
        import subprocess
        import sys
        for order in ('router_encryption_utils, router_utils', 'router_utils, router_encryption_utils'):
            result = subprocess.run([sys.executable, '-c', 'from modules import ' + order], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_supplied_thenc_fixture_is_preserved(self):
        data_root = Path.home() / ('Documents/' + ROOT.name + 'Data/routers')
        source = data_root / 'templates/Vodafone_Ultra_Hub-template.bin'
        if not source.is_file():
            self.skipTest('Local Vodafone fixture unavailable')
        original = source.read_bytes()
        wrapper = router.parse_router_wrapper(original, self.vodafone)
        self.assertEqual(wrapper['header'] + wrapper['iv'] + wrapper['encrypted'] + wrapper['signature'], original)
        with self.assertRaisesRegex(ValueError, 'device key unavailable'):
            router.decode_router_config(str(source), self.vodafone, str(data_root / 'templatePasswords/Vodafone_Ultra_Hub-password.txt'))
        self.assertEqual(source.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
