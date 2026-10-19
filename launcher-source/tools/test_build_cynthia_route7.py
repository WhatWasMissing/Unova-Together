"""Safety checks for the Cynthia patch builder's final ROM-copy staging path."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import build_cynthia_route7 as builder


class CynthiaBuildOutputTests(unittest.TestCase):
    def test_legacy_pending_symlink_is_not_followed_or_replaced(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'patched.nds'
            external_target = root / 'outside.nds'
            legacy_pending = output.with_name(output.name + '.pending')
            try:
                legacy_pending.symlink_to(external_target)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f'file symlinks unavailable: {exc}')
            rom = SimpleNamespace(saveToFile=lambda path: Path(path).write_bytes(b'patched ROM'))

            result = builder.save_rom_copy(rom, output)

            self.assertEqual(result, output)
            self.assertEqual(output.read_bytes(), b'patched ROM')
            self.assertFalse(external_target.exists())
            self.assertTrue(legacy_pending.is_symlink())

    def test_exclusive_staging_collision_does_not_overwrite_hardlink(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'patched.nds'
            sentinel = root / 'outside.bin'
            sentinel.write_bytes(b'preserve this file')
            token = 'a' * 32
            staging = output.with_name(output.name + '.' + token + '.pending')
            try:
                staging.hardlink_to(sentinel)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f'hard links unavailable: {exc}')
            rom = SimpleNamespace(saveToFile=lambda path: Path(path).write_bytes(b'patched ROM'))

            with patch.object(builder.uuid, 'uuid4', return_value=SimpleNamespace(hex=token)):
                with self.assertRaises(FileExistsError):
                    builder.save_rom_copy(rom, output)

            self.assertEqual(sentinel.read_bytes(), b'preserve this file')
            self.assertTrue(staging.exists())
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
