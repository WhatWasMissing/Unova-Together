"""Bounded installation storage; mvq1303 / WhatWasMissing. Never prune user data."""
from contextlib import contextmanager
import hashlib, json, os, re, subprocess, sys
from pathlib import Path, PurePosixPath
import stat

SLOT=re.compile(r'\d{1,4}\.\d{1,4}\.\d{1,4}(?:-repair-[a-f0-9]{12})?')
RECEIPT='.installed-files.json'
BINARIES={'.exe','.dll','.pyd'}
PRIVATE={'.nds','.gba','.sav','.save','.dsv','.bin','.toml','.ini','.json','.mch'}

def linked(path):
    return path.is_symlink() or path.is_junction()

def safe(path,base):
    """Check every ancestor before any filesystem mutation, including junctions."""
    path=Path(path).absolute();base=Path(base).resolve()
    if not path.is_relative_to(base) or not path.resolve().is_relative_to(base):return False
    cursor=path
    while cursor!=base:
        if linked(cursor):return False
        cursor=cursor.parent
    return not linked(base)

def hardlinked(path):
    """Return true for a regular file with another directory entry to its data."""
    try:info=Path(path).stat(follow_symlinks=False)
    except FileNotFoundError:return False
    return stat.S_ISREG(info.st_mode) and info.st_nlink>1

def safe_managed_path(path,base):
    """Validate a managed path against reparse points and external hard links."""
    return safe(path,base) and not hardlinked(path)

def files(root):
    for directory,dirs,names in os.walk(root):
        dirs[:]=[n for n in dirs if not linked(Path(directory)/n)]
        for name in names:
            path=Path(directory)/name
            if not linked(path):yield path

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def read(path,limit=4*1024*1024):
    if linked(path) or path.stat().st_size>limit:raise ValueError('Invalid installation record.')
    return json.loads(path.read_text(encoding='utf-8'))

def atomic(path,value):
    pending=path.with_name(path.name+'.pending')
    if linked(path) or linked(pending) or hardlinked(path) or hardlinked(pending):
        raise ValueError('Unsafe installation record.')
    pending.write_text(json.dumps(value,indent=2),encoding='utf-8');os.replace(pending,path)

def record_package(root):
    root=Path(root).resolve()
    entries={p.relative_to(root).as_posix():digest(p) for p in files(root) if p.name!=RECEIPT}
    atomic(root/RECEIPT,{'schema':1,'files':entries})

def remember_previous(home,current,next_slot):
    home=Path(home).resolve();base=home/'.updates/versions';current=Path(current).resolve()
    if (current.name=='Unova-Together' and SLOT.fullmatch(current.parent.name)
            and current.parent.parent==base and current.parent.name!=next_slot
            and safe(current,home) and (current/'builds/current/melonDS.exe').is_file()):
        atomic(home/'.updates/rollback.json',{'slot':current.parent.name})

def share_binaries(root,reference):
    """Reuse identical immutable binaries on the same volume; copy fallback is intact."""
    root,reference=Path(root).resolve(),Path(reference).resolve();shared=0
    for directory in ('builds/current','launcher'):
        for target in files(root/directory):
            if target.suffix.lower() not in BINARIES or not safe(target,root):continue
            source=reference/target.relative_to(root)
            try:
                if not safe(source,reference) or not source.is_file() or source.stat().st_size!=target.stat().st_size or source.samefile(target):continue
                if digest(source)!=digest(target):continue
                pending=target.with_name(target.name+'.share-pending')
                if pending.exists() or linked(pending):continue
                size=target.stat().st_size;unique=target.stat().st_nlink==1
                try:os.link(source,pending);os.replace(pending,target)
                finally:
                    if pending.exists():pending.unlink()
                if unique:shared+=size
            except OSError:continue
    return shared

