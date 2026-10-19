"""Unova Together by mvq1303: official GitHub, side-by-side verified updates."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import threading
import urllib.parse
import urllib.request
import zipfile
import uuid

REPO = 'WhatWasMissing/Unova-Together'
API = f'https://api.github.com/repos/{REPO}/releases?per_page=30'
PATCHNOTES_URL = f'https://raw.githubusercontent.com/{REPO}/main/patchnotes/index.json'
MAX_ARCHIVE = 768 * 1024 * 1024
MAX_EXPANDED = 1536 * 1024 * 1024

def version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r'v?(\d{1,4})\.(\d{1,4})\.(\d{1,4})', value)
    if not match:
        raise ValueError('Unsupported release version')
    return tuple(map(int, match.groups()))

def asset_url(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError('Update is not an official GitHub release asset')
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise ValueError('Update is not an official GitHub release asset') from exc
    if (parsed.scheme != 'https' or parsed.hostname != 'github.com' or
            parsed.username or parsed.password or port or
            not parsed.path.lower().startswith('/' + REPO.lower() + '/releases/download/') or
            parsed.query or parsed.fragment):
        raise ValueError('Update is not an official GitHub release asset')
    return value

def _open(url: str):
    request = urllib.request.Request(url, headers={'User-Agent': 'Unova-Together-Launcher',
                                                  'Accept': 'application/vnd.github+json'})
    return urllib.request.urlopen(request, timeout=30)

def fetch_releases(opener=_open) -> list:
    with opener(API) as response:
        raw = response.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('Release response is too large')
    releases = json.loads(raw)
    if not isinstance(releases, list):
        raise ValueError('Invalid GitHub release response')
    return releases


def latest_release(opener=_open) -> dict:
    return select_latest(fetch_releases(opener))


def select_latest(releases: list) -> dict:
    candidates = []
    for item in releases:
        if not isinstance(item, dict) or item.get('draft') or not item.get('published_at'):
            continue
        try:
            numbers = version(item['tag_name'])
        except (KeyError, ValueError, TypeError):
            continue
        label = '.'.join(map(str, numbers))
        wanted = f'Unova-Together-{label}-Windows-x64.zip'
        sums = f'SHA256SUMS-Unova-Together-{label}.txt'
        raw_assets = item.get('assets')
        if not isinstance(raw_assets, list):
            continue
        assets: dict[str, list[dict]] = {}
        for asset in raw_assets:
            if not isinstance(asset, dict):
                continue
            name = asset.get('name')
            if isinstance(name, str):
                assets.setdefault(name, []).append(asset)
        if len(assets.get(wanted, [])) != 1 or len(assets.get(sums, [])) != 1:
            continue
        archive_asset = assets[wanted][0]
        checksum_asset = assets[sums][0]
        size = archive_asset.get('size')
        if type(size) is not int or not 0 < size <= MAX_ARCHIVE:
            continue
        try:
            archive_url = asset_url(archive_asset.get('browser_download_url'))
            checksum_url = asset_url(checksum_asset.get('browser_download_url'))
        except ValueError:
            continue
        candidates.append({'version': label, 'numbers': numbers, 'name': wanted, 'size': size,
                           'prerelease': bool(item.get('prerelease')),
                           'url': archive_url, 'sums': checksum_url})
    if not candidates:
        raise ValueError('No compatible Windows release is available')
    stable = [r for r in candidates if not r['prerelease']]
    return max(stable or candidates, key=lambda r: r['numbers'])


def release_news(releases: list) -> list[dict]:
    """Plain, bounded release notes. Never execute remote HTML or open supplied URLs."""
    news = []
    for item in releases[:30]:
        if not isinstance(item, dict) or item.get('draft') or not item.get('published_at'):
            continue
        try:
            numbers = version(item['tag_name'])
        except (KeyError, ValueError, TypeError):
            continue
        label = '.'.join(map(str, numbers))
        def clean(value, maximum):
            return ''.join(c for c in str(value or '') if c in '\n\t' or ord(c) >= 32)[:maximum]
        news.append({'version': label, 'title': clean(item.get('name') or 'Release '+label, 100),
                     'body': clean(item.get('body'), 16000),
                     'date': clean(item.get('published_at'), 10),
                     'url': f'https://github.com/{REPO}/releases/tag/v{label}'})
    return sorted(news, key=lambda n: version(n['version']), reverse=True)[:12]


def patch_note_news(items: list) -> list[dict]:
    """Validate the repository's versioned patch-note index for the launcher."""
    if not isinstance(items, list) or len(items) > 100:
        raise ValueError('Invalid patch notes index')
    news, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            numbers = version(item['version'])
        except (KeyError, TypeError, ValueError):
            continue
        label = '.'.join(map(str, numbers))
        filename = f'RELEASE_NOTES_{label}.md'
        if item.get('file') != filename or label in seen:
            continue
        title = ''.join(c for c in str(item.get('title') or 'What changed')
                        if c in '\n\t' or ord(c) >= 32)[:120].strip()
        body = ''.join(c for c in str(item.get('body') or '')
                       if c in '\n\t' or ord(c) >= 32)[:12000].strip()
        if not body:
            continue
        seen.add(label)
        news.append({'version': label, 'title': title or 'What changed', 'file': filename, 'body': body,
                     'date': '', 'url': f'https://github.com/{REPO}/blob/main/patchnotes/{filename}'})
    if not news:
        raise ValueError('No valid patch notes found')
    return sorted(news, key=lambda n: version(n['version']), reverse=True)


