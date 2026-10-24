"""Focused byte-level tests for the exact-build dialogue renderer patcher."""

from __future__ import annotations

import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path


PATCHER_PATH = Path(__file__).with_name("dialogue_art_patch.py")
SPEC = importlib.util.spec_from_file_location("dialogue_art_patch", PATCHER_PATH)
assert SPEC is not None and SPEC.loader is not None
patcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(patcher)


class DialogueArtPatchTests(unittest.TestCase):
    def test_thumb_branch_round_trip(self) -> None:
        for source, target in (
            (0x021884F2, 0x021D58F8),
            (0x021A8D06, 0x021D5798),
            (0x021D5788, 0x021D5790),
            (0x021D5790, 0x021D5788),
        ):
            with self.subTest(source=hex(source), target=hex(target)):
                encoded = patcher.encode_thumb_bl(source, target)
                self.assertEqual(patcher.decode_thumb_bl(source, encoded), target)

    def test_native_art_resource_round_trip(self) -> None:
        indexed = bytes((x + y * 3) % 16 for y in range(16) for x in range(24))
        ncgr = patcher.build_ncgr(indexed, 24, 16)
        self.assertEqual(patcher.decode_ncgr(ncgr), (24, 16, indexed))

        nclr = patcher.build_nclr([(i * 17, i * 11, i * 7) for i in range(16)])
        patcher.validate_nclr(nclr)

    def make_autoload_image(self):
        data = bytearray(bytes(range(256)) * ((patcher.ROM_ARM9_EXPECTED_SIZE + 255) // 256))
        del data[patcher.ROM_ARM9_EXPECTED_SIZE:]
        struct.pack_into("<6I", data, patcher.ARM9_MODULE_PARAMS_OFFSET,
                         0x0209EBC0, 0x0209EC00, 0x0209D740, 0x0209D740, 0x0214F500, 0)
        for index, entry in enumerate(patcher.ARM9_AUTOLOAD_ENTRIES):
            struct.pack_into("<4I", data, patcher.ARM9_AUTOLOAD_TABLE_OFFSET + index * 16, *entry)
        struct.pack_into("<I", data, patcher.ARM9_ITCM_ARENA_LITERAL_OFFSET, 0x01FF93A0)
        return bytes(data)

    def test_itcm_extension_preserves_other_autoload_data_and_bss(self):
        original = self.make_autoload_image()
        payload = b"art-hook" * 7
        actual = patcher._extend_itcm_image(original, payload)
        size = 64
        insert = patcher.ARM9_ITCM_INSERT_OFFSET
        self.assertEqual(len(actual), len(original) + size)
        self.assertEqual(actual[insert:insert + len(payload)], payload)
        self.assertEqual(actual[insert + len(payload):insert + size], bytes(size - len(payload)))
        table = patcher.ARM9_AUTOLOAD_TABLE_OFFSET
        self.assertEqual(actual[insert + size:table + size], original[insert:table])
        self.assertEqual(actual[table + size + 16:], original[table + 16:])
        self.assertEqual(struct.unpack_from("<4I", actual, table + size),
                         (0x01FF8000, 0x13E0, 0x01FF8000, 0))
        self.assertEqual(struct.unpack_from("<6I", actual, patcher.ARM9_MODULE_PARAMS_OFFSET),
                         (0x0209EC00, 0x0209EC40, 0x0209D740, 0x0209D740, 0x0214F500, 0))
        self.assertEqual(struct.unpack_from("<I", actual, patcher.ARM9_ITCM_ARENA_LITERAL_OFFSET)[0],
                         0x01FF93E0)

    def test_itcm_extension_rejects_changed_metadata_and_bad_payloads(self):
        original = self.make_autoload_image()
        for offset in (patcher.ARM9_MODULE_PARAMS_OFFSET, patcher.ARM9_AUTOLOAD_TABLE_OFFSET,
                       patcher.ARM9_ITCM_ARENA_LITERAL_OFFSET):
            changed = bytearray(original)
            changed[offset] ^= 1
            with self.subTest(offset=hex(offset)), self.assertRaises(patcher.PatchError):
                patcher._extend_itcm_image(changed, b"1234")
        for payload in (b"", bytes(patcher.ITCM_HELPER_MAX_SIZE + 1)):
            with self.assertRaises(patcher.PatchError):
                patcher._extend_itcm_image(original, payload)
        with self.assertRaises(patcher.PatchError):
            patcher.encode_thumb_bl(0x021A8D0E, 0x0809EC18)

    def test_reviewed_actor_hook_calls_decode_to_the_exact_targets(self) -> None:
        for address, (_, expected_target, expected_bytes) in patcher.BRANCH_HOOKS.items():
            with self.subTest(address=hex(address)):
                self.assertEqual(patcher.decode_thumb_call(address, expected_bytes), expected_target)
        self.assertEqual(patcher.BRANCH_HOOKS[patcher.ACTOR_CREATE_HOOK_ADDRESS][1], 0x021551A4)
        self.assertEqual(patcher.BRANCH_HOOKS[patcher.ACTOR_CREATE_HOOK_ADDRESS][2],
                         bytes.fromhex("ac f7 49 fa"))
        self.assertEqual(patcher.BRANCH_HOOKS[0x0218880A][1], 0x020787A8)
        self.assertEqual(patcher.BRANCH_HOOKS[0x0218883C][1], 0x020787A8)

    def test_actor_hook_modes_select_registration_and_cleanup_sites(self) -> None:
        creation = patcher.ACTOR_CREATE_HOOK_ADDRESS
        cleanup = patcher.ACTOR_CLEANUP_HOOK_ADDRESSES
        expected_actor_sites = {
            "full": {creation, *cleanup},
            "create-only": {creation},
            "cleanup-only": set(cleanup),
            "disabled": set(),
        }
        for mode, expected in expected_actor_sites.items():
            with self.subTest(mode=mode):
                actual = set(patcher._active_branch_hooks(mode))
                self.assertEqual(actual & ({creation} | set(cleanup)), expected)
        with self.assertRaises(patcher.PatchError):
            patcher._active_branch_hooks("unknown")

    def test_fixed_system_art_is_explicit_opt_in(self):
        self.assertFalse(set(patcher._active_branch_hooks("full")) & patcher.FIELD_HOOK_ADDRESSES)
        self.assertEqual(set(patcher._active_branch_hooks("full", True)) & patcher.FIELD_HOOK_ADDRESSES,
                         patcher.FIELD_HOOK_ADDRESSES)

    def test_profile_name_renders_only_inside_the_nameplate(self) -> None:
        indexed = bytearray(patcher.ART_WIDTH * patcher.ART_HEIGHT)
        palette = [(0, 0, 0)] + [(index * 16, index * 12, index * 8) for index in range(1, 16)]
        patcher.draw_nameplate(indexed, palette, "Emma")
        drawn = [index for index, pixel in enumerate(indexed) if pixel]
        self.assertTrue(drawn)
        xs = [index % patcher.ART_WIDTH for index in drawn]
        ys = [index // patcher.ART_WIDTH for index in drawn]
        self.assertGreaterEqual(min(xs), patcher.NAMEPLATE_LEFT)
        self.assertLess(max(xs), patcher.NAMEPLATE_LEFT + patcher.NAMEPLATE_WIDTH)
        self.assertGreaterEqual(min(ys), patcher.NAMEPLATE_TOP)
        self.assertLess(max(ys), patcher.NAMEPLATE_TOP + 10)
        with self.assertRaises(patcher.PatchError):
            patcher.draw_nameplate(indexed, palette, "Emma?")

    def test_speaker_manifest_requires_exact_identity_unless_test_wildcard_is_enabled(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dialogue-profile-test-") as temp_name:
            manifest_path = Path(temp_name) / "profiles.json"
            manifest = {"profiles": [{
                "name": "Emma",
                "zone_id": 17,
                "actor_uid": 4,
                "art": str(patcher.DEFAULT_ART),
            }]}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            loaded = patcher.load_speaker_profiles(manifest_path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual((loaded[0]["zone_id"], loaded[0]["actor_uid"]), (17, 4))
            self.assertEqual((loaded[0]["ncgr"], loaded[0]["nclr"]), (14, 15))

            manifest["profiles"][0]["actor_uid"] = 0xFFFF
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(patcher.PatchError):
                patcher.load_speaker_profiles(manifest_path)
            self.assertEqual(patcher.load_speaker_profiles(manifest_path, allow_wildcards=True)[0]["actor_uid"],
                             0xFFFF)

    def test_renderer_keeps_field_heap_and_bss_layout(self) -> None:
        self.assertEqual(patcher.FIELD_HEAP_ORIGINAL_SIZE, 0x10000)
        self.assertEqual(patcher.OVERLAY36_BSS_SIZE, 0x10040)
        self.assertEqual(patcher.ITCM_HELPER_BASE, 0x01FF93A0)
        self.assertEqual(patcher.BRANCH_HOOKS[0x0218A070][0], patcher.BRANCH_HOOKS[0x0218A082][0])


if __name__ == "__main__":
    unittest.main()
