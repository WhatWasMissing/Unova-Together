"""Publishing must reuse working cached credentials without opening authentication UI."""
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

import publish_release as publisher


class CachedCredentialTests(unittest.TestCase):
    def test_account_credential_avoids_stale_repository_entry(self):
        cached = subprocess.CompletedProcess([], 0, 'username=owner\npassword=test-only\n', '')
        with patch.object(publisher.subprocess, 'run', return_value=cached) as fill, \
                patch.object(publisher.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"login":"owner"}')):
            headers = publisher.cached_github_headers('owner/repo', '.')
        self.assertEqual(headers['Authorization'], 'Bearer test-only')
        self.assertEqual(fill.call_count, 1)
        self.assertNotIn('path=', fill.call_args.kwargs['input'])
        self.assertEqual(fill.call_args.kwargs['env']['GCM_INTERACTIVE'], 'never')
        self.assertEqual(fill.call_args.kwargs['env']['GIT_TERMINAL_PROMPT'], '0')

    def test_expired_credentials_fail_without_interactive_retry(self):
        cached = subprocess.CompletedProcess([], 0, 'password=expired-test-only\n', '')
        expired = urllib.error.HTTPError('https://api.github.com/user', 401, 'Expired', {}, None)
        with patch.object(publisher.subprocess, 'run', return_value=cached) as fill, \
                patch.object(publisher.urllib.request, 'urlopen', side_effect=expired), \
                self.assertRaisesRegex(RuntimeError, 'no interactive sign-in'):
            publisher.cached_github_headers('owner/repo', '.')
        self.assertEqual(fill.call_count, 2)
        self.assertIn('path=owner/repo.git', fill.call_args.kwargs['input'])
        self.assertTrue(all(call.kwargs['env']['GCM_INTERACTIVE'] == 'never' for call in fill.call_args_list))


class ExplicitReleaseInputTests(unittest.TestCase):
    def make_inputs(self, folder):
        root = Path(folder)
        notes = root / 'notes.md'
        asset = root / 'release.zip'
        notes.write_text('Player-facing release notes.\n', encoding='utf-8')
        asset.write_bytes(b'release asset fixture')
        return [
            '--version', '2.0.17',
            '--repo', 'WhatWasMissing/Unova-Together',
            '--commit', 'a' * 40,
            '--notes', str(notes),
            '--title', 'Unova Together 2.0.17',
            '--asset', str(asset),
        ]

    def test_missing_publish_inputs_stop_before_credential_access(self):
        with patch.object(publisher, 'cached_github_headers') as credentials:
            with self.assertRaises(SystemExit):
                publisher.main([])
        credentials.assert_not_called()

    def test_rejects_wrong_repository_before_credential_access(self):
        with tempfile.TemporaryDirectory() as folder:
            argv = self.make_inputs(folder)
            argv[argv.index('--repo') + 1] = 'WhatWasMissing/PokePlay'
            with patch.object(publisher, 'cached_github_headers') as credentials:
                with self.assertRaises(SystemExit):
                    publisher.main(argv)
            credentials.assert_not_called()

    def test_rejects_missing_assets_and_duplicate_asset_names(self):
        with tempfile.TemporaryDirectory() as folder:
            argv = self.make_inputs(folder)
            argv[argv.index('--asset') + 1] = str(Path(folder) / 'missing.zip')
            with self.assertRaises(SystemExit):
                publisher.parse_args(argv)

            first = Path(folder) / 'one' / 'same.zip'
            second = Path(folder) / 'two' / 'same.zip'
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_bytes(b'one')
            second.write_bytes(b'two')
            argv = self.make_inputs(folder)
            argv.extend(['--asset', str(second)])
            argv[argv.index('--asset') + 1] = str(first)
            with self.assertRaises(SystemExit):
                publisher.parse_args(argv)

    def test_remote_commit_is_checked_before_release_api_access(self):
        with tempfile.TemporaryDirectory() as folder:
            argv = self.make_inputs(folder)
            calls = []

            def fake_urlopen(request, timeout):
                calls.append((request.full_url, request.method))
                return io.BytesIO(b'{"sha":"' + b'0' * 40 + b'"}')

            with patch.object(publisher, 'cached_github_headers', return_value={}), \
                    patch.object(publisher.urllib.request, 'urlopen', side_effect=fake_urlopen):
                with self.assertRaisesRegex(RuntimeError, 'did not confirm commit'):
                    publisher.main(argv)

            self.assertEqual(len(calls), 1)
            self.assertIn('/commits/' + 'a' * 40, calls[0][0])
            self.assertNotIn('/releases', calls[0][0])


if __name__ == '__main__':
    unittest.main()
