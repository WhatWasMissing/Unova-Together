"""Single-download Unova Together bootstrap. mvq1303 / WhatWasMissing."""
from pathlib import Path
import argparse, ctypes, json, os, shutil, subprocess, sys
import unova_updater as updates
import launcher_migration

def _assert_safe_bundle_path(path,home):
    import unova_storage as storage
    if not storage.safe_managed_path(path,home):
        raise ValueError('Unsafe installation path; nothing was installed')

def launcher_executable(root):
    path=Path(root)/'launcher/Pokemon Together.exe'
    if not path.is_file():raise ValueError('Cached shared launcher is missing. Remove this bundle slot and run again.')
    return path

def install_bundle(home,payload,metadata):
    home=Path(home).resolve();home.mkdir(parents=True,exist_ok=True)
    version='.'.join(map(str,updates.version(metadata['version'])))
    digest=metadata['sha256']
    if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('Invalid bundled checksum.')
    slot=version+'-repair-'+digest[:12]
    updates_dir=home/'.updates';_assert_safe_bundle_path(updates_dir,home)
    updates_dir.mkdir(exist_ok=True);_assert_safe_bundle_path(updates_dir,home)
    versions=updates_dir/'versions';_assert_safe_bundle_path(versions,home)
    versions.mkdir(exist_ok=True);_assert_safe_bundle_path(versions,home)
    target=versions/slot;root=target/'Unova-Together'
    _assert_safe_bundle_path(target,home)
    marker=updates_dir/'active.json';state=home/'.standalone.json'
    marker_pending=marker.with_suffix('.pending');state_pending=state.with_suffix('.pending')
    for path in (marker,state,marker_pending,state_pending):_assert_safe_bundle_path(path,home)
    current=updates.active_root(home,allow_missing=True)
    previous={}
    if state.exists():
        if state.stat().st_size>4096:raise ValueError('Invalid standalone state.')
        previous=json.loads(state.read_text())
    active={}
    if marker.exists():active=json.loads(marker.read_text())
    try: current_revision=int((current/'launcher/BUILD_REVISION.txt').read_text().strip())
    except (OSError,ValueError): current_revision=0
    bundled_revision=int(metadata.get('launcher_revision',0))
    activate=not marker.exists() or updates.installed_version(home)<updates.version(version) or (
        updates.installed_version(home)==updates.version(version) and bundled_revision>current_revision) or (
        active.get('slot')==previous.get('slot') and updates.installed_version(home)<=updates.version(version)
        and bundled_revision>=current_revision)
    if not activate:return current
    if not target.exists():
        import tempfile
        with tempfile.TemporaryDirectory(prefix='bundle-',dir=versions) as temp:
            work=Path(temp);extracted=updates.extract_verified(Path(payload),work,digest)
            if updates.local_version(extracted)!=updates.version(version):raise ValueError('Bundled version does not match metadata.')
            revision_file=extracted/'launcher/BUILD_REVISION.txt'
            try: extracted_revision=int(revision_file.read_text().strip())
            except (OSError,ValueError): extracted_revision=0
            if extracted_revision!=bundled_revision:raise ValueError('Bundled launcher revision does not match metadata.')
            updates.record_integrity(extracted)
            config=current/'builds/current/melonDS.toml'
            if activate and config.is_file():shutil.copy2(config,extracted/'builds/current/melonDS.toml')
            import unova_storage as storage
            storage.share_binaries(extracted,current);storage.record_package(extracted)
            for path in (updates_dir,versions,target,marker,state,marker_pending,state_pending):
                _assert_safe_bundle_path(path,home)
            Path(temp).rename(target)
    launcher_executable(root)
    if activate:
        import unova_storage as storage
        storage.remember_previous(home,current,slot)
        config=current/'builds/current/melonDS.toml'
        if current!=root and config.is_file():shutil.copy2(config,root/'builds/current/melonDS.toml')
        for path in (updates_dir,marker,marker_pending):_assert_safe_bundle_path(path,home)
        storage.atomic(marker,{'version':version,'slot':slot})
    _assert_safe_bundle_path(state_pending,home)
    _assert_safe_bundle_path(state,home)
    import unova_storage as storage
    storage.atomic(state,{'version':version,'slot':slot})
    return updates.active_root(home,allow_missing=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data-dir',type=Path);parser.add_argument('--self-test',type=Path)
    args=parser.parse_args()
    home=args.data_dir or Path(os.environ.get('LOCALAPPDATA',Path.home()))/'UnovaTogether/Standalone'
    home=home.expanduser().resolve()
    assets=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'single-exe'
    metadata=json.loads((assets/'bundle.json').read_text())
    # Share the updater's OS-owned lock, preventing two first runs extracting
    # or activating the same bundle at once. Never replace a live game file.
    import unova_storage as storage
    with storage.installation_lock(home,'Another Unova Together setup or update is running. Try again shortly.'):
        root=install_bundle(home,assets/'runtime.zip',metadata)
    if not args.self_test:
        try:launcher_migration.schedule(home,root,default_entry=True)
        except (OSError,ValueError):pass
    command=[str(launcher_executable(root)),'--home',str(home)]
    if args.self_test:command+=['--self-test',str(args.self_test.resolve())]
    # PyInstaller's child must have its own unpacking lifetime, otherwise the
    # game can outlive the temporary bootstrap extraction directory.
    env=dict(os.environ);env['PYINSTALLER_RESET_ENVIRONMENT']='1'
    if args.self_test:subprocess.run(command,cwd=root,env=env,check=True,timeout=45)
    else:subprocess.Popen(command,cwd=root,env=env)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        if os.name=='nt' and '--self-test' not in sys.argv:
            ctypes.windll.user32.MessageBoxW(None,str(exc),'Unova Together could not start',0x10)
        else:print(str(exc),file=sys.stderr)
        raise SystemExit(1)