def running_paths():
    paths=[Path(sys.executable).resolve()]
    if os.name!='nt':return paths
    command="Get-CimInstance Win32_Process -Filter \"Name = 'melonDS.exe' OR Name = 'Unova Together.exe' OR Name = 'Pokemon Together.exe' OR Name = 'Pokemon Together Bootstrap.exe' OR Name = 'Repair-Launcher.exe'\" | Select-Object Name,ExecutablePath | ConvertTo-Json -Compress"
    result=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,text=True,timeout=12,creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode or result.stderr.strip():raise OSError('Could not check running installations; cleanup was skipped.')
    rows=json.loads(result.stdout) if result.stdout.strip() else []
    if isinstance(rows,dict):rows=[rows]
    if any(not row.get('ExecutablePath') for row in rows):raise OSError('A running installation could not be identified; cleanup was skipped.')
    paths.extend(Path(row['ExecutablePath']).resolve() for row in rows)
    return paths

@contextmanager
def installation_lock(home, conflict_message='Another installation is in progress. Try cleanup again when it finishes.'):
    updates=home/'.updates'
    if not safe(updates,home):raise ValueError('Unsafe update folder.')
    updates.mkdir(parents=True,exist_ok=True);lock=updates/'install.lock'
    if not safe_managed_path(updates,home) or not safe_managed_path(lock,home):
        raise ValueError('Unsafe installation lock.')
    with lock.open('a+b') as guard:
        if guard.tell()==0:guard.write(b'0');guard.flush()
        guard.seek(0)
        if os.name=='nt':
            import msvcrt
            try:msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
            except OSError as exc:raise ValueError(conflict_message) from exc
            try:yield
            finally:guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            try:fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except OSError as exc:raise ValueError(conflict_message) from exc
            try:yield
            finally:fcntl.flock(guard,fcntl.LOCK_UN)

def entries(root,reference):
    """Legacy receipts prove runtime ownership; identical launcher binaries prove reuse."""
    receipt=root/RECEIPT
    if receipt.is_file():
        record=read(receipt)
        if record.get('schema')!=1:raise ValueError('Unknown installation record.')
        return record['files'],False
    record=read(root/'.launcher-integrity.json')['files']
    owned={name:value for name,value in record.items() if name.startswith('builds/current/') and Path(name).suffix.lower() in {'.exe','.dll'}}
    for path in files(root/'launcher'):
        other=reference/path.relative_to(root)
        if path.suffix.lower() in BINARIES and safe(other,reference) and other.is_file():
            try:
                if path.stat().st_size==other.stat().st_size and digest(path)==digest(other):owned[path.relative_to(root).as_posix()]=digest(path)
            except OSError:pass
    return owned,True

def _progress(callback, **event):
    if callback is None:return
    try:callback(event)
    except Exception:pass

def cleanup(home,processes=None,recheck=False,progress=None):
    home=Path(home).resolve()
    with installation_lock(home):return _cleanup(home,processes,recheck,progress)

