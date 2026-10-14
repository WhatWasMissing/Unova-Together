"""Launcher preferences and opt-in AR codes. mvq1303 / WhatWasMissing.

ROMs and saves are read-only here; native melonDS executes activated codes.
"""
from pathlib import Path
import hashlib, json, os, re, struct, subprocess
from collections.abc import Mapping
import tomlkit

CATALOG = json.loads((Path(__file__).parent/'assets/cheats.json').read_text(encoding='utf-8'))
MARKER = 'Unova Together launcher cheats'

def identify(path):
    path = Path(path)
    try:
        with path.open('rb') as handle:
            header = handle.read(0x200)
            if len(header) != 0x200 or header[12:16] != b'IREO':return None
            offset, entry, address, size = struct.unpack_from('<4I',header,0x20)
            if address != 0x02004000 or not 0 < size <= 8*1024*1024 or offset < 0x200 or offset+size > path.stat().st_size:return None
            handle.seek(offset);digest = hashlib.sha256(handle.read(size)).hexdigest()
        if digest not in CATALOG['profiles']:return None
        key = hashlib.sha256(str(path.resolve()).casefold().encode()).hexdigest()[:24]
        return {'key':key,'profile':CATALOG['profiles'][digest],'digest':digest}
    except (OSError,ValueError):return None

def running(executable):
    """Check only this exact runtime, including games opened outside the launcher."""
    if os.name != 'nt':return False
    result = subprocess.run(['powershell.exe','-NoProfile','-Command',
        'Get-Process melonDS -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path'],
        capture_output=True,text=True,timeout=8,creationflags=subprocess.CREATE_NO_WINDOW)
    return any(Path(line.strip()).resolve()==Path(executable).resolve() for line in result.stdout.splitlines() if line.strip())

def any_running():
    if os.name!='nt':return False
    result=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-Process melonDS -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path'],capture_output=True,text=True,timeout=8,creationflags=subprocess.CREATE_NO_WINDOW)
    return bool(result.stdout.strip())

def read_document(runtime):
    path=Path(runtime)/'melonDS.toml'
    if not path.exists():return tomlkit.document()
    if path.stat().st_size > 2*1024*1024:raise ValueError('Emulator settings file is too large.')
    doc=tomlkit.parse(path.read_text(encoding='utf-8-sig'))
    for key,value in doc.items():
        if key=='Screen' or re.fullmatch(r'Instance\d+',key):
            if not isinstance(value,Mapping):raise ValueError('Invalid emulator settings table: '+key)
            if key!='Screen' and 'Audio' in value and not isinstance(value['Audio'],Mapping):raise ValueError('Invalid emulator audio settings table.')
    return doc

def defaults(runtime):
    try:
        doc=read_document(runtime);instance=doc.get('Instance0',{})
        return {'pause':bool(doc.get('PauseLostFocus',False)),
                'volume':round(instance.get('Audio',{}).get('Volume',256)*100/256),
                'filter':bool(doc.get('Screen',{}).get('Filter',True)),
                'companion_interactions':True,'reduced_follower_motion':False,'soaring':False,'soaring_collision_debug':False}
    except (OSError,ValueError,TypeError,tomlkit.exceptions.ParseError):return {'pause':False,'volume':100,'filter':True,'companion_interactions':True,'reduced_follower_motion':False,'soaring':False,'soaring_collision_debug':False}

def atomic(path,text):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    pending=path.with_name(path.name+'.launcher-pending')
    try:
        pending.write_text(text,encoding='utf-8');os.replace(pending,path)
    finally:
        if pending.exists():pending.unlink()

