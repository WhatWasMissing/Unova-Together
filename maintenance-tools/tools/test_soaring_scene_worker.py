"""Palette alias and asynchronous flight-request rejection regressions."""
import json,struct,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import ndspy.texture
from build_battle_surroundings import texture_pack
from soaring_scene_worker import SoaringWorker,export_scene,export_with_budget
from types import SimpleNamespace
from PIL import Image

class SoaringWorkerTests(unittest.TestCase):
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
            return [(('terrain-1','grass','palette'),[(0,0,0,0,0),(1,0,0,1,0),(0,0,1,0,1)])],{'terrain-1':pack},{'omittedProps':[],'chunks':[1]}
        source=SimpleNamespace(headers=headers,areas=areas,matrices=[matrix],scene=scene)
        with tempfile.TemporaryDirectory() as temporary:
            result=export_scene(source,1,600,20,0,Path(temporary)/'neighbor')
            self.assertEqual(result['sourceZone'],1);self.assertEqual(result['zone'],2)
            self.assertEqual(calls[0][0],2);self.assertTrue(calls[0][1]['flight'])
            self.assertEqual(calls[0][1]['radius'],4096);self.assertEqual(calls[0][1]['layout_matrix'],0)
            self.assertEqual(result['format'],2);self.assertEqual(result['radius'],4096)
            self.assertEqual(result['seaTiles'],0) # The atlas sea is a zero-mesh background.
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
