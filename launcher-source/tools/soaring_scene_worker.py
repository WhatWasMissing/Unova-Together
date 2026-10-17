"""Local flight scenery from the player's real field meshes. mvq1303, GPL-3.0-or-later."""
from pathlib import Path
from types import SimpleNamespace
from functools import lru_cache
import heapq, json, math, os, threading, uuid, time, struct
import ndspy.rom
import ndspy.color
from build_battle_surroundings import FieldSource, texture_pack
from battle_surroundings_worker import atomic_json
from extract_battle_surroundings import matrix_cells
from soaring_geometry import collision_debug_tiles


_MATRIX_SCALE=512  # 32 map tiles per matrix cell, at 16 world units per tile.
_WATER_ZONE=240  # Undella Bay in the user's English Black 2 Redux decomp.
_REGION_DATA_FILE=Path(__file__).with_name('soaring_region_data.json')


@lru_cache(maxsize=1)
def soaring_region_catalog():
    """Load compact named-place and route metadata generated from the decomp."""
    try:
        catalog=json.loads(_REGION_DATA_FILE.read_text(encoding='utf-8'))
    except (OSError,ValueError):
        return {'places':[],'connections':[]}
    if catalog.get('schema')!=1 or len(catalog.get('places',()))>256:
        return {'places':[],'connections':[]}
    return catalog


