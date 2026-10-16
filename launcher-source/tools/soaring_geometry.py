"""Flight-only shell completion and conservative native landing tiles.

Unova Together, mvq1303, GPL-3.0-or-later. Original ROM geometry is preserved;
added walls belong only to the optional flight renderer, not native field data.
"""
import math
import struct
from collections import Counter

from soaring_height_tables import MAP_HEIGHT_OFFSET_TABLE, MAP_HEIGHT_SLOPE_TABLE


def normal(vertices):
    a,b,c=vertices[:3]
    u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    length=math.sqrt(sum(x*x for x in n))
    return tuple(x/length for x in n) if length>1e-6 else (0,0,0)


def close_building_shell(geometry):
    """Extend exposed roof boundary edges down where a wall is absent.

    Trees, billboards and flat props have no broad elevated roof and are left
    alone. Existing wall coverage keeps closed models unchanged.
    """
    points=[v for _,face in geometry for v in face]
    if not points:return geometry,0
    lo=[min(v[i] for v in points) for i in range(3)]
    hi=[max(v[i] for v in points) for i in range(3)]
    if hi[1]-lo[1]<12 or min(hi[0]-lo[0],hi[2]-lo[2])<8:return geometry,0
    if max(hi[0]-lo[0],hi[2]-lo[2])/min(hi[0]-lo[0],hi[2]-lo[2])>4:return geometry,0
    walls=[(pair,face) for pair,face in geometry if abs(normal(face)[1])<.15 and max(v[1] for v in face)-min(v[1] for v in face)>8]
    roofs=[(pair,face) for pair,face in geometry if abs(normal(face)[1])>.35 and min(v[1] for v in face)>lo[1]+(hi[1]-lo[1])*.35]
    if not walls or not roofs:return geometry,0
    roof_points=[v for _,face in roofs for v in face]
    roof_lo=[min(v[i] for v in roof_points) for i in range(3)]
    roof_hi=[max(v[i] for v in roof_points) for i in range(3)]
    key=lambda v:tuple(round(c,3) for c in v[:3])
    edges=Counter();records={}
    for _,face in roofs:
        for a,b in zip(face,face[1:]+face[:1]):
            edge=tuple(sorted((key(a),key(b))));edges[edge]+=1;records[edge]=(a,b)
    result=list(geometry);added=0
    for edge,count in edges.items():
        if count!=1:continue
        a,b=records[edge];dx=b[0]-a[0];dz=b[2]-a[2];length=math.hypot(dx,dz)
        if length<4:continue
        # Complete only the outer shell, never interior roof triangulation,
        # skylights or ornamental seams. Those are not missing building walls.
        if not any(all(abs(v[axis]-bound)<.5 for v in (a,b)) for axis in (0,2) for bound in (roof_lo[axis],roof_hi[axis])):continue
        mx,mz=(a[0]+b[0])/2,(a[2]+b[2])/2
        def covers(face):
            # A wall must share the edge's plane and cover its midpoint and
            # height. A wall elsewhere in the building is not a substitute.
            return (all(abs((v[0]-a[0])*dz-(v[2]-a[2])*dx)/length<8 for v in face)
                    and min(v[0] for v in face)-8<=mx<=max(v[0] for v in face)+8
                    and min(v[2] for v in face)-8<=mz<=max(v[2] for v in face)+8
                    and max(v[1] for v in face)>=min(a[1],b[1])-8)
        if any(covers(face) for _,face in walls):continue
        pair,wall=min(walls,key=lambda item:sum((sum(v[i] for v in item[1])/len(item[1])-(mx if i==0 else mz))**2 for i in (0,2)))
        u0=min(v[3] for v in wall);u1=max(v[3] for v in wall)
        v0=min(v[4] for v in wall);v1=max(v[4] for v in wall)
        if u1-u0<1 or v1-v0<1:continue
        result.append((pair,[(a[0],a[1],a[2],u0,v0),(b[0],b[1],b[2],u1,v0),
                            (b[0],lo[1],b[2],u1,v1),(a[0],lo[1],a[2],u0,v1)]))
        added+=1
    return result,added


_WATER_TILE_CLASSES={0x3d,0x3e,0x3f,0x40,0x41,0x42,0x43,0x44,0x7c,0x72,0x73,0x74,0x75}
_MIN_LANDING_NORMAL_Y=.82


def _chunk_terrain_sections(chunk):
    """Return terrain sections using the Black 2 chunk headers."""
    magic=bytes(chunk[:2])
    if magic in (b'WB',b'RD'):
        if len(chunk)<16:return []
        start,end=struct.unpack_from('<II',chunk,8)
        ranges=[(start,end)]
    elif magic==b'GC':
        if len(chunk)<20:return []
        first,second,end=struct.unpack_from('<III',chunk,8)
        ranges=[(first,second),(second,end)]
    else:
        return []
    if any(start<4 or start>=end or end>len(chunk) for start,end in ranges):return []
    return [memoryview(chunk)[start:end] for start,end in ranges]


def _height_from_plane(normal,offset,position_x,position_z):
    """Sample a decomp MapTerrainBuf plane in Nitro fixed-point units."""
    nx,ny,nz=normal
    if ny<=0:return None
    normal_x=nx/4096.;normal_y=ny/4096.;normal_z=-nz/4096.
    if normal_y<=1e-6:return None
    return -(offset/4096.+normal_x*position_x+normal_z*position_z)/normal_y


