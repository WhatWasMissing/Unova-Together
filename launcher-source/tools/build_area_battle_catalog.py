"""Build local area arenas and an explicit coverage manifest. mvq1303, GPL-3.0-or-later."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import ndspy.rom
import ndspy.narc
from build_area_battle_scene import build
from install_area_battle_fixture import model_name


def catalog(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    output.mkdir(parents=True)
    rom = ndspy.rom.NintendoDSRom.fromFile(str(source))
    headers = ndspy.narc.NARC(rom.getFileByName('a/0/1/2')).files[0]
    areas, zones = {}, []
    for zone in range(len(headers)//48):
        area = struct.unpack_from('<H', headers, zone*48+2)[0]
        if area not in areas:
            try:
                report = build(rom, zone, output/f'area-{area}', general=True, compact=True, preview=False)
                areas[area] = {'model': f'area-{area}/area-arena.nsbmd',
                              'sha256': report['modelSHA256'], 'bytes': report['modelBytes'],
                              'quads': report['quads'], 'textures': report['textures']}
            except (ValueError, IndexError, struct.error) as error:
                areas[area] = {'fallback': 'original native background', 'reason': str(error)}
        zones.append({'zone': zone, 'area': area})
    raw=source.read_bytes();fat=struct.unpack_from('<I',raw,0x48)[0]
    fid=rom.filenames.idOf('a/0/1/1');start,end=struct.unpack_from('<II',raw,fat+fid*8)
    pos=start+struct.unpack_from('<H',raw,start+12)[0];entries=payload=None
    for _ in range(struct.unpack_from('<H',raw,start+14)[0]):
        kind=raw[pos:pos+4];length=struct.unpack_from('<I',raw,pos+4)[0]
        if kind==b'BTAF':entries=pos+12
        if kind==b'GMIF':payload=pos+8
        pos+=length
    slots=[]
    for i,data in enumerate(ndspy.narc.NARC(rom.getFileByName('a/0/1/1')).files):
        _,name=model_name(data)
        if name and name.startswith('batt_bg'):
            lo,hi=struct.unpack_from('<II',raw,entries+i*8)
            slots.append({'offset':payload+lo,'bytes':hi-lo,'name':name,
                          'sha256':hashlib.sha256(raw[payload+lo:payload+hi]).hexdigest()})
    report = {'format': 1, 'romBytes':len(raw),'slots':slots, 'romSHA256': hashlib.sha256(raw).hexdigest(),
              'romAssetSHA256':hashlib.sha256(raw[0x8000:]).hexdigest(),
              'romHeaderSHA256':hashlib.sha256(raw[:512]).hexdigest(),
              'zones': zones, 'areas': areas,
              'coverage': {'zoneHeaders': len(zones), 'areaGroups': len(areas),
                           'exportedAreas': sum('model' in x for x in areas.values()),
                           'fallbackAreas': sum('fallback' in x for x in areas.values())},
              'status': 'Generated local assets. Native battle integration requires validation.',
              'attribution': 'Unova Together by mvq1303 / WhatWasMissing; graphics from the supplied ROM'}
    (output/'catalog.json').write_text(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', required=True);p.add_argument('--output', required=True)
    args=p.parse_args();print(json.dumps(catalog(args.rom,args.output)['coverage']))
