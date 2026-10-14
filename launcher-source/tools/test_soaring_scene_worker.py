"""Palette alias and asynchronous flight-request rejection regressions."""
import json,struct,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import ndspy.texture
from build_battle_surroundings import texture_pack
from soaring_scene_worker import SoaringWorker,build_flyway_routes,make_flyway_faces,make_region_fill_faces,export_scene,export_with_budget
from soaring_geometry import collision_debug_tiles,landing_tiles
from types import SimpleNamespace
from PIL import Image

class SoaringWorkerTests(unittest.TestCase):
    def test_region_gaps_get_visual_routes_without_collision_data(self):
        # Three real map islands in a line should be joined with two routes.
        routes=build_flyway_routes(5,1,(0,-1,1,-1,2))
        self.assertEqual(len(routes),2)
        faces=make_flyway_faces(routes,0,0,4096)
        self.assertTrue(faces)
        self.assertEqual({face[0] for face in faces},{0,1,2})
        # Geometry only supplies appearance; collision still comes from the ROM.
        self.assertTrue(all(len(face[1])==3 for face in faces))

    def test_regional_fill_adds_sea_and_contextual_forest_deterministically(self):
        grid=[-1]*49
        for z in range(1,6):
            for x in range(1,6):
                if (x,z)!=(3,3):grid[z*7+x]=z*7+x
        faces,biome=make_region_fill_faces(7,7,grid,3.5*512,3.5*512,4096)
        repeated,repeat_biome=make_region_fill_faces(7,7,grid,3.5*512,3.5*512,4096)
        self.assertEqual(faces,repeated)
        self.assertEqual(biome,repeat_biome)
        self.assertGreaterEqual(len(faces),3)
        self.assertEqual(faces[0][0],0) # deep-sea underlay
        self.assertEqual(biome[3*7+3],1) # a gap ringed by authored land becomes forest
        self.assertTrue(any(face[0] in (2,3,4) for face in faces))
        self.assertEqual(biome[0],0) # unsupported map edge stays open sea

    def test_zone_event_positions_are_decoded_for_landing_clearance(self):
        headers=bytearray(48);struct.pack_into('<H',headers,22,0)
        record=struct.pack('<12HIHHI',1,162,0,0,0,7,1,0,0,0,0,0,0,12,19,0)
        event=struct.pack('<IBBBB',8+len(record),0,1,0,0)+record
        source=SimpleNamespace(headers=headers,events=[event])
        from build_battle_surroundings import FieldSource
        self.assertEqual(FieldSource.event_objects(source,0),[(12,19)])

    def test_landing_whitelist_skips_npc_interaction_radius(self):
        permission=bytearray(4+32*32*8);struct.pack_into('<HH',permission,0,32,32)
        chunk=bytearray(16+len(permission));struct.pack_into('<II',chunk,8,16,len(chunk));chunk[16:]=permission
        square=[(-256,0,-256,0,0),(256,0,-256,1,0),(256,0,256,1,1),(-256,0,256,0,1)]
        landings=landing_tiles(chunk,[(('terrain','floor','palette'),square)],1,0,0,(256,0,256),0,[],[(8,8)])
        positions={(entry[1],entry[2]) for entry in landings}
        self.assertNotIn((8,8),positions)
        self.assertNotIn((6,8),positions)
        self.assertIn((5,8),positions)

    def test_collision_debug_classifies_real_ground_and_blockers(self):
        permission=bytearray(4+32*32*8)
        struct.pack_into('<HH',permission,0,32,32)
        struct.pack_into('<4H',permission,4+(0*32+1)*8,0,0,0,129) # blocked
        struct.pack_into('<4H',permission,4+(0*32+2)*8,2,0,0,0)   # slope
        struct.pack_into('<4H',permission,4+(0*32+3)*8,0,0,7,0)   # special behavior
        chunk=bytearray(16+len(permission));struct.pack_into('<II',chunk,8,16,len(chunk));chunk[16:]=permission
        face=[(-256,0,-256,0,0),(256,0,-256,1,0),(256,0,256,1,1),(-256,0,256,0,1)]
        tiles=collision_debug_tiles(chunk,[(('terrain','floor','palette'),face)],0,0,(248,0,248),0,[],radius=60)
        kinds={(tile[0],tile[1]):tile[3] for tile in tiles}
        self.assertEqual(kinds[(0,0)],0)
        self.assertEqual(kinds[(1,0)],1)
        self.assertEqual(kinds[(2,0)],2)
        self.assertEqual(kinds[(3,0)],2)

    def test_scene_budget_falls_back_to_widest_valid_radius(self):
        calls=[]
        def export(_source,_zone,_x,_z,_y,_directory,radius):
            calls.append(radius)
            if radius in (4096,3072):raise ValueError('This map exceeds the flight scenery budget')
            return {'radius':radius}
        with patch('soaring_scene_worker.export_scene',side_effect=export):
            result=export_with_budget(None,191,10,20,30,Path('unused'))
        self.assertEqual(calls,[4096,3072,2560])
        self.assertEqual(result,{'radius':2560})

    def test_region_atlas_streams_matrix_links_and_fills_edges(self):
        headers=bytearray(3*48)
        struct.pack_into('<HH',headers,48+2,0,0)
        struct.pack_into('<HH',headers,96+2,1,1) # This tile belongs to an alternate matrix.
        areas=bytearray(20);areas[6]=areas[16]=1
        matrix=struct.pack('<IHH4i',1,2,1,0,1,1,2)
        texture=SimpleNamespace(width=2,height=2,renderAsImage=lambda _:Image.new('RGBA',(2,2),'green'))
        pack=SimpleNamespace(textures=[('grass',texture)],palettes=[('palette',SimpleNamespace(colors=[(0,31,0,31)]))])
        calls=[]
        def scene(zone,x,z,y,**kwargs):
            calls.append((zone,kwargs))
            return [(('terrain-1','grass','palette'),[(0,0,0,0,0),(1,0,0,1,0),(0,0,1,0,1)])],{'terrain-1':pack},{'omittedProps':[],'chunks':[1],'collisionTiles':[[9,12,0,0]] if kwargs.get('collision_debug') else []}
        source=SimpleNamespace(headers=headers,areas=areas,matrices=[matrix],scene=scene,collision_debug=True)
        with tempfile.TemporaryDirectory() as temporary:
            result=export_scene(source,1,600,20,0,Path(temporary)/'neighbor')
            self.assertEqual(result['sourceZone'],1);self.assertEqual(result['zone'],2)
            self.assertEqual(calls[0][0],2);self.assertTrue(calls[0][1]['flight'])
            self.assertEqual(calls[0][1]['radius'],4096);self.assertEqual(calls[0][1]['layout_matrix'],0)
            self.assertEqual(result['format'],2);self.assertEqual(result['radius'],4096)
            self.assertEqual(result['seaTiles'],0) # The atlas sea is a zero-mesh background.
            self.assertEqual(len(result['regionFaces']),2)
            self.assertEqual(result['atlasBiome'],[2,2])
            self.assertTrue(result['collisionDebug']);self.assertEqual(result['collisionTiles'],[[9,12,0,0]])
            self.assertTrue(calls[0][1]['collision_debug'])
            self.assertEqual(len(result['faces']),1)
            edge=export_scene(source,1,1200,20,0,Path(temporary)/'edge')
            self.assertEqual(edge['sourceZone'],1);self.assertEqual(edge['chunks'],[1])

    def test_native_palette_aliases_keep_the_actual_colours(self):
        first=ndspy.texture.Palette(0,0,0,struct.pack('<16H',*range(16)))
        second=ndspy.texture.Palette(0,0,0,struct.pack('<16H',*range(16,32)))
        pack=ndspy.texture.NSBTX();pack.palettes=[('first',first),('alias',second)]
        raw=bytearray(pack.save());offset=struct.unpack_from('<I',raw,16)[0]
        dictionary=struct.unpack_from('<I',raw,offset+52)[0]
        info=dictionary+struct.unpack_from('<H',raw,offset+dictionary+6)[0]
        self.assertEqual(struct.unpack_from('<H',raw,offset+info)[0],4)
        first_offset=struct.unpack_from('<H',raw,offset+info+4)[0]
        struct.pack_into('<H',raw,offset+info+8,first_offset)
        broken=ndspy.texture.NSBTX(raw)
        self.assertFalse(dict(broken.palettes)['first'].colors)
        repaired=texture_pack(raw)
        for _,palette in repaired.palettes:self.assertEqual(palette.colors[:16],first.colors)

    def test_invalid_requests_do_not_read_the_rom_or_stall_the_caller(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with patch('soaring_scene_worker.ndspy.rom.NintendoDSRom.fromFile') as read:
                worker=SoaringWorker(root/'private.nds',root/'cache')
                try:
                    request=root/'cache/request-test.json'
                    request.write_text(json.dumps({'zone':191,'worldX':float('nan'),'worldZ':10,'worldY':0}))
                    ready=root/'cache/ready-test.json';deadline=time.monotonic()+3
                    while not ready.is_file() and time.monotonic()<deadline:time.sleep(.02)
                    self.assertTrue(ready.is_file());self.assertIn('error',json.loads(ready.read_text()));read.assert_not_called()
                finally:worker.stop.set();worker.thread.join(timeout=3)

if __name__=='__main__':unittest.main()
