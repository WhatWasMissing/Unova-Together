"""Local flight scenery from the player's real field meshes. mvq1303, GPL-3.0-or-later."""
from pathlib import Path
from types import SimpleNamespace
import json, math, os, threading, uuid, time, struct
import ndspy.rom
import ndspy.color
from build_battle_surroundings import FieldSource
from battle_surroundings_worker import atomic_json
from extract_battle_surroundings import matrix_cells


def export_scene(source, zone, x, z, y, directory, radius=4096):
    ndspy.color.prepareLUTs()
    if not all(math.isfinite(v) for v in (x,z,y)):raise ValueError('Invalid flight position')
    source_zone=zone
    source_area,matrix=struct.unpack_from('<HH',source.headers,zone*48+2)
    width,depth,ids,zones=matrix_cells(source.matrices[matrix])
    cx,cz=int(x//512),int(z//512)
    if not 0<=cx<width or not 0<=cz<depth:
        # Stay with the take-off region's matrix beyond its authored edge;
        # SoaringScene supplies cloud-sea there and fog hides the hard edge.
        zone=source_zone
    elif ids[cz*width+cx]>=0 and zones is not None and zones[cz*width+cx]>=0:
        zone=zones[cz*width+cx]
    if not 0<=zone<len(source.headers)//48:raise ValueError('Unsupported neighbouring zone')
    area,neighbor_matrix=struct.unpack_from('<HH',source.headers,zone*48+2)
    if not source.areas[source_area*10+6]:raise ValueError('Take flight outdoors')
    faces,packs,report=source.scene(zone,x,z,y,radius=radius,keep_centre=True,flight=True,layout_matrix=matrix)
    if len(faces)>32000:raise ValueError('This map exceeds the flight scenery budget')
    # A handful of Redux matrix cells point at alternate or partial chunks
    # whose texture dictionaries omit names seen in their model. Skip those
    # faces and let the atlas sea safely cover the gap.
    faces=[(pair,vertices) for pair,vertices in faces
           if pair[0] in packs and pair[1] in dict(packs[pair[0]].textures)
           and pair[2] in dict(packs[pair[0]].palettes)]
    pairs=sorted({pair for pair,_ in faces})
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
    result={'format':2,'zone':zone,'sourceZone':source_zone,'world':[x,y,z],'textures':textures,'textureModes':texture_modes,'faces':geometry,
            'omittedProps':report['omittedProps'],'chunks':report['chunks'],
            'landings':report.get('landings',[]),'closedBacks':report.get('closedBacks',0),'radius':radius,
            'atlasMatrix':matrix,'atlasSize':[width,depth],'seaTiles':0}
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
    def __init__(self,rom,directory):
        self.rom=Path(rom).resolve();self.directory=Path(directory).resolve()
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
                    if source is None:source=FieldSource(ndspy.rom.NintendoDSRom.fromFile(str(self.rom)))
                    destination=self.directory/('scene-'+uuid.uuid4().hex)
                    result=export_with_budget(source,zone,x,z,y,destination)
                    atomic_json(request.with_name(request.name.replace('request-','ready-')),{'scene':destination.name+'/scene.json','zone':zone,'omittedProps':len(result['omittedProps'])})
                except (OSError,ValueError,KeyError,IndexError,struct.error) as error:
                    atomic_json(request.with_name(request.name.replace('request-','ready-')),{'error':str(error)[:160]})
                handled.add(request.name)
