"""Updater settings transfer must not write through a linked destination."""
import hashlib
import io
import os
from pathlib import Path
import tempfile
import threading
import unittest
import zipfile
from unittest.mock import patch

import unova_updater as updater


class UpdaterSettingsCopyTests(unittest.TestCase):
    def test_install_does_not_write_through_linked_settings_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            home = base / "home"
            runtime = home / "builds/current"
            runtime.mkdir(parents=True)
            (runtime / "melonDS.exe").write_bytes(b"old executable")
            (runtime / "VERSION.txt").write_text("Unova Together 0.3.4")
            (runtime / "melonDS.toml").write_text("player controls")

            raw = io.BytesIO()
            with zipfile.ZipFile(raw, "w") as archive:
                archive.writestr("Unova-Together/builds/current/melonDS.exe", b"new executable")
                archive.writestr("Unova-Together/builds/current/VERSION.txt", b"Unova Together 0.3.5")
                archive.writestr("Unova-Together/builds/current/melonDS.toml", b"packaged settings")
            payload = raw.getvalue()
            name = "Unova-Together-0.3.5-Windows-x64.zip"
            release_base = f"https://github.com/{updater.REPO}/releases/download/v0.3.5/"
            release = {
                "version": "0.3.5",
                "name": name,
                "size": len(payload),
                "url": release_base + name,
                "sums": release_base + "SHA256SUMS-Unova-Together-0.3.5.txt",
            }
            checksum_file = (hashlib.sha256(payload).hexdigest() + "  " + name + "\n").encode()
            outside = base / "external-controls.toml"
            outside.write_text("keep these controls")

            original_extract = updater.extract_verified

            def extract_with_linked_settings(archive, destination, expected):
                root = original_extract(archive, destination, expected)
                settings = root / "builds/current/melonDS.toml"
                settings.unlink()
                os.link(outside, settings)
                return root

            def opener(url):
                return io.BytesIO(checksum_file if url == release["sums"] else payload)

            caught = None
            with patch.object(updater, "extract_verified", side_effect=extract_with_linked_settings):
                try:
                    updater.install(home, release, threading.Event(), lambda *_: None, opener)
                except ValueError as error:
                    caught = error

            self.assertEqual(outside.read_text(), "keep these controls")
            self.assertIsNotNone(caught, "A linked update settings file must be rejected.")
            self.assertIn("Unsafe managed file", str(caught))
            self.assertFalse((home / ".updates/active.json").exists())
            self.assertEqual((runtime / "melonDS.toml").read_text(), "player controls")


if __name__ == "__main__":
    unittest.main()
