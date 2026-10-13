"""Unova Together native arena prototype. Copyright (C) 2026 mvq1303.

Reads a player's ROM, resolves the zone's actual area texture pack, and exports
a small textured NSBMD arena. Never changes the ROM, game memory, or saves.
Runtime installation is intentionally separate: these models need native battle
camera/animation validation before replacing a battle background.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import argparse
import copy
import hashlib
import json
import struct

import ndspy.rom
import ndspy.narc
import ndspy.texture
import ndspy.color
import ndspy.model
from vendor.nsbmd_writer import WriteFile as writer


def render_preview(output, faces, names):
    """Small software preview of exported geometry, not a game screenshot."""
    import numpy as np
    from PIL import Image
    width, height = 512, 384
    pixels = np.zeros((height, width, 4), dtype=np.uint8)
    pixels[:] = (168, 204, 218, 255)
    depth = np.full((height, width), np.inf)
    eye = np.array([210., 150., -260.])
    forward = np.array([0., 10., 30.])-eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0., 1., 0.]); right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    textures = [np.asarray(Image.open(output/(n+'.png')).convert('RGBA')) for n in names]
    for material, points in faces:
        vertices = np.asarray(points)-eye
        distances = vertices@forward
        if min(distances) <= 1:
            continue
        screen = np.column_stack((width/2 + 390*(vertices@right)/distances,
                                  height/2 - 390*(vertices@up)/distances))
        uv = np.array([[0., 1.], [1., 1.], [1., 0.], [0., 0.]])
        for indices in [[0, 1, 2], [0, 2, 3]]:
            p = screen[indices]; d = distances[indices]
            lo = np.maximum(np.floor(p.min(axis=0)).astype(int), [0, 0])
            hi = np.minimum(np.ceil(p.max(axis=0)).astype(int), [width-1, height-1])
            if np.any(hi < lo):
                continue
            x, y = np.meshgrid(np.arange(lo[0], hi[0]+1)+.5, np.arange(lo[1], hi[1]+1)+.5)
            denom = (p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
            if abs(denom) < 1e-6:
                continue
            a = ((p[1,1]-p[2,1])*(x-p[2,0])+(p[2,0]-p[1,0])*(y-p[2,1]))/denom
            b = ((p[2,1]-p[0,1])*(x-p[2,0])+(p[0,0]-p[2,0])*(y-p[2,1]))/denom
            weights = np.stack([a, b, 1-a-b], axis=-1)
            inverse = np.sum(weights/d, axis=-1)
            z = 1/np.maximum(inverse, 1e-9)
            coords = (weights/d)@uv[indices] * z[...,None]
            texture = textures[material]
            tx = np.clip((coords[...,0]*(texture.shape[1]-1)).astype(int), 0, texture.shape[1]-1)
            ty = np.clip((coords[...,1]*(texture.shape[0]-1)).astype(int), 0, texture.shape[0]-1)
            colour = texture[ty, tx]
            region = np.s_[lo[1]:hi[1]+1, lo[0]:hi[0]+1]
            valid = np.all(weights >= -1e-6, axis=-1) & (z < depth[region]) & (colour[...,3] >= 128)
            pixels[region][valid] = colour[valid]
            pixels[region][valid, 3] = 255
            depth[region][valid] = z[valid]
    Image.fromarray(pixels).save(output/'geometry-preview.png')


def area_assets(rom, zone):
    if rom.idCode != b'IREO':
        raise ValueError('English Black 2 is required')
    zones = ndspy.narc.NARC(rom.getFileByName('a/0/1/2')).files[0]
    if len(zones) % 48 or not 0 <= zone < len(zones) // 48:
        raise ValueError('Zone is outside the verified 48-byte zone table')
    area = struct.unpack_from('<H', zones, zone * 48 + 2)[0]
    areas = rom.getFileByName('a/0/1/3')
    if len(areas) % 10 or area * 10 + 10 > len(areas):
        raise ValueError('Area is outside the verified 10-byte area table')
    texture_id = struct.unpack_from('<H', areas, area * 10 + 2)[0]
    packs = ndspy.narc.NARC(rom.getFileByName('a/0/1/4')).files
    if texture_id >= len(packs):
        raise ValueError('Area texture index is out of bounds')
    return area, texture_id, ndspy.texture.NSBTX(packs[texture_id])


def build(rom, zone, output, *, general=False, compact=False, preview=True):
    ndspy.color.prepareLUTs()
    area, texture_id, source = area_assets(rom, zone)
    # Explicit verified outdoor texture families. Unsupported indoor packs fail
    # rather than silently borrowing graphics from a different location.
    textures, palettes = dict(source.textures), dict(source.palettes)
    texture_names = ['grass01ax', 'fence_01', 'ki02ax']
    exterior = bool(rom.getFileByName('a/0/1/3')[area*10+6])
    if general:
        usable = [name for name in textures if name+'_pl' in palettes]
        if not usable:
            raise ValueError(f'Area {area} has no verified texture/palette pairs')
        def pick(keys, fallback):
            for key in keys:
                for name in usable:
                    if key in name.lower(): return name
            return fallback
        floor = pick(['grass01ax', 'road', 'yuka', 'floor', 'michi'] if exterior
                     else ['yuka', 'floor', 'road'], usable[0])
        edge = pick(['fence', 'saku', 'gake'] if exterior else ['kabe', 'wall'], floor)
        detail = pick(['ki02ax', 'green', 'ki03'] if exterior else ['kabe2', 'kabe', 'wall'], edge)
        texture_names = [floor, edge, detail]
    for name in texture_names:
        if name not in textures or name + '_pl' not in palettes:
            raise ValueError(f'Unsupported area {area}: missing {name} / palette')
    selected = copy.deepcopy(source)
    # Some areas lack distinct detail assets. Unique export names keep Nitro's
    # Patricia dictionaries valid even when one source texture serves two roles.
    export_names = ['ut_floor', 'ut_edge', 'ut_detail'] if general else texture_names
    if compact:
        if exterior:
            native=ndspy.model.NSBMD(ndspy.narc.NARC(rom.getFileByName('a/0/1/1')).files[74])
            sky=copy.deepcopy(dict(native.textures)['batt_sky01'])
            if sky.format!=ndspy.texture.TextureFormat.I8 or (sky.width,sky.height)!=(128,64):
                raise ValueError('Unexpected native sky format')
            sky.data1=bytes(sky.data1[y*128+x] for y in range(0,64,2) for x in range(0,128,2))
            sky.width,sky.height=64,32
            textures['ut_sky_source']=sky;palettes['ut_sky_source_pl']=dict(native.palettes)['batt_sky01_pl']
            texture_names.append('ut_sky_source')
        else:
            texture_names.append(texture_names[1])
        export_names.append('ut_sky')
    selected.textures = [(alias, textures[name]) for alias, name in zip(export_names, texture_names)]
    selected.palettes = [(alias+'_pl', palettes[name+'_pl']) for alias, name in zip(export_names, texture_names)]
    packed = selected.save()[20:]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name, texture in zip(texture_names, [t for _,t in selected.textures]):
        colours = [ndspy.color.pack(*c) for c in palettes[name + '_pl'].colors]
        texture.renderAsImage(NS(colors=colours)).save(output / (name + '.png'))

    faces = []
    # Clear, open centre for four battlers; boundary scenery stays outside it.
    step = 80 if compact else 32
    for z in range(-160, 160, step):
        for x in range(-160, 160, step):
            faces.append((0, [(x, -1, z), (x, -1, z+step), (x+step, -1, z+step), (x+step, -1, z)]))
    for x in range(-160, 160, 32):
        faces.append((1, [(x, 0, 160), (x+32, 0, 160), (x+32, 24, 160), (x, 24, 160)]))
    for x in [-144, -96, -48, 48, 96, 144]:
        faces.append((2, [(x-16, 0, 184), (x+16, 0, 184), (x+16, 64, 184), (x-16, 64, 184)]))
    assert len(faces) <= 128
    if compact:
        # Native battle background extents are about 35 world units. Field
        # assets use 16 units per tile, so the export needs its own arena scale.
        faces = [(i, [tuple(v*.21875 for v in point) for point in points]) for i, points in faces]
        # The native battle camera turns around the arena. Put scenery on all
        # four sides and closer than the original field-sized perimeter.
        faces = faces[:16]
        for side in range(4):
            def rotate(point):
                x,y,z=point
                for _ in range(side): x,z=-z,x
                return x,y,z
            for x in [-15,-5,5]:
                faces.append((1,[rotate(p) for p in [(x,0,15),(x+10,0,15),(x+10,5.25,15),(x,5.25,15)]]))
            for x in [-10,0,10]:
                faces.append((2,[rotate(p) for p in [(x-3.5,0,18),(x+3.5,0,18),(x+3.5,14,18),(x-3.5,14,18)]]))
            faces.append((3,[rotate(p) for p in [(-40,-1,40),(40,-1,40),(40,45,40),(-40,45,40)]]))
    lists = []
    sbc = [2, 0, 1, 0x26, 0, 0, 0, 0, 0xb]
    for material in range(len(texture_names)):
        commands = []
        for index, points in faces:
            if index != material:
                continue
            tex = textures[texture_names[index]]
            commands += [0x40, 1, 0x20, 0x7fff]
            for (x, y, z), (u, v) in zip(points, [(0, tex.height), (tex.width, tex.height), (tex.width, 0), (0, 0)]):
                commands += [0x22, (u*16 & 0xffff) | ((v*16 & 0xffff) << 16)]
                xyz = [round(n * 4096 / 128) & 0xffff for n in (x, y, z)]
                commands += [0x23, xyz[0] | xyz[1] << 16, xyz[2]]
            commands += [0x41]
        lists.append(commands)
        sbc += [4, material, 5, material]
    sbc += [1]
    scale = .21875 if compact else 1
    points=[point for _,quad in faces for point in quad]
    low=[min(p[i] for p in points) for i in range(3)];high=[max(p[i] for p in points) for i in range(3)]
    data = NS(NSBCommands=sbc, scaleX=128*4096,
              boundsX=round(low[0]*4096),boundsY=round(low[1]*4096),boundsZ=round(low[2]*4096),
              boundsXWidth=round((high[0]-low[0])*4096),boundsHeight=round((high[1]-low[1])*4096),boundsZWidth=round((high[2]-low[2])*4096))
    materials = [NS(name='area_'+str(i), tex_ind=i, pal_ind=i, use_vcol=True,
                    DIF_AMB=0x7fff7fff, SPE_EMI=0, POLY_ATTR_OR=0x001f00c0,
                    POLY_ATTR_MASK=0xffffffff, TEXIMAGE_PARAMS=0,
                    tex_width=textures[name].width, tex_height=textures[name].height)
                 for i, name in enumerate(texture_names)]
    node = NS(name='root', validTransform=False,
              inverseMatrix=[[int(i == j) for j in range(4)] for i in range(4)])
    target = output / 'area-arena.nsbmd'
    writer.WriteFile([lists], [data], [materials], [[node]],
                     NS(texNames=export_names, paletteNames=[n+'_pl' for n in export_names], fileContents=packed),
                     ['batt_stage01'], True, str(target))
    raw = bytearray(target.read_bytes())
    mdl = struct.unpack_from('<I', raw, 16)[0]
    info = mdl + 8
    off = struct.unpack_from('<H', raw, info + 6)[0]
    model = mdl + struct.unpack_from('<I', raw, info + off + 4)[0]
    # Vendored field writer's fixed one-material header is overridden for this
    # three-material model; each corresponding dictionary is already emitted.
    raw[model+24] = len(materials)
    raw[model+25] = len(materials)
    struct.pack_into('<HHHH', raw, model + 36, len(faces)*4, len(faces), 0, len(faces))
    struct.pack_into('<II', raw, model + 56, data.scaleX, 16777216//data.scaleX)
    target.write_bytes(raw)
    # Structural checks include the embedded texture block and round-trip decode.
    assert raw[:4] == b'BMD0' and struct.unpack_from('<I', raw, 8)[0] == len(raw)
    texoff = struct.unpack_from('<I', raw, 20)[0]
    assert raw[texoff:texoff+4] == b'TEX0'
    verify = b'BTX0' + struct.pack('<HHIHHI', 0xfeff, 1, 20+len(raw)-texoff, 16, 1, 20) + raw[texoff:]
    assert len(ndspy.texture.NSBTX(verify).textures) == len(texture_names)
    if preview: render_preview(output, faces, texture_names)
    report = dict(zone=zone, area=area, texturePack=texture_id, textures=texture_names,
                  quads=len(faces), vertices=len(faces)*4, modelBytes=len(raw),
                  modelSHA256=hashlib.sha256(raw).hexdigest(),
                  status='exported prototype; not installed or battle-tested',
                  geometry=faces,
                  formatSources=['https://github.com/ds-pokemon-hacking/CTRMapV/blob/master/src/ctrmap/formats/pokemon/gen5/zone/VZoneHeader.java',
                                 'https://github.com/ds-pokemon-hacking/CTRMapV/blob/master/src/ctrmap/formats/pokemon/gen5/area/VAreaHeader.java'])
    (output/'report.json').write_text(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True)
    parser.add_argument('--zone', type=int, required=True)
    parser.add_argument('--output', required=True, help='New directory; existing output is never overwritten')
    args = parser.parse_args()
    report = build(ndspy.rom.NintendoDSRom.fromFile(args.rom), args.zone, args.output)
    print(json.dumps({k: v for k, v in report.items() if k != 'geometry'}, indent=2))
