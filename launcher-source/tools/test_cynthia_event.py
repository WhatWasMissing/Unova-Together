"""Regression coverage for the launcher-local BPS story-event variant."""
from __future__ import annotations

import hashlib
import json
import mmap
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib
from unittest.mock import patch

from launcher_ui import cynthia_event
from build_bps_patch import _number


def _test_patch(source: bytes, actions: list[tuple[int, int, bytes]]) -> bytes:
    """Build a tiny BPS stream from (mode, length, payload) test actions."""
    out = bytearray(b"BPS1")
    out += _number(len(source)) + _number(sum(length for _, length, _ in actions)) + _number(0)
    source_cursor = target_cursor = 0
    for mode, length, payload in actions:
        out += _number(((length - 1) << 2) | mode)
        if mode == 1:
            out += payload
        elif mode == 2:
            delta = payload
            out += _number((abs(delta) << 1) | int(delta < 0))
            source_cursor += delta + length
        elif mode == 3:
            delta = payload
            out += _number((abs(delta) << 1) | int(delta < 0))
            target_cursor += delta + length
        target_cursor += length if mode != 3 else 0
    out += struct.pack("<III", zlib.crc32(source) & 0xFFFFFFFF,
                       0, 0)
    # Target CRC is patched after simulating the expected bytes in each test.
    return out


def _finish_patch(patch: bytes, source: bytes, expected: bytes) -> bytes:
    result = bytearray(patch)
    struct.pack_into("<I", result, len(result) - 8, zlib.crc32(expected) & 0xFFFFFFFF)
    struct.pack_into("<I", result, len(result) - 4, zlib.crc32(result[:-4]) & 0xFFFFFFFF)
    return bytes(result)


class CynthiaEventTests(unittest.TestCase):
    def test_bps_source_read_literal_and_copy_actions(self):
        source = b"abcdefgh"
        expected = b"abcXYXYefgh!"
        actions = [(0, 3, b""), (1, 2, b"XY"), (3, 2, 3), (2, 4, 4), (1, 1, b"!")]
        patch = _finish_patch(_test_patch(source, actions), source, expected)
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "source.nds"
            patch_path = Path(directory) / "event.bps"
            source_path.write_bytes(source)
            patch_path.write_bytes(patch)
            with source_path.open("rb") as sf, patch_path.open("rb") as pf:
                with mmap.mmap(sf.fileno(), 0, access=mmap.ACCESS_READ) as source_map:
                    with mmap.mmap(pf.fileno(), 0, access=mmap.ACCESS_READ) as patch_map:
                        result = cynthia_event._apply_bps(source_map, patch_map, len(expected))
            self.assertEqual(bytes(result), expected)

    def test_corrupt_patch_is_rejected_before_copy_is_written(self):
        source = b"a small local rom"
        patch = bytearray(_finish_patch(_test_patch(source, [(1, 4, b"test")]), source, b"test"))
        patch[5] ^= 1
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "source.nds"
            patch_path = Path(directory) / "bad.bps"
            source_path.write_bytes(source)
            patch_path.write_bytes(patch)
            with source_path.open("rb") as sf, patch_path.open("rb") as pf:
                with mmap.mmap(sf.fileno(), 0, access=mmap.ACCESS_READ) as source_map:
                    with mmap.mmap(pf.fileno(), 0, access=mmap.ACCESS_READ) as patch_map:
                        with self.assertRaisesRegex(ValueError, "checksum"):
                            cynthia_event._apply_bps(source_map, patch_map, 4)

    def test_unreviewed_rom_is_left_untouched_and_rejected_for_event_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "personal.nds"
            source.write_bytes(b"not a reviewed ROM")
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            with self.assertRaises(cynthia_event.UnsupportedRomError):
                cynthia_event.prepare_variant(source, root)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
            self.assertFalse((root / ".launcher-cynthia-route7").exists())

    def test_cynthia_cache_junction_outside_home_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "launcher-home"
            root.mkdir()
            outside = base / "outside-cache"
            outside.mkdir()
            source = root / "reviewed.nds"
            source_bytes = b"reviewed source rom"
            expected = b"patched source rom"
            source.write_bytes(source_bytes)
            patch_path = root / "event.bps"
            patch_path.write_bytes(_finish_patch(
                _test_patch(source_bytes, [(1, len(expected), expected)]),
                source_bytes,
                expected,
            ))

            cache = root / ".launcher-cynthia-route7"
            if os.name == "nt":
                def quote(value):
                    return "'" + str(value).replace("'", "''") + "'"
                result = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command",
                     f"New-Item -ItemType Junction -Path {quote(cache)} -Target {quote(outside)} | Out-Null"],
                    capture_output=True,
                )
                if result.returncode:
                    self.skipTest("directory junctions unavailable")
            else:
                cache.symlink_to(outside, target_is_directory=True)

            source_hash = hashlib.sha256(source_bytes).hexdigest()
            descriptor = (patch_path.name, hashlib.sha256(expected).hexdigest(), len(expected))
            with patch.dict(cynthia_event._PATCHES, {source_hash: descriptor}):
                with self.assertRaisesRegex(ValueError, "cache folder is unsafe"):
                    cynthia_event.prepare_variant(source, root, patch_root=patch_path)

            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual(list(outside.iterdir()), [])

    def test_event_copy_preserves_preexisting_pending_hardlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "reviewed.nds"
            source_bytes = b"reviewed source rom"
            expected = b"patched source rom"
            source.write_bytes(source_bytes)
            patch_path = root / "event.bps"
            patch_path.write_bytes(_finish_patch(
                _test_patch(source_bytes, [(1, len(expected), expected)]),
                source_bytes,
                expected,
            ))

            cache = root / ".launcher-cynthia-route7"
            cache.mkdir()
            target = cache / "reviewed - Cynthia Route 7.nds"
            manifest = target.with_suffix(".json")
            pending = target.with_name(target.name + ".pending")
            pending_manifest = manifest.with_name(manifest.name + ".pending")
            rom_sentinel = root / "keep-rom-sentinel.bin"
            manifest_sentinel = root / "keep-manifest-sentinel.bin"
            rom_sentinel.write_bytes(b"do not overwrite ROM sentinel")
            manifest_sentinel.write_bytes(b"do not overwrite manifest sentinel")
            try:
                pending.hardlink_to(rom_sentinel)
                pending_manifest.hardlink_to(manifest_sentinel)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"hard links unavailable: {exc}")

            source_hash = hashlib.sha256(source_bytes).hexdigest()
            target_hash = hashlib.sha256(expected).hexdigest()
            descriptor = (patch_path.name, target_hash, len(expected))
            with patch.dict(cynthia_event._PATCHES, {source_hash: descriptor}):
                result = cynthia_event.prepare_variant(source, root, patch_root=patch_path)

            self.assertEqual(result.read_bytes(), expected)
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual(rom_sentinel.read_bytes(), b"do not overwrite ROM sentinel")
            self.assertEqual(manifest_sentinel.read_bytes(), b"do not overwrite manifest sentinel")
            self.assertTrue(pending.exists())
            self.assertTrue(pending_manifest.exists())
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["output_sha256"], target_hash)


if __name__ == "__main__":
    unittest.main()
