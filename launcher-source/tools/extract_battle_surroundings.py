"""Read-only nearby field geometry capture. Unova Together, mvq1303.

Exports real terrain chunks and their placement, not generated arena scenery.
Not installed as battle backgrounds: native resource budgets and placed props
must be resolved before this capture can safely become a battle scene.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import ndspy.narc
import ndspy.rom
import ndspy.model
from build_area_battle_scene import area_assets


def matrix_cells(data):
    if len(data) < 8:
        raise ValueError('Truncated map matrix')
    flags, width, height = struct.unpack_from('<IHH', data)
    if flags not in (0, 1) or not width or not height or width*height > 65536:
        raise ValueError('Unsupported map matrix')
    count = width*height
    if len(data) != 8 + count*4*(1+flags):
        raise ValueError('Invalid map matrix length')
    chunks = struct.unpack_from(f'<{count}i', data, 8)
    zones = struct.unpack_from(f'<{count}i', data, 8+count*4) if flags else None
    return width, height, chunks, zones


def terrain_model(data):
    if len(data) < 20 or data[:4] != b'WB\x03\0':
        raise ValueError('Unsupported field chunk container')
    offsets = struct.unpack_from('<4I', data, 4)
    if offsets[0] != 20 or any(a > b for a, b in zip(offsets, offsets[1:])) or offsets[-1] > len(data):
        raise ValueError('Invalid field chunk offsets')
    model = data[offsets[0]:offsets[1]]
    if len(model) < 24 or model[:4] != b'BMD0' or struct.unpack_from('<I', model, 8)[0] != len(model):
        raise ValueError('Invalid terrain model')
    if not ndspy.model.NSBMD(model).models:
        raise ValueError('Empty terrain model')
    return model, data[offsets[-2]:offsets[-1]]


def field_chunk_model(data):
    """Return a field chunk's model, props, and whether it has native terrain.

    BW2's decomp distinguishes WB chunks (model, terrain and props) from NG
    chunks (model and props only). NG maps still need their authored geometry
    drawn, but their models do not define collision or landing ground.
    """
    if data[:4] == b'WB\x03\0':
        model, props = terrain_model(data)
        return model, props, True
    if data[:4] == b'GC\x04\0' and len(data) >= 24:
        _magic, section_count, model_offset, terrain0_offset, terrain1_offset, props_offset, end_offset = struct.unpack_from('<HHIIIII', data)
        if (section_count != 4 or model_offset < 24 or
                not model_offset < terrain0_offset < terrain1_offset <= props_offset <= end_offset <= len(data)):
            raise ValueError('Invalid GC field chunk offsets')
        model = data[model_offset:terrain0_offset]
        props = data[props_offset:end_offset]
        if len(model) < 24 or model[:4] != b'BMD0' or struct.unpack_from('<I', model, 8)[0] != len(model):
            raise ValueError('Invalid GC field model')
        if not props:
            props = bytes(4)
        if len(props) < 4:
            raise ValueError('Truncated GC props')
        count = struct.unpack_from('<I', props)[0]
        if count > 1024 or 4 + count * 16 > len(props):
            raise ValueError('Invalid GC props')
        return model, props, True
    if data[:4] != b'NG\x02\0' or len(data) < 16:
        raise ValueError('Unsupported field chunk container')
    _magic, section_count, model_offset, props_offset, end_offset = struct.unpack_from('<HHIII', data)
    if (section_count != 2 or model_offset < 16 or
            not model_offset < props_offset <= end_offset <= len(data)):
        raise ValueError('Invalid NG field chunk offsets')
    model = data[model_offset:props_offset]
    props = data[props_offset:end_offset]
    if len(model) < 24 or model[:4] != b'BMD0' or struct.unpack_from('<I', model, 8)[0] != len(model):
        raise ValueError('Invalid NG field model')
    if len(props) < 4:
        raise ValueError('Truncated NG props')
    count = struct.unpack_from('<I', props)[0]
    if count > 1024 or len(props) != 4 + count * 16:
        raise ValueError('Invalid NG props')
    if model[:4] != b'BMD0':
        raise ValueError('Invalid NG field model')
    return model, props, False


def capture(rom, zone, x, z, output, radius=1):
    if not all(math.isfinite(v) and v >= 0 for v in (x,z)) or radius not in (0,1,2):
        raise ValueError('Invalid capture coordinates or radius')
    area, texture, pack = area_assets(rom, zone)
    headers = ndspy.narc.NARC(rom.getFileByName('a/0/1/2')).files[0]
    matrix = struct.unpack_from('<H', headers, zone*48+4)[0]
    matrices = ndspy.narc.NARC(rom.getFileByName('a/0/0/9')).files
    width,height,ids,zones = matrix_cells(matrices[matrix])
    cx,cz = int(x)//32,int(z)//32
    if cx >= width or cz >= height or ids[cz*width+cx] < 0:
        raise ValueError('Player coordinates do not select an occupied matrix cell')
    if zones is not None and zones[cz*width+cx] != zone:
        raise ValueError('Coordinates belong to another zone; live matrix replacement needs resolution')
    chunks = ndspy.narc.NARC(rom.getFileByName('a/0/0/8')).files
    selected=[]
    for mz in range(max(0,cz-radius),min(height,cz+radius+1)):
        for mx in range(max(0,cx-radius),min(width,cx+radius+1)):
            cid=ids[mz*width+mx]
            if cid < 0: continue
            if zones is not None:
                neighbor=zones[mz*width+mx]
                if not 0 <= neighbor < len(headers)//48:
                    continue
                if struct.unpack_from('<H',headers,neighbor*48+2)[0] != area:
                    continue  # A neighboring area may require another texture pack.
            if cid >= len(chunks): raise ValueError('Chunk index outside archive')
            model,props=terrain_model(chunks[cid])
            selected.append((mx,mz,cid,model,props))
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    (output/'area-textures.nsbtx').write_bytes(pack.save())
    records=[]
    for mx,mz,cid,model,props in selected:
        stem=f'cell-{mx}-{mz}-chunk-{cid}'
        (output/(stem+'.nsbmd')).write_bytes(model)
        (output/(stem+'-props.bin')).write_bytes(props)
        records.append(dict(cell=[mx,mz],chunk=cid,model=stem+'.nsbmd',
                            sha256=hashlib.sha256(model).hexdigest(),bytes=len(model),
                            centreRelativeWorld=[(mx*32+16-x)*16,0,(mz*32+16-z)*16],
                            props=stem+'-props.bin'))
    report=dict(zone=zone,area=area,texturePack=texture,matrix=matrix,
                playerTile=[x,z],matrixDimensions=[width,height],chunks=records,
                status='actual field terrain capture; not installed into battles',
                limitations=['Static ROM matrix; live seasonal/story replacements not resolved',
                             'Default 32-tile chunk placement; special map types need live verification',
                             'Placed prop records preserved but models not assembled',
                             'Terrain not cropped or fitted to native battle resource slots'])
    (output/'surroundings.json').write_text(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',required=True);p.add_argument('--zone',type=int,required=True)
    p.add_argument('--x',type=float,required=True);p.add_argument('--z',type=float,required=True)
    p.add_argument('--radius',type=int,default=1);p.add_argument('--output',required=True)
    a=p.parse_args()
    print(json.dumps(capture(ndspy.rom.NintendoDSRom.fromFile(a.rom),a.zone,a.x,a.z,a.output,a.radius),indent=2))
