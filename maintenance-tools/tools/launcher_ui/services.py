"""Player-facing launcher tools by mvq1303 / WhatWasMissing."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, ipaddress, json, os, platform, re, socket, uuid, zipfile, threading, time, zlib
import urllib.request
from . import versioning
from . import player_model_preferences as model_preferences


class RelayCompatibilityError(ValueError):
    def __init__(self, message, *, replaceable_local=False, relay_build=None):
        super().__init__(message)
        self.replaceable_local=replaceable_local
        self.relay_build=relay_build

GUIDES=('PLAYER_GUIDE.md','KNOWN_ISSUES.md','TAILSCALE_COOP.md','UDP_SERVER_GUIDE.md','LAUNCHER.md','COMPANION_INTERACTIONS.md','COOP_TOOLS.md','RELEASE_CHECKS_1.0.6.md','FEATURES.md','ROADMAP.md')
MAX_BACKUP_FILES=32
MAX_BACKUP_FILE_SIZE=16*1024*1024
MAX_BACKUP_MANIFEST_SIZE=16384
MAX_BACKUP_ARCHIVE_SIZE=64*1024*1024

def _safe_guide_path(path,home):
    import unova_storage as storage
    try:return storage.safe_managed_path(path,home)
    except (OSError,RuntimeError):return False

def refresh_guides(home):
    """Pin a bounded text-only guide set to one official GitHub commit."""
    from unova_updater import REPO
    home=Path(home).resolve();directory=home/'.updates/guides'
    if not _safe_guide_path(directory,home):raise ValueError('Unsafe guide cache path.')
    def fetch(url,host,limit):
        request=urllib.request.Request(url,headers={'User-Agent':'Unova-Together-guides'})
        with urllib.request.urlopen(request,timeout=8) as response:
            from urllib.parse import urlparse
            final=urlparse(response.geturl())
            if final.scheme!='https' or final.hostname!=host:raise ValueError('Unexpected guide download location')
            data=response.read(limit+1)
            if len(data)>limit:raise ValueError('Guide download too large')
            return data.decode('utf-8')
    reference=json.loads(fetch('https://api.github.com/repos/'+REPO+'/git/ref/heads/main','api.github.com',65536))
    if reference.get('object',{}).get('type')!='commit':raise ValueError('Invalid guide branch reference')
    commit=reference['object']['sha']
    if not isinstance(commit,str) or not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Invalid guide revision')
    directory.mkdir(parents=True,exist_ok=True)
    if not _safe_guide_path(directory,home):raise ValueError('Unsafe guide cache path.')
    target=directory/(commit+'.json')
    if not _safe_guide_path(target,home):raise ValueError('Unsafe guide cache path.')
    if not target.is_file():
        docs={name:fetch('https://raw.githubusercontent.com/'+REPO+'/'+commit+'/docs/'+name,'raw.githubusercontent.com',131072) for name in GUIDES}
        if any(not text.strip() or '\x00' in text for text in docs.values()):raise ValueError('Invalid guide text')
        if not _safe_guide_path(target,home):raise ValueError('Unsafe guide cache path.')
        prefs.atomic_write(target,lambda stream:stream.write(json.dumps(docs).encode('utf-8')))
    marker=directory/'active.json'
    if not _safe_guide_path(marker,home):raise ValueError('Unsafe guide cache path.')
    prefs.atomic_write(marker,lambda stream:stream.write(json.dumps({'commit':commit}).encode('utf-8')))
    return commit

def cached_guide(home,name):
    if name not in GUIDES:raise ValueError('Unknown setup guide')
    home=Path(home).resolve();directory=home/'.updates/guides'
    try:
        if not _safe_guide_path(directory,home):return None
        marker=directory/'active.json'
        if not _safe_guide_path(marker,home):return None
        commit=json.loads(marker.read_text())['commit']
        if not re.fullmatch('[0-9a-f]{40}',commit):return None
        target=directory/(commit+'.json')
        if not _safe_guide_path(target,home):return None
        if target.stat().st_size>1000000:return None
        text=json.loads(target.read_text(encoding='utf-8'))[name]
        if not isinstance(text,str) or len(text.encode('utf-8'))>131072 or '\x00' in text:return None
        guide=directory/name
        if not _safe_guide_path(guide,home):return None
        prefs.atomic_write(guide,lambda stream:stream.write(text.encode('utf-8')))
        return guide
    except (OSError,ValueError,KeyError,TypeError):return None

def check_relay(values,start_local,restart_local=None):
    """Probe the actual protocol; only a refused loopback endpoint may be hosted here."""
    value=network(values)
    try:return probe(value)
    except RelayCompatibilityError as exc:
        if value['host'].lower() not in ('127.0.0.1','localhost') or not exc.replaceable_local:
            raise
        if restart_local is None:
            raise ValueError(str(exc)+' Stop the old local relay and check again.') from exc
        restart_local(value['port'])
        deadline=time.monotonic()+8
        while True:
            try:return 'Outdated local relay replaced. '+probe(value)
            except (OSError,ValueError) as retry_error:
                if time.monotonic()>=deadline:
                    raise ValueError('The old local relay was stopped, but the updated relay did not become ready. Check transfer/presence-relay.log and try again.') from retry_error
                time.sleep(.15)
    except ValueError as exc:
        if value['host'].lower() not in ('127.0.0.1','localhost') or 'No presence relay is listening' not in str(exc):raise
        start_local(value['port'])
        deadline=time.monotonic()+8
        while True:
            try:return 'Local relay started. '+probe(value)
            except ValueError:
                if time.monotonic()>=deadline:raise
                time.sleep(.15)
from . import preferences as prefs

def profile(rom='',save_dir='',name='Player',label='Main game'):
    return {'id':uuid.uuid4().hex,'label':label[:40],'rom':rom,'save_dir':save_dir,'player':name[:32],
            'preferences':{},'lan_role':'Host','lan_slots':16,'join_host':'','network':{'mode':'Local LAN','host':'127.0.0.1','port':8765,'room':'pokeplay-test'}}

def normalize(item):
    clean=profile();clean['id']=item['id']
    for key,limit in (('rom',2048),('save_dir',2048),('label',40),('player',32)):
        value=item.get(key,clean[key]);clean[key]=value[:limit] if isinstance(value,str) else clean[key]
    clean['preferences']=normalize_preferences(item.get('preferences',{}))
    try:clean['network']=network(item.get('network',clean['network']))
    except (ValueError,TypeError,AttributeError):pass
    clean['lan_role']=item.get('lan_role') if item.get('lan_role') in ('Host','Join') else ('Host' if clean['network']['host'].lower() in ('localhost','127.0.0.1') else 'Join')
    try:clean['lan_slots']=max(2,min(16,int(item.get('lan_slots',16))))
    except (TypeError,ValueError):clean['lan_slots']=16
    previous=item.get('join_host',clean['network']['host'] if clean['lan_role']=='Join' else '')
    clean['join_host']=previous if isinstance(previous,str) and len(previous)<=253 else ''
    return clean

def normalize_preferences(values):
    if not isinstance(values,dict):return {}
    clean={k:v for k,v in values.items() if (k in ('pause','filter','area_scenery','companion_interactions','reduced_follower_motion','coop_exp_suppression') and type(v) is bool) or (k=='volume' and type(v) is int and 0<=v<=100) or (k=='player_model' and type(v) is int and 0<=v<=65535)}
    clean.update(model_preferences.normalize_settings(values))
    return clean

def save_files(item):
    rom=Path(item.get('rom',''));directory=Path(item.get('save_dir') or rom.parent)
    if not rom.name or not directory.is_dir():return []
    pattern=re.compile(re.escape(rom.stem)+r'(?:\.\d+)?\.(?:sav|save|dsv)$',re.I)
    return sorted(p for p in directory.iterdir() if pattern.fullmatch(p.name) and p.is_file() and not p.is_symlink())

def _safe_backup_path(path,home):
    import unova_storage as storage
    try:return storage.safe_managed_path(path,home)
    except (OSError,RuntimeError):return False

def _save_backup_directory(home,item):
    identifier=str(item.get('id','')) if isinstance(item,dict) else ''
    if not re.fullmatch(r'[a-f0-9]{32}',identifier):raise ValueError('Invalid profile identifier.')
    home=Path(home).resolve();folder=home/'save-backups'/identifier
    if not _safe_backup_path(folder,home):raise ValueError('Unsafe save backup path.')
    return home,folder

def backup(home,item,reason='manual'):
    home,folder=_save_backup_directory(home,item)
    files=save_files(item)
    if not files:return None
    if len(files)>MAX_BACKUP_FILES:raise ValueError(f'Too many save files to back up (maximum {MAX_BACKUP_FILES}).')
    folder.mkdir(parents=True,exist_ok=True)
    if not _safe_backup_path(folder,home):raise ValueError('Unsafe save backup path.')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    target=folder/(stamp+'-'+reason+'-'+uuid.uuid4().hex[:6]+'.zip')
    manifest={'profile':item['id'],'created':datetime.now(timezone.utc).isoformat(),'reason':reason,'files':[]}
    total_size=0
    pending=target.with_suffix('.pending')
    try:
        if not _safe_backup_path(folder,home) or not _safe_backup_path(pending,home) or not _safe_backup_path(target,home):
            raise ValueError('Unsafe save backup path.')
        with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as bundle:
            for path in files:
                if path.stat().st_size>MAX_BACKUP_FILE_SIZE:raise ValueError('Save exceeds backup size limit: '+path.name)
                data=path.read_bytes()
                if len(data)>MAX_BACKUP_FILE_SIZE:raise ValueError('Save exceeds backup size limit: '+path.name)
                total_size+=len(data)
                if total_size>MAX_BACKUP_ARCHIVE_SIZE-MAX_BACKUP_MANIFEST_SIZE:
                    raise ValueError('Combined saves exceed backup size limit.')
                bundle.writestr(path.name,data)
                manifest['files'].append({'name':path.name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            manifest_data=json.dumps(manifest,indent=2).encode('utf-8')
            if len(manifest_data)>MAX_BACKUP_MANIFEST_SIZE:raise ValueError('Backup manifest exceeds size limit.')
            if total_size+len(manifest_data)>MAX_BACKUP_ARCHIVE_SIZE:raise ValueError('Combined saves exceed backup size limit.')
            bundle.writestr('manifest.json',manifest_data)
        if not _safe_backup_path(folder,home) or not _safe_backup_path(pending,home) or not _safe_backup_path(target,home):
            raise ValueError('Unsafe save backup path.')
        os.replace(pending,target)
    finally:
        if pending.exists():pending.unlink()
    return target

def backups(home,item):
    try:home,folder=_save_backup_directory(home,item)
    except (ValueError,TypeError):return []
    if not folder.is_dir():return []
    return sorted((path for path in folder.glob('*.zip') if _safe_backup_path(path,home)),reverse=True)

def backup_label(path):
    match=re.fullmatch(r'(\d{8}-\d{6})-(.+)-[a-f0-9]{6}',Path(path).stem)
    if not match:return Path(path).stem
    try:stamp=datetime.strptime(match[1],'%Y%m%d-%H%M%S').strftime('%d %b %Y, %H:%M:%S UTC')
    except ValueError:return Path(path).stem
    reason={'manual':'Manual backup','before-restore':'Before restore','before-update':'Before update'}.get(match[2],match[2].replace('-',' ').capitalize())
    return stamp+' · '+reason

def restore(home,item,archive):
    home,allowed=_save_backup_directory(home,item)
    archive=Path(os.path.abspath(archive))
    if (archive.parent!=allowed or archive.suffix.lower()!='.zip' or
            not _safe_backup_path(allowed,home) or not _safe_backup_path(archive,home) or not archive.is_file()):
        raise ValueError('Select a safe backup for this profile.')
    directory=Path(item.get('save_dir') or Path(item['rom']).parent).resolve()
    payload=[]
    with zipfile.ZipFile(archive) as bundle:
        entries=bundle.infolist()
        if len(entries)>MAX_BACKUP_FILES+1 or sum(entry.file_size for entry in entries)>MAX_BACKUP_ARCHIVE_SIZE:raise ValueError('Backup exceeds size limits.')
        if len({entry.filename for entry in entries})!=len(entries):raise ValueError('Backup contains duplicate files.')
        members={entry.filename:entry for entry in entries}
        manifest_info=members.get('manifest.json')
        if manifest_info is None or manifest_info.is_dir() or manifest_info.file_size>MAX_BACKUP_MANIFEST_SIZE:raise ValueError('Invalid backup manifest.')
        def read_member(info):
            if info.flag_bits&1 or info.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):
                raise ValueError('Backup contains an unsupported file.')
            try:return bundle.read(info)
            except (zipfile.BadZipFile,RuntimeError,NotImplementedError,EOFError,zlib.error) as exc:
                raise ValueError('Backup is damaged or cannot be read.') from exc
        try:manifest=json.loads(read_member(manifest_info))
        except (UnicodeError,json.JSONDecodeError) as exc:raise ValueError('Invalid backup manifest.') from exc
        if not isinstance(manifest,dict):raise ValueError('Invalid backup manifest.')
        if manifest.get('profile')!=item['id']:raise ValueError('Backup belongs to a different profile.')
        files=manifest.get('files')
        if not isinstance(files,list) or not 1<=len(files)<=MAX_BACKUP_FILES:raise ValueError('Invalid backup manifest.')
        pattern=re.escape(Path(item['rom']).stem)+r'(?:\.\d+)?\.(?:sav|save|dsv)'
        validated=[];seen=set()
        for entry in files:
            if not isinstance(entry,dict):raise ValueError('Invalid backup manifest.')
            name=entry.get('name');size=entry.get('size');checksum=entry.get('sha256')
            if (not isinstance(name,str) or type(size) is not int or not 0<=size<=MAX_BACKUP_FILE_SIZE or
                    not isinstance(checksum,str) or not re.fullmatch(r'[0-9a-f]{64}',checksum) or name in seen):
                raise ValueError('Invalid backup manifest.')
            if not re.fullmatch(pattern,name,re.I):raise ValueError('Backup contains an unexpected file.')
            info=members.get(name)
            if info is None or info.is_dir() or info.file_size!=size:raise ValueError('Backup save file is missing or has the wrong size.')
            seen.add(name);validated.append((name,size,checksum,info))
        if set(members)!=(seen|{'manifest.json'}):raise ValueError('Backup contains unexpected files.')
        for name,size,checksum,info in validated:
            data=read_member(info)
            if len(data)!=size or hashlib.sha256(data).hexdigest()!=checksum:raise ValueError('Backup checksum mismatch.')
            target=directory/name
            if target.is_symlink() or not target.resolve().is_relative_to(directory):raise ValueError('Unsafe save destination.')
            payload.append((target,data))
    backup(home,item,'before-restore');directory.mkdir(parents=True,exist_ok=True)
    for path,data in payload:
        prefs.atomic_write(path,lambda stream:stream.write(data))
    return len(payload)

def network(values):
    host=values.get('host','').strip();room=values.get('room','').strip()
    try:port=int(values.get('port',8765))
    except (ValueError,TypeError):raise ValueError('Relay port must be a number.')
    if not host or len(host)>253 or any(c.isspace() for c in host) or '/' in host or ':' in host:raise ValueError('Enter a hostname or IPv4 address, without a URL or port.')
    if not 1<=port<=65535:raise ValueError('Relay port must be 1–65535.')
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',room):raise ValueError('Room uses 1–64 letters, numbers, dots, underscores or hyphens.')
    mode=values.get('mode','Local LAN')
    if mode not in ('Local LAN','Internet UDP','Tailscale backup','Solo'):raise ValueError('Choose a supported play mode.')
    return {'host':host,'port':port,'room':room,'mode':mode}

def probe(values):
    values=network(values)
    # Socket timeout does not bound DNS lookup on Windows. Resolve in a daemon
    # thread and cap that wait too; a bad address must not keep Tools busy.
    done=threading.Event();addresses=[];errors=[]
    def resolve():
        try:addresses.extend(socket.getaddrinfo(values['host'],values['port'],socket.AF_INET,socket.SOCK_STREAM))
        except OSError as exc:errors.append(exc)
        finally:done.set()
    threading.Thread(target=resolve,daemon=True).start()
    if not done.wait(3):raise TimeoutError('Hostname lookup timed out. Check the relay address.')
    if errors:raise errors[0]
    if not addresses:raise ValueError('Relay hostname has no IPv4 address.')
    try:
        connection=socket.create_connection(addresses[0][4],timeout=3)
    except OSError as exc:
        if getattr(exc,'winerror',None)==10061 or isinstance(exc,ConnectionRefusedError):
            raise ValueError(f"Connection saved. No presence relay is listening at {values['host']}:{values['port']}. Start the presence relay on that computer and check its port. This is separate from native LAN / the UDP server.") from exc
        raise ValueError(f"Connection saved. Could not reach presence relay {values['host']}:{values['port']}: {exc}") from exc
    with connection:
        connection.settimeout(3)
        connection.sendall((json.dumps({'type':'join','version':1,'name':'launcher-check','room':'launcher-check-'+uuid.uuid4().hex[:10]})+'\n').encode())
        data=b''
        while b'\n' not in data and len(data)<=8192:
            part=connection.recv(min(1024,8193-len(data)))
            if not part:break
            data+=part
        if len(data)>8192:raise ValueError('Relay response exceeds size limit.')
        try:message=json.loads(data.split(b'\n')[0])
        except (UnicodeError,json.JSONDecodeError) as exc:raise ValueError('Address responds, but it is not a compatible presence relay.') from exc
        if not isinstance(message,dict) or message.get('type')!='welcome' or message.get('version')!=1:
            raise ValueError('Address responds, but it is not a compatible presence relay.')
        expected_build=versioning.current_version()
        relay_build=message.get('buildVersion')
        if not isinstance(relay_build,str) or not relay_build:
            raise RelayCompatibilityError(
                'The relay does not report its build version. Update and restart the relay host.',
                replaceable_local=True)
        try:
            older=versioning.numbers(relay_build)<versioning.numbers(expected_build)
        except ValueError:
            # An unknown build can only be replaced on loopback, and the
            # process helper independently verifies ownership before stopping it.
            older=True
        if relay_build!=expected_build:
            raise RelayCompatibilityError(
                f'Relay build {relay_build} does not match this launcher ({expected_build}). Update and restart the relay host.',
                replaceable_local=older,relay_build=relay_build)
        if message.get('fieldZonePresence') is not True:
            raise RelayCompatibilityError(
                f'Relay build {relay_build} is missing field-zone sharing. Restart the relay host after updating.',
                replaceable_local=True,relay_build=relay_build)
    return f'Presence relay reachable (build {expected_build}). Native LAN/UDP pairing must still be checked in-game.'

def save_connection(runtime,values,player='Player'):
    """Persist independently of reachability; native panels watch this file."""
    values=network(values)
    request=dict(values,player=str(player).strip()[:32] or 'Player',revision=uuid.uuid4().hex)
    prefs.atomic(Path(runtime)/'launcher-connection.json',json.dumps(request))
    return request

def checks(root,item):
    runtime=Path(root)/'builds/current';messages=[]
    if not (runtime/'melonDS.exe').is_file():messages.append('BLOCK: Emulator missing. Use Repair installation.')
    rom=Path(item.get('rom',''))
    if not rom.is_file() or rom.suffix.lower()!='.nds':messages.append('BLOCK: Choose an existing .nds ROM.')
    else:
        info=prefs.identify(rom)
        messages.append('ROM: '+(info['profile'] if info else 'Unreviewed ROM — compatibility cannot be confirmed.'))
    doc=prefs.read_document(runtime)
    if not doc.get('LimitFPS',True) or float(doc.get('TargetFPS',60))>61:messages.append('CHECK: Frame limit is off or above 60 FPS. Use normal speed before co-op.')
    if doc.get('PauseLostFocus',False):messages.append('CHECK: Pause on focus loss is enabled. Leave it off for co-op.')
    messages+=['IN-GAME: Turn C-Gear wireless off; active state cannot be read before launch.',
               'PARTNER: Use the same mod version and ROM revision. Partner state cannot be verified before connecting.']
    return messages

def integrity(root):
    root=Path(root).resolve();manifest=root/'.launcher-integrity.json'
    if not manifest.exists():return 'No installation checksum record. Repair creates one from the verified download.'
    if manifest.stat().st_size>1024*1024:raise ValueError('Installation checksum record is too large.')
    try:record=json.loads(manifest.read_text(encoding='utf-8'))
    except (UnicodeError,json.JSONDecodeError) as exc:raise ValueError('Invalid installation checksum record.') from exc
    if not isinstance(record,dict):raise ValueError('Invalid installation checksum record.')
    files=record.get('files')
    if not isinstance(files,dict) or not 0<len(files)<=4096:raise ValueError('Invalid installation checksum record.')
    changed=[]
    for name,expected in files.items():
        if not isinstance(name,str) or not isinstance(expected,str) or not re.fullmatch('[a-f0-9]{64}',expected):raise ValueError('Invalid installation checksum entry.')
        path=root/name
        if not path.resolve().is_relative_to(root) or path.suffix.lower() not in {'.exe','.dll'}:raise ValueError('Invalid installation checksum entry.')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:changed.append(name)
    return ('Verified '+str(len(files))+' game files against the installation record.' if not changed else
            'Missing or changed files: '+', '.join(changed[:10])+'. Use Repair game files.')

def diagnostics(root,destination,home=None):
    """Export bounded, redacted text logs only, never dumps, saves or ROMs."""
    root=Path(root).resolve();destination=Path(destination)
    reports={'platform':platform.platform(),'launcher':'Unova Together by mvq1303 / WhatWasMissing'}
    runtime=root/'builds/current'
    if (runtime/'VERSION.txt').is_file():reports['version']=(runtime/'VERSION.txt').read_text(errors='replace')[:1024]
    if (runtime/'melonDS.exe').is_file():reports['emulator_sha256']=hashlib.sha256((runtime/'melonDS.exe').read_bytes()).hexdigest()
    files=[];home=Path(home).resolve() if home else root
    for directory in dict.fromkeys((root/'transfer',home/'transfer',runtime/'diagnostics')):
        if directory.is_dir():
            for path in sorted(directory.rglob('*.log')):
                if path.is_file() and not path.is_symlink() and (path.resolve().is_relative_to(root) or path.resolve().is_relative_to(home)):files.append(path)
    def redact(text):
        text=re.sub(r'(?im)(\b(?:proxy-)?authorization\s*[:=]\s*)[^\r\n]+',r'\1[REDACTED]',text)
        text=re.sub(r'''(?i)(["']?(?:access[_ -]?key|api[_ -]?key|token|password|secret|authorization|cookie)["']?\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;}]+)''',r'\1[REDACTED]',text)
        text=re.sub(r'(?:[A-Za-z]:[\\/]|/Users/|/home/)\S+', '[LOCAL PATH]',text)
        def redact_ip(match):
            value=match.group(0);candidate=value.strip('[]').split('%',1)[0]
            try:ipaddress.ip_address(candidate)
            except ValueError:return value
            return '[IP]'
        text=re.sub(r'(?<![\w.])\[?[0-9A-Fa-f:.]+(?:%[0-9A-Za-z_.-]+)?\]?(?![\w.])',redact_ip,text)
        return re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b','[IP]',text)
    def write_report(stream):
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr('summary.json',json.dumps(reports,indent=2))
            for index,path in enumerate(files[:20]):
                with path.open('rb') as handle:handle.seek(max(0,path.stat().st_size-65536));data=handle.read(65536)
                bundle.writestr('logs/'+str(index+1)+'.log',redact(data.decode('utf-8',errors='replace')))
            bundle.writestr('README.txt','Text logs are automatically redacted; review before sharing. No ROMs, saves, RAM dumps, launcher profiles or credentials are included.')
    return prefs.atomic_write(destination,write_report)
