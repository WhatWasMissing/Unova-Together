"""Encounter-centred native field scenery. mvq1303, GPL-3.0-or-later.

Static terrain/props from the supplied ROM, cropped to a bounded native arena.
No game logic or saves are edited. Unsupported skeletons retain fallback scenery.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import copy
import hashlib
import json
import math
import struct
import ndspy.rom
import ndspy.narc
import ndspy.texture
import ndspy.color
import ndspy.model
from PIL import Image
from extract_battle_surroundings import matrix_cells, terrain_model
from field_scene_geometry import decode, crop_face
from vendor.nsbmd_writer import WriteFile as writer


def container(data, signature):
    if len(data)<8 or data[:2]!=signature:raise ValueError('Container signature')
    count=struct.unpack_from('<H',data,2)[0]
    if not count or count>4096 or 4+4*(count+1)>len(data):raise ValueError('Container count')
    offsets=struct.unpack_from(f'<{count+1}I',data,4)
    if offsets[0]<4+4*(count+1) or offsets[-1]>len(data) or any(a>b for a,b in zip(offsets,offsets[1:])):
        raise ValueError('Container bounds')
    return [data[a:b] for a,b in zip(offsets,offsets[1:])]


class FieldSource:
    def __init__(self,rom):
        self.rom=rom
        if rom.idCode!=b'IREO':raise ValueError('English Black 2 required')
        self.headers=self.arc('a/0/1/2')[0]
        self.areas=rom.getFileByName('a/0/1/3')
        self.matrices=self.arc('a/0/0/9');self.chunks=self.arc('a/0/0/8')
        self.packs=self.arc('a/0/1/4');self.props_cache={}
        self.terrain_cache={};self.texture_cache={}

    def arc(self,name):return ndspy.narc.NARC(self.rom.getFileByName(name)).files

    def properties(self,area):
        if area in self.props_cache:return self.props_cache[area]
        group=struct.unpack_from('<H',self.areas,area*10)[0]
        exterior=bool(self.areas[area*10+6])
        files=container(self.arc('a/2/2/5' if exterior else 'a/2/2/6')[group],b'AB')
        half=len(files)//2
        if len(files)%2:raise ValueError('Building registry pairs')
        models={struct.unpack_from('<H',entry)[0]:files[i+half] for i,entry in enumerate(files[:half])}
        pack=ndspy.texture.NSBTX(self.arc('a/1/7/4' if exterior else 'a/1/7/5')[group])
        self.props_cache[area]=(models,pack)
        return models,pack

    def scene(self,zone,x,z,height):
        if not 0<=zone<len(self.headers)//48 or not all(math.isfinite(v) for v in (x,z,height)):
            raise ValueError('Invalid encounter')
        area,matrix=struct.unpack_from('<HH',self.headers,zone*48+2)
        width,depth,ids,zones=matrix_cells(self.matrices[matrix])
        cx,cz=int(x//512),int(z//512)
        if x<0 or z<0 or cx>=width or cz>=depth or ids[cz*width+cx]<0:
            raise ValueError('Encounter outside occupied matrix')
        if zones is not None and zones[cz*width+cx]!=zone:
            raise ValueError('Live zone differs from static matrix')
        tid=struct.unpack_from('<H',self.areas,area*10+2)[0]
        pack=ndspy.texture.NSBTX(self.packs[tid])
        packs={'terrain':pack};faces=[];omitted=[];sources=[]
        for mz in range(max(0,cz-1),min(depth,cz+2)):
            for mx in range(max(0,cx-1),min(width,cx+2)):
                cid=ids[mz*width+mx]
                if cid<0:continue
                neighbor=zones[mz*width+mx] if zones is not None else zone
                if not 0<=neighbor<len(self.headers)//48 or struct.unpack_from('<H',self.headers,neighbor*48+2)[0]!=area:continue
                model,props=terrain_model(self.chunks[cid])
                origin=(mx*512+256-x,0,mz*512+256-z)
                sources.append(cid)
                for pair,vertices in decode(bytes(model)):
                    transformed=[(v[0]+origin[0],v[1]-height,v[2]+origin[2],v[3],v[4]) for v in vertices]
                    cropped=crop_face(transformed,176)
                    if len(cropped)>=3:faces.append((('terrain',)+pair,cropped))
                count=struct.unpack_from('<I',props)[0] if len(props)>=4 else 0
                if count>1024 or 4+count*16>len(props):raise ValueError('Placed prop bounds')
                for i in range(count):
                    px,py,pz,rotation,uid=struct.unpack_from('<iiiH',props,4+i*16)+(struct.unpack_from('>H',props,18+i*16)[0],)
                    px=px/4096+origin[0];py=py/4096-height;pz=origin[2]-pz/4096
                    if abs(px)>240 or abs(pz)>240:continue
                    try:
                        models,prop_pack=self.properties(area);packs['props']=prop_pack
                        # Texture maps are static; skeleton animation is deliberately unsupported.
                        geometry=decode(bytes(models[uid]));angle=rotation*2*math.pi/65536
                        sine,cosine=math.sin(angle),math.cos(angle)
                        for pair,vertices in geometry:
                            transformed=[(v[0]*cosine+v[2]*sine+px,v[1]+py,-v[0]*sine+v[2]*cosine+pz,v[3],v[4]) for v in vertices]
                            cropped=crop_face(transformed,176)
                            # Buildings must not swallow the four-battler centre.
                            if len(cropped)>=3 and min(max(abs(v[0]),abs(v[2])) for v in cropped)>64:
                                faces.append((('props',)+pair,cropped))
                    except (ValueError,KeyError,IndexError,struct.error) as error:omitted.append(f'prop {uid}: {error}')
        if not faces:raise ValueError('No supported nearby geometry')
        return faces,packs,dict(zone=zone,area=area,matrix=matrix,world=[x,height,z],chunks=sources,omittedProps=sorted(set(omitted)))


def compress_texture(texture,palette):
    colors=[ndspy.color.pack(*c) for c in palette.colors]
    if not colors:raise ValueError('Empty source palette')
    # ndspy's I4 renderer eagerly expands sixteen entries even when a ROM
    # palette only stores eight and the unused indices never occur.
    if texture.format==ndspy.texture.TextureFormat.I4:
        if any((byte&15)>=len(colors) or (byte>>4)>=len(colors) for byte in texture.data1):
            raise ValueError('Texture references missing palette entries')
        colors+= [0]*max(0,16-len(colors))
    image=texture.renderAsImage(NS(colors=colors)).convert('RGBA')
    original=image.size
    image=image.resize((32,32),Image.Resampling.NEAREST)
    indexed=image.convert('RGB').quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    rgb=indexed.getpalette();rgb+= [0]*(768-len(rgb));palette_bytes=bytes(2)
    for i in range(15):
        r,g,b=rgb[i*3:i*3+3];palette_bytes+=struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10))
    indices=bytes(0 if a<128 else index+1 for index,(_,_,_,a) in zip(indexed.getdata(),image.getdata()))
    packed=bytes(indices[i]|indices[i+1]<<4 for i in range(0,len(indices),2))
    tex=ndspy.texture.Texture.fromFlags(0,0,True,True,False,False,32,32,ndspy.texture.TextureFormat.I4,True,0,0,packed,b'')
    return tex,ndspy.texture.Palette(0,0,0,palette_bytes),original


def export(source,zone,x,z,height,output,budget=16384):
    ndspy.color.prepareLUTs()
    faces,packs,report=source.scene(zone,x,z,height)
    # Preserve all floor coverage before nearby vertical scenery. A strict
    # polygon/material budget bounds native loading, memory and draw costs.
    triangles=[]
    for pair,polygon in faces:
        for i in range(1,len(polygon)-1):
            tri=[polygon[0],polygon[i],polygon[i+1]]
            low=max(v[1] for v in tri)-min(v[1] for v in tri)<.25
            distance=sum(v[0]*v[0]+v[2]*v[2] for v in tri)/3
            triangles.append((not low,distance,pair,tri))
    triangles.sort(key=lambda t:(t[0],t[1] if t[2][0]=='props' or not t[0] else t[1]+100000))
    selected=[];pairs=[];floor_count=0;compressed={};invalid=set()
    # A continuous underlay prevents holes when the native budget excludes
    # some fine terrain faces. Its texture is chosen from actual nearby floor.
    for vertical,distance,pair,tri in triangles:
        if vertical or any(word in pair[1].lower() for word in ('kage','shadow','yuki','kusa')):continue
        pack=packs[pair[0]]
        try:
            tex=dict(pack.textures)[pair[1]];pal=dict(pack.palettes)[pair[2]]
            compressed[pair]=compress_texture(tex,pal)
        except (ValueError,KeyError,IndexError):continue
        pairs.append(pair)
        size=compressed[pair][2];u,v=size
        points=[(-35.2,-1.25,-35.2,0,0),(-35.2,-1.25,35.2,0,v*4),(35.2,-1.25,35.2,u*4,v*4),(35.2,-1.25,-35.2,u*4,0)]
        selected.extend([(0,[points[0],points[1],points[2]]),(0,[points[0],points[2],points[3]])]);floor_count=2
        break
    for vertical,distance,pair,tri in triangles:
        if not vertical and floor_count>=48:continue
        if pair not in pairs:
            if pair in invalid:continue
            if not vertical and len(pairs)>=6:continue
            if len(pairs)>=12:continue
            pack=packs[pair[0]]
            if pair[1] not in dict(pack.textures) or pair[2] not in dict(pack.palettes):continue
            try:compressed[pair]=compress_texture(dict(pack.textures)[pair[1]],dict(pack.palettes)[pair[2]])
            except (ValueError,IndexError):invalid.add(pair);continue
            pairs.append(pair)
        # Flatten central floor to native platform height; keep edge relief.
        transformed=[(v[0]*.2,(-1 if not vertical and max(abs(v[0]),abs(v[2]))<64 else max(-8,min(48,v[1]*.2))),v[2]*.2,v[3],v[4]) for v in tri]
        selected.append((pairs.index(pair),transformed))
        if not vertical:floor_count+=1
        if len(selected)>=72:break
    # Surround the cropped patch with a distant backdrop. The game's rotating
    # camera otherwise exposes the empty space beyond the extracted terrain.
    area=report['area'];exterior=bool(source.areas[area*10+6])
    if exterior:
        native=ndspy.model.NSBMD(source.arc('a/0/1/1')[74])
        sky=ndspy.texture.NSBTX();sky.textures=[('sky',dict(native.textures)['batt_sky01'])];sky.palettes=[('sky_pl',dict(native.palettes)['batt_sky01_pl'])]
        packs['backdrop']=sky;backdrop=('backdrop','sky','sky_pl')
    else:
        terrain=packs['terrain'];available=dict(terrain.palettes)
        walls=[name for name,_ in terrain.textures if any(word in name.lower() for word in ('kabe','wall')) and name+'_pl' in available and available[name+'_pl'].colors]
        backdrop=('terrain',walls[0],walls[0]+'_pl') if walls else pairs[0]
    if backdrop not in pairs:
        p=packs[backdrop[0]];compressed[backdrop]=compress_texture(dict(p.textures)[backdrop[1]],dict(p.palettes)[backdrop[2]])
        pairs.append(backdrop)
    index=pairs.index(backdrop);tw,th=compressed[backdrop][2]
    for side in range(4):
        points=[]
        for vx,vy,vz,u,v in [(-44,-2,44,0,th),(44,-2,44,tw,th),(44,48,44,tw,0),(-44,48,44,0,0)]:
            for _ in range(side):vx,vz=-vz,vx
            points.append((vx,vy,vz,u,v))
        selected.extend([(index,[points[0],points[1],points[2]]),(index,[points[0],points[2],points[3]])])
    report['backdropTexture']=backdrop
    if len(selected)<4:raise ValueError('Insufficient supported terrain')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    pack=ndspy.texture.NSBTX();sizes=[]
    for i,pair in enumerate(pairs):
        tex,pal,size=compressed[pair]
        name=f'ut_local{i}';pack.textures.append((name,tex));pack.palettes.append((name+'_pl',pal));sizes.append(size)
    lists=[];sbc=[2,0,1,0x26,0,0,0,0,0xb]
    for material in range(len(pairs)):
        commands=[]
        for index,vertices in selected:
            if index!=material:continue
            commands.extend([0x40,0,0x20,0x7fff])
            for vx,vy,vz,u,v in vertices:
                tw,th=sizes[index]
                u=round(u*32/tw*16);v=round(v*32/th*16)
                commands.extend([0x22,(u&65535)|((v&65535)<<16)])
                xyz=[round(n*4096/128)&65535 for n in (vx,vy,vz)]
                commands.extend([0x23,xyz[0]|(xyz[1]<<16),xyz[2]])
            commands.append(0x41)
        lists.append(commands);sbc.extend([4,material,5,material])
    sbc.append(1)
    points=[v for _,tri in selected for v in tri];low=[min(p[i] for p in points) for i in range(3)];high=[max(p[i] for p in points) for i in range(3)]
    data=NS(NSBCommands=sbc,scaleX=128*4096,boundsX=round(low[0]*4096),boundsY=round(low[1]*4096),boundsZ=round(low[2]*4096),boundsXWidth=round((high[0]-low[0])*4096),boundsHeight=round((high[1]-low[1])*4096),boundsZWidth=round((high[2]-low[2])*4096))
    materials=[NS(name=f'local{i}',tex_ind=i,pal_ind=i,use_vcol=True,DIF_AMB=0x7fff7fff,SPE_EMI=0,POLY_ATTR_OR=0x001f00c0,POLY_ATTR_MASK=0xffffffff,TEXIMAGE_PARAMS=0,tex_width=32,tex_height=32) for i in range(len(pairs))]
    node=NS(name='root',validTransform=False,inverseMatrix=[[int(i==j) for j in range(4)] for i in range(4)])
    path=output/'surroundings.nsbmd'
    writer.WriteFile([lists],[data],[materials],[[node]],NS(texNames=[n for n,_ in pack.textures],paletteNames=[n for n,_ in pack.palettes],fileContents=pack.save()[20:]),['batt_stage01'],True,str(path))
    raw=bytearray(path.read_bytes());mdl=struct.unpack_from('<I',raw,16)[0]
    info=mdl+8;off=struct.unpack_from('<H',raw,info+6)[0];model=mdl+struct.unpack_from('<I',raw,info+off+4)[0]
    raw[model+24]=raw[model+25]=len(materials)
    struct.pack_into('<4H',raw,model+36,len(selected)*3,len(selected),len(selected),0)
    struct.pack_into('<II',raw,model+56,data.scaleX,16777216//data.scaleX)
    if len(raw)>budget:raise ValueError(f'Nearby scene exceeds native budget: {len(raw)} > {budget}')
    ndspy.model.NSBMD(raw)
    path.write_bytes(raw)
    report.update(model='surroundings.nsbmd',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),triangles=len(selected),materials=pairs,textureSizes=sizes,
                  status='cropped static ROM terrain; nearby supported static props; centre cleared',
                  geometry=selected)
    (output/'scene.json').write_text(json.dumps(report,indent=2))
    return report

