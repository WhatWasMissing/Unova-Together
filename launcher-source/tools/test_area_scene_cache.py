"""Path and manifest safety checks for the opt-in area-scenery cache."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import area_scene_cache


class AreaSceneCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.home = self.base / 'launcher-home'
        self.home.mkdir()
        self.rom = self.home / 'reviewed.nds'
        data = bytearray(b'disposable ROM fixture')
        data[12:16] = b'IREO'
        self.rom.write_bytes(data)
        self.cache = self.home / 'area-scenes'
        self.digest = hashlib.sha256(self.rom.read_bytes()).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def write_catalog(self, rom, output):
        output = Path(output)
        output.mkdir(parents=True)
        (output / 'catalog.json').write_text(json.dumps({
            'format': 1,
            'romSHA256': hashlib.sha256(Path(rom).read_bytes()).hexdigest(),
        }), encoding='utf-8')

    def test_valid_catalog_is_generated_then_reused(self):
        before = self.rom.read_bytes()
        with patch.object(area_scene_cache, 'catalog', side_effect=self.write_catalog) as generate:
            first = area_scene_cache.prepare_catalog(self.rom, self.cache)
            second = area_scene_cache.prepare_catalog(self.rom, self.cache)
        self.assertEqual(first, self.cache / self.digest / 'catalog.json')
        self.assertEqual(second, first)
        self.assertEqual(generate.call_count, 1)
        self.assertEqual(self.rom.read_bytes(), before)

    def test_non_object_manifest_returns_cache_validation_error(self):
        destination = self.cache / self.digest
        destination.mkdir(parents=True)
        (destination / 'catalog.json').write_text('[]', encoding='utf-8')
        with patch.object(area_scene_cache, 'catalog') as generate:
            with self.assertRaisesRegex(ValueError, 'Scenery cache is invalid'):
                area_scene_cache.prepare_catalog(self.rom, self.cache)
        generate.assert_not_called()

    def test_cache_junction_outside_home_is_rejected_before_catalog_write(self):
        outside = self.base / 'outside-cache'
        outside.mkdir()
        if os.name == 'nt':
            def quote(value):
                return "'" + str(value).replace("'", "''") + "'"
            result = subprocess.run(
                ['powershell.exe', '-NoProfile', '-Command',
                 f'New-Item -ItemType Junction -Path {quote(self.cache)} -Target {quote(outside)} | Out-Null'],
                capture_output=True,
            )
            if result.returncode:
                self.skipTest('directory junctions unavailable')
        else:
            self.cache.symlink_to(outside, target_is_directory=True)

        with patch.object(area_scene_cache, 'catalog', side_effect=self.write_catalog) as generate:
            with self.assertRaisesRegex(ValueError, 'Unsafe scenery cache path'):
                area_scene_cache.prepare_catalog(self.rom, self.cache)
        generate.assert_not_called()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual(self.rom.read_bytes()[12:16], b'IREO')

    def test_manifest_hardlink_is_rejected_without_touching_external_file(self):
        destination = self.cache / self.digest
        destination.mkdir(parents=True)
        manifest = destination / 'catalog.json'
        outside = self.base / 'keep-scenery-sentinel.json'
        outside.write_text(json.dumps({'format': 1, 'romSHA256': self.digest}), encoding='utf-8')
        try:
            manifest.hardlink_to(outside)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f'hard links unavailable: {exc}')

        with patch.object(area_scene_cache, 'catalog') as generate:
            with self.assertRaisesRegex(ValueError, 'Unsafe scenery cache path'):
                area_scene_cache.prepare_catalog(self.rom, self.cache)
        generate.assert_not_called()
        self.assertTrue(manifest.samefile(outside))
        self.assertEqual(json.loads(outside.read_text(encoding='utf-8'))['romSHA256'], self.digest)


if __name__ == '__main__':
    unittest.main(verbosity=2)
