"""Install one area's scenery in a DISPOSABLE ROM for native battle testing.

Changes only standard batt_bg models. Keeps platform, animation, script, team,
save and Pokéstar resources intact. Fails if a replacement cannot fit its slot.
Copyright (C) 2026 mvq1303. GPL-3.0-or-later.
"""
from pathlib import Path
import argparse, struct, json, hashlib
import ndspy.rom
import ndspy.narc


def model_name(raw):
    if raw[:4] != b'BMD0': return None, None
    mdl=struct.unpack_from('<I',raw,16)[0];d=mdl+8
    if raw[d+1]!=1: raise ValueError('Only one-model files are supported')
    info=d+struct.unpack_from('<H',raw,d+6)[0]
    name=info+8
    return name, bytes(raw[name:name+16]).rstrip(b'\0').decode('ascii')


def install(source, model, destination):
    source,model,destination=map(lambda p:Path(p).resolve(),(source,model,destination))
    root=Path(__file__).resolve().parents[1]/'test-fixtures/coop-launcher'
    if not destination.is_relative_to(root): raise ValueError('Output must be a private co-op fixture')
    if destination.exists(): raise FileExistsError(destination)
    replacement=bytearray(model.read_bytes());name_offset,_=model_name(replacement)
    rom=ndspy.rom.NintendoDSRom.fromFile(str(source));raw=bytearray(source.read_bytes())
    fileid=rom.filenames.idOf('a/0/1/1');fat=struct.unpack_from('<I',raw,0x48)[0]
    archive_start,archive_end=struct.unpack_from('<II',raw,fat+fileid*8)
    pos=archive_start+struct.unpack_from('<H',raw,archive_start+12)[0]
    entries=payload=None
    for _ in range(struct.unpack_from('<H',raw,archive_start+14)[0]):
        kind=raw[pos:pos+4];length=struct.unpack_from('<I',raw,pos+4)[0]
        if kind==b'BTAF': entries=pos+12
        if kind==b'GMIF': payload=pos+8
        pos+=length
    if entries is None or payload is None: raise ValueError('Invalid battle archive')
    archive=ndspy.narc.NARC(rom.getFileByName('a/0/1/1'));changes=[]
    for i,original in enumerate(archive.files):
        _,name=model_name(original)
        if name is None or not name.startswith('batt_bg'):continue
        start,end=struct.unpack_from('<II',raw,entries+i*8)
        if len(replacement)>end-start: raise ValueError(f'Model does not fit {name}')
        entry=bytearray(replacement);entry[name_offset:name_offset+16]=name.encode().ljust(16,b'\0')
        raw[payload+start:payload+end]=entry+bytes(end-start-len(entry))
        changes.append({'entry':i,'name':name,'offset':payload+start,'bytes':end-start})
    if not changes: raise ValueError('No standard battle backgrounds found')
    # Verify the archive parser still sees all entries and every unrelated
    # resource is byte-identical. No repack or FAT offset changes are allowed.
    actual=ndspy.narc.NARC(raw[archive_start:archive_end]);changed={x['entry'] for x in changes}
    assert len(actual.files)==len(archive.files)
    for i,(a,b) in enumerate(zip(actual.files,archive.files)):
        if i not in changed: assert a==b
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
    report={'source':str(source),'destination':str(destination),'changes':changes,
            'sourceSHA256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),
            'outputSHA256':hashlib.sha256(raw).hexdigest(),
            'status':'Private experimental ROM. Native battle validation required.'}
    destination.with_suffix('.scene.json').write_text(json.dumps(report,indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',required=True)
    p.add_argument('--model',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();r=install(a.rom,a.model,a.output);print(len(r['changes']),'standard backgrounds replaced in private fixture')
