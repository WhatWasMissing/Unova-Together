"""Local flight scenery from the player's real field meshes. mvq1303, GPL-3.0-or-later."""
from pathlib import Path
from types import SimpleNamespace
from functools import lru_cache
import heapq, json, math, os, threading, uuid, time, struct
import ndspy.rom
import ndspy.color
from build_battle_surroundings import FieldSource
from battle_surroundings_worker import atomic_json
from extract_battle_surroundings import matrix_cells
from soaring_geometry import collision_debug_tiles


_MATRIX_SCALE=512  # 32 map tiles per matrix cell, at 16 world units per tile.


def flight_matrix_offsets(source, root_matrix):
    """Find reciprocal, fly-enabled outdoor matrix links using the ROM's warps.

    BW2 stores warp positions in 1/16-tile world units. A reciprocal pair
    gives an exact translation between two map matrices; inconsistent or
    indoor links are rejected instead of guessed from map names.
    """
    cached=getattr(source,'_flight_matrix_offsets',None)
    if cached is not None and root_matrix in cached:return cached[root_matrix]
    if not all(hasattr(source,key) for key in ('headers','events','areas','matrices')):
        return {root_matrix:(0,0)}
    count=len(source.headers)//48
    eligible=[];matrix_zones={}
    for zone in range(count):
        offset=zone*48
        area,matrix=struct.unpack_from('<HH',source.headers,offset+2)
        flags=struct.unpack_from('<H',source.headers,offset+30)[0]
        if (not flags&0x2000 or matrix>=len(source.matrices) or
                area*10+7>len(source.areas) or not source.areas[area*10+6]):continue
        eligible.append(zone);matrix_zones.setdefault(matrix,[]).append(zone)
    zone_warps={}
    for zone in eligible:
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
    edge_offsets={}
    for zone,records in zone_warps.items():
        matrix=struct.unpack_from('<H',source.headers,zone*48+4)[0]
        for index,warp in enumerate(records):
            if warp is None:continue
            dest,dest_warp,x,z=warp
            reverse=zone_warps.get(dest,())
            if dest not in zone_warps or dest_warp>=len(reverse):continue
            back=reverse[dest_warp]
            if back is None or back[0]!=zone or back[1]!=index:continue
            dest_matrix=struct.unpack_from('<H',source.headers,dest*48+4)[0]
            if dest_matrix==matrix:continue
            dx=x-back[2];dz=z-back[3]
            if dx%16 or dz%16:continue
            edge=(min(matrix,dest_matrix),max(matrix,dest_matrix))
            signed=(dx,dz) if matrix<dest_matrix else (-dx,-dz)
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
    caches=cached if cached is not None else {}
    caches[root_matrix]=offsets
    source._flight_matrix_offsets=caches
    return offsets


def merged_flight_grid(source, offsets):
    """Merge linked matrices into a bounded, coarse atlas for flight visuals."""
    layouts={}
    min_x=min_z=10**9;max_x=max_z=-10**9
    for matrix,(ox,oz) in offsets.items():
        width,depth,ids,zones=matrix_cells(source.matrices[matrix])
        layouts[matrix]=(width,depth,ids,zones)
        min_x=min(min_x,math.floor(ox/_MATRIX_SCALE));min_z=min(min_z,math.floor(oz/_MATRIX_SCALE))
        max_x=max(max_x,math.ceil((ox+width*_MATRIX_SCALE)/_MATRIX_SCALE))
        max_z=max(max_z,math.ceil((oz+depth*_MATRIX_SCALE)/_MATRIX_SCALE))
    width,height=max_x-min_x,max_z-min_z
    if width<1 or height<1 or width*height>4096:
        raise ValueError('Connected flight region exceeds atlas bounds')
    cells=[-1]*(width*height)
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
                    for gx in range(max(0,left),min(width-1,right)+1):cells[gz*width+gx]=1
    return min_x,min_z,width,height,tuple(cells),layouts


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


