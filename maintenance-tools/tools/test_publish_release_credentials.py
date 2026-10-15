"""Publishing must reuse working cached credentials without opening authentication UI."""
import io
import subprocess
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


if __name__ == '__main__':
    unittest.main()
