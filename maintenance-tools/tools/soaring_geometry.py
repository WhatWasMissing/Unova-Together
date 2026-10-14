"""Flight-only shell completion and conservative native landing tiles.

Unova Together, mvq1303, GPL-3.0-or-later. Original ROM geometry is preserved;
added walls belong only to the optional flight renderer, not native field data.
"""
import math
import struct
from collections import Counter


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


def landing_tiles(chunk,terrain,zone,mx,mz,origin,height,obstacles,npc_tiles=()):
    """Whitelist ordinary flat walkable tiles, with actual mesh height.

    Native WB permissions have an 8-byte tile record. Flags 0/128 with behavior
    0 are ordinary ground; blocked 129, water and special behaviors are excluded.
    Slopes, stacked levels and ambiguous geometry are deliberately excluded.
    """
    begin,end=struct.unpack_from('<II',chunk,8);permission=chunk[begin:end]
    if len(permission)<4 or struct.unpack_from('<HH',permission)!=(32,32) or len(permission)<8196:return []
    buckets={}
    for _,face in terrain:
        if max(v[1] for v in face)-min(v[1] for v in face)>.25:continue
        for i in range(1,len(face)-1):
            a,b,c=face[0],face[i],face[i+1]
            area=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
            if abs(area)<1e-6:continue
            left=max(0,int(math.floor((min(v[0] for v in (a,b,c))-origin[0]+256)/16)))
            right=min(31,int(math.floor((max(v[0] for v in (a,b,c))-origin[0]+256)/16)))
            top=max(0,int(math.floor((min(v[2] for v in (a,b,c))-origin[2]+256)/16)))
            bottom=min(31,int(math.floor((max(v[2] for v in (a,b,c))-origin[2]+256)/16)))
            for z in range(top,bottom+1):
                for x in range(left,right+1):buckets.setdefault((x,z),[]).append((a,b,c,area))
    result=[]
    for (tx,tz),triangles in buckets.items():
        slope,_,behavior,flags=struct.unpack_from('<4H',permission,4+(tz*32+tx)*8)
        if slope!=0 or behavior!=0 or flags not in (0,128):continue
        px=origin[0]-256+tx*16+8;pz=origin[2]-256+tz*16+8
        if any(a-8<=px<=b+8 and c-8<=pz<=d+8 for a,b,c,d in obstacles):continue
        # Static event objects can stand on ordinary tiles that the map's
        # collision grid marks as clear. Keep landings away from them so the
        # player doesn't arrive inside an NPC's interaction/collision space.
        global_x=mx*32+tx;global_z=mz*32+tz
        if any(max(abs(global_x-nx),abs(global_z-nz))<=2 for nx,nz in npc_tiles):continue
        heights=[]
        for a,b,c,area in triangles:
            w0=((b[2]-c[2])*(px-c[0])+(c[0]-b[0])*(pz-c[2]))/area
            w1=((c[2]-a[2])*(px-c[0])+(a[0]-c[0])*(pz-c[2]))/area
            if min(w0,w1,1-w0-w1)>=-1e-6:heights.append(a[1]+height)
        if not heights or max(heights)-min(heights)>.25:continue
        result.append([zone,mx*32+tx,mz*32+tz,round(sum(heights)/len(heights),5)])
    return result


def collision_debug_tiles(chunk,terrain,mx,mz,origin,height,obstacles,radius=1350):
    """Return compact, local collision samples for the optional Soaring overlay.

    Kinds are 0=ordinary walkable ground, 1=blocked/prop-covered, and
    2=slope or special behavior. These are inspection colors only; they do
    not change the conservative native landing whitelist.
    """
    begin,end=struct.unpack_from('<II',chunk,8);permission=chunk[begin:end]
    if len(permission)<8196 or struct.unpack_from('<HH',permission)!=(32,32):return []
    buckets={}
    for _,face in terrain:
        for i in range(1,len(face)-1):
            a,b,c=face[0],face[i],face[i+1]
            area=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
            if abs(area)<1e-6:continue
            left=max(0,int(math.floor((min(v[0] for v in (a,b,c))-origin[0]+256)/16)))
            right=min(31,int(math.floor((max(v[0] for v in (a,b,c))-origin[0]+256)/16)))
            top=max(0,int(math.floor((min(v[2] for v in (a,b,c))-origin[2]+256)/16)))
            bottom=min(31,int(math.floor((max(v[2] for v in (a,b,c))-origin[2]+256)/16)))
            for tz in range(top,bottom+1):
                for tx in range(left,right+1):buckets.setdefault((tx,tz),[]).append((a,b,c,area))
    result=[]
    for (tx,tz),triangles in buckets.items():
        px=origin[0]-256+tx*16+8;pz=origin[2]-256+tz*16+8
        if px*px+pz*pz>radius*radius:continue
        heights=[]
        for a,b,c,area in triangles:
            w0=((b[2]-c[2])*(px-c[0])+(c[0]-b[0])*(pz-c[2]))/area
            w1=((c[2]-a[2])*(px-c[0])+(a[0]-c[0])*(pz-c[2]))/area
            if min(w0,w1,1-w0-w1)>=-1e-6:heights.append(a[1]+height)
        if not heights or max(heights)-min(heights)>.25:continue
        slope,_,behavior,flags=struct.unpack_from('<4H',permission,4+(tz*32+tx)*8)
        blocked=flags not in (0,128) or any(a-8<=px<=b+8 and c-8<=pz<=d+8 for a,b,c,d in obstacles)
        kind=1 if blocked else 2 if behavior!=0 or slope!=0 else 0
        result.append([mx*32+tx,mz*32+tz,round(sum(heights)/len(heights),3),kind])
    return result
