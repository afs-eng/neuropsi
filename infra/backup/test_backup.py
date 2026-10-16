import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('backup', Path(__file__).with_name('backup.py'))
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)

URL = 'postgresql://example:private%3Apassword@example.render.com/neurobd'


class BackupTests(unittest.TestCase):
    def test_empty_url_has_actionable_message(self):
        with self.assertRaisesRegex(backup.ConfigError, 'Nenhuma URL recebida'):
            backup.connection('')

    def test_malformed_port_does_not_expose_secret(self):
        with self.assertRaises(backup.ConfigError) as result:
            backup.connection('postgresql://user:private-secret@host:invalid/db')
        self.assertNotIn('private-secret', str(result.exception))
        self.assertIn('porta', str(result.exception))

    def test_setup_internal_url_explains_external_url(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(backup, 'CONFIG', Path(directory) / 'missing.json'):
                with patch.object(backup.getpass, 'getpass', return_value='postgresql://user:private-secret@dpg-internal-a/db'):
                    with patch('sys.argv', ['backup.py', 'setup']):
                        with patch('sys.stderr', new_callable=io.StringIO) as stderr:
                            with self.assertRaises(SystemExit) as result:
                                backup.main()
            self.assertEqual(result.exception.code, 1)
            self.assertIn('External Database URL', stderr.getvalue())
            self.assertNotIn('private-secret', stderr.getvalue())

    def test_credentials_use_private_temporary_pgpass(self):
        with patch.dict(os.environ, {'PGPASSWORD': 'inherited', 'PGSERVICE': 'remote'}):
            with backup.pg_environment(URL) as env:
                self.assertNotIn('PGPASSWORD', env)
                self.assertNotIn('PGSERVICE', env)
                self.assertEqual(env['PGSSLMODE'], 'require')
                password_file = Path(env['PGPASSFILE'])
                self.assertEqual(password_file.stat().st_mode & 0o777, 0o600)
                self.assertEqual(password_file.read_text(), '*:*:*:*:private\\:password\n')
            self.assertFalse(password_file.exists())

    def test_success_publishes_dump_only_after_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            def fake_run(arguments, url):
                self.assertEqual(url, URL)
                if arguments[0] == 'pg_dump':
                    Path(arguments[-1]).write_bytes(b'dump')
                else:
                    self.assertEqual(list(Path(directory).glob('*.dump')), [])

            with patch.object(backup, 'run_pg', side_effect=fake_run) as run:
                backup.backup({'source_url': URL, 'backup_dir': directory})
            self.assertEqual(run.call_count, 2)
            self.assertEqual(len(list(Path(directory).glob('*.dump'))), 1)
            self.assertEqual(list(Path(directory).glob('*.partial')), [])

    def test_failed_backup_keeps_previous_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path(directory) / 'previous.dump'
            previous.write_bytes(b'valid previous copy')

            def fail(arguments, url):
                Path(arguments[-1]).write_bytes(b'incomplete')
                raise RuntimeError('simulated failure')

            with patch.object(backup, 'run_pg', side_effect=fail):
                with self.assertRaises(RuntimeError):
                    backup.backup({'source_url': URL, 'backup_dir': directory})
            self.assertEqual(previous.read_bytes(), b'valid previous copy')
            self.assertEqual(list(Path(directory).glob('*.partial')), [])
            self.assertEqual(list(Path(directory).glob('*.dump')), [previous])

    def test_catalog_failure_does_not_publish_dump(self):
        with tempfile.TemporaryDirectory() as directory:
            def fail_validation(arguments, url):
                if arguments[0] == 'pg_dump':
                    Path(arguments[-1]).write_bytes(b'invalid archive')
                else:
                    raise RuntimeError('invalid archive')

            with patch.object(backup, 'run_pg', side_effect=fail_validation):
                with self.assertRaises(RuntimeError):
                    backup.backup({'source_url': URL, 'backup_dir': directory})
            self.assertEqual(list(Path(directory).glob('*.dump')), [])
            self.assertEqual(list(Path(directory).glob('*.partial')), [])

    def test_restore_refuses_remote_database(self):
        with patch.object(backup, 'run_pg') as run:
            with self.assertRaises(ValueError):
                backup.restore({'local_url': URL}, '/nonexistent.dump')
            run.assert_not_called()

    def test_restore_uses_transaction_without_clean(self):
        with tempfile.NamedTemporaryFile() as archive:
            config = {'local_url': 'postgresql://local:password@127.0.0.1:55432/recovery?sslmode=disable'}
            with patch('builtins.input', return_value='RESTAURAR LOCAL'):
                with patch.object(backup, 'run_pg') as run:
                    backup.restore(config, archive.name)
            arguments = run.call_args.args[0]
            self.assertIn('--single-transaction', arguments)
            self.assertIn('--exit-on-error', arguments)
            self.assertNotIn('--clean', arguments)

    def test_private_config_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'secret.json'
            backup.private_write(path, 'original')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                backup.private_write(path, 'replacement')
            self.assertEqual(path.read_text(), 'original')


if __name__ == '__main__':
    unittest.main()
