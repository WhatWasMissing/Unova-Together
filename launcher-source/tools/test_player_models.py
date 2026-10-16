"""Regression checks for the ROM-backed animated player model selector."""
import struct
import unittest

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


if __name__ == '__main__':
    unittest.main(verbosity=2)
