"""Regression checks for the ROM-backed animated player model selector."""
import json
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from launcher_ui import player_models, services


def actor_row(model_id, *, entity=1, scene=10, controller=13, texture=0, model=1):
    row = bytearray(player_models.CONFIG_RECORD_SIZE)
    struct.pack_into('<H', row, 0, model_id)
    row[2] = entity
    row[3] = scene
    row[9] = controller
    struct.pack_into('<HH', row, 16, texture, model)
    return row


class PlayerModelTests(unittest.TestCase):
    def test_only_normal_walking_entries_change(self):
        prefix = b'overlay-prefix'
        source = prefix + player_models.PLAYER_MAP_SIGNATURE + b'overlay-suffix'
        result = player_models._patch_player_map(source, 4715)
        offset = len(prefix)
        self.assertEqual(struct.unpack_from('<H', result, offset)[0], 4715)
        self.assertEqual(struct.unpack_from('<H', result, offset + 40)[0], 4715)
        self.assertEqual(result[offset + 2:offset + 40], source[offset + 2:offset + 40])
        self.assertEqual(result[offset + 42:], source[offset + 42:])
        self.assertEqual(source[offset:offset + 2], struct.pack('<H', 0xE7))

    def test_rejects_missing_or_ambiguous_player_mapping(self):
        with self.assertRaisesRegex(ValueError, 'player-model table'):
            player_models._patch_player_map(b'not a player table', 4715)
        ambiguous = player_models.PLAYER_MAP_SIGNATURE * 2
        with self.assertRaisesRegex(ValueError, 'player-model table'):
            player_models._patch_player_map(ambiguous, 4715)

    def test_catalog_requires_animated_humanoid_and_matching_model_resources(self):
        config = bytearray(4 + player_models.CONFIG_COUNT * player_models.CONFIG_RECORD_SIZE)
        struct.pack_into('<I', config, 0, player_models.CONFIG_COUNT)
        config[4:4 + 28] = actor_row(4715)
        config[4 + 28:4 + 56] = actor_row(4716, controller=1)
        config[4 + 56:4 + 84] = actor_row(4717, scene=1)
        config[4 + 84:4 + 112] = actor_row(4718, texture=2)
        models = player_models._actor_models(bytes(config), [b'BTX0texture', b'BMD0model'])
        self.assertEqual(models, [4715])

    def test_model_choice_survives_profile_normalization(self):
        profile = services.profile(rom='game.nds')
        profile['preferences'] = {'player_model': 4715, 'volume': 60}
        normalized = services.normalize(profile)
        self.assertEqual(normalized['preferences'], {'player_model': 4715, 'volume': 60})
        profile['preferences']['player_model'] = -1
        self.assertNotIn('player_model', services.normalize(profile)['preferences'])

    def test_model_copy_preserves_preexisting_pending_hardlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'reviewed.nds'
            source.write_bytes(b'reviewed ROM fixture')
            target = root / '.launcher-player-models' / source.name
            manifest = target.with_name(source.name + '.player-model.json')
            pending = target.with_name(target.name + '.pending')
            pending_manifest = manifest.with_name(manifest.name + '.pending')
            rom_sentinel = root / 'keep-rom-sentinel.bin'
            manifest_sentinel = root / 'keep-manifest-sentinel.bin'
            rom_sentinel.write_bytes(b'do not overwrite ROM sentinel')
            manifest_sentinel.write_bytes(b'do not overwrite manifest sentinel')
            try:
                pending.parent.mkdir(parents=True)
                pending.hardlink_to(rom_sentinel)
                pending_manifest.hardlink_to(manifest_sentinel)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f'hard links unavailable: {exc}')

            model_id = 4715
            patched_rom = b'prepared ROM fixture'
            overlay_data = bytearray(42)
            struct.pack_into('<H', overlay_data, 0, model_id)
            struct.pack_into('<H', overlay_data, 40, model_id)
            overlay = SimpleNamespace(data=overlay_data)
            source_rom = SimpleNamespace(saveToFile=lambda path: Path(path).write_bytes(patched_rom))
            checked_rom = SimpleNamespace(arm9OverlayTable=object(), files={})
            with patch.object(player_models, '_load_rom', side_effect=[source_rom, checked_rom]), \
                 patch.object(player_models, '_patch_rom'), \
                 patch.object(player_models.ndspy.code, 'loadOverlayTable', return_value={player_models.OVERLAY_ID: overlay}), \
                 patch.object(player_models, '_player_map_offset', return_value=0):
                result = player_models.prepare_variant(source, root, model_id)

            self.assertEqual(result.read_bytes(), patched_rom)
            self.assertEqual(source.read_bytes(), b'reviewed ROM fixture')
            self.assertEqual(rom_sentinel.read_bytes(), b'do not overwrite ROM sentinel')
            self.assertEqual(manifest_sentinel.read_bytes(), b'do not overwrite manifest sentinel')
            self.assertTrue(pending.exists())
            self.assertTrue(pending_manifest.exists())
            self.assertEqual(json.loads(manifest.read_text(encoding='utf-8'))['model_id'], model_id)


if __name__ == '__main__':
    unittest.main(verbosity=2)
