"""Build separate player and corresponding-source downloads from the installed runtime."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HELPERS = (
    'presence_server.py', 'coop_social.py', 'item_trading_relay.py', 'pokemon_trading_relay.py',
    'ensure_presence_relay.py', 'run-python.cmd', 'online_wireless_relay.py',
    'online_wireless_bridge.py', 'online_udp_protocol.py', 'online_udp_relay.py',
    'online_udp_bridge.py', 'requirements-online-udp.txt', 'setup_tailscale_firewall.ps1',
    'unova_launcher.py', 'unova_updater.py', 'build_unova_launcher.py',
)
COMMANDS = ('Online Co-op.cmd', 'Install UDP Dependencies.cmd', 'Start LAN Presence Relay.cmd')
DOCS = ('PLAYER_GUIDE.md', 'KNOWN_ISSUES.md', 'TAILSCALE_COOP.md', 'UDP_SERVER_GUIDE.md',
        'LAUNCHER.md', 'COMPANIONS_AND_SOARING.md', 'COOP_TOOLS.md', 'FEATURES.md',
        'ROADMAP.md', 'RELEASE_CHECKS_1.0.6.md')
FORBIDDEN = {'.nds', '.sav', '.dsv', '.ramdump', '.ml1', '.ml2', '.ml3', '.ml4', '.ml8', '.pem', '.key'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--runtime-root',type=Path,help='Verified staged runtime; avoids replacing a running beta')
    parser.add_argument('--artifact-dir',type=Path,help='Fresh output directory beneath downloads/releases')
    parser.add_argument('--pyinstaller-python',type=Path,help='Python environment with PyInstaller for the standalone download')
    args = parser.parse_args()
    version = args.version
    if not version or any(c not in '0123456789.-abcdefghijklmnopqrstuvwxyz' for c in version):
        parser.error('Invalid version')
    current = args.runtime_root.resolve() if args.runtime_root else ROOT/'builds/current'
    if not current.is_relative_to(ROOT/'builds'):
        raise ValueError('Runtime must be staged within workspace builds')
    repo = ROOT/'tools/unova-together-release'
    output = args.artifact_dir.resolve() if args.artifact_dir else ROOT/'downloads/releases'
    if not output.is_relative_to(ROOT/'downloads/releases'):
        raise ValueError('Release artifacts must stay under downloads/releases')
    if args.artifact_dir and output.exists() and any(output.iterdir()):
        raise FileExistsError('Artifact directory must be fresh')
    output.mkdir(parents=True,exist_ok=True)
    runtime = output/f'Unova-Together-{version}-Windows-x64.zip'
    source = output/f'Unova-Together-{version}-Source.zip'
    standalone=output/'Unova-Together.exe'
    sums=output/f'SHA256SUMS-Unova-Together-{version}.txt'
    release_label=output.name if args.artifact_dir else f'release-{version}'
    stage_root=ROOT/'builds'/release_label
    stage=stage_root/'Unova-Together'
    work_root=ROOT/'test-fixtures'/f'{release_label}-single-exe'
    standalone_dir=stage_root/'standalone'
    if any(path.exists() for path in (runtime,source,standalone,sums,stage_root,work_root)):
        raise RuntimeError('Release output exists; choose a fresh version')
    config = tomllib.loads((current/'melonDS.toml').read_text(encoding='utf-8-sig'))
    controls = ['PauseLostFocus = false', 'LimitFPS = true', 'TargetFPS = 60.0',
                '[MP]', 'RecvTimeout = 100', 'FrameWaitBudget = 8', '[JIT]', 'Enable = false', '']
    for name, values in config.items():
        if not name.startswith('Instance') or not isinstance(values, dict):
            continue
        for section in ('Keyboard', 'Joystick'):
            bindings = values.get(section, {})
            if bindings:
                controls.append(f'[{name}.{section}]')
                controls.extend(f'{key} = {value}' for key, value in bindings.items()
                                if isinstance(value, int) and not isinstance(value, bool))
                controls.append('')
    portable = '\n'.join(controls)
    tailscale = ROOT/'downloads/dependencies/tailscale'
    manifest = json.loads((tailscale/'bundle.json').read_text())
    assert hashlib.sha256((tailscale/manifest['installer']).read_bytes()).hexdigest() == manifest['sha256']
    with zipfile.ZipFile(runtime, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.write(current/'melonDS.exe', 'Unova-Together/builds/current/melonDS.exe')
        z.writestr('Unova-Together/builds/current/VERSION.txt', f'Unova Together {version}\nBy mvq1303 (GitHub: WhatWasMissing).\n')
        for path in sorted(current.rglob('*.dll')):
            if 'diagnostics' not in path.relative_to(current).parts:
                z.write(path, 'Unova-Together/builds/current/'+path.relative_to(current).as_posix())
        z.writestr('Unova-Together/builds/current/melonDS.toml', portable)
        for name in HELPERS:
            z.write(ROOT/'tools'/name, 'Unova-Together/tools/'+name)
        for path in sorted((ROOT/'tools/launcher_ui').rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                z.write(path,'Unova-Together/tools/launcher_ui/'+path.relative_to(ROOT/'tools/launcher_ui').as_posix())
        for name in COMMANDS:
            z.write(ROOT/name, 'Unova-Together/'+name)
        z.writestr('Unova-Together/Start Emulator.cmd', '@echo off\r\ncd /d "%~dp0builds\\current"\r\nstart "" melonDS.exe\r\n')
        launcher=ROOT/'builds/mod-hub/current/Pokemon Together'
        assert (launcher/'Pokemon Together.exe').is_file()
        for path in sorted(launcher.rglob('*')):
            if path.is_file():z.write(path,'Unova-Together/launcher/'+path.relative_to(launcher).as_posix())
        z.writestr('Unova-Together/Start Unova Together.cmd','@echo off\r\ncd /d "%~dp0"\r\nstart "" "launcher\\Pokemon Together.exe"\r\n')
        for name in DOCS:
            z.write(repo/'docs'/name, 'Unova-Together/docs/'+name)
        z.write(repo/'RELEASE_NOTES_1.0.6.md', 'Unova-Together/RELEASE_NOTES_1.0.6.md')
        for name in ('README.md', 'LICENSE', 'LICENSING.md', 'AUTHORSHIP.md'):
            z.write(repo/name, 'Unova-Together/'+name)
        z.writestr('Unova-Together/START HERE.md', '# Start here\n\nRun **Start Unova Together.cmd**, choose your own ROM and select Play. The launcher checks official GitHub releases and offers verified updates. Follow docs/PLAYER_GUIDE.md to connect. Both players need matching ROMs/builds and independent saves.\n')
        for name in (manifest['installer'], 'bundle.json', 'LICENSE.txt', 'README.txt'):
            z.write(tailscale/name, 'Unova-Together/setup/Tailscale/'+name)
    source_root = ROOT/'melonDS-source-1.1'
    with zipfile.ZipFile(source, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(source_root.rglob('*')):
            relative = path.relative_to(source_root)
            if not path.is_file() or any(part in {'.git', 'build', '__pycache__'} for part in relative.parts):
                continue
            if path.suffix.lower() in FORBIDDEN:
                raise RuntimeError(f'Private/game file in source: {relative}')
            z.write(path, 'Unova-Together-Source/source/melonDS/'+relative.as_posix())
        for name in HELPERS:
            z.write(ROOT/'tools'/name, 'Unova-Together-Source/tools/'+name)
        for path in sorted((ROOT/'tools/launcher_ui').rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                z.write(path,'Unova-Together-Source/tools/launcher_ui/'+path.relative_to(ROOT/'tools/launcher_ui').as_posix())
        for name in ('test_unova_updater.py','test_unova_single_exe.py','unova_single_exe.py','build_unova_single_exe.py','test_launcher_ui.py','test_launcher_preferences.py','test_launcher_cheat_engine.py','test_launcher_services.py','test_release_input_bounds.py','test_companion_and_soaring.py','test_overworld_companion.py','check_lan_player_list_validation.cpp','check_battle_presence.cpp','check_post_battle_presence.cpp','check_rival_agreement.cpp','test_rival_payload.py','test_coop_boss_payload.py','test_coop_story_return.py','test_coop_field_return.py','verify_coop_runtime.py','audit_native_enemy_setup.py','verify_rival_startups.py'):
            z.write(ROOT/'tools'/name,'Unova-Together-Source/tools/'+name)
        for name in COMMANDS:
            z.write(ROOT/name, 'Unova-Together-Source/'+name)
        z.write(source_root/'LICENSE', 'Unova-Together-Source/LICENSE')
        z.writestr('Unova-Together-Source/README.md',
            f'Corresponding source for Unova Together {version}.\n\n'
            'Build the emulator using source/melonDS/README.md and HOWTO.md. '
            'CMake build files, native payload source and dependency notices are included. '
            'The connection helpers are Python source in tools/. No ROM, save or firmware is included.\n')
    for archive in (runtime, source):
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            assert not any(Path(n).suffix.lower() in FORBIDDEN for n in z.namelist())
            assert not any('/.git/' in n or '/test-fixtures/' in n or '/diagnostics/' in n for n in z.namelist())
    with zipfile.ZipFile(runtime) as z:
        assert z.read('Unova-Together/builds/current/melonDS.exe') == (current/'melonDS.exe').read_bytes()
        assert z.read('Unova-Together/builds/current/VERSION.txt').startswith(f'Unova Together {version}'.encode())
        packed = tomllib.loads(z.read('Unova-Together/builds/current/melonDS.toml').decode())
        assert packed['Instance0']['Keyboard'] == config['Instance0']['Keyboard']
        assert all(k in {'PauseLostFocus','LimitFPS','TargetFPS','MP','JIT'} or k.startswith('Instance') for k in packed)
        assert not any('/source/' in n for n in z.namelist())
        assert 'Unova-Together/docs/COMPANIONS_AND_SOARING.md' in z.namelist()
        assert 'Unova-Together/RELEASE_NOTES_1.0.6.md' in z.namelist()
    with zipfile.ZipFile(source) as z:
        assert 'Unova-Together-Source/tools/test_companion_and_soaring.py' in z.namelist()
        assert 'Unova-Together-Source/tools/test_overworld_companion.py' in z.namelist()
    stage_root.mkdir(parents=True)
    with zipfile.ZipFile(runtime) as z:z.extractall(stage_root)
    subprocess.run([sys.executable,str(ROOT/'tools/build_unova_single_exe.py'),
        '--runtime-root',str(stage),'--work-dir',str(work_root),'--output-dir',str(standalone_dir),
        *(['--pyinstaller-python',str(args.pyinstaller_python.resolve())] if args.pyinstaller_python else [])],check=True,cwd=ROOT)
    shutil.copy2(standalone_dir/'Unova Together.exe',standalone)
    sums.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in (runtime,source,standalone)), encoding='utf-8')
    print(json.dumps({'version':version, 'exeSHA256':hashlib.sha256((current/'melonDS.exe').read_bytes()).hexdigest(),
        'assets':[{'name':p.name,'bytes':p.stat().st_size} for p in (runtime,source,standalone,sums)],
        'portableControlsVerified':True, 'privateFilesExcluded':True}, indent=2))

if __name__ == '__main__':
    main()
