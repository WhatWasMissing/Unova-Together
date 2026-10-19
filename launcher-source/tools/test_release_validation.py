"""Verify release guards reject failed checks even under Python optimization."""
from pathlib import Path
import hashlib
import runpy
import subprocess
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_PACKAGERS = (
    REPOSITORY_ROOT / 'launcher-source/tools/package_unova_release.py',
    REPOSITORY_ROOT / 'maintenance-tools/tools/package_unova_release.py',
)
PACKAGERS = tuple(path for path in REPOSITORY_PACKAGERS if path.is_file())
if not PACKAGERS:
    PACKAGERS = (Path(__file__).resolve().with_name('package_unova_release.py'),)
CHECK = (
    "import runpy,sys; "
    "runpy.run_path(sys.argv[1])['require_release_condition'](False, 'negative control')"
)


class ReleaseValidationTests(unittest.TestCase):
    def test_release_guards_stay_active_under_python_optimization(self):
        for packager in PACKAGERS:
            with self.subTest(packager=packager):
                result = subprocess.run(
                    [sys.executable, '-O', '-c', CHECK, str(packager)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0, f'{packager} accepted a failed release check')
                self.assertIn('Release package validation failed: negative control', result.stderr)

    def test_runtime_must_embed_fingerprint_of_packaged_shop_overlay_source(self):
        patch_header = b'Gen5ShopOverlayPatch target 3DC1FED8'
        marker = hashlib.sha256(patch_header).hexdigest().encode('utf-16le')
        for packager in PACKAGERS:
            with self.subTest(packager=packager):
                check = runpy.run_path(str(packager))['runtime_matches_shop_overlay_source']
                self.assertTrue(check(b'MZ' + marker, patch_header))
                self.assertFalse(check(b'MZ' + marker, patch_header + b' changed'))
                self.assertFalse(check(b'MZ without build fingerprint', patch_header))


if __name__ == '__main__':
    unittest.main()