def make_region_fill_faces(width,depth,cell_ids,x,z,radius):
    """Cover open regional gaps with a deep-sea underlay and forest islets.

    Generated faces are renderer-only. They never affect collision or landing
    eligibility. Forest fills are placed only in empty cells supported by a
    substantial cluster of authored land, so open-water coastlines stay sea.
    """
    faces=[]
    extent=max(3600.,min(7600.,radius+1200.))
    y=-72.
    corners=[(-extent,y,-extent),(extent,y,-extent),(extent,y,extent),(-extent,y,extent)]
    faces.extend([[0,[list(corners[0]),list(corners[1]),list(corners[2])]],
                  [0,[list(corners[0]),list(corners[2]),list(corners[3])]]])
    biome=[2 if value>=0 else 0 for value in cell_ids]
    eligible=[]
    for cell,value in enumerate(cell_ids):
        if value>=0:continue
        gx, gz=cell%width,cell//width
        center_x=(gx+.5)*512-x;center_z=(gz+.5)*512-z
        if math.hypot(center_x,center_z)>min(2500.,radius+350.):continue
        neighbours=0
        for dz in range(-2,3):
            for dx in range(-2,3):
                nx,nz=gx+dx,gz+dz
                if 0<=nx<width and 0<=nz<depth and cell_ids[nz*width+nx]>=0:
                    neighbours+=1
        if neighbours>=8:eligible.append((math.hypot(center_x,center_z),cell,gx,gz))
    eligible.sort()
    for _,cell,gx,gz in eligible:
        if len(faces)>4700:break
        biome[cell]=1
        left=gx*512-x+24;right=(gx+1)*512-x-24
        front=gz*512-z+24;back=(gz+1)*512-z-24
        floor_y=-20.
        a=(left,floor_y,front);b=(right,floor_y,front);c=(right,floor_y,back);d=(left,floor_y,back)
        faces.extend([[1,[list(a),list(b),list(c)]],[1,[list(a),list(c),list(d)]]])
        # Stable per-cell pseudo-random placement keeps rebuilt scenes still.
        state=(cell*1103515245+12345)&0x7fffffff
        def rand(limit):
            nonlocal state
            state=(state*1103515245+12345)&0x7fffffff
            return (state%1000000)/1000000*limit
        for _tree in range(3):
            if len(faces)>4700:break
            tx=gx*512-x+75+rand(362);tz=gz*512-z+75+rand(362)
            radius_tree=18+rand(13);height=34+rand(19);base=floor_y
            trunk=5+rand(3)
            ring=[]
            for side in range(5):
                angle=side*math.tau/5+rand(.2)
                ring.append((tx+math.cos(angle)*radius_tree,base+height*.45,tz+math.sin(angle)*radius_tree))
            top=(tx,base+height,tz);lower=(tx,base+height*.16,tz)
            colors=(2,3)
            for side in range(5):
                faces.append([colors[side%2],[list(ring[side]),list(ring[(side+1)%5]),list(top)]])
                faces.append([3,[list(ring[side]),list(lower),list(ring[(side+1)%5])]])
            # A narrow, dark trunk ties the crown to the forest floor.
            t0=(tx-trunk,base,tz-trunk);t1=(tx+trunk,base,tz-trunk)
            t2=(tx+trunk,base,tz+trunk);t3=(tx-trunk,base,tz+trunk)
            u0=(tx-trunk,base+height*.2,tz-trunk);u1=(tx+trunk,base+height*.2,tz-trunk)
            u2=(tx+trunk,base+height*.2,tz+trunk);u3=(tx-trunk,base+height*.2,tz+trunk)
            for quad in ((t0,t1,u1,u0),(t1,t2,u2,u1),(t2,t3,u3,u2),(t3,t0,u0,u3)):
                p,q,r,s=quad
                faces.extend([[4,[list(p),list(q),list(r)]],[4,[list(p),list(r),list(s)]]])
    return faces,biome


def export_scene(source, zone, x, z, y, directory, radius=4096):
    ndspy.color.prepareLUTs()
    if not all(math.isfinite(v) for v in (x,z,y)):raise ValueError('Invalid flight position')
    source_zone=zone
    source_area,matrix=struct.unpack_from('<HH',source.headers,zone*48+2)
    if not source.areas[source_area*10+6]:raise ValueError('Take flight outdoors')
    offsets=flight_matrix_offsets(source,matrix)
    origin_x,origin_z,width,depth,ids,layouts=merged_flight_grid(source,offsets)
    matrix_zones={}
    for candidate in range(len(source.headers)//48):
        area_id,matrix_id=struct.unpack_from('<HH',source.headers,candidate*48+2)
        if matrix_id in offsets and source.areas[area_id*10+6]:
            matrix_zones.setdefault(matrix_id,candidate)
    if matrix not in matrix_zones:matrix_zones[matrix]=source_zone
    # The displayed zone follows the player into a linked matrix, but the
    # sourceZone remains the take-off map so the native flight session stays valid.
    zone=source_zone
    for matrix_id,(matrix_x,matrix_z) in offsets.items():
        offset_x,offset_z=offsets[matrix_id]
        local_x,local_z=x-offset_x,z-offset_z
        mw,mh,chunk_ids,matrix_map_zones=layouts[matrix_id]
        cx,cz=int(local_x//_MATRIX_SCALE),int(local_z//_MATRIX_SCALE)
        if 0<=cx<mw and 0<=cz<mh and chunk_ids[cz*mw+cx]>=0:
            candidate=matrix_map_zones[cz*mw+cx] if matrix_map_zones is not None else -1
            if 0<=candidate<len(source.headers)//48:
                candidate_area=struct.unpack_from('<H',source.headers,candidate*48+2)[0]
                if source.areas[candidate_area*10+6]:
                    zone=candidate;break
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
                keep_centre=True,flight=True,layout_matrix=matrix_id,collision_debug=collision_debug)
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
    region_faces,atlas_biome=make_region_fill_faces(width,depth,ids,atlas_x,atlas_z,radius)
    if len(faces)+len(flyway_faces)+len(region_faces)+len(collision_tiles)>32000:
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
    result={'format':3,'zone':zone,'sourceZone':source_zone,'world':[x,y,z],'textures':textures,'textureModes':texture_modes,'faces':geometry,
            'omittedProps':sorted(set(omitted_props)),'chunks':sorted(set(chunks)),
            'landings':landings,'closedBacks':closed_backs,'radius':radius,
            'atlasMatrix':matrix,'atlasSize':[width,depth],'atlasOriginCell':[origin_x,origin_z],'atlasGrid':atlas_grid,
            'atlasBiome':atlas_biome,'flywayRoutes':routes,'flywayFaces':flyway_faces,'regionFaces':region_faces,
            'matrixOffsets':{str(mid):list(offset) for mid,offset in sorted(offsets.items())},
            'collisionDebug':collision_debug,'collisionTiles':collision_tiles,'seaTiles':0}
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
                    if type(zone) is not int or not 0<zone<4096:raise ValueError('Invalid flight map')
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
