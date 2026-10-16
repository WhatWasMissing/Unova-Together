"""Regression coverage for the launcher-local BPS story-event variant."""
from __future__ import annotations

import hashlib
import mmap
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

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


if __name__ == "__main__":
    unittest.main()