def managed_codes(existing,selected):
    # Replace only our category. Existing ROOT-level codes and nested user
    # categories remain byte-for-byte. Our generated category has no children.
    if len(existing.encode('utf-8'))>2*1024*1024:raise ValueError('Cheat file is too large.')
    lines=existing.splitlines(keepends=True);kept=[];inside=False
    for line in lines:
        if re.fullmatch(r'CAT 0 '+re.escape(MARKER)+r'\s*',line):inside=True;continue
        if inside and line.strip()=='ROOT':inside=False;continue
        if inside and line.startswith('CAT '):raise ValueError('Managed cheat category was edited; keep it unchanged or remove it first.')
        if not inside:kept.append(line)
    if inside:raise ValueError('Managed cheat category is incomplete.')
    text=''.join(kept).rstrip('\r\n')+'\n\nCAT 0 '+MARKER+'\n'
    for item in CATALOG['codes']:
        words=item['words'].split()
        text+=f"CODE {int(bool(selected.get(item['id'],False)))} {item['name']}\nDESC {item['activation']}\n"
        text+=''.join(' '.join(words[i:i+2])+'\n' for i in range(0,len(words),2))
    return text+'ROOT\n'

def apply(runtime,rom,preferences,selected,profile,home):
    runtime=Path(runtime);rom=Path(rom).resolve()
    if running(runtime/'melonDS.exe'):raise ValueError('Close this build’s emulator before applying settings or cheats.')
    if not preferences and not selected:return
    doc=read_document(runtime)
    if 'pause' in preferences:doc['PauseLostFocus']=bool(preferences['pause'])
    if 'filter' in preferences:doc.setdefault('Screen',tomlkit.table())['Filter']=bool(preferences['filter'])
    instances=[key for key in doc if re.fullmatch(r'Instance\d+',key)] or ['Instance0']
    for key in instances:
        instance=doc.setdefault(key,tomlkit.table())
        if 'volume' in preferences:
            volume=preferences['volume']
            if type(volume) is not int or not 0<=volume<=100:raise ValueError('Volume must be between 0 and 100.')
            instance.setdefault('Audio',tomlkit.table())['Volume']=round(volume*256/100)
    if selected:
        # Re-check at write time: changing the file after UI detection cannot
        # enable a code on an unreviewed ROM.
        current=identify(rom)
        if not current or not profile or current['digest']!=profile['digest']:raise ValueError('Cheats require a supported Black 2 / Redux ROM.')
        directory=Path(home).resolve()/'.launcher-cheats'/current['key']
        path=directory/(rom.stem+'.mch')
        instance=doc.setdefault('Instance0',tomlkit.table())
        source=path
        if not source.exists():
            old=Path(instance.get('CheatFilePath','') or rom.parent)
            if not old.is_absolute():old=runtime/old
            source=old/(rom.stem+'.mch')
            if not source.exists() and '.launcher-cheats' in old.parts:source=rom.with_suffix('.mch')
        if source.exists() and source.stat().st_size>2*1024*1024:raise ValueError('Cheat file is too large.')
        original=source.read_text(encoding='utf-8-sig') if source.exists() else ''
        text=managed_codes(original,selected)
        state_path=directory/'original-switches.json'
        if state_path.exists():
            if state_path.stat().st_size>16384:raise ValueError('Cheat switch backup is too large.')
            switches=json.loads(state_path.read_text(encoding='utf-8'))
            if not isinstance(switches,dict):raise ValueError('Cheat switch backup is invalid.')
        else:
            switches={key:bool(doc.get(key,{}).get('EnableCheats',False)) for key in instances}
            atomic(state_path,json.dumps(switches))
        atomic(path,text)
        for key in instances:
            instance=doc.setdefault(key,tomlkit.table())
            instance['CheatFilePath']=str(directory)
            instance['EnableCheats']=True if any(selected.values()) else bool(switches.get(key,False))
    path=runtime/'melonDS.toml'
    if path.exists() and not path.with_name('melonDS.toml.before-launcher-settings').exists():
        atomic(path.with_name('melonDS.toml.before-launcher-settings'),path.read_text(encoding='utf-8-sig'))
    atomic(path,tomlkit.dumps(doc))
