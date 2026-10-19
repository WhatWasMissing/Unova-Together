"""Preserve client launcher entry points across updates. mvq1303 / WhatWasMissing."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import time
import uuid
from contextlib import contextmanager
import unova_updater as updates

PRODUCT = 'pokemon-together'
ENTRY = 'launcher-entry.json'
SIDECAR = '.launcher-home.json'
REPORT = 'launcher-migration.json'
BRIDGE = 'Pokemon Together Bootstrap.exe'


def read(path):
    path = Path(path)
    if path.stat().st_size > 8192:raise ValueError('Launcher record is too large.')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('schema') != 1 or data.get('product') != PRODUCT:
        raise ValueError('Invalid shared launcher record.')
    return data


def atomic(path, data):
    path = Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    pending = path.with_name(path.name+'.pending-'+uuid.uuid4().hex)
    try:
        pending.write_text(json.dumps(data,indent=2),encoding='utf-8')
        os.replace(pending,path)
    finally:
        pending.unlink(missing_ok=True)


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def active_launcher(home):
    home = Path(home).resolve();root = updates.active_root(home)
    launcher = root/'launcher/Pokemon Together.exe'
    info = json.loads((launcher.parent/'BUILD_INFO.json').read_text(encoding='utf-8'))
    if info.get('product') != PRODUCT or updates.version(info.get('version','')) < (1,0,8):
        raise ValueError('Install release 1.0.8 or newer through Updates before repairing the old launcher.')
    if not launcher.is_file():raise ValueError('The updated shared launcher is missing.')
    return root,launcher


def register_entry(home, executable, root):
    home = Path(home).resolve();executable = Path(executable).resolve();root = Path(root).resolve()
    # An update-slot executable is a destination, not the user's original shortcut.
    if executable.name != 'Pokemon Together.exe' or executable.is_relative_to(home/'.updates'):
        return
    record = home/'.updates'/ENTRY
    if record.exists():return
    atomic(record,{'schema':1,'product':PRODUCT,'entry':str(executable),'home':str(home)})


def validate_entry(entry, home, active):
    entry = Path(entry).absolute();home = Path(home).resolve()
    if entry.name != 'Pokemon Together.exe' or entry.is_symlink() or entry.parent.is_symlink():
        raise ValueError('Select the original shared Pokemon Together.exe launcher.')
    entry = entry.resolve()
    if entry == Path(active).resolve():
        raise ValueError('Select the old launcher used by your shortcut, rather than the executable inside the current update folder.')
    if entry.exists():
        try:known = (entry.parent/'VERSION.txt').read_text(encoding='utf-8').startswith('Pokemon Together Launcher ')
        except OSError:known = False
        try:known = known or read(entry.parent/SIDECAR)['home'] == str(home)
        except (OSError,ValueError,KeyError):pass
        if not known:raise ValueError('That file is not a recognised shared launcher installation.')
    elif entry != home/'launcher/Pokemon Together.exe':
        raise ValueError('The selected launcher no longer exists.')
    return entry


@contextmanager
def repair_lock(home):
    import unova_storage as storage
    home=Path(home).resolve();directory=home/'.updates'
    if not storage.safe_managed_path(directory,home):raise ValueError('Unsafe launcher repair folder.')
    directory.mkdir(parents=True,exist_ok=True);lock=directory/'launcher-migration.lock'
    if not storage.safe_managed_path(directory,home) or not storage.safe_managed_path(lock,home):
        raise ValueError('Unsafe launcher repair lock.')
    with lock.open('a+b') as guard:
        if guard.tell()==0:guard.write(b'0');guard.flush()
        guard.seek(0)
        if os.name=='nt':
            import msvcrt
            try:msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
            except OSError:raise ValueError('Another launcher repair is running.')
            try:yield
            finally:guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:yield
            finally:fcntl.flock(guard,fcntl.LOCK_UN)


def migrate(home, entry, source, *, timeout=0, status=lambda text:None):
    with repair_lock(home):return _migrate_unlocked(home,entry,source,timeout=timeout,status=status)


def _migrate_unlocked(home, entry, source, *, timeout=0, status=lambda text:None):
    home = Path(home).resolve();root,active = active_launcher(home)
    entry = validate_entry(entry,home,active);source = Path(source).resolve()
    if not source.is_file() or source == entry:raise ValueError('The launcher bootstrap is missing.')
    checksum = digest(source);sidecar = entry.parent/SIDECAR
    record = {'schema':1,'product':PRODUCT,'entry':str(entry),'home':str(home),'bridge_sha256':checksum}
    try:
        old_record = read(sidecar)
        if old_record.get('home') == str(home) and old_record.get('bridge_sha256') == digest(entry):
            atomic(home/'.updates'/ENTRY,old_record)
            atomic(home/'.updates'/REPORT,{**old_record,'state':'installed'})
            return entry
    except (OSError,ValueError):pass
    entry.parent.mkdir(parents=True,exist_ok=True)
    pending = entry.with_name('.launcher-update-'+uuid.uuid4().hex+'.exe')
    previous = sidecar.read_bytes() if sidecar.exists() else None
    shutil.copy2(source,pending)
    backup = None;deadline = time.monotonic()+timeout
    try:
        while True:
            try:
                if entry.exists():
                    backup = entry.with_name('Pokemon Together.before-migration-'+uuid.uuid4().hex[:12]+'.exe')
                    # Windows permits renaming many loaded executables. If a lock forbids
                    # it, leave the old entry intact and wait for its window to close.
                    os.replace(entry,backup)
                break
            except PermissionError:
                status('Close the old launcher window to finish. Your game can remain open.')
                if time.monotonic() >= deadline:raise ValueError('Close the old launcher and run Repair Launcher again.')
                time.sleep(.25)
        try:
            atomic(sidecar,record)
            os.replace(pending,entry)
        except Exception:
            if backup is not None and backup.exists() and not entry.exists():os.replace(backup,entry)
            if previous is None:sidecar.unlink(missing_ok=True)
            else:sidecar.write_bytes(previous)
            raise
        atomic(home/'.updates'/ENTRY,record)
        atomic(home/'.updates'/REPORT,{**record,'state':'installed','backup':str(backup) if backup else None})
        status('Repaired. Your existing launcher shortcut now opens the active release.')
        return entry
    finally:
        pending.unlink(missing_ok=True)


def bootstrap_target(executable, requested_home=None):
    executable = Path(executable).resolve()
    home = Path(requested_home) if requested_home else Path(read(executable.parent/SIDECAR)['home'])
    root,target = active_launcher(home)
    if target.resolve() == executable:raise ValueError('The launcher entry points to itself. Run Repair Launcher.')
    return Path(home).resolve(),root,target


def schedule(home, root, *, default_entry=False):
    home = Path(home).resolve();bridge = Path(root)/'launcher'/BRIDGE
    if Path(root).resolve()==home:return
    try:record = read(home/'.updates'/ENTRY)
    except (OSError,ValueError):
        if not default_entry:return
        record={'entry':str(home/'launcher/Pokemon Together.exe')}
    if not isinstance(record.get('entry'),str):return
    if not bridge.is_file():return
    env = dict(os.environ,PYINSTALLER_RESET_ENVIRONMENT='1')
    subprocess.Popen([str(bridge),'--migrate','--home',str(home),'--entry',record['entry'],'--timeout','120'],
                     cwd=root,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