def _cleanup(home,processes,recheck,progress=None):
    from unova_updater import active_root
    base=home/'.updates/versions';active=active_root(home,allow_missing=True)
    report={'removedBytes':0,'reclaimedBytes':0,'sharedBytes':0,'removedFiles':0,'prunedSlots':[],'keptSlots':[],'skipped':[]}
    if not base.exists():
        _progress(progress,phase='scan',stage='complete',total=0,completed=0)
        return report
    if not safe(base,home) or not safe(active,home):raise ValueError('Unsafe installation path. Nothing was cleaned.')
    if not (active/'builds/current/melonDS.exe').is_file():raise ValueError('Active installation is incomplete. Repair it before cleaning older builds.')
    running=running_paths() if processes is None else [Path(p).resolve() for p in processes]
    slots=[p for p in base.iterdir() if SLOT.fullmatch(p.name) and p.is_dir() and safe(p,home)]
    keep={active.parent.name} if active.parent.parent==base else set()
    rollback=None
    try:
        candidate=read(home/'.updates/rollback.json')['slot']
        if SLOT.fullmatch(candidate) and candidate not in keep and (base/candidate/'Unova-Together/builds/current/melonDS.exe').is_file():rollback=candidate
    except (OSError,ValueError,KeyError,TypeError):pass
    if rollback is None:
        eligible=[p for p in slots if p.name not in keep and (p/'Unova-Together/builds/current/melonDS.exe').is_file()]
        if eligible:rollback=max(eligible,key=lambda p:(tuple(int(x) for x in p.name.split('-')[0].split('.')),p.stat().st_mtime_ns)).name
    if rollback:keep.add(rollback)
    for slot in slots:
        if any(p.is_relative_to(slot.resolve()) for p in running):keep.add(slot.name)
    report['keptSlots']=sorted(keep)
    _progress(progress,phase='scan',stage='start',slots=len(slots))
    if rollback and safe(base/rollback,home):report['sharedBytes']=share_binaries(active,base/rollback/'Unova-Together')
    plans=[];slot_state={};scanned=0
    for slot in slots:
        if slot.name in keep:continue
        root=slot/'Unova-Together'
        if not safe(root,home):continue
        if not recheck:
            try:
                if read(root/'.storage-pruned.json').get('schema')==1:continue
            except (OSError,ValueError,TypeError):pass
        try:owned,legacy=entries(root,active)
        except (OSError,ValueError,KeyError,TypeError):report['skipped'].append(slot.name+': no valid installation record');continue
        if not isinstance(owned,dict) or len(owned)>10000:report['skipped'].append(slot.name+': invalid file list');continue
        slot_state[slot.name]={'root':root,'removed':0,'locked':False}
        for name,expected in owned.items():
            scanned+=1
            if not isinstance(name,str) or not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):continue
            relative=PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:continue
            path=root/name
            if path.suffix.lower() in PRIVATE or re.fullmatch(r'\.ml\d+',path.suffix.lower()):continue
            # Old standalone EXEs test this sentinel before delegating to the current build.
            if name in {'launcher/Unova Together.exe','builds/current/VERSION.txt'}:continue
            if not safe(path,home) or not path.is_file():continue
            try:
                if digest(path)==expected:plans.append((slot.name,path,expected))
            except OSError:slot_state[slot.name]['locked']=True
            if scanned%25==0:
                _progress(progress,phase='scan',stage='checking',slots=len(slots),scanned=scanned,slot=slot.name)
    _progress(progress,phase='delete',stage='start',total=len(plans),completed=0)
    completed=0
    for slot_name,path,expected in plans:
        state=slot_state[slot_name]
        try:
            if not safe(path,home) or not path.is_file() or digest(path)!=expected:
                completed+=1
                _progress(progress,phase='delete',stage='checked',total=len(plans),completed=completed,path=str(path))
                continue
            stat=path.stat();path.unlink();state['removed']+=1;report['removedFiles']+=1;report['removedBytes']+=stat.st_size
            if stat.st_nlink==1:report['reclaimedBytes']+=stat.st_size
            _progress(progress,phase='delete',stage='deleted',total=len(plans),completed=completed+1,path=str(path))
        except OSError:
            state['locked']=True
            _progress(progress,phase='delete',stage='skipped',total=len(plans),completed=completed+1,path=str(path),reason='File is in use or could not be removed.')
        completed+=1
    for slot_name,state in slot_state.items():
        root=state['root'];slot=root.parent
        if state['removed']:report['prunedSlots'].append(slot_name)
        if not state['locked']:atomic(root/'.storage-pruned.json',{'schema':1})
        directories=[]
        for directory,dirs,names in os.walk(slot):
            dirs[:]=[name for name in dirs if not linked(Path(directory)/name)]
            directories.append(Path(directory))
        for path in reversed(directories):
            if path in (slot,root) or not safe(path,home):continue
            try:
                path.rmdir()
                _progress(progress,phase='delete',stage='directory',total=len(plans),completed=completed,path=str(path))
            except OSError:pass
    atomic(home/'.updates/storage-last.json',report)
    _progress(progress,phase='delete',stage='complete',total=len(plans),completed=completed)
    return report

def summary(report):
    recovered=(report['reclaimedBytes']+report['sharedBytes'])/(1024*1024)
    return (f'Freed approximately {recovered:,.1f} MB from old installations. '
            f"Cleaned {len(report['prunedSlots'])} old build(s). Active, rollback and running builds are kept. "
            'Saves, ROMs, backups and unrecognised or modified files are kept.'+
            (f" Skipped {len(report['skipped'])} build(s) without a valid installation record." if report['skipped'] else ''))