def fetch_patch_notes(opener=_open) -> list[dict]:
    request_url = PATCHNOTES_URL
    with opener(request_url) as response:
        final = urllib.parse.urlsplit(response.geturl()) if hasattr(response, 'geturl') else urllib.parse.urlsplit(request_url)
        if final.scheme != 'https' or final.hostname != 'raw.githubusercontent.com' or \
                final.path != f'/{REPO}/main/patchnotes/index.json':
            raise ValueError('Unexpected patch notes location')
        raw = response.read(512 * 1024 + 1)
    if len(raw) > 512 * 1024:
        raise ValueError('Patch notes index is too large')
    index = json.loads(raw)
    if not isinstance(index, dict) or type(index.get('schema')) is not int or index['schema'] != 1:
        raise ValueError('Unsupported patch notes index')
    return patch_note_news(index.get('notes'))


def launcher_feed(opener=_open) -> dict:
    # Patch notes live in the repository now, separately from GitHub Releases.
    # Fetch them even when the Releases API has been trimmed, rate-limited, or
    # temporarily unavailable so older notes remain readable on their own.
    try:
        releases = fetch_releases(opener)
    except (OSError, ValueError):
        releases = []
    try:
        news = fetch_patch_notes(opener)
        news_source = 'patchnotes'
    except (OSError, ValueError, json.JSONDecodeError):
        news = release_news(releases)
        news_source = 'releases-fallback'
    try:
        release = select_latest(releases)
    except ValueError:
        release = None
    if release is None and not news:
        raise ValueError('Could not load update information or patch notes')
    return {'release': release, 'news': news, 'newsSource': news_source}

def active_root(home: Path, allow_missing=False) -> Path:
    home = home.resolve()
    marker = home / '.updates/active.json'
    if not marker.exists():
        return home
    try:
        if marker.stat().st_size > 4096:
            raise ValueError('Invalid update state')
        item = json.loads(marker.read_text(encoding='utf-8'))
        if not isinstance(item, dict):
            raise ValueError('Invalid update state')
        label = '.'.join(map(str, version(item['version'])))
        slot=item.get('slot',label)
        if not isinstance(slot,str) or not re.fullmatch(re.escape(label)+r'(?:-repair-[a-f0-9]{12})?',slot):
            raise ValueError('Invalid update installation slot')
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
        if allow_missing:
            return home
        if isinstance(exc, ValueError):
            raise
        raise ValueError('Invalid update state') from exc
    root = home / '.updates/versions' / slot / 'Unova-Together'
    if not root.resolve().is_relative_to(home) or (not allow_missing and not (root / 'builds/current/melonDS.exe').is_file()):
        raise ValueError('Installed update is unavailable')
    return root

