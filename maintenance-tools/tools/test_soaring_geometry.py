"""Flight shell and native ground-landing regressions; fixtures self-clean."""
import struct
import unittest
from soaring_geometry import close_building_shell,landing_tiles,_sample_chunk_terrain


def face(points):
    return ('wall','palette'),[tuple(p)+uv for p,uv in zip(points,[(0,0),(16,0),(16,16),(0,16)])]


class FlightGeometryTests(unittest.TestCase):
    def test_only_missing_building_wall_is_completed(self):
        roof=face([(-16,24,-16),(16,24,-16),(16,24,16),(-16,24,16)])
        walls=[face([(-16,24,-16),(16,24,-16),(16,0,-16),(-16,0,-16)]),
               face([(16,24,-16),(16,24,16),(16,0,16),(16,0,-16)]),
               face([(-16,24,16),(-16,24,-16),(-16,0,-16),(-16,0,16)])]
        result,count=close_building_shell([roof]+walls)
        self.assertEqual(count,1);self.assertEqual(len(result),5)
        self.assertTrue(all(v[2]==16 for v in result[-1][1]))
        self.assertEqual(close_building_shell(result)[1],0)
        self.assertEqual(close_building_shell(walls)[1],0) # No roof: don't box trees.

    def test_collision_ground_water_obstacles_and_height(self):
        terrain=bytearray(struct.pack('<HH',32,32)+struct.pack('<HHI',0,3,0x00800000)*1024)
        # BW2 MapTile types: collision flag bit 0, class 0x3f is surf water.
        for x,tile_type in [(1,0x00810001),(2,0x0000003f),(4,0x00010000)]:
            struct.pack_into('<HHI',terrain,4+x*8,0,3,tile_type)
        # A steep but valid plane is kept out of the landing whitelist.
        struct.pack_into('<HHI',terrain,4+3*8,2<<2,3,0x00800000)
        chunk=b'WB\x03\0'+struct.pack('<4I',20,20,20+len(terrain),20+len(terrain))+terrain
        # Render geometry can have stacked surfaces; the native collision data
        # chooses the real ground height instead of averaging those meshes.
        ground=[face([(-256,32,-256),(256,32,-256),(256,32,256),(-256,32,256)]),
                face([(-256,64,-256),(256,64,-256),(256,64,256),(-256,64,256)])]
        sites=landing_tiles(chunk,ground,96,2,3,(0,0,0),48,[(0,16,0,16)],[(70,102)])
        self.assertGreater(len(sites),900)
        index={(site[1]-64,site[2]-96):site for site in sites}
        self.assertNotIn((1,0),index);self.assertNotIn((2,0),index)
        self.assertNotIn((3,0),index);self.assertNotIn((4,0),index)
        self.assertNotIn((16,16),index);self.assertEqual(index[(0,0)],[96,64,96,0])
        self.assertNotIn((6,6),index) # NPC interaction radius is clear of landings.

    def test_height_sampler_follows_split_tile_diagonal_at_center(self):
        terrain=bytearray(struct.pack('<HH',32,32))
        terrain.extend(struct.pack('<HHI',2,0,0x00800000)*1024)
        terrain.extend(struct.pack('<4H',0,2,3,3))
        sample=_sample_chunk_terrain(memoryview(terrain),16,16,b'WB')
        self.assertIsNotNone(sample)
        self.assertAlmostEqual(sample[2],0x323/4096.)

    def test_gc_uses_both_native_height_layers_and_picks_upper_walkable_floor(self):
        lower=bytearray(struct.pack('<HH',32,32)+struct.pack('<HHI',0,3,0x00800000)*1024)
        upper=bytearray(struct.pack('<HH',32,32)+struct.pack('<HHI',0,6,0x00800000)*1024)
        # Offsets 3 and 6 are distinct; set the upper floor's height index to a
        # known native plane without relying on rendered mesh positions.
        chunk=b'GC\x04\0'+struct.pack('<5I',24,24,24+len(lower),24+len(lower)+len(upper),24+len(lower)+len(upper))+lower+upper
        sites=landing_tiles(chunk,[],64,0,0,(0,0,0),0,[])
        self.assertEqual(len(sites),1024)
        self.assertGreater(sites[0][3],0)

    def test_rd_chunk_height_layout_is_sampled(self):
        record=struct.pack('<6h2iI',0,4096,0,0,4096,0,0,0,0x00800000)
        terrain=struct.pack('<HH',32,32)+record*1024
        chunk=b'RD\x03\0'+struct.pack('<4I',20,20,20+len(terrain),20+len(terrain))+terrain
        sites=landing_tiles(chunk,[],96,0,0,(0,0,0),0,[])
        self.assertEqual(len(sites),1024)
        self.assertEqual(sites[0],[96,0,0,0])


if __name__=='__main__':unittest.main()
