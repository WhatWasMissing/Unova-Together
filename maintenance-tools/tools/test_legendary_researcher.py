"""Tests for BW2 map-position and terrain-collision checks used by the ROM audit."""
from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from audit_legendary_researcher import terrain_tile, world_to_matrix_cell  # noqa: E402

DECOMP = Path(r"F:\gen5decomps\pokebw2-main")
if DECOMP.is_dir():
    sys.path.insert(0, str(DECOMP))
    sys.path.insert(0, str(DECOMP / "tools/data"))


def one_tile_wb(tile_type: int) -> bytes:
    start = 16
    end = start + 4 + 8
    chunk = bytearray(end)
    chunk[:2] = b"WB"
    struct.pack_into("<II", chunk, 8, start, end)
    struct.pack_into("<HH", chunk, start, 1, 1)
    struct.pack_into("<HHI", chunk, start + 4, 0, 0, tile_type)
    return bytes(chunk)


class MapPositionTests(unittest.TestCase):
    def test_candidate_world_position_resolves_to_nuvema_map_tile(self):
        self.assertEqual(world_to_matrix_cell(778, 744), (24, 23, 10, 8))


@unittest.skipUnless(DECOMP.is_dir(), "BW2 decomp data is needed to parse map terrain")
class TerrainCollisionTests(unittest.TestCase):
    def test_nonblocking_tile_flags_are_reported_walkable(self):
        # Redux Nuvema candidate tile: class 0 and flags 0x80; bit 0 is clear.
        tile = terrain_tile(one_tile_wb(0x00800000), 0, 0)["layers"][0]
        self.assertTrue(tile["valid"])
        self.assertFalse(tile["blocksCollision"])

    def test_collision_flag_blocks_tile(self):
        tile = terrain_tile(one_tile_wb(0x00010000), 0, 0)["layers"][0]
        self.assertTrue(tile["valid"])
        self.assertTrue(tile["blocksCollision"])

    def test_invalid_tile_blocks_collision(self):
        tile = terrain_tile(one_tile_wb(0x000000FF), 0, 0)["layers"][0]
        self.assertFalse(tile["valid"])
        self.assertTrue(tile["blocksCollision"])

    def test_out_of_bounds_tile_is_rejected(self):
        with self.assertRaises(ValueError):
            terrain_tile(one_tile_wb(0), 1, 0)


if __name__ == "__main__":
    unittest.main()
