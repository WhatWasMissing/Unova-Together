"""Palette alias and asynchronous flight-request rejection regressions."""
import json,struct,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import ndspy.texture
from build_battle_surroundings import texture_pack
from soaring_scene_worker import (SoaringWorker,build_flyway_routes,make_flyway_faces,
                                  make_region_fill_faces,flight_matrix_offsets,flight_matrix_aliases,
                                  flight_matrix_layout,merged_flight_grid,export_scene,
                                  export_with_budget,interior_water_cells,atlas_water_cells,
                                  flight_atlas_coverage,make_water_faces,
                                  flight_water_material,_FLIGHT_WORLD_OFFSETS,
                                  _FLIGHT_SUPPLEMENTAL_WORLD_OFFSETS,
                                  _FLIGHT_CONFIRMED_WARP_WORLD_OFFSETS,
                                  active_flight_matrix_preference,atlas_landmarks,
                                  decomp_region_routes,_nearest_region_biome)
from soaring_geometry import collision_debug_tiles,landing_tiles
from types import SimpleNamespace
from PIL import Image
from extract_battle_surroundings import field_chunk_model
from field_scene_geometry import (node_transform,_multiply_affine,_identity_affine,
                                  _render_commands)

class SoaringWorkerTests(unittest.TestCase):
    def test_static_nitro_nodes_apply_translation_and_pivot_rotation(self):
        translated=bytearray(16)
        struct.pack_into('<Hh3i',translated,0,0xf806,0,12*4096,-2*4096,7*4096)
        matrix=node_transform(translated,0)
        self.assertEqual(tuple(matrix[i][3] for i in range(3)),(12.0,-2.0,7.0))

        pivot=bytearray(8)
        # Pivot form 2 rotates the X axis onto Y; a=1, b=0.
        struct.pack_into('<Hh2h',pivot,0,0x2f,0,4096,0)
        rotation=node_transform(pivot,0)
        self.assertEqual(tuple(rotation[row][0] for row in range(3)),(0.0,1.0,0.0))

    def test_nitro_render_commands_compose_nodes_and_matrix_stack(self):
        root=_identity_affine()
        child=tuple(tuple((1.0 if row==col else 0.0) if col<3 else (4.0,0.0,5.0)[row]
                          for col in range(4)) for row in range(3))
        sibling=tuple(tuple((1.0 if row==col else 0.0) if col<3 else (0.0,0.0,8.0)[row]
                            for col in range(4)) for row in range(3))
        triangle=[[(0,0,0,0,0),(1,0,0,1,0),(0,0,1,0,1)]]
        # Save node 0, load it before node 1 and store node 1, then reload 0
        # before rendering node 2. This catches sibling transforms leaking.
        commands=bytes((0x26,0,0,0,0, 0x66,1,0,0,1,0,
                        0x02,1,1, 0x0b, 0x04,0, 0x05,0, 0x2b,
                        0x46,2,0,0,0, 0x02,2,1, 0x0b, 0x05,0, 0x2b, 0x01))
        result=_render_commands(commands,[root,child,sibling],[triangle],[('ground','grass')])
        self.assertEqual(len(result),2)
        self.assertEqual(result[0][1][0][:3],(4.0,0.0,5.0))
        self.assertEqual(result[0][1][1][:3],(5.0,0.0,5.0))
        self.assertEqual(result[1][1][0][:3],(0.0,0.0,8.0))

    def test_nitro_billboard_command_keeps_a_crossed_static_plane(self):
        triangle=[[(0,0,0,0,0),(1,0,0,1,0),(0,0,1,0,1)]]
        commands=bytes((0x02,0,1, 0x07,0, 0x04,0, 0x05,0, 0x01))
        result=_render_commands(commands,[_identity_affine()],[triangle],[('ground','grass')])
        self.assertEqual(len(result),2)
        self.assertEqual(result[1][1][1][:3],(0.0,0.0,-1.0))

    def test_ng_field_chunks_render_model_without_inventing_collision_ground(self):
        model=bytearray(24);model[:4]=b'BMD0';struct.pack_into('<I',model,8,len(model))
        model=bytes(model);props=struct.pack('<I',1)+bytes(16)
        chunk=b'NG\x02\0'+struct.pack('<III',16,16+len(model),16+len(model)+len(props))+model+props
        parsed_model,parsed_props,has_terrain=field_chunk_model(chunk)
        self.assertEqual(parsed_model,model)
        self.assertEqual(parsed_props,props)
        self.assertFalse(has_terrain)
        with self.assertRaisesRegex(ValueError,'Invalid NG props'):
            broken=bytearray(chunk);struct.pack_into('<I',broken,16+len(model),2)
            field_chunk_model(bytes(broken))

    def test_gc_field_chunks_keep_their_two_terrain_layers(self):
        model=bytearray(24);model[:4]=b'BMD0';struct.pack_into('<I',model,8,len(model))
        model=bytes(model);layer0=b'lower';layer1=b'upper';props=struct.pack('<I',1)+bytes(16)
        model_offset=24;terrain0=model_offset+len(model);terrain1=terrain0+len(layer0)
        props_offset=terrain1+len(layer1);end_offset=props_offset+len(props)
        chunk=(b'GC\x04\0'+struct.pack('<5I',model_offset,terrain0,terrain1,props_offset,end_offset)+
               model+layer0+layer1+props)
        parsed_model,parsed_props,has_terrain=field_chunk_model(chunk)
        self.assertEqual(parsed_model,model)
        self.assertEqual(parsed_props,props)
        self.assertTrue(has_terrain)

    @staticmethod
    def _flight_fixture():
        headers=bytearray(12*48)
        for zone,area,matrix,event in ((7,0,0,0),(11,1,1,1)):
            struct.pack_into('<HH',headers,zone*48+2,area,matrix)
            struct.pack_into('<H',headers,zone*48+22,event)
            struct.pack_into('<H',headers,zone*48+30,0x2000)
        areas=bytearray(20);areas[6]=areas[16]=1
        def event(destination,x,z):
            warp=struct.pack('<HHHH6H',destination,0,0,0,x,0,z,1,1,0)
            return struct.pack('<IBBBB',8+len(warp),0,0,1,0)+warp
        matrices=[struct.pack('<IHHii',1,1,1,10,7),
                  struct.pack('<IHHii',1,1,1,12,11)]
        return SimpleNamespace(headers=headers,areas=areas,events=[event(11,160,320),event(7,32,16)],matrices=matrices)

    def test_reciprocal_outdoor_warps_merge_matrix_frames(self):
        source=self._flight_fixture()
        self.assertEqual(flight_matrix_offsets(source,0),{0:(0,0),1:(128,304)})
        source=self._flight_fixture()
        texture=SimpleNamespace(width=2,height=2,renderAsImage=lambda _:Image.new('RGBA',(2,2),'green'))
        pack=SimpleNamespace(textures=[('grass',texture)],palettes=[('palette',SimpleNamespace(colors=[(0,31,0,31)]))])
        calls=[]
        def scene(zone,x,z,y,**kwargs):
            calls.append((zone,x,z,kwargs['layout_matrix']))
            tx,tz=(3,4) if zone==7 else (7,8)
            return [(('terrain','grass','palette'),[(0,0,0,0,0),(1,0,0,1,0),(0,0,1,0,1)])],{ 'terrain':pack },{
                'omittedProps':[],'chunks':[zone],'landings':[[zone,tx,tz,0]],
                'collisionTiles':[[tx,tz,0,0]]}
        source.scene=scene
        source.collision_debug=True
        with tempfile.TemporaryDirectory() as temporary:
            result=export_scene(source,7,50,50,0,Path(temporary)/'linked')
        self.assertEqual({call[0] for call in calls},{7,11})
        self.assertEqual(result['format'],3)
        self.assertEqual(result['matrixOffsets'],{'0':[0,0],'1':[128,304]})
        self.assertEqual(result['atlasOriginCell'],[0,0])
        self.assertEqual(result['atlasSize'],[2,2])
        self.assertIn([7,3,4,0,56,72],result['landings'])
        self.assertIn([11,7,8,0,248,440],result['landings'])
        self.assertIn([15,27,0,0],result['collisionTiles'])
        self.assertEqual(result['chunks'],[7,11])

    def test_destination_warp_places_unambiguous_one_way_outdoor_link(self):
        headers=bytearray(12*48)
        for zone,area,matrix,event_id in ((7,0,0,0),(11,1,1,1)):
            struct.pack_into('<HH',headers,zone*48+2,area,matrix)
            struct.pack_into('<H',headers,zone*48+22,event_id)
        areas=bytearray(20);areas[6]=areas[16]=1
        def event(destination,x,z):
            warp=struct.pack('<HHHH6H',destination,0,0,0,x,0,z,1,1,0)
            return struct.pack('<IBBBB',8+len(warp),0,0,1,0)+warp
        # The destination warp exits to another zone instead of reciprocating
        # to zone 7. Its index and local position still anchor the arrival map.
        source=SimpleNamespace(headers=headers,areas=areas,
            events=[event(11,160,320),event(12,32,16)],
            matrices=[struct.pack('<IHHi',0,1,1,10),struct.pack('<IHHi',0,1,1,11)],
            rom=SimpleNamespace(idCode=b'IREO'))
        self.assertEqual(flight_matrix_offsets(source,0),{0:(0,0),1:(128,304)})

    def test_destination_warp_can_anchor_from_the_known_arrival_side(self):
        headers=bytearray(13*48)
        for zone,area,matrix,event_id in ((7,0,0,0),(11,1,1,1),(12,0,0,2)):
            struct.pack_into('<HH',headers,zone*48+2,area,matrix)
            struct.pack_into('<H',headers,zone*48+22,event_id)
        areas=bytearray(20);areas[6]=areas[16]=1
        def event(warps):
            records=b''.join(struct.pack('<HHHH6H',dest,dest_warp,0,0,x,0,z,1,1,0)
                             for dest,dest_warp,x,z in warps)
            return struct.pack('<IBBBB',8+len(records),0,0,len(warps),0)+records
        # The unplaced map points to an existing arrival coordinate, but that
        # destination's exit goes elsewhere instead of reciprocating.
        source=SimpleNamespace(headers=headers,areas=areas,
            events=[event([(12,0,160,320)]),event([(7,0,32,16)]),event([])],
            matrices=[struct.pack('<IHHi',0,1,1,10),struct.pack('<IHHi',0,1,1,11)],
            rom=SimpleNamespace(idCode=b'IREO'))
        self.assertEqual(flight_matrix_offsets(source,0),{0:(0,0),1:(128,304)})

    def test_indoor_only_matrix_can_relay_a_consistent_outdoor_grid_path(self):
        headers=bytearray(13*48)
        for zone,area,matrix,event_id in ((7,0,0,0),(11,1,1,1),(12,2,2,2)):
            struct.pack_into('<HH',headers,zone*48+2,area,matrix)
            struct.pack_into('<H',headers,zone*48+22,event_id)
        areas=bytearray(30)
        areas[6]=areas[26]=1

        def event(warps):
            records=b''.join(struct.pack('<HHHH6H',dest,dest_warp,0,0,x,0,z,1,1,0)
                             for dest,dest_warp,x,z in warps)
            return struct.pack('<IBBBB',8+len(records),0,0,len(warps),0)+records

        # The outdoor maps are separated by one interior-only transition
        # matrix. Its reciprocal grid warps still define an exact world frame.
        source=SimpleNamespace(headers=headers,areas=areas,
            events=[event([(11,0,160,320)]),
                    event([(7,0,32,16),(12,0,160,320)]),
                    event([(11,1,32,16)])],
            matrices=[struct.pack('<IHHi',0,1,1,10),
                      struct.pack('<IHHi',0,1,1,11),
                      struct.pack('<IHHi',0,1,1,12)],
            rom=SimpleNamespace(idCode=b'IREO'))
        self.assertEqual(flight_matrix_offsets(source,0),
                         {0:(0,0),2:(256,608)})

    def test_conflicting_one_way_warp_offsets_are_not_guessed(self):
        headers=bytearray(12*48)
        for zone,area,matrix,event_id in ((7,0,0,0),(8,0,0,1),(11,1,1,2)):
            struct.pack_into('<HH',headers,zone*48+2,area,matrix)
            struct.pack_into('<H',headers,zone*48+22,event_id)
        areas=bytearray(20);areas[6]=areas[16]=1
        def event(warps):
            records=b''.join(struct.pack('<HHHH6H',dest,dest_warp,0,0,x,0,z,1,1,0)
                             for dest,dest_warp,x,z in warps)
            return struct.pack('<IBBBB',8+len(records),0,0,len(warps),0)+records
        source=SimpleNamespace(headers=headers,areas=areas,
            events=[event([(11,0,160,320)]),event([(11,1,416,416)]),
                    event([(12,0,32,16),(13,0,96,96)])],
            matrices=[struct.pack('<IHHi',0,1,1,10),struct.pack('<IHHi',0,1,1,11)],
            rom=SimpleNamespace(idCode=b'IREO'))
        self.assertEqual(flight_matrix_offsets(source,0),{0:(0,0)})

    def test_flight_links_include_outdoor_maps_without_vanilla_fly_access(self):
        source=self._flight_fixture()
        # In the BW2 decomp, fly_from is a zone-header permission for the
        # vanilla Fly move. Soaring has its own outdoor launch flow and must
        # still render connected exterior maps where that bit is unset.
        struct.pack_into('<H',source.headers,11*48+30,0x0008)
        self.assertEqual(flight_matrix_offsets(source,0),{0:(0,0),1:(128,304)})

    def test_identical_chunk_matrices_share_a_frame_and_merge_outdoor_zones(self):
        headers=bytearray(12*48)
        struct.pack_into('<HH',headers,7*48+2,0,0)
        struct.pack_into('<HH',headers,11*48+2,1,1)
        areas=bytearray(20);areas[6]=areas[16]=1
        # OVERWORLD_2 uses the same placed terrain chunks as OVERWORLD while
        # supplying extra per-cell zone ids for gate-area context.
        matrices=[struct.pack('<IHHii',1,1,1,10,-1),
                  struct.pack('<IHHii',1,1,1,10,11)]
        source=SimpleNamespace(headers=headers,areas=areas,events=[],matrices=matrices)
        self.assertEqual(flight_matrix_aliases(source),{0:0,1:0})
        self.assertEqual(flight_matrix_offsets(source,1),{0:(0,0)})
        self.assertEqual(flight_matrix_layout(source,0)[3],(11,))
        self.assertEqual(merged_flight_grid(source,{0:(0,0)})[-1][0][3],(11,))

    def test_black2_town_map_anchors_add_outdoor_matrices_missing_from_warp_graph(self):
        headers=bytearray(118*48)
        struct.pack_into('<HH',headers,2,0,0)
        struct.pack_into('<HH',headers,48+2,1,117)
        areas=bytearray(20);areas[6]=areas[16]=1
        matrices=[struct.pack('<IHHi',0,1,1,index) for index in range(118)]
        source=SimpleNamespace(headers=headers,areas=areas,events=[],matrices=matrices,
                              rom=SimpleNamespace(idCode=b'IREO'))
        offsets=flight_matrix_offsets(source,0)
        self.assertEqual(offsets[0],(0,0))
        self.assertEqual(offsets[117],(6656,4608))

    def test_supplemental_outdoor_regions_are_complete_and_connected(self):
        expected={2,4,5,6,7,8,9,10,93,103,119,162,189,211,225,226,
                  228,229,230,231,232,233,234,235,314,372,387,416}
        self.assertEqual(set(_FLIGHT_SUPPLEMENTAL_WORLD_OFFSETS),expected)
        all_outdoor={0,1,2,3,4,5,6,7,8,9,10,11,14,16,41,87,93,103,
                     106,107,117,119,128,132,133,135,136,162,182,183,189,
                     190,208,210,211,224,225,226,228,229,230,231,232,233,
                     234,235,238,250,251,255,256,273,275,296,297,314,337,
                     338,348,356,357,372,380,383,384,387,390,414,416}
        anchored=set(_FLIGHT_WORLD_OFFSETS)|set(_FLIGHT_CONFIRMED_WARP_WORLD_OFFSETS)|expected
        self.assertEqual(anchored,all_outdoor)

        def box(matrix,dimensions):
            anchors=(_FLIGHT_WORLD_OFFSETS if matrix in _FLIGHT_WORLD_OFFSETS
                     else _FLIGHT_SUPPLEMENTAL_WORLD_OFFSETS)
            x,z=anchors[matrix]
            width,depth=dimensions
            return x,z,x+width*512,z+depth*512

        def touches(a,b):
            overlap_x=max(a[0],b[0])<min(a[2],b[2])
            overlap_z=max(a[1],b[1])<min(a[3],b[3])
            return ((a[2]==b[0] or b[2]==a[0]) and overlap_z or
                    (a[3]==b[1] or b[3]==a[1]) and overlap_x)

        def connected(matrices,dimensions):
            boxes={matrix:box(matrix,dimensions[matrix]) for matrix in matrices}
            reached={next(iter(matrices))}
            while True:
                additions={other for matrix in reached for other in matrices-reached
                           if touches(boxes[matrix],boxes[other])}
                if not additions:break
                reached.update(additions)
            return reached

        # Castelia's supplemental blocks join the verified 2x2 city matrix.
        city={132,2,4,5,6,7,8,9,10}
        city_dims={132:(2,2),2:(1,2),4:(1,2),5:(1,2),6:(1,2),
                   7:(1,1),8:(1,1),9:(1,1),10:(1,1)}
        self.assertEqual(connected(city,city_dims),city)

        # Entrée Forest's nine scenes form one 3x3 group beside Entralink.
        forest={117,119,228,229,230,231,232,233,234,235}
        forest_dims={matrix:(2,2) if matrix==117 else (1,1) for matrix in forest}
        self.assertEqual(connected(forest,forest_dims),forest)

        # The unsupported Victory Road sections touch the warp-placed route.
        victory={337,162,387}
        victory_dims={337:(3,2),162:(2,2),387:(2,2)}
        self.assertEqual(connected(victory,victory_dims),victory)

        # Explicit points match the decomp's Fly coordinates and parent maps.
        self.assertEqual(_FLIGHT_SUPPLEMENTAL_WORLD_OFFSETS[93],
                         (16*(145-5),16*(210-4)))
        self.assertEqual(_FLIGHT_SUPPLEMENTAL_WORLD_OFFSETS[103],
                         (16*(371-5),16*(499-4)))
        self.assertEqual(_FLIGHT_SUPPLEMENTAL_WORLD_OFFSETS[189],
                         (16*(111-5),16*(266-4)))

    def test_overlapping_matrix_cells_use_one_nearest_external_chunk(self):
        root=struct.pack('<IHH2i',0,2,1,10,11)
        overlay=struct.pack('<IHHi',0,1,1,12)
        source=SimpleNamespace(matrices=[root,overlay])
        _ox,_oz,width,height,cells,_layouts,masks=merged_flight_grid(
            source,{0:(0,0),1:(512,0)},with_masks=True)
        self.assertEqual((width,height),(2,1))
        self.assertEqual(cells,(1,1))
        self.assertEqual(masks,{0:(True,False),1:(True,)})

    def test_active_takeoff_matrix_can_render_when_other_maps_occlude_it(self):
        source=SimpleNamespace(matrices=[
            struct.pack('<IHH2i',0,2,1,10,11),
            struct.pack('<IHH2i',0,2,1,12,13),
            struct.pack('<IHH2i',0,2,1,14,15)])
        offsets={0:(0,0),1:(0,0),2:(0,0)}
        ordinary=merged_flight_grid(source,offsets,with_masks=True)
        self.assertEqual(ordinary[-1][2],(False,False))
        visible=merged_flight_grid(source,offsets,with_masks=True,
                                   preferred_matrix=2)
        self.assertEqual(visible[-1][2],(True,True))
        self.assertEqual(visible[-1][1],(False,False))
        layouts={2:(2,1,(14,15),None)}
        masks={2:(False,True)}
        self.assertEqual(active_flight_matrix_preference(2,256,256,layouts,masks),2)
        self.assertIsNone(active_flight_matrix_preference(2,768,256,layouts,masks))
        self.assertIsNone(active_flight_matrix_preference(0,256,256,layouts,{0:(False,)}))

    def test_visible_zone_follows_the_matrix_that_owns_the_overlapping_chunk(self):
        source=self._flight_fixture()
        # Put a representative zone before zone 11 in the same matrix. The
        # cell's zone overlay must win; a missing overlay must fall back to
        # that representative instead of keeping the take-off zone.
        struct.pack_into('<HH',source.headers,9*48+2,1,1)
        struct.pack_into('<H',source.headers,9*48+22,0xffff)
        texture=SimpleNamespace(width=2,height=2,renderAsImage=lambda _:Image.new('RGBA',(2,2),'green'))
        pack=SimpleNamespace(textures=[('grass',texture)],palettes=[('palette',SimpleNamespace(colors=[(0,31,0,31)]))])
        def scene(zone,x,z,y,**kwargs):
            return [(('terrain','grass','palette'),[(0,0,0,0,0),(1,0,0,1,0),(0,0,1,0,1)])],{'terrain':pack},{'omittedProps':[],'chunks':[zone],'landings':[],'collisionTiles':[]}
        source.scene=scene
        with tempfile.TemporaryDirectory() as temporary:
            result=export_scene(source,7,200,350,0,Path(temporary)/'owner')
            source.matrices[1]=struct.pack('<IHHii',1,1,1,12,-1)
            fallback=export_scene(source,7,200,350,0,Path(temporary)/'fallback')
        self.assertEqual(result['sourceZone'],7)
        self.assertEqual(result['zone'],11)
        self.assertEqual(fallback['zone'],9)

    def test_region_gaps_get_visual_routes_without_collision_data(self):
        # Three real map islands in a line should be joined with two routes.
        routes=build_flyway_routes(5,1,(0,-1,1,-1,2))
        self.assertEqual(len(routes),2)
        faces=make_flyway_faces(routes,0,0,4096)
        self.assertTrue(faces)
        self.assertEqual({face[0] for face in faces},{0,1,2})
        # Geometry only supplies appearance; collision still comes from the ROM.
        self.assertTrue(all(len(face[1])==3 for face in faces))

    def test_native_water_covers_every_empty_cell_inside_the_atlas(self):
        # Two separated authored regions retain their convex-hull helper for
        # shaping terrain, while the rendered sea covers the full map bounds.
        width,depth=10,7;grid=[-1]*(width*depth)
        for z in range(2,5):
            for x in (1,2,6,7):grid[z*width+x]=z*width+x
        hull_cells=interior_water_cells(width,depth,grid)
        self.assertIn(3*width+4,hull_cells)
        self.assertIn(3*width+0,hull_cells) # closes the one-cell diagonal/coast edge
        self.assertNotIn(3*width+9,hull_cells)
        self.assertEqual(hull_cells,interior_water_cells(width,depth,grid))
        cells=atlas_water_cells(width,depth,grid)
        self.assertIn(3*width+9,cells) # map corners receive the tiled sea too
        self.assertEqual(len(cells),width*depth-sum(value>=0 for value in grid))
        coverage=flight_atlas_coverage(width,depth,grid)
        self.assertEqual(coverage['enclosedVoidCells'],0)
        self.assertEqual(coverage['unfilledCellsTouchingMap'],0)
        self.assertEqual(coverage['coveredComponents'],1)
        self.assertEqual(coverage['outerBoundaryCells'],0)
        self.assertEqual(coverage['coveredCells'],width*depth)
        faces=make_water_faces(cells,width,0,0,4*512,3*512,4096,5)
        self.assertEqual(len(faces),len(cells))
        self.assertTrue(all(face[0]==5 and len(face[1])==4 for face in faces))
        self.assertEqual(faces[0][1][0][1],-34.)
        self.assertEqual(faces[0][1][1][3]-faces[0][1][0][3],32)

    def test_export_places_water_under_atlas_corner_gaps(self):
        headers=bytearray(8*48);struct.pack_into('<HH',headers,7*48+2,0,0)
        areas=bytearray(10);areas[6]=1
        matrix=struct.pack('<IHH4i',0,2,2,1,-1,-1,-1)
        texture=SimpleNamespace(width=32,height=32,
            renderAsImage=lambda _:Image.new('RGBA',(32,32),'cyan'))
        palette=SimpleNamespace(colors=[(0,31,31,31)])
        def scene(*_args,**_kwargs):
            return [],{}, {'omittedProps':[],'chunks':[]}
        source=SimpleNamespace(headers=headers,areas=areas,matrices=[matrix],scene=scene,
                               _flight_water_material=(texture,palette))
        with tempfile.TemporaryDirectory() as temporary:
            result=export_scene(source,7,128,128,0,Path(temporary)/'corner-gaps')
        self.assertEqual(result['atlasSize'],[2,2])
        self.assertEqual(result['seaTiles'],3)
        self.assertTrue(result['textures'])

    def test_water_material_uses_the_decomp_identified_undella_pack(self):
        from soaring_scene_worker import _WATER_ZONE
        headers=bytearray((_WATER_ZONE+1)*48);struct.pack_into('<H',headers,_WATER_ZONE*48+2,0)
        areas=bytearray(10);struct.pack_into('<H',areas,2,0)
        texture=SimpleNamespace(width=32,height=32,renderAsImage=lambda _:Image.new('RGBA',(32,32),'cyan'))
        palette=SimpleNamespace(colors=[(0,31,31,31)])
        pack=SimpleNamespace(textures=[('sea_mizu1',texture)],palettes=[('sea_mizu1_pl',palette)])
        source=SimpleNamespace(headers=headers,areas=areas,packs=[b'undella-map-pack'])
        with patch('soaring_scene_worker.texture_pack',return_value=pack) as unpack:
            material=flight_water_material(source)
            self.assertEqual(material,(texture,palette))
            self.assertEqual(flight_water_material(source),material)
            unpack.assert_called_once_with(b'undella-map-pack')

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

    def test_decomp_named_routes_project_into_the_live_atlas(self):
        catalog={'connections':[['ZONE_A','ZONE_B'],['ZONE_A','ZONE_C']],
                 'places':[]}
        landmarks=[
            {'zoneKey':'ZONE_A','worldX':2.5*512,'worldZ':3.5*512},
            {'zoneKey':'ZONE_B','worldX':4.0*512,'worldZ':3.5*512},
            {'zoneKey':'ZONE_C','worldX':80*512,'worldZ':3.5*512},
        ]
        routes=decomp_region_routes(10,8,0,0,landmarks,catalog)
        self.assertEqual(len(routes),1)
        self.assertEqual((routes[0]['from'],routes[0]['to']),('ZONE_A','ZONE_B'))
        self.assertEqual(routes[0]['points'],((2.5,3.5),(4.,3.5)))

    def test_decomp_place_biomes_use_world_cell_units(self):
        places=[{'worldX':4*512,'worldZ':6*512,'biome':4}]
        self.assertEqual(_nearest_region_biome(4.2,5.9,places),4)
        self.assertIsNone(_nearest_region_biome(20,20,places))

    def test_decomp_overworld_and_fly_coordinates_anchor_named_places(self):
        headers=bytearray(10*48)
        for zone,matrix in ((7,0),(8,0),(9,1)):
            struct.pack_into('<HH',headers,zone*48+2,0,matrix)
        areas=bytearray(10);areas[6]=1
        matrix0=struct.pack('<IHH4i',1,2,1,10,11,7,-1)
        matrix1=struct.pack('<IHH2i',0,2,1,12,13)
        source=SimpleNamespace(headers=headers,areas=areas,matrices=[matrix0,matrix1])
        catalog={'mainMatrix':0,'townMapToWorldX':[10,2,3],
                 'townMapToWorldZ':[20,4,5],
                 'places':[
                     {'zone':'ZONE_TOWN','zoneId':7,'name':'Mapped Town','type':0,
                      'map':[2,3],'fly':True,'flyPosition':[100,0,200],
                      'matrix':0,'biome':'settlement'},
                     {'zone':'ZONE_ROUTE','zoneId':8,'name':'Mapped Route','type':2,
                      'map':[0,0],'fly':False,'matrix':0,'biome':'route',
                      'mainCell':[1.5,.5]},
                     {'zone':'ZONE_OTHER','zoneId':9,'name':'Other Place','type':2,
                      'map':[2,3],'fly':False,'matrix':1,'biome':'forest'},
                 ]}
        landmarks=atlas_landmarks(source,{0:(100,200),1:(500,600)},catalog=catalog)
        by_zone={place['zoneKey']:place for place in landmarks}
        self.assertEqual((by_zone['ZONE_TOWN']['worldX'],by_zone['ZONE_TOWN']['worldZ']),
                         (1700,3400))
        self.assertEqual((by_zone['ZONE_ROUTE']['worldX'],by_zone['ZONE_ROUTE']['worldZ']),
                         (868,456))
        self.assertEqual((by_zone['ZONE_OTHER']['worldX'],by_zone['ZONE_OTHER']['worldZ']),
                         (123,243))

    def test_decomp_biome_shapes_authored_gap_without_creating_landing_data(self):
        grid=[-1]*49
        for z in range(1,6):
            for x in range(1,6):
                if (x,z)!=(3,3):grid[z*7+x]=z*7+x
        place={'zone':12,'name':'Desert Resort','type':2,'biome':4,
               'worldX':3.5*512,'worldZ':3.5*512}
        faces,biome=make_region_fill_faces(
            7,7,grid,3.5*512,3.5*512,4096,origin=(0,0),
            region_places=[place])
        self.assertEqual(biome[3*7+3],4)
        self.assertTrue(any(face[0]==4 for face in faces))
        # Generated scenery is returned separately from ROM-derived landing
        # sites; this helper has no path that can add a landing.
        self.assertTrue(all(len(face)==2 and len(face[1])==3 for face in faces))

    def test_zone_event_positions_are_decoded_for_landing_clearance(self):
        headers=bytearray(48);struct.pack_into('<H',headers,22,0)
        record=struct.pack('<12HIHHI',1,162,0,0,0,7,1,0,0,0,0,0,0,12,19,0)
        event=struct.pack('<IBBBB',8+len(record),0,1,0,0)+record
        source=SimpleNamespace(headers=headers,events=[event])
        from build_battle_surroundings import FieldSource
        self.assertEqual(FieldSource.event_objects(source,0),[(12,19)])

    def test_landing_whitelist_skips_npc_interaction_radius(self):
        terrain=bytearray(struct.pack('<HH',32,32)+struct.pack('<HHI',0,3,0x00800000)*1024)
        chunk=b'WB\x03\0'+struct.pack('<4I',20,20,20+len(terrain),20+len(terrain))+terrain
        landings=landing_tiles(chunk,[],1,0,0,(256,0,256),0,[],[(8,8)])
        positions={(entry[1],entry[2]) for entry in landings}
        self.assertNotIn((8,8),positions)
        self.assertNotIn((6,8),positions)
        self.assertIn((5,8),positions)

    def test_collision_debug_classifies_real_ground_and_blockers(self):
        terrain=bytearray(struct.pack('<HH',32,32)+struct.pack('<HHI',0,3,0x00800000)*1024)
        struct.pack_into('<HHI',terrain,4+(0*32+1)*8,0,3,0x00810001) # blocked
        struct.pack_into('<HHI',terrain,4+(0*32+2)*8,2<<2,3,0x00800000) # steep
        struct.pack_into('<HHI',terrain,4+(0*32+3)*8,0,3,0x0000003f) # surf water
        chunk=b'WB\x03\0'+struct.pack('<4I',20,20,20+len(terrain),20+len(terrain))+terrain
        tiles=collision_debug_tiles(chunk,[],0,0,(248,0,248),0,[],radius=60)
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
            self.assertEqual(result['format'],3);self.assertEqual(result['radius'],4096)
            self.assertEqual(result['seaTiles'],0) # Synthetic fixture has no native ROM texture packs.
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
                    worker.started=0 # Ignore filesystem timestamp precision in this deterministic test.
                    request=root/'cache/request-test.json'
                    request.write_text(json.dumps({'zone':191,'worldX':float('nan'),'worldZ':10,'worldY':0}))
                    ready=root/'cache/ready-test.json';deadline=time.monotonic()+6
                    while not ready.is_file() and time.monotonic()<deadline:time.sleep(.02)
                    self.assertTrue(ready.is_file());self.assertIn('error',json.loads(ready.read_text()));read.assert_not_called()
                finally:worker.stop.set();worker.thread.join(timeout=3)

    def test_zone_zero_is_accepted_as_a_real_soaring_map(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with patch('soaring_scene_worker.ndspy.rom.NintendoDSRom.fromFile') as read, \
                 patch('soaring_scene_worker.FieldSource', return_value=SimpleNamespace()), \
                 patch('soaring_scene_worker.export_with_budget',
                       return_value={'omittedProps':[]}) as export:
                worker=SoaringWorker(root/'private.nds',root/'cache')
                try:
                    worker.started=0
                    request=root/'cache/request-zone-zero.json'
                    request.write_text(json.dumps({'zone':0,'worldX':256,
                                                   'worldZ':256,'worldY':0}))
                    ready=root/'cache/ready-zone-zero.json';deadline=time.monotonic()+6
                    while not ready.is_file() and time.monotonic()<deadline:time.sleep(.02)
                    self.assertTrue(ready.is_file())
                    response=json.loads(ready.read_text())
                    self.assertNotIn('error',response)
                    self.assertEqual(response['zone'],0)
                    read.assert_called_once()
                    self.assertEqual(export.call_args.args[1],0)
                finally:worker.stop.set();worker.thread.join(timeout=3)

if __name__=='__main__':unittest.main()