def _sample_chunk_terrain(section,tile_x,tile_z,chunk_type):
    """Port FieldChunkAccessor_GetTerrainCore/ RD_GetTerrain at tile center."""
    if len(section)<4:return None
    width,depth=struct.unpack_from('<HH',section)
    if not (0<width<=64 and 0<depth<=64 and tile_x<width and tile_z<depth):return None
    index=tile_z*width+tile_x
    pos_x=-width*8+tile_x*16+8
    pos_z=-depth*8+tile_z*16+8
    if chunk_type==b'RD':
        offset=4+index*24
        if offset+24>len(section):return None
        values=struct.unpack_from('<6h2iI',section,offset)
        packed=values[8];tile_type=packed&0x7fffffff;diagonal=packed>>31
        if diagonal==0:
            plane=0 if 8+8<16 else 1
        else:
            plane=0 if 8>8 else 1
        normal=values[plane*3:plane*3+3]
        height_offset=values[6+plane]
        height=_height_from_plane(normal,height_offset,pos_x,pos_z)
        return (tile_type,height,normal[1]/4096.) if height is not None else None

    tile_offset=4+index*8
    if tile_offset+8>len(section):return None
    shape_slope,height_index,tile_word=struct.unpack_from('<HHI',section,tile_offset)
    shape=shape_slope&3;slope=shape_slope>>2;diagonal=tile_word>>31
    tile_type=tile_word&0x7fffffff
    if shape==0:
        slope_index=slope;offset_index=height_index
    elif shape==2:
        splits_start=4+width*depth*8
        split_offset=splits_start+height_index*8
        if split_offset+8>len(section):return None
        slope0_word,slope1,offset0,offset1=struct.unpack_from('<4H',section,split_offset)
        if diagonal==0:
            plane=0 if 8+8<16 else 1
        else:
            plane=0 if 8>8 else 1
        slope_index=(slope0_word>>2) if plane==0 else slope1
        offset_index=offset0 if plane==0 else offset1
    else:
        return tile_type,0.,1.
    if slope_index*3+2>=len(MAP_HEIGHT_SLOPE_TABLE) or offset_index>=len(MAP_HEIGHT_OFFSET_TABLE):return None
    slope_offset=slope_index*3
    normal=MAP_HEIGHT_SLOPE_TABLE[slope_offset:slope_offset+3]
    height=_height_from_plane(normal,MAP_HEIGHT_OFFSET_TABLE[offset_index],pos_x,pos_z)
    return (tile_type,height,normal[1]/4096.) if height is not None else None


def _walkable_terrain(tile_type,normal_y):
    """Apply the decomp's MapTile_IsValid/MapTile_BlocksCollision rules."""
    if tile_type==0xffffffff:return False
    tile_class=tile_type&0xffff
    flags=(tile_type>>16)&0xffff
    if tile_class==0xff or flags&1 or tile_class in _WATER_TILE_CLASSES:return False
    return normal_y>=_MIN_LANDING_NORMAL_Y


def landing_tiles(chunk,terrain,zone,mx,mz,origin,height,obstacles,npc_tiles=()):
    """Find safe landings from BW2's actual layered field-height and tile data.

    Rendering meshes can stack water beds, roads and bridges in one cell; the
    decomp's MapTerrainBuf is the source of truth for the walkable surface.
    """
    sections=_chunk_terrain_sections(chunk)
    if not sections:return []
    if any(len(section)<4 or struct.unpack_from('<HH',section)!=(32,32) for section in sections):return []
    result=[]
    for tz in range(32):
        for tx in range(32):
            surfaces=[sample for section in sections
                      if (sample:=_sample_chunk_terrain(section,tx,tz,bytes(chunk[:2]))) is not None
                      and _walkable_terrain(sample[0],sample[2])]
            if not surfaces:continue
            # The highest collision-valid plane is the surface presented to a
            # flight approach; it avoids selecting the underpass below bridges.
            _tile_type,ground,_normal_y=max(surfaces,key=lambda sample:sample[1])
            px=origin[0]-256+tx*16+8;pz=origin[2]-256+tz*16+8
            if any(a-8<=px<=b+8 and c-8<=pz<=d+8 for a,b,c,d in obstacles):continue
            global_x=mx*32+tx;global_z=mz*32+tz
            if any(max(abs(global_x-nx),abs(global_z-nz))<=2 for nx,nz in npc_tiles):continue
            result.append([zone,global_x,global_z,round(ground,5)])
    return result


def collision_debug_tiles(chunk,terrain,mx,mz,origin,height,obstacles,radius=1350):
    """Return native collision samples for the optional Soaring overlay.

    Kinds are 0=walkable ground, 1=blocked/prop-covered, and 2=water or steep
    ground. The same decomp height data drives the landing whitelist.
    """
    sections=_chunk_terrain_sections(chunk)
    if not sections:return []
    if any(len(section)<4 or struct.unpack_from('<HH',section)!=(32,32) for section in sections):return []
    result=[]
    for tz in range(32):
        for tx in range(32):
            samples=[sample for section in sections
                     if (sample:=_sample_chunk_terrain(section,tx,tz,bytes(chunk[:2]))) is not None]
            if not samples:continue
            tile_type,ground,normal_y=max(samples,key=lambda sample:sample[1])
            px=origin[0]-256+tx*16+8;pz=origin[2]-256+tz*16+8
            if px*px+pz*pz>radius*radius:continue
            tile_class=tile_type&0xffff
            flags=(tile_type>>16)&0xffff
            prop_blocked=any(a-8<=px<=b+8 and c-8<=pz<=d+8 for a,b,c,d in obstacles)
            kind=1 if tile_type==0xffffffff or tile_class==0xff or flags&1 or prop_blocked else 2 if normal_y<_MIN_LANDING_NORMAL_Y or tile_class in _WATER_TILE_CLASSES else 0
            result.append([mx*32+tx,mz*32+tz,round(ground,3),kind])
    return result
