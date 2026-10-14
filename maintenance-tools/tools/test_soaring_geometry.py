"""Flight shell and native ground-landing regressions; fixtures self-clean."""
import struct
import unittest
from soaring_geometry import close_building_shell,landing_tiles


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
        permission=bytearray(struct.pack('<HH',32,32)+struct.pack('<4H',0,0,0,128)*1024)
        for x,record in [(1,(0,0,1,129)),(2,(0,0,63,22)),(3,(4,0,0,128)),(4,(0,0,212,1))]:
            struct.pack_into('<4H',permission,4+x*8,*record)
        chunk=b'WB\x03\0'+struct.pack('<4I',20,20,20+len(permission),20+len(permission))+permission
        ground=[face([(-256,32,-256),(256,32,-256),(256,32,256),(-256,32,256)])]
        sites=landing_tiles(chunk,ground,96,2,3,(0,0,0),48,[(0,16,0,16)])
        self.assertGreater(len(sites),900)
        index={(site[1]-64,site[2]-96):site for site in sites}
        self.assertNotIn((1,0),index);self.assertNotIn((2,0),index)
        self.assertNotIn((3,0),index);self.assertNotIn((4,0),index)
        self.assertNotIn((16,16),index);self.assertEqual(index[(0,0)],[96,64,96,80])
        stacked=ground+[face([(-256,64,-256),(256,64,-256),(256,64,256),(-256,64,256)])]
        self.assertEqual(landing_tiles(chunk,stacked,96,2,3,(0,0,0),48,[]),[])


if __name__=='__main__':unittest.main()