def local_version(root: Path) -> tuple[int, int, int]:
    text = (root / 'builds/current/VERSION.txt').read_text(encoding='utf-8-sig')
    match = re.search(r'\b(\d{1,4}\.\d{1,4}\.\d{1,4})\b', text)
    return version(match.group(1)) if match else (0, 0, 0)

def installed_version(home: Path):
    root=active_root(home,allow_missing=True)
    try:
        return local_version(root)
    except (OSError, UnicodeError, ValueError, TypeError):
        marker=Path(home)/'.updates/active.json'
        try:
            if marker.stat().st_size <= 4096:
                item=json.loads(marker.read_text(encoding='utf-8'))
                if isinstance(item,dict):return version(item.get('version'))
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
            pass
        return (0,0,0)

def checksum(raw: bytes, name: str) -> str:
    matches = []
    for line in raw.decode('utf-8-sig').splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?([^\r\n]+)', line)
        if match and match.group(2) == name:
            matches.append(match.group(1).lower())
    if len(matches) != 1:
        raise ValueError('Release checksum is missing or ambiguous')
    return matches[0]

def extract_verified(archive: Path, destination: Path, expected: str) -> Path:
    digest = hashlib.sha256()
    with archive.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != expected:
        raise ValueError('Download checksum mismatch; nothing was installed')
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        if len(entries) > 10000 or sum(e.file_size for e in entries) > MAX_EXPANDED:
            raise ValueError('Update archive exceeds size limits')
        seen = set()
        for entry in entries:
            name = entry.filename
            path = PurePosixPath(name)
            if ('\\' in name or ':' in name or path.is_absolute() or
                    '..' in path.parts or not path.parts or path.parts[0] != 'Unova-Together' or
                    any(part.endswith((' ', '.')) for part in path.parts) or
                    any(part.split('.')[0].upper() in {'CON','PRN','AUX','NUL',
                        *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))}
                        for part in path.parts)):
                raise ValueError('Unsafe archive path')
            identity = name.rstrip('/').casefold()
            if identity in seen or ((entry.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError('Duplicate or linked archive entry')
            seen.add(identity)
            if path.suffix.lower() in {'.nds','.gba','.sav','.save','.dsv','.ramdump','.ml1','.ml2','.ml8'}:
                raise ValueError('Update unexpectedly contains game/save files')
            target = destination.joinpath(*path.parts)
            if not target.resolve().is_relative_to(destination):
                raise ValueError('Archive escapes update folder')
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(entry) as source, target.open('xb') as out:
                    shutil.copyfileobj(source, out, 1024 * 1024)
    root = destination / 'Unova-Together'
    if not (root / 'builds/current/melonDS.exe').is_file():
        raise ValueError('Update has no emulator')
    return root

def install(home: Path, release: dict, cancel: threading.Event, progress, opener=_open) -> Path:
    home=home.resolve();updates=home/'.updates'
    _assert_safe_update_path(updates,home)
    updates.mkdir(exist_ok=True)
    _assert_safe_update_path(updates,home)
    lock=updates/'install.lock'
    _assert_safe_update_path(lock,home)
    # OS-owned locks release even if the launcher is terminated mid-download.
    with lock.open('a+b') as guard:
        if guard.tell()==0:guard.write(b'0');guard.flush()
        guard.seek(0)
        if os.name=='nt':
            import msvcrt
            try:msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
            except OSError as exc:raise ValueError('Another launcher is installing an update') from exc
            try:return _install_unlocked(home,release,cancel,progress,opener)
            finally:guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_UNLCK,1)
        import fcntl
        try:fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:raise ValueError('Another launcher is installing an update') from exc
        try:return _install_unlocked(home,release,cancel,progress,opener)
        finally:fcntl.flock(guard,fcntl.LOCK_UN)

def _assert_safe_update_path(path: Path, home: Path) -> None:
    """Refuse update paths that traverse reparse points or hard-linked metadata."""
    import unova_storage as storage
    if not storage.safe_managed_path(path, home):
        raise ValueError('Unsafe update path; nothing was installed')

def _install_unlocked(home: Path, release: dict, cancel: threading.Event, progress, opener=_open) -> Path:
    home = home.resolve()
    label = '.'.join(map(str, version(release['version'])))
    repairing=release.get('_repair') is True
    slot=label+'-repair-'+uuid.uuid4().hex[:12] if repairing else label
    current = active_root(home,allow_missing=True)
    updates = home / '.updates'
    _assert_safe_update_path(updates,home)
    updates.mkdir(exist_ok=True)
    versions = updates / 'versions'
    _assert_safe_update_path(versions,home)
    versions.mkdir(exist_ok=True)
    destination=versions / slot
    _assert_safe_update_path(destination,home)
    # Check the legacy fixed staging name for unsafe leftovers, but publish
    # activation metadata through the shared exclusive/unique staging writer.
    marker=updates / 'active.json.pending'
    active=updates / 'active.json'
    _assert_safe_update_path(marker,home)
    _assert_safe_update_path(active,home)
    if destination.exists():
        raise ValueError('This version is already installed; no files were replaced')
    if shutil.disk_usage(home).free < release['size'] * 3 + 128 * 1024 * 1024:
        raise ValueError('Not enough free disk space for a safe update')
    with opener(asset_url(release['sums'])) as response:
        sums = response.read(65537)
    if len(sums) > 65536:
        raise ValueError('Checksum file is too large')
    expected = checksum(sums, release['name'])
    with tempfile.TemporaryDirectory(prefix='install-', dir=updates) as temp:
        work = Path(temp)
        archive = work / 'release.zip'
        digest = hashlib.sha256()
        total = 0
        with opener(asset_url(release['url'])) as response, archive.open('xb') as output:
            while True:
                if cancel.is_set():
                    raise InterruptedError('Update cancelled; your installed version is unchanged')
                block = response.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                if total > release['size'] or total > MAX_ARCHIVE:
                    raise ValueError('Download exceeds the expected size')
                output.write(block); digest.update(block); progress(total, release['size'])
        if total != release['size'] or digest.hexdigest() != expected:
            raise ValueError('Incomplete or corrupt download; nothing was installed')
        if cancel.is_set():
            raise InterruptedError('Update cancelled')
        root = extract_verified(archive, work / 'unpacked', expected)
        record_integrity(root)
        old_config = current / 'builds/current/melonDS.toml'
        if old_config.exists():
            import unova_storage as storage
            storage.atomic_copy(old_config, root / 'builds/current/melonDS.toml', home)
        launcher=current/'launcher' if (current/'launcher').is_dir() else home/'launcher'
        if repairing and launcher.is_dir():
            # Repair game files without downgrading the launcher running it.
            shutil.copytree(launcher,root/'launcher',dirs_exist_ok=True)
        if local_version(root) != version(label):
            raise ValueError('Archive version differs from release')
        if cancel.is_set():
            raise InterruptedError('Update cancelled')
        import unova_storage as storage
        storage.share_binaries(root,current)
        storage.record_package(root)
        if cancel.is_set():raise InterruptedError('Update cancelled; your installed version is unchanged')
        storage.remember_previous(home,current,slot)
        _assert_safe_update_path(updates,home)
        _assert_safe_update_path(versions,home)
        _assert_safe_update_path(destination,home)
        _assert_safe_update_path(marker,home)
        _assert_safe_update_path(active,home)
        (work / 'unpacked').rename(destination)
        _assert_safe_update_path(marker,home)
        _assert_safe_update_path(active,home)
        storage.atomic(active, {'version': label,'slot':slot})
    return active_root(home)

def record_integrity(root: Path):
    root=Path(root).resolve();runtime=root/'builds/current'
    files={}
    for path in sorted(runtime.rglob('*')):
        if path.is_file() and not path.is_symlink() and path.suffix.lower() in {'.exe','.dll'}:
            files[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    import unova_storage as storage
    storage.atomic(root/'.launcher-integrity.json',{'files':files})