def atlas_landmarks(source,offsets,layouts=None,catalog=None):
    """Resolve decomp Town Map places into the active ROM's flight atlas.

    Chunk-zone centroids take priority. Town Map coordinates fill in named
    exterior places that have no zone-labelled cell in their local matrix.
    The markers guide scenery only; they never become landing candidates.
    """
    catalog=catalog if catalog is not None else soaring_region_catalog()
    if not catalog.get('places') or not hasattr(source,'headers'):
        return []
    aliases=flight_matrix_aliases(source)
    layouts=layouts if layouts is not None else {
        matrix:flight_matrix_layout(source,matrix,aliases) for matrix in offsets
    }
    count=len(source.headers)//48
    x_coeff=catalog.get('townMapToWorldX',(0,0,0))
    z_coeff=catalog.get('townMapToWorldZ',(0,0,0))
    main_offset=offsets.get(catalog.get('mainMatrix',0),(0,0))
    result=[]
    for place in catalog['places']:
        zone=place.get('zoneId',-1)
        if not isinstance(zone,int) or not 0<=zone<count:
            continue
        raw_matrix=struct.unpack_from('<H',source.headers,zone*48+4)[0]
        matrix=aliases.get(raw_matrix,raw_matrix)
        if matrix not in offsets:
            continue
        layout=layouts.get(matrix)
        cells=[]
        if layout is not None:
            width,depth,_ids,zones=layout
            if zones is not None:
                cells=[index for index,value in enumerate(zones) if value==zone]
        if cells:
            width=layout[0]
            local_x=sum(index%width+.5 for index in cells)/len(cells)
            local_z=sum(index//width+.5 for index in cells)/len(cells)
            world_x=offsets[matrix][0]+local_x*_MATRIX_SCALE
            world_z=offsets[matrix][1]+local_z*_MATRIX_SCALE
            # The decomp stores actual Fly destinations in 16-unit tile
            # coordinates. On the authored main overworld these give more
            # precise town anchors than a whole-chunk centroid.
            fly_position=place.get('flyPosition')
            if (matrix==catalog.get('mainMatrix') and place.get('fly') and
                    isinstance(fly_position,(list,tuple)) and len(fly_position)>=3):
                world_x=main_offset[0]+int(fly_position[0])*16
                world_z=main_offset[1]+int(fly_position[2])*16
        else:
            main_cell=place.get('mainCell')
            if place.get('matrix')==catalog.get('mainMatrix') and isinstance(main_cell,(list,tuple)) and len(main_cell)==2:
                world_x=main_offset[0]+float(main_cell[0])*_MATRIX_SCALE
                world_z=main_offset[1]+float(main_cell[1])*_MATRIX_SCALE
            else:
                map_position=place.get('map',(0,0))
                map_x,map_y=map_position
                world_x=(x_coeff[0]+x_coeff[1]*map_x+x_coeff[2]*map_y)+main_offset[0]
                world_z=(z_coeff[0]+z_coeff[1]*map_x+z_coeff[2]*map_y)+main_offset[1]
        biome={'coast':0,'forest':1,'route':2,'grassland':2,
               'settlement':2,'mountain':3,'desert':4}.get(place.get('biome'),2)
        result.append({
            'zone':zone,'zoneKey':str(place.get('zone',''))[:64],
            'name':str(place.get('name',''))[:48],
            'type':int(place.get('type',2)),'biome':biome,
            'fly':bool(place.get('fly',False)),
            'worldX':round(world_x,3),'worldZ':round(world_z,3),
            'mapX':int(place.get('map',[0,0])[0]),
            'mapY':int(place.get('map',[0,0])[1]),
        })
    return result

# Absolute placements in the Black 2 Redux overworld frame. The first group is
# solved from reciprocal outdoor grid warps. The remaining town-map anchors
# are calibrated from the BW2 decomp's place markers and zone fly coordinates,
# then snapped to chunk boundaries. They fill standalone outdoor maps that do
# not have one unambiguous reciprocal grid-warp path.
_FLIGHT_WORLD_OFFSETS={
    0:(0,0),14:(12752,8864),16:(7968,8240),41:(8880,8128),107:(6832,7168),
    136:(3632,352),183:(3264,1856),190:(10032,4848),208:(2528,1440),
    224:(9440,8304),238:(7536,5824),255:(1536,9200),256:(3072,10816),
    337:(8640,176),414:(1632,9392),
    87:(8192,0),106:(4608,6144),117:(6656,4608),128:(-512,2048),
    132:(7168,10240),133:(8704,9216),135:(8192,6656),182:(8192,2560),
    273:(13312,3584),338:(12288,11776),357:(9216,6144),380:(2560,8192),
}
# Exact reciprocal-grid placements currently discovered from the Black 2
# overworld frame. Keeping them explicit lets flight start from these maps as
# well as from the overworld without needing to rediscover a possibly
# ambiguous path from that local takeoff point.
_FLIGHT_CONFIRMED_WARP_WORLD_OFFSETS={
    1:(6640,10544),3:(6656,9536),11:(5472,9488),210:(8208,-96),
    250:(11744,11456),251:(11744,11456),275:(432,11040),
    296:(4896,9520),297:(4480,9008),348:(12064,11776),356:(9168,6160),
    383:(8128,-688),384:(8176,-1088),390:(8176,-1088),
}
# Supported supplemental placements. These fill Black 2 Redux's exterior
# matrices that cannot be placed by the reciprocal warp graph. Parent Fly
# points anchor the named maps; small route/story scenes without a spatial
# warp are packed next to their matching outdoor area. The Redux-only 416 map
# is tied to Route 19 by its area id and its populated centre chunk.
_FLIGHT_SUPPLEMENTAL_WORLD_OFFSETS={
    # Castelia's rail-style city sections form one contiguous extension.
    2:(8192,10240),4:(8704,10240),5:(9216,10240),6:(9728,10240),
    7:(8192,11264),8:(8704,11264),9:(9216,11264),10:(9728,11264),
    # Decomp parent Fly points: Twist Mountain, Desert Resort, and Route 7.
    93:(2240,3296),103:(5856,7920),189:(1696,4192),
    # Entrée Forest base and eight separate story scenes, beside Entralink.
    119:(8192,4608),228:(7680,4096),229:(8192,4096),230:(8704,4096),
    231:(7680,4608),232:(8704,4608),233:(7680,5120),234:(8192,5120),
    235:(8704,5120),
    # Victory Road sections with rail/indoor-only transitions.
    162:(10176,176),387:(8640,1200),
    # League approach and Black/White version-specific gates.
    211:(8016,-544),225:(9920,6016),226:(9904,6016),
    # A shared Hidden Grotto beside Lostlorn; Nature Preserve beside Anville.
    314:(8048,5824),372:(512,2048),
    # Redux-only zone 615/616 has no decomp coordinates. Keep its populated
    # centre chunk beside Aspertia's Route 19 entrance without overlaying Gym.
    416:(944,10608),
}
_FLIGHT_WORLD_ANCHOR_TILES={
    14:(5,4),87:(19,49),106:(20,48),117:(16,16),128:(5,4),132:(3,1),
    133:(0,0),135:(5,4),136:(5,4),182:(5,4),183:(5,4),190:(5,4),
    238:(5,4),273:(0,0),337:(43,18),338:(5,4),357:(42,38),380:(31,50),
    93:(5,4),103:(5,4),119:(16,16),162:(16,16),189:(5,4),211:(30,83),
    225:(5,4),226:(5,4),228:(5,4),229:(5,4),230:(5,4),231:(5,4),
    232:(5,4),233:(5,4),234:(5,4),235:(5,4),314:(5,4),372:(16,16),
    387:(5,4),416:(32,32),
}


def flight_matrix_aliases(source):
    """Find matrices that reuse the exact same placed chunk grid.

    Black 2's OVERWORLD and OVERWORLD_2 have identical dimensions and chunk
    ids; the second matrix supplies alternate per-cell zone ids for gates.
    They are two zone tables over one world coordinate frame, not two places
    to draw on top of each other.
    """
    cached=getattr(source,'_flight_matrix_aliases',None)
    if cached is not None:return cached
    groups={}
    for matrix,data in enumerate(getattr(source,'matrices',())):
        try:width,depth,cell_ids,_zones=matrix_cells(data)
        except (ValueError,struct.error):continue
        groups.setdefault((width,depth,cell_ids),[]).append(matrix)
    aliases={}
    for members in groups.values():
        canonical=min(members)
        for matrix in members:aliases[matrix]=canonical
    source._flight_matrix_aliases=aliases
    return aliases


def flight_matrix_layout(source,matrix,aliases=None):
    """Return a canonical chunk grid with outdoor zone tables combined."""
    aliases=aliases if aliases is not None else flight_matrix_aliases(source)
    canonical=aliases.get(matrix,matrix)
    width,depth,cell_ids,zones=matrix_cells(source.matrices[canonical])
    if zones is None:return width,depth,cell_ids,zones
    combined=list(zones)
    members=sorted(candidate for candidate,base in aliases.items() if base==canonical)
    headers=getattr(source,'headers',b'');areas=getattr(source,'areas',b'')
    for alias in members:
        if alias==canonical:continue
        _w,_d,_ids,other_zones=matrix_cells(source.matrices[alias])
        if other_zones is None:continue
        for cell,candidate in enumerate(other_zones):
            if combined[cell]>=0 or candidate<0 or candidate>=len(headers)//48:continue
            area=struct.unpack_from('<H',headers,candidate*48+2)[0]
            if area*10+7<=len(areas) and areas[area*10+6]:combined[cell]=candidate
    return width,depth,cell_ids,tuple(combined)


def _flight_matrix_owner_score(matrix,offset,dimensions,world_cell_x,world_cell_z,
                               preferred_matrix=None):
    """Use the same anchor priority for atlas ownership and current-zone lookup."""
    if matrix==0:
        score=(1,0,matrix)
    else:
        width,depth=dimensions
        anchor=_FLIGHT_WORLD_ANCHOR_TILES.get(matrix)
        if anchor is None:anchor=((width-1)*16,(depth-1)*16)
        anchor_x=offset[0]+anchor[0]*16;anchor_z=offset[1]+anchor[1]*16
        centre_x=(world_cell_x+.5)*_MATRIX_SCALE
        centre_z=(world_cell_z+.5)*_MATRIX_SCALE
        score=(0,(anchor_x-centre_x)**2+(anchor_z-centre_z)**2,matrix)
    if preferred_matrix is not None:
        return (0 if matrix==preferred_matrix else 1,*score)
    return score


def flight_matrix_owner_at(source,offsets,x,z,layouts=None,preferred_matrix=None):
    """Return the matrix and local cell whose chunk owns this world cell."""
    layouts=layouts if layouts is not None else {
        matrix:flight_matrix_layout(source,matrix) for matrix in offsets
    }
    world_cell_x=math.floor(x/_MATRIX_SCALE);world_cell_z=math.floor(z/_MATRIX_SCALE)
    candidates=[]
    for matrix,(ox,oz) in offsets.items():
        width,depth,ids,zones=layouts[matrix]
        cx=math.floor((x-ox)/_MATRIX_SCALE);cz=math.floor((z-oz)/_MATRIX_SCALE)
        if not (0<=cx<width and 0<=cz<depth):continue
        local_cell=cz*width+cx
        if ids[local_cell]<0:continue
        score=_flight_matrix_owner_score(matrix,(ox,oz),(width,depth),world_cell_x,
                                         world_cell_z,preferred_matrix)
        candidates.append((score,matrix,local_cell))
    if not candidates:return None
    _score,matrix,local_cell=min(candidates)
    return matrix,local_cell


def active_flight_matrix_preference(matrix,x,z,layouts,masks):
    """Prefer the takeoff map only when its occupied launch cell is occluded."""
    if matrix==0 or matrix not in layouts:return None
    width,depth,ids,_zones=layouts[matrix]
    cx,cz=math.floor(x/_MATRIX_SCALE),math.floor(z/_MATRIX_SCALE)
    if not (0<=cx<width and 0<=cz<depth):return None
    cell=cz*width+cx
    if ids[cell]<0 or masks[matrix][cell]:return None
    return matrix


def flight_matrix_offsets(source, root_matrix):
    """Place outdoor matrices from reciprocal grid warps in the ROM.

    BW2 stores warp positions in 1/16-tile world units. A reciprocal pair
    gives an exact translation between map matrices. Outdoor placements are
    established first; indoor-only matrices may relay a placement only when
    every discovered path agrees. The native ``fly_from`` zone flag only
    controls the game's Fly move; it does not mark whether a destination is
    outdoor or safe to render during custom Soaring.
    """
    if not all(hasattr(source,key) for key in ('headers','events','areas','matrices')):
        return {root_matrix:(0,0)}
    aliases=flight_matrix_aliases(source)
    root_matrix=aliases.get(root_matrix,root_matrix)
    cached=getattr(source,'_flight_matrix_offsets',None)
    if cached is not None and root_matrix in cached:return cached[root_matrix]
    count=len(source.headers)//48
    eligible=[];matrix_zones={}
    for zone in range(count):
        offset=zone*48
        area,matrix=struct.unpack_from('<HH',source.headers,offset+2)
        if (matrix>=len(source.matrices) or
                area*10+7>len(source.areas) or not source.areas[area*10+6]):continue
        matrix=aliases.get(matrix,matrix)
        eligible.append(zone);matrix_zones.setdefault(matrix,[]).append(zone)
    # Read warp coordinates for every zone, including gate/alternate-area
    # headers whose own area is not marked exterior. A destination warp still
    # supplies the exact local coordinate frame for its matrix. Several
    # Redux outdoor matrices enter through a non-exterior gate zone that
    # shares the anchored overworld matrix; filtering those records out loses
    # an otherwise exact placement (for example, the Black/White Forest
    # gate transition).
    zone_warps={}
    for zone in range(count):
        header=zone*48
        event_id=struct.unpack_from('<H',source.headers,header+22)[0]
        if event_id==0xffff or event_id>=len(source.events):continue
        data=source.events[event_id]
        if len(data)<8:continue
        bg_count,npc_count,warp_count,_trigger_count=data[4:8]
        pos=8+bg_count*20+npc_count*36
        if warp_count>255 or pos+warp_count*20>len(data):continue
        records=[]
        for index in range(warp_count):
            item=pos+index*20
            dest,dest_warp=struct.unpack_from('<HH',data,item)
            is_rail=struct.unpack_from('<H',data,item+6)[0]
            if is_rail:
                records.append(None);continue
            x,_y,z,_width,_height,_unknown=struct.unpack_from('<6H',data,item+8)
            records.append((dest,dest_warp,x,z))
        zone_warps[zone]=records
    outdoor_matrices=set(matrix_zones)
    edge_offsets={}
    all_edge_offsets={}
    for zone,records in zone_warps.items():
        raw_matrix=struct.unpack_from('<H',source.headers,zone*48+4)[0]
        matrix=aliases.get(raw_matrix,raw_matrix)
        for index,warp in enumerate(records):
            if warp is None:continue
            dest,dest_warp,x,z=warp
            reverse=zone_warps.get(dest,())
            if dest not in zone_warps or dest_warp>=len(reverse):continue
            back=reverse[dest_warp]
            if back is None or back[0]!=zone or back[1]!=index:continue
            raw_dest_matrix=struct.unpack_from('<H',source.headers,dest*48+4)[0]
            dest_matrix=aliases.get(raw_dest_matrix,raw_dest_matrix)
            if dest_matrix==matrix:continue
            dx=x-back[2];dz=z-back[3]
            if dx%16 or dz%16:continue
            edge=(min(matrix,dest_matrix),max(matrix,dest_matrix))
            signed=(dx,dz) if matrix<dest_matrix else (-dx,-dz)
            all_edge_offsets.setdefault(edge,set()).add(signed)
            # Preserve the original outdoor-only graph for root placements:
            # some indoor warps are portals between distant areas and must not
            # move already established scenery.
            if matrix in outdoor_matrices and dest_matrix in outdoor_matrices:
                edge_offsets.setdefault(edge,set()).add(signed)
    graph={}
    for (a,b),values in sorted(edge_offsets.items()):
        if len(values)!=1:continue
        dx,dz=next(iter(values))
        graph.setdefault(a,[]).append((b,(dx,dz)))
        graph.setdefault(b,[]).append((a,(-dx,-dz)))
    offsets={root_matrix:(0,0)};pending=[root_matrix]
    while pending:
        matrix=pending.pop(0)
        for other,delta in sorted(graph.get(matrix,())):
            proposed=(offsets[matrix][0]+delta[0],offsets[matrix][1]+delta[1])
            if other not in offsets:
                offsets[other]=proposed;pending.append(other)
            # Conflicting loops are intentionally ignored; the first exact
            # reciprocal path remains deterministic and prevents map jumps.

    # The decomp supplies Town Map anchors for outdoor places on matrices that
    # are not reachable through a unique reciprocal grid warp. Use these only
    # for the matching Black 2 ROM and only when the matrix is actually used by
    # an outdoor zone. Existing warp-derived placements always take precedence.
    rom=getattr(source,'rom',None)
    world_offsets=_FLIGHT_WORLD_OFFSETS
    # Supplemental story/transition placements describe the full local Redux
    # ROM, not small synthetic sources used by the warp-graph tests. Requiring
    # the real BW2 zone and matrix counts prevents those fixtures from being
    # silently forced onto unrelated hand-authored positions.
    is_full_redux=(getattr(rom,'idCode',None)==b'IREO' and
                   len(source.headers)//48>600 and len(source.matrices)>416)
    if is_full_redux:
        world_offsets={**_FLIGHT_WORLD_OFFSETS,
                       **_FLIGHT_CONFIRMED_WARP_WORLD_OFFSETS,
                       **_FLIGHT_SUPPLEMENTAL_WORLD_OFFSETS}
    if getattr(rom,'idCode',None)==b'IREO' and root_matrix in world_offsets:
        root_world=world_offsets[root_matrix]
        for matrix,world in world_offsets.items():
            if matrix in matrix_zones and matrix<len(source.matrices):
                offsets.setdefault(matrix,(world[0]-root_world[0],world[1]-root_world[1]))

        # Grow from every confirmed placement over unique reciprocal links.
        # If two placed neighbours disagree about an unknown matrix, leave it
        # unresolved rather than choosing an arbitrary story instance.
        while True:
            proposals={}
            for matrix,position in offsets.items():
                for other,delta in graph.get(matrix,()):
                    if other in offsets:continue
                    candidate=(position[0]+delta[0],position[1]+delta[1])
                    proposals.setdefault(other,set()).add(candidate)
            additions={matrix:next(iter(values)) for matrix,values in proposals.items()
                       if len(values)==1 and matrix in matrix_zones}
            if not additions:break
            offsets.update(additions)

        # Indoor-only matrices can still carry exact, reciprocal grid warp
        # coordinates between outdoor parts of one continuous field (notably
        # the Castelia Sewers and Victory Road). Use them as transit nodes
        # after the established outdoor placements are fixed. A candidate is
        # accepted only when all currently anchored paths agree; if a later
        # path exposes a conflicting placement, keep that matrix unresolved.
        bridge_graph={}
        for (a,b),values in sorted(all_edge_offsets.items()):
            if len(values)!=1:continue
            dx,dz=next(iter(values))
            bridge_graph.setdefault(a,[]).append((b,(dx,dz)))
            bridge_graph.setdefault(b,[]).append((a,(-dx,-dz)))
        bridge_positions=dict(offsets)
        bridge_seeds=set(offsets)
        bridge_blocked=set()
        while True:
            proposals={}
            for matrix,position in bridge_positions.items():
                for other,delta in bridge_graph.get(matrix,()):
                    if other in bridge_positions or other in bridge_blocked:continue
                    candidate=(position[0]+delta[0],position[1]+delta[1])
                    proposals.setdefault(other,set()).add(candidate)
            additions={matrix:next(iter(values)) for matrix,values in proposals.items()
                       if len(values)==1}
            if not additions:break
            bridge_positions.update(additions)
            conflicts=set()
            for matrix,position in additions.items():
                for other,delta in bridge_graph.get(matrix,()):
                    if other not in bridge_positions:continue
                    expected=(position[0]+delta[0],position[1]+delta[1])
                    if bridge_positions[other]!=expected:
                        conflicts.add(matrix)
                        if other not in bridge_seeds:conflicts.add(other)
            for matrix in conflicts:
                if matrix in bridge_seeds:continue
                bridge_positions.pop(matrix,None)
                bridge_blocked.add(matrix)
        for matrix,position in bridge_positions.items():
            if matrix in matrix_zones and matrix not in offsets:
                offsets[matrix]=position

        # Some outdoor transition maps encode an arrival warp but omit a
        # reciprocal exit back to the source zone. The source warp's
        # destination-warp index still identifies a real coordinate in the
        # destination matrix, so it can provide an exact placement from
        # either side when every proposal agrees. Ambiguous story instances
        # (for example, Black City Gate) remain unplaced rather than guessed.
        while True:
            proposals={}
            for matrix,position in offsets.items():
                for zone in matrix_zones.get(matrix,()):
                    for warp in zone_warps.get(zone,()):
                        if warp is None:continue
                        dest,dest_warp,x,z=warp
                        if dest not in zone_warps or dest_warp>=len(zone_warps[dest]):continue
                        landing=zone_warps[dest][dest_warp]
                        if landing is None:continue
                        raw_dest_matrix=struct.unpack_from('<H',source.headers,dest*48+4)[0]
                        dest_matrix=aliases.get(raw_dest_matrix,raw_dest_matrix)
                        if dest_matrix==matrix or dest_matrix not in matrix_zones or dest_matrix in offsets:continue
                        dx,dz=x-landing[2],z-landing[3]
                        if dx%16 or dz%16:continue
                        proposals.setdefault(dest_matrix,set()).add((position[0]+dx,position[1]+dz))
            for matrix in matrix_zones.keys()-offsets.keys():
                for zone in matrix_zones.get(matrix,()):
                    for warp in zone_warps.get(zone,()):
                        if warp is None:continue
                        dest,dest_warp,x,z=warp
                        if dest not in zone_warps or dest_warp>=len(zone_warps[dest]):continue
                        landing=zone_warps[dest][dest_warp]
                        if landing is None:continue
                        raw_dest_matrix=struct.unpack_from('<H',source.headers,dest*48+4)[0]
                        dest_matrix=aliases.get(raw_dest_matrix,raw_dest_matrix)
                        if dest_matrix==matrix or dest_matrix not in offsets:continue
                        dx,dz=landing[2]-x,landing[3]-z
                        if dx%16 or dz%16:continue
                        proposals.setdefault(matrix,set()).add((offsets[dest_matrix][0]+dx,
                                                                 offsets[dest_matrix][1]+dz))
            additions={matrix:next(iter(values)) for matrix,values in proposals.items()
                       if len(values)==1 and matrix in matrix_zones}
            if not additions:break
            offsets.update(additions)
    caches=cached if cached is not None else {}
    caches[root_matrix]=offsets
    source._flight_matrix_offsets=caches
    return offsets


def merged_flight_grid(source, offsets, with_masks=False, preferred_matrix=None):
    """Merge linked matrices into a bounded, coarse atlas for flight visuals."""
    layouts={}
    aliases=flight_matrix_aliases(source)
    min_x=min_z=10**9;max_x=max_z=-10**9
    for matrix,(ox,oz) in offsets.items():
        width,depth,ids,zones=flight_matrix_layout(source,matrix,aliases)
        layouts[matrix]=(width,depth,ids,zones)
        min_x=min(min_x,math.floor(ox/_MATRIX_SCALE));min_z=min(min_z,math.floor(oz/_MATRIX_SCALE))
        max_x=max(max_x,math.ceil((ox+width*_MATRIX_SCALE)/_MATRIX_SCALE))
        max_z=max(max_z,math.ceil((oz+depth*_MATRIX_SCALE)/_MATRIX_SCALE))
    width,height=max_x-min_x,max_z-min_z
    if width<1 or height<1 or width*height>4096:
        raise ValueError('Connected flight region exceeds atlas bounds')
    cells=[-1]*(width*height)
    masks={matrix:[False]*(mw*mh) for matrix,(mw,mh,_ids,_zones) in layouts.items()}
    owners={}
    for matrix,(ox,oz) in offsets.items():
        matrix_width,matrix_depth,ids,_zones=layouts[matrix]
        for mz in range(matrix_depth):
            for mx in range(matrix_width):
                if ids[mz*matrix_width+mx]<0:continue
                left=math.floor((ox+mx*_MATRIX_SCALE)/_MATRIX_SCALE)-min_x
                right=math.floor((ox+(mx+1)*_MATRIX_SCALE-1e-6)/_MATRIX_SCALE)-min_x
                top=math.floor((oz+mz*_MATRIX_SCALE)/_MATRIX_SCALE)-min_z
                bottom=math.floor((oz+(mz+1)*_MATRIX_SCALE-1e-6)/_MATRIX_SCALE)-min_z
                for gz in range(max(0,top),min(height-1,bottom)+1):
                    for gx in range(max(0,left),min(width-1,right)+1):
                        key=gz*width+gx;cells[key]=1
                        score=_flight_matrix_owner_score(matrix,(ox,oz),
                            (matrix_width,matrix_depth),gx+min_x,gz+min_z,
                            preferred_matrix)
                        previous=owners.get(key)
                        if previous is None or score<previous[0]:
                            owners[key]=(score,matrix,mz*matrix_width+mx)
    for _key,matrix,local_cell in owners.values():masks[matrix][local_cell]=True
    result=(min_x,min_z,width,height,tuple(cells),layouts)
    if with_masks:return (*result,{matrix:tuple(mask) for matrix,mask in masks.items()})
    return result


def _cross2(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def _convex_hull(points):
    """Return the deterministic convex hull of map-cell corner points."""
    points=sorted(set(points))
    if len(points)<3:return points
    lower=[]
    for point in points:
        while len(lower)>=2 and _cross2(lower[-2],lower[-1],point)<=0:lower.pop()
        lower.append(point)
    upper=[]
    for point in reversed(points):
        while len(upper)>=2 and _cross2(upper[-2],upper[-1],point)<=0:upper.pop()
        upper.append(point)
    return lower[:-1]+upper[:-1]


def interior_water_cells(width,depth,cell_ids,edge_margin=.75):
    """Fill atlas gaps inside the outer map footprint with native sea tiles.

    The hull uses the corners of real matrix cells, so disconnected authored
    regions share a continuous water backdrop while space beyond their outer
    footprint remains the distant boundary. The small margin closes diagonal
    edge cracks without extending the water more than one atlas cell.
    """
    occupied=[i for i,value in enumerate(cell_ids) if value>=0]
    if not occupied:return ()
    corners=[]
    for cell in occupied:
        gx,gz=cell%width,cell//width
        corners.extend(((gx,gz),(gx+1,gz),(gx+1,gz+1),(gx,gz+1)))
    hull=_convex_hull(corners)
    if len(hull)<3:return ()
    result=[]
    for cell,value in enumerate(cell_ids):
        if value>=0:continue
        gx,gz=cell%width,cell//width;point=(gx+.5,gz+.5)
        inside=True
        for index,a in enumerate(hull):
            b=hull[(index+1)%len(hull)]
            # Hull points are counter-clockwise; a negative cross-product is
            # distance outside an edge, normalized by that edge's length.
            cross=_cross2(a,b,point)
            if cross < -edge_margin*math.hypot(b[0]-a[0],b[1]-a[1]):
                inside=False;break
        if inside:result.append(cell)
    return tuple(result)


def atlas_water_cells(width,depth,cell_ids):
    """Return every empty cell inside the rectangular flight-map bounds.

    The convex hull is useful for shaping decorative land between real field
    maps, but it is too small to serve as the rendered background: its corners
    leave visible holes inside the map's rectangular atlas. Back every unused
    atlas cell with the game's tiled sea so all in-map gaps have scenery.
    """
    if width<1 or depth<1 or len(cell_ids)!=width*depth:
        raise ValueError('Invalid flight atlas dimensions')
    return tuple(index for index,value in enumerate(cell_ids) if value<0)


def flight_atlas_coverage(width,depth,cell_ids,edge_margin=.75):
    """Summarize whether real maps and the sea backdrop cover the full atlas."""
    if width<1 or depth<1 or len(cell_ids)!=width*depth:
        raise ValueError('Invalid flight atlas dimensions')
    land={index for index,value in enumerate(cell_ids) if value>=0}
    water=set(atlas_water_cells(width,depth,cell_ids))
    covered=land|water
    empty=set(range(width*depth))-covered

    edge=[index for index in empty
          if index%width in (0,width-1) or index//width in (0,depth-1)]
    outside=set(edge);pending=list(edge)
    while pending:
        index=pending.pop();x=index%width;z=index//width
        neighbours=(index-1 if x else -1,index+1 if x+1<width else -1,
                    index-width if z else -1,index+width if z+1<depth else -1)
        for neighbour in neighbours:
            if neighbour in empty and neighbour not in outside:
                outside.add(neighbour);pending.append(neighbour)
    enclosed=empty-outside

    edge_gaps=set()
    for index in empty:
        x=index%width;z=index//width
        for nx,nz in ((x-1,z),(x+1,z),(x,z-1),(x,z+1),
                      (x-1,z-1),(x+1,z-1),(x-1,z+1),(x+1,z+1)):
            if 0<=nx<width and 0<=nz<depth and nz*width+nx in land:
                edge_gaps.add(index);break

    remaining=set(covered);components=0
    while remaining:
        components+=1
        pending=[remaining.pop()]
        while pending:
            index=pending.pop();x=index%width;z=index//width
            neighbours=(index-1 if x else -1,index+1 if x+1<width else -1,
                        index-width if z else -1,index+width if z+1<depth else -1)
            for neighbour in neighbours:
                if neighbour in remaining:
                    remaining.remove(neighbour);pending.append(neighbour)
    return {
        'width':width,'depth':depth,'mappedCells':len(land),
        'seaFillCells':len(water),'coveredCells':len(covered),
        'outerBoundaryCells':len(outside),'enclosedVoidCells':len(enclosed),
        'unfilledCellsTouchingMap':len(edge_gaps),
        'coveredComponents':components,
    }


def make_water_faces(cells,width,origin_x,origin_z,atlas_x,atlas_z,radius,texture_index):
    """Build textured, renderer-only sea quads for the empty atlas footprint."""
    faces=[]
    for cell in cells:
        gx,gz=cell%width,cell//width
        left=(gx*512-atlas_x);right=((gx+1)*512-atlas_x)
        front=(gz*512-atlas_z);back=((gz+1)*512-atlas_z)
        if math.hypot((left+right)*.5,(front+back)*.5)>radius+363:continue
        # sea_mizu1 is a 32x32 native BW2 water tile. One texture repeat spans
        # 16 world units, yielding 32 seamless repeats per 512-unit atlas cell.
        u0=((origin_x+gx)*32)%32;u1=u0+32
        v0=((origin_z+gz)*32)%32;v1=v0+32
        y=-34.
        vertices=[[left,y,front,u0,v0],[right,y,front,u1,v0],
                  [right,y,back,u1,v1],[left,y,back,u0,v1]]
        faces.append([texture_index,vertices])
    return faces


def flight_water_material(source):
    """Get a native tiled sea texture and palette from the user's ROM.

    Prefer Undella Bay's map pack (named as zone 240 in the Black 2 decomp),
    then search other ROM packs for the same native material if that map has
    been changed by a ROM revision.
    """
    cached=getattr(source,'_flight_water_material',None)
    if cached is not None:return cached
    packs=getattr(source,'packs',())
    preferred=[]
    headers=getattr(source,'headers',b'');areas=getattr(source,'areas',b'')
    if len(headers)>(_WATER_ZONE*48+4) and len(areas)>=2:
        area=struct.unpack_from('<H',headers,_WATER_ZONE*48+2)[0]
        if area*10+4<=len(areas):
            pack_id=struct.unpack_from('<H',areas,area*10+2)[0]
            if pack_id<len(packs):preferred.append(pack_id)
    order=preferred+[index for index in range(len(packs)) if index not in preferred]
    for index in order:
        try:pack=texture_pack(packs[index])
        except (ValueError,IndexError,struct.error):continue
        textures=dict(pack.textures);palettes=dict(pack.palettes)
        texture_name='sea_mizu1';palette_name='sea_mizu1_pl'
        texture=textures.get(texture_name);palette=palettes.get(palette_name)
        if texture is None or palette is None or (texture.width,texture.height)!=(32,32) or not palette.colors:continue
        cached=(texture,palette);source._flight_water_material=cached
        return cached
    return None


@lru_cache(maxsize=8)
def build_flyway_routes(width,depth,cell_ids):
    """Join disconnected real map islands with decorative, non-collision flyways."""
    count=width*depth
    occupied={i for i,value in enumerate(cell_ids) if value>=0}
    owner=[-1]*count;components=[]
    for seed in sorted(occupied):
        if owner[seed]>=0:continue
        index=len(components);component=[];stack=[seed];owner[seed]=index
        while stack:
            cell=stack.pop();component.append(cell);cx=cell%width;cz=cell//width
            for nxt in (cell-1 if cx else -1,cell+1 if cx+1<width else -1,
                        cell-width if cz else -1,cell+width if cz+1<depth else -1):
                if nxt>=0 and cell_ids[nxt]>=0 and owner[nxt]<0:owner[nxt]=index;stack.append(nxt)
        components.append(component)
    if len(components)<2:return []
    edges=[]
    for source,component in enumerate(components):
        distance={cell:0. for cell in component};root={cell:cell for cell in component};parent={}
        queue=[(0.,cell) for cell in component];heapq.heapify(queue);best={}
        while queue:
            cost,cell=heapq.heappop(queue)
            if cost!=distance.get(cell):continue
            cx=cell%width;cz=cell//width
            for nxt in (cell-1 if cx else -1,cell+1 if cx+1<width else -1,
                        cell-width if cz else -1,cell+width if cz+1<depth else -1):
                if nxt<0:continue
                target=owner[nxt]
                if target==source:continue
                if target>=0:
                    candidate=cost+.5
                    if target not in best or candidate<best[target][0]:best[target]=(candidate,nxt,cell)
                    continue
                candidate=cost+1
                if candidate<distance.get(nxt,float('inf')):
                    distance[nxt]=candidate;root[nxt]=root[cell];parent[nxt]=cell
                    heapq.heappush(queue,(candidate,nxt))
        for target,(cost,end,last_gap) in best.items():
            if target<=source:continue
            reverse=[last_gap]
            while reverse[-1] in parent:reverse.append(parent[reverse[-1]])
            reverse.reverse();cells=[root[last_gap],*reverse[1:],end]
            points=[(cell%width+.5,cell//width+.5) for cell in cells]
            if len(points)>2:
                points[0]=((points[0][0]+points[1][0])*.5,(points[0][1]+points[1][1])*.5)
                points[-1]=((points[-1][0]+points[-2][0])*.5,(points[-1][1]+points[-2][1])*.5)
            edges.append((cost,source,target,points))
    parent_component=list(range(len(components)))
    def root_component(i):
        while parent_component[i]!=i:
            parent_component[i]=parent_component[parent_component[i]];i=parent_component[i]
        return i
    routes=[]
    for cost,a,b,points in sorted(edges,key=lambda edge:(edge[0],edge[1],edge[2])):
        ra,rb=root_component(a),root_component(b)
        if ra==rb:continue
        parent_component[rb]=ra
        routes.append(points)
        if len(routes)==len(components)-1:break
    return routes


def make_flyway_faces(routes,x,z,radius):
    """Create lightweight ribbons above the void; these never enter collision data."""
    faces=[]
    def quad(category,a,b,c,d):
        faces.append([category,[list(a),list(b),list(c)]])
        faces.append([category,[list(a),list(c),list(d)]])
    for route in routes:
        lengths=[math.hypot((b[0]-a[0])*512,(b[1]-a[1])*512) for a,b in zip(route,route[1:])]
        total=sum(lengths);travelled=0.
        for a,b,length in zip(route,route[1:],lengths):
            mx=((a[0]+b[0])*.5)*512-x;mz=((a[1]+b[1])*.5)*512-z
            if math.hypot(mx,mz)>radius+300:travelled+=length;continue
            dx,dz=b[0]-a[0],b[1]-a[1];size=math.hypot(dx,dz)
            if not size:travelled+=length;continue
            nx,nz=-dz/size,dx/size
            progress0=travelled/max(1,total);progress1=(travelled+length)/max(1,total)
            def point(p,offset,extra=0):
                progress=progress1 if p is b else progress0
                y=-26+9*math.sin(math.pi*progress)+extra
                return ((p[0]*512-x)+nx*offset,y,(p[1]*512-z)+nz*offset)
            for left,right,category,height in ((-38,38,0,0),(-45,-38,1,5),(38,45,1,5),(-3,3,2,1)):
                quad(category,point(a,left,height),point(a,right,height),point(b,right,height),point(b,left,height))
            travelled+=length
    return faces


def _connector_cells(width,depth,routes):
    """Rasterize separated field-scene links into empty atlas cells."""
    cells=set()
    for route in routes:
        if isinstance(route,dict):route=route.get('points',())
        for a,b in zip(route,route[1:]):
            steps=max(1,int(math.ceil(max(abs(b[0]-a[0]),abs(b[1]-a[1]))*3)))
            for index in range(steps+1):
                fraction=index/steps
                cx=math.floor(a[0]+(b[0]-a[0])*fraction)
                cz=math.floor(a[1]+(b[1]-a[1])*fraction)
                for ox,oz in ((0,0),(-1,0),(1,0),(0,-1),(0,1)):
                    nx,nz=cx+ox,cz+oz
                    if 0<=nx<width and 0<=nz<depth:
                        cells.add(nz*width+nx)
    return cells


def _nearest_region_biome(world_x,world_z,places,max_distance=10):
    nearest=None;best=max_distance*max_distance
    for place in places:
        dx=place['worldX']/_MATRIX_SCALE-world_x
        dz=place['worldZ']/_MATRIX_SCALE-world_z
        distance=dx*dx+dz*dz
        if distance<best:
            best=distance;nearest=place
    return nearest.get('biome',2) if nearest is not None else None


def decomp_region_routes(width,depth,origin_x,origin_z,landmarks,catalog=None,
                         max_length=8.):
    """Project the decomp's named Unova route links into the Soaring atlas.

    These paths only guide generated scenery and map markers. They do not
    create field collision or landing targets.
    """
    catalog=catalog if catalog is not None else soaring_region_catalog()
    by_key={place.get('zoneKey'):place for place in landmarks
            if place.get('zoneKey')}
    routes=[]
    for link in catalog.get('connections',()):
        if not isinstance(link,(list,tuple)) or len(link)!=2:continue
        start,end=(by_key.get(key) for key in link)
        if start is None or end is None:continue
        a=(start['worldX']/_MATRIX_SCALE-origin_x,
           start['worldZ']/_MATRIX_SCALE-origin_z)
        b=(end['worldX']/_MATRIX_SCALE-origin_x,
           end['worldZ']/_MATRIX_SCALE-origin_z)
        if not all(math.isfinite(value) for value in (*a,*b)):continue
        if not (0<=a[0]<=width and 0<=a[1]<=depth and
                0<=b[0]<=width and 0<=b[1]<=depth):continue
        if math.hypot(b[0]-a[0],b[1]-a[1])>max_length:continue
        routes.append({'from':link[0],'to':link[1],'points':(a,b)})
    return routes


def make_region_fill_faces(width,depth,cell_ids,x,z,radius,origin=(0,0),
                           link_routes=(),region_places=()):
    """Build decomp-anchored, non-collision terrain between regional scenes.

    Missing-cell corridors connect separated outdoor matrices. Their nearby
    Black 2 Town Map anchors choose forest, grassland, mountain, coast and
    desert details. Landings remain restricted to decoded ROM collision.
    """
    faces=[]
    extent=max(3600.,min(7600.,radius+1200.))
    y=-72.
    corners=[(-extent,y,-extent),(extent,y,-extent),(extent,y,extent),(-extent,y,extent)]
    faces.extend([[0,[list(corners[0]),list(corners[1]),list(corners[2])]],
                  [0,[list(corners[0]),list(corners[2]),list(corners[3])]]])
    biome=[2 if value>=0 else 0 for value in cell_ids]
    links=_connector_cells(width,depth,link_routes)
    water=set(interior_water_cells(width,depth,cell_ids))
    eligible=[]
    for cell,value in enumerate(cell_ids):
        if value>=0 or cell not in water:continue
        gx,gz=cell%width,cell//width
        center_x=(gx+.5)*512-x;center_z=(gz+.5)*512-z
        if math.hypot(center_x,center_z)>min(2500.,radius+350.):continue
        neighbours=0
        for dz in range(-2,3):
            for dx in range(-2,3):
                nx,nz=gx+dx,gz+dz
                if 0<=nx<width and 0<=nz<depth and cell_ids[nz*width+nx]>=0:
                    neighbours+=1
        if neighbours<8 and cell not in links:continue
        world_cell_x=origin[0]+gx+.5;world_cell_z=origin[1]+gz+.5
        local_biome=_nearest_region_biome(world_cell_x,world_cell_z,region_places)
        if local_biome is None:local_biome=1 if neighbours>=8 else 2
        if local_biome==0 and cell not in links:continue
        if local_biome==0:local_biome=2
        eligible.append((math.hypot(center_x,center_z),cell,gx,gz,local_biome))
    eligible.sort()
    land_cells={entry[1] for entry in eligible}
    for _,cell,gx,gz,land_biome in eligible:
        if len(faces)>5600:break
        biome[cell]=land_biome
        left=gx*512-x+24;right=(gx+1)*512-x-24
        front=gz*512-z+24;back=(gz+1)*512-z-24
        floor_y=-19. if land_biome==3 else -20.
        a=(left,floor_y,front);b=(right,floor_y,front)
        c=(right,floor_y,back);d=(left,floor_y,back)
        material={1:1,2:2,3:3,4:4}.get(land_biome,2)
        faces.extend([[material,[list(a),list(b),list(c)]],
                      [material,[list(a),list(c),list(d)]]])
        # A shallow shore bank visually joins new terrain to the sea plane.
        for gx2,gz2,p,q in ((gx,gz-1,a,b),(gx+1,gz,b,c),
                            (gx,gz+1,c,d),(gx-1,gz,d,a)):
            if not (0<=gx2<width and 0<=gz2<depth):continue
            neighbour=gz2*width+gx2
            if cell_ids[neighbour]>=0 or neighbour in land_cells:continue
            low_p=(p[0],-34.,p[2]);low_q=(q[0],-34.,q[2])
            faces.extend([[4,[list(p),list(q),list(low_q)]],
                          [4,[list(p),list(low_q),list(low_p)]]])
        # Stable per-cell pseudo-random details keep a rebuilt map identical.
        state=(cell*1103515245+12345)&0x7fffffff
        def rand(limit):
            nonlocal state
            state=(state*1103515245+12345)&0x7fffffff
            return (state%1000000)/1000000*limit
        if land_biome==1:
            for _tree in range(3):
                if len(faces)>6000:break
                tx=gx*512-x+75+rand(362);tz=gz*512-z+75+rand(362)
                tree_radius=18+rand(13);height=34+rand(19);base=floor_y
                trunk=5+rand(3);ring=[]
                for side in range(5):
                    angle=side*math.tau/5+rand(.2)
                    ring.append((tx+math.cos(angle)*tree_radius,
                                 base+height*.45,tz+math.sin(angle)*tree_radius))
                top=(tx,base+height,tz);lower=(tx,base+height*.16,tz)
                for side in range(5):
                    faces.append([[1,2][side%2],
                                  [list(ring[side]),list(ring[(side+1)%5]),list(top)]])
                    faces.append([2,[list(ring[side]),list(lower),list(ring[(side+1)%5])]])
                t0=(tx-trunk,base,tz-trunk);t1=(tx+trunk,base,tz-trunk)
                t2=(tx+trunk,base,tz+trunk);t3=(tx-trunk,base,tz+trunk)
                u0=(tx-trunk,base+height*.2,tz-trunk);u1=(tx+trunk,base+height*.2,tz-trunk)
                u2=(tx+trunk,base+height*.2,tz+trunk);u3=(tx-trunk,base+height*.2,tz+trunk)
                for quad in ((t0,t1,u1,u0),(t1,t2,u2,u1),(t2,t3,u3,u2),(t3,t0,u0,u3)):
                    p,q,r,s=quad
                    faces.extend([[4,[list(p),list(q),list(r)]],
                                  [4,[list(p),list(r),list(s)]]])
        elif land_biome==3:
            for peak in range(2 if cell in links else 3):
                if len(faces)>6000:break
                tx=gx*512-x+95+rand(322);tz=gz*512-z+95+rand(322)
                peak_radius=36+rand(28);peak_height=54+rand(88);ring=[]
                for side in range(5):
                    angle=side*math.tau/5+rand(.15)
                    ring.append((tx+math.cos(angle)*peak_radius,
                                 floor_y+peak_height*.42,tz+math.sin(angle)*peak_radius))
                top=(tx,floor_y+peak_height,tz);base=(tx,floor_y,tz)
                for side in range(5):
                    faces.append([[3,4][side%2],
                                  [list(ring[side]),list(ring[(side+1)%5]),list(top)]])
                    faces.append([4,[list(ring[side]),list(base),list(ring[(side+1)%5])]])
        elif land_biome==4:
            for _ridge in range(2):
                if len(faces)>6000:break
                cx=gx*512-x+70+rand(370);cz=gz*512-z+70+rand(370)
                half=70+rand(65);height=7+rand(14)
                p=(cx-half,floor_y+1,cz);q=(cx,floor_y+height,cz+rand(35)-17)
                r=(cx+half,floor_y+1,cz);s=(cx,floor_y+1,cz+72)
                faces.extend([[4,[list(p),list(q),list(s)]],
                              [4,[list(s),list(q),list(r)]]])
    # Keep the native parser's bounded scenery limit strict even when the
    # final tree or mountain cell reaches the cap.
    return faces[:6000],biome


def export_scene(source, zone, x, z, y, directory, radius=4096):
    ndspy.color.prepareLUTs()
    if not all(math.isfinite(v) for v in (x,z,y)):raise ValueError('Invalid flight position')
    source_zone=zone
    source_area,raw_matrix=struct.unpack_from('<HH',source.headers,zone*48+2)
    aliases=flight_matrix_aliases(source)
    matrix=aliases.get(raw_matrix,raw_matrix)
    if not source.areas[source_area*10+6]:raise ValueError('Take flight outdoors')
    offsets=flight_matrix_offsets(source,matrix)
    origin_x,origin_z,width,depth,ids,layouts,layout_masks=merged_flight_grid(source,offsets,with_masks=True)
    preferred_matrix=None
    # A few story/rail maps share their coordinate frame with a larger field
    # and can lose the launch cell to that field's chunks. Let the active map
    # own overlaps only when its actual takeoff cell would otherwise vanish.
    preferred_matrix=active_flight_matrix_preference(
        matrix,x,z,layouts,layout_masks)
    if preferred_matrix is not None:
        origin_x,origin_z,width,depth,ids,layouts,layout_masks=merged_flight_grid(
            source,offsets,with_masks=True,preferred_matrix=preferred_matrix)
    matrix_zones={}
    for candidate in range(len(source.headers)//48):
        area_id,raw_matrix_id=struct.unpack_from('<HH',source.headers,candidate*48+2)
        matrix_id=aliases.get(raw_matrix_id,raw_matrix_id)
        if matrix_id in offsets and source.areas[area_id*10+6]:
            matrix_zones.setdefault(matrix_id,candidate)
    if matrix not in matrix_zones:matrix_zones[matrix]=source_zone
    # Keep the visible zone aligned with the matrix whose chunk wins atlas
    # ownership at this position. The sourceZone remains the take-off map so
    # the native flight session stays valid.
    zone=source_zone
    owner=flight_matrix_owner_at(source,offsets,x,z,layouts,preferred_matrix)
    if owner is not None:
        matrix_id,local_cell=owner
        matrix_map_zones=layouts[matrix_id][3]
        candidate=(matrix_map_zones[local_cell] if matrix_map_zones is not None
                   else matrix_zones.get(matrix_id,-1))
        if not 0<=candidate<len(source.headers)//48:
            candidate=matrix_zones.get(matrix_id,source_zone)
        if 0<=candidate<len(source.headers)//48:
            candidate_area=struct.unpack_from('<H',source.headers,candidate*48+2)[0]
            if source.areas[candidate_area*10+6]:zone=candidate
    collision_debug=bool(getattr(source,'collision_debug',False))
    faces=[];packs={};landings=[];collision_tiles=[];omitted_props=[];chunks=[];closed_backs=0
    for matrix_id,(offset_x,offset_z) in sorted(offsets.items()):
        mw,mh,chunk_ids,matrix_map_zones=layouts[matrix_id]
        left,top=offset_x,offset_z;right=offset_x+mw*_MATRIX_SCALE;bottom=offset_z+mh*_MATRIX_SCALE
        dx=max(left-x,0,x-right);dz=max(top-z,0,z-bottom)
        if math.hypot(dx,dz)>radius+_MATRIX_SCALE:continue
        local_x,local_z=x-offset_x,z-offset_z
        cx,cz=int(local_x//_MATRIX_SCALE),int(local_z//_MATRIX_SCALE)
        representative=matrix_zones.get(matrix_id,source_zone)
        if 0<=cx<mw and 0<=cz<mh and matrix_map_zones is not None:
            candidate=matrix_map_zones[cz*mw+cx]
            if 0<=candidate<len(source.headers)//48:
                candidate_area=struct.unpack_from('<H',source.headers,candidate*48+2)[0]
                if source.areas[candidate_area*10+6]:representative=candidate
        try:
            part_faces,part_packs,report=source.scene(representative,local_x,local_z,y,radius=radius,
                keep_centre=True,flight=True,layout_matrix=matrix_id,layout_zones=matrix_map_zones,
                layout_mask=layout_masks[matrix_id],
                collision_debug=collision_debug)
        except (ValueError,IndexError,KeyError,struct.error):
            continue
        faces.extend(part_faces);packs.update(part_packs)
        omitted_props.extend(report.get('omittedProps',[]));chunks.extend(report.get('chunks',[]))
        closed_backs+=report.get('closedBacks',0)
        tile_x=round(offset_x/16);tile_z=round(offset_z/16)
        for site in report.get('landings',[]):
            if len(site)!=4:continue
            global_x=offset_x+site[1]*16+8;global_z=offset_z+site[2]*16+8
            # Only the nearby whitelist is needed; flight refreshes the scene
            # before the rider reaches the edge of this window.
            if math.hypot(global_x-x,global_z-z)>768:continue
            landings.append([site[0],site[1],site[2],site[3],global_x,global_z])
        for tile in report.get('collisionTiles',[]):
            if len(tile)==4:collision_tiles.append([tile[0]+tile_x,tile[1]+tile_z,tile[2],tile[3]])
    if len(faces)>32000:raise ValueError('This map exceeds the flight scenery budget')
    # Some Redux cells point at alternate chunks whose texture dictionaries
    # omit names used by their models. Let the atlas sea cover those gaps.
    faces=[(pair,vertices) for pair,vertices in faces
           if pair[0] in packs and pair[1] in dict(packs[pair[0]].textures)
           and pair[2] in dict(packs[pair[0]].palettes)]
    pairs=sorted({pair for pair,_ in faces})
    atlas_grid=[1 if cid>=0 else 0 for cid in ids]
    origin_world_x,origin_world_z=origin_x*_MATRIX_SCALE,origin_z*_MATRIX_SCALE
    atlas_x,atlas_z=x-origin_world_x,z-origin_world_z
    routes=build_flyway_routes(width,depth,tuple(ids))
    flyway_faces=make_flyway_faces(routes,atlas_x,atlas_z,radius)
    catalog=soaring_region_catalog()
    landmarks=atlas_landmarks(source,offsets,layouts,catalog)
    decomp_routes=decomp_region_routes(width,depth,origin_x,origin_z,
                                       landmarks,catalog)
    corridor_routes=[link['points'] for link in decomp_routes]
    region_routes=[*routes,*corridor_routes]
    region_faces,atlas_biome=make_region_fill_faces(
        width,depth,ids,atlas_x,atlas_z,radius,
        origin=(origin_x,origin_z),link_routes=region_routes,
        region_places=landmarks)
    # Cover every unused cell within the atlas rectangle. The convex-hull sea
    # fill used for terrain placement left the map's outer corners unrendered.
    water_cells=atlas_water_cells(width,depth,ids)
    water_material=flight_water_material(source)
    water_faces=(make_water_faces(water_cells,width,origin_x,origin_z,atlas_x,atlas_z,radius,len(pairs))
                 if water_material is not None else [])
    if len(faces)+len(water_faces)+len(flyway_faces)+len(region_faces)+len(collision_tiles)>32000:
        raise ValueError('This map exceeds the flight scenery budget')
    directory=Path(directory);directory.mkdir(parents=True)
    textures=[];texture_modes=[]
    for i,(kind,texture_name,palette_name) in enumerate(pairs):
        pack=packs[kind];texture=dict(pack.textures)[texture_name];palette=dict(pack.palettes)[palette_name]
        colours=[ndspy.color.pack(*c) for c in palette.colors]
        if not colours:raise ValueError('Empty flight texture palette')
        # Nitro palettes may omit unused entries; ndspy eagerly expands the
        # complete indexed lookup table even when those indices are unused.
        colours.extend([0]*max(0,256-len(colours)))
        if texture.width>1024 or texture.height>1024:raise ValueError('Flight texture exceeds budget')
        name=f'texture-{i}.png'
        texture.renderAsImage(SimpleNamespace(colors=colours)).save(directory/name)
        textures.append(name)
        texture_modes.append([bool(getattr(texture,key,True if key.startswith('repeat') else False)) for key in ('repeatS','repeatT','mirrorS','mirrorT')])
    indices={pair:i for i,pair in enumerate(pairs)}
    geometry=[[indices[pair],[[round(v,5) for v in vertex] for vertex in vertices]] for pair,vertices in faces]
    if water_material is not None and water_faces:
        texture,palette=water_material
        colours=[ndspy.color.pack(*colour) for colour in palette.colors]
        colours.extend([0]*max(0,256-len(colours)))
        texture.renderAsImage(SimpleNamespace(colors=colours)).save(directory/f'texture-{len(textures)}.png')
        textures.append(f'texture-{len(textures)}.png')
        # The 32x32 ROM tile repeats in both directions for continuous water.
        texture_modes.append([True,True,False,False])
        geometry.extend(water_faces)
    atlas_markers=[[round(place['worldX']/_MATRIX_SCALE-origin_x,4),
                    round(place['worldZ']/_MATRIX_SCALE-origin_z,4),
                    place['name'],place['type'],place['biome'],place['fly'],
                    place['zone']]
                   for place in landmarks]
    result={'format':3,'zone':zone,'sourceZone':source_zone,'world':[x,y,z],'textures':textures,'textureModes':texture_modes,'faces':geometry,
            'omittedProps':sorted(set(omitted_props)),'chunks':sorted(set(chunks)),
            'landings':landings,'closedBacks':closed_backs,'radius':radius,
            'atlasMatrix':matrix,'atlasSize':[width,depth],'atlasOriginCell':[origin_x,origin_z],'atlasGrid':atlas_grid,
            'atlasBiome':atlas_biome,'atlasLandmarks':atlas_markers,
            'decompRoutes':[link['points'] for link in decomp_routes],
            'decompRouteNames':[[link['from'],link['to']] for link in decomp_routes],
            'flywayRoutes':routes,'flywayFaces':flyway_faces,'regionFaces':region_faces,
            'regionConnectorCount':len(decomp_routes),
            'matrixOffsets':{str(mid):list(offset) for mid,offset in sorted(offsets.items())},
            'collisionDebug':collision_debug,'collisionTiles':collision_tiles,'seaTiles':len(water_faces)}
    (directory/'scene.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
    return result


def export_with_budget(source,zone,x,z,y,directory):
    """Use the widest regional scene that fits native face and file limits."""
    for radius in (4096,3072,2560,2048,1536,1024):
        try:
            return export_scene(source,zone,x,z,y,directory,radius=radius)
        except ValueError as error:
            if 'flight scenery budget' not in str(error):raise
    raise ValueError('Nearby map exceeds the flight scenery budget')


class SoaringWorker:
    def __init__(self,rom,directory,collision_debug=False):
        self.rom=Path(rom).resolve();self.directory=Path(directory).resolve()
        self.collision_debug=bool(collision_debug)
        self.directory.mkdir(parents=True,exist_ok=True)
        self.stop=threading.Event();self.started=time.time()
        self.thread=threading.Thread(target=self.run,name='Soaring map scenery',daemon=True);self.thread.start()

    def run(self):
        source=None;handled=set()
        while not self.stop.wait(.2):
            for request in self.directory.glob('request-*.json'):
                if request.name in handled:continue
                try:
                    if request.stat().st_mtime<self.started:continue
                    if request.stat().st_size>4096:raise ValueError('Invalid flight request')
                    data=json.loads(request.read_text());zone=data['zone'];x=data['worldX'];z=data['worldZ'];y=data['worldY']
                    # Zone 0 is a real outdoor Redux map used by matrix 357;
                    # it is not a sentinel. Keep the ROM index bound while
                    # accepting every valid unsigned zone ID, including zero.
                    if type(zone) is not int or not 0<=zone<4096:raise ValueError('Invalid flight map')
                    if not all(type(v) in (int,float) and math.isfinite(v) and -32768<=v<=131072 for v in (x,y,z)):raise ValueError('Invalid flight position')
                    if source is None:
                        source=FieldSource(ndspy.rom.NintendoDSRom.fromFile(str(self.rom)))
                        source.collision_debug=self.collision_debug
                    destination=self.directory/('scene-'+uuid.uuid4().hex)
                    result=export_with_budget(source,zone,x,z,y,destination)
                    atomic_json(request.with_name(request.name.replace('request-','ready-')),{'scene':destination.name+'/scene.json','zone':zone,'omittedProps':len(result['omittedProps'])})
                except (OSError,ValueError,KeyError,IndexError,struct.error) as error:
                    atomic_json(request.with_name(request.name.replace('request-','ready-')),{'error':str(error)[:160]})
                handled.add(request.name)
