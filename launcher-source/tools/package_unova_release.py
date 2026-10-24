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
REPO = ROOT.parent
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT.parent.parent.parent
HELPERS = (
    'presence_server.py', 'coop_social.py', 'item_trading_relay.py', 'pokemon_trading_relay.py',
    'ensure_presence_relay.py', 'run-python.cmd', 'online_wireless_relay.py',
    'online_wireless_bridge.py', 'online_udp_protocol.py', 'online_udp_relay.py',
    'online_udp_bridge.py', 'requirements-online-udp.txt', 'setup_tailscale_firewall.ps1',
    'unova_launcher.py', 'unova_updater.py', 'unova_storage.py', 'build_unova_launcher.py',
    'emulator_agent.py', 'unova_agent.py', 'build_unova_agent.py', 'requirements-agent-tools.txt',
    'launcher_migration.py', 'unova_launcher_bootstrap.py', 'build_unova_bootstrap.py',
    'battle_surroundings_worker.py','build_battle_surroundings.py',
    'field_scene_geometry.py','extract_battle_surroundings.py','area_scene_cache.py',
    'build_area_battle_scene.py','build_area_battle_catalog.py',
)
COMMANDS = ('Online Co-op.cmd', 'Install UDP Dependencies.cmd', 'Start LAN Presence Relay.cmd')
DOCS = ('PLAYER_GUIDE.md', 'KNOWN_ISSUES.md', 'TAILSCALE_COOP.md', 'UDP_SERVER_GUIDE.md',
        'LAUNCHER.md', 'COMPANION_INTERACTIONS.md', 'COOP_TOOLS.md', 'FEATURES.md',
        'ROADMAP.md', 'BAG_CAPACITY.md', 'FOLLOWING_POKEMON.md', 'FOLLOWER_ART_CREDITS.md',
        'FOLLOWER_ART_TERMS.md', 'FOLLOWER_VARIANTS.md', 'HGSS_FOLLOWER_IMPORT.md',
        'RELEASE_ASSET_NOTICES_2.0.32.md', 'AGENT_TOOLS_VERIFICATION_2.0.32.md',
        'AGENT_TOOLS.md', 'EMULATOR_AGENT_CONTROL.md')
FORBIDDEN = {'.nds', '.gba', '.sav', '.save', '.dsv', '.ramdump', '.ml1', '.ml2', '.ml3', '.ml4', '.ml5', '.ml6', '.ml7', '.ml8', '.pem', '.key', '.pyc'}

def require_release_condition(condition, message):
    if not condition:
        raise RuntimeError(f'Release package validation failed: {message}')

def runtime_matches_shop_overlay_source(runtime: bytes, patch_header: bytes) -> bool:
    """Match the PE version-resource fingerprint to the packaged patch source."""
    fingerprint = hashlib.sha256(patch_header).hexdigest()
    return fingerprint.encode('utf-16le') in runtime

def check_launcher_ui_mirror():
    checker = REPOSITORY_ROOT/'launcher-source/tools/check_launcher_tree_parity.py'
    if not checker.is_file():
        raise RuntimeError(f'Launcher UI parity checker is missing: {checker}')
    subprocess.run([sys.executable, str(checker)], check=True, cwd=REPOSITORY_ROOT)

def tool_source(name):
    """Prefer this checkout's canonical helper over a shared workspace copy."""
    source=ROOT/'tools'/name
    if source.is_file():return source
    return WORKSPACE/'tools'/name

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--runtime-root',type=Path,help='Verified staged runtime; avoids replacing a running beta')
    parser.add_argument('--launcher-root',type=Path,help='Built launcher directory; avoids replacing the current launcher')
    parser.add_argument('--artifact-dir',type=Path,help='Fresh output directory beneath downloads/releases')
    parser.add_argument('--pyinstaller-python',type=Path,help='Python environment with PyInstaller for the standalone download')
    parser.add_argument('--base-source-archive',type=Path,help='Previous official source archive to preserve the matching emulator source')
    parser.add_argument('--native-source-root',type=Path,help='Exact modified emulator source tree used for the staged binary')
    args = parser.parse_args()
    version = args.version
    if not version or any(c not in '0123456789.-abcdefghijklmnopqrstuvwxyz' for c in version):
        parser.error('Invalid version')
    check_launcher_ui_mirror()
    current = args.runtime_root.resolve() if args.runtime_root else WORKSPACE/'builds/current'
    if not current.is_relative_to(WORKSPACE/'builds'):
        raise ValueError('Runtime must be staged within workspace builds')
    launcher = args.launcher_root.resolve() if args.launcher_root else WORKSPACE/'builds/release-launcher-1.0.20/Pokemon Together'
    if not launcher.is_relative_to(WORKSPACE/'builds'):
        raise ValueError('Launcher must be staged within workspace builds')
    repo = REPO
    output = args.artifact_dir.resolve() if args.artifact_dir else WORKSPACE/'downloads/releases'
    if not output.is_relative_to(WORKSPACE/'downloads/releases'):
        raise ValueError('Release artifacts must stay under downloads/releases')
    if args.artifact_dir and output.exists() and any(output.iterdir()):
        raise FileExistsError('Artifact directory must be fresh')
    output.mkdir(parents=True,exist_ok=True)
    runtime = output/f'Unova-Together-{version}-Windows-x64.zip'
    source = output/f'Unova-Together-{version}-Source.zip'
    standalone=output/'Unova-Together.exe'
    agent_asset=output/'Unova-Agent-Tools.exe'
    agent_licenses=output/'Unova-Agent-Tools-LICENSES.txt'
    asset_notices=output/'Unova-Together-ASSET-NOTICES.txt'
    repair=output/'Repair-Launcher.exe'
    sums=output/f'SHA256SUMS-Unova-Together-{version}.txt'
    release_label=output.name if args.artifact_dir else f'release-{version}'
    stage_root=WORKSPACE/'builds'/release_label
    stage=stage_root/'Unova-Together'
    source_root=args.native_source_root.resolve() if args.native_source_root else WORKSPACE/'melonDS-source-1.1'
    freebios_notice_path=source_root/'freebios/drastic_bios_readme.txt'
    asset_notice_doc=repo/'docs/RELEASE_ASSET_NOTICES_2.0.32.md'
    if args.native_source_root and not source_root.is_relative_to(WORKSPACE/'builds'):
        raise ValueError('Modified emulator source must be staged under workspace builds')
    patch_header=source_root/'src/Gen5ShopOverlayPatch.h'
    patch_header_bytes=patch_header.read_bytes() if patch_header.is_file() else None
    if args.base_source_archive:
        with zipfile.ZipFile(args.base_source_archive) as base:
            packaged_header='Unova-Together-Source/source/melonDS/src/Gen5ShopOverlayPatch.h'
            if packaged_header not in base.namelist():
                raise RuntimeError('Base corresponding-source archive is missing the Mega shop patch source.')
            if base.read(packaged_header) != patch_header_bytes:
                raise RuntimeError('Modified source changed the existing shop patch payload; verify the matching binary before packaging.')
    require_release_condition(patch_header_bytes is not None, 'Mega shop overlay patch source is missing')
    require_release_condition(freebios_notice_path.is_file(), 'FreeBIOS redistribution notice is missing')
    freebios_notice_text=freebios_notice_path.read_text(encoding='utf-8').strip()
    require_release_condition(freebios_notice_text in asset_notice_doc.read_text(encoding='utf-8'),
                              'Full FreeBIOS binary redistribution notice is missing from release asset notices')
    require_release_condition(
        patch_header_bytes is not None and runtime_matches_shop_overlay_source((current/'melonDS.exe').read_bytes(), patch_header_bytes),
        'Staged emulator was not built from the packaged Mega shop overlay patch source; rebuild it before packaging',
    )
    if args.base_source_archive:
        if not args.base_source_archive.is_file():
            raise FileNotFoundError(f'Base corresponding-source archive is missing: {args.base_source_archive}')
        with zipfile.ZipFile(args.base_source_archive) as base:
            if not any(name.startswith('Unova-Together-Source/source/melonDS/') for name in base.namelist()):
                raise RuntimeError('Base corresponding-source archive is missing the packaged emulator source.')
    work_root=WORKSPACE/'builds'/f'{release_label}-single-exe-work'
    standalone_dir=stage_root/'standalone'
    agent_build_dir=WORKSPACE/'builds'/f'agent-tools-{release_label}'
    agent_work_dir=WORKSPACE/'builds'/f'agent-tools-pyinstaller-{release_label}'
    if any(path.exists() for path in (runtime,source,standalone,agent_asset,agent_licenses,asset_notices,repair,sums,stage_root,work_root,
                                      agent_build_dir,agent_work_dir)):
        raise RuntimeError('Release output exists; choose a fresh version')
    config = tomllib.loads((current/'melonDS.toml').read_text(encoding='utf-8-sig'))
    require_release_condition(
        isinstance(config.get('Instance0'), dict) and isinstance(config['Instance0'].get('Keyboard'), dict),
        'Staged runtime config is missing the Instance0 keyboard mappings',
    )
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
    tailscale = WORKSPACE/'downloads/dependencies/tailscale'
    manifest = json.loads((tailscale/'bundle.json').read_text())
    require_release_condition(
        hashlib.sha256((tailscale/manifest['installer']).read_bytes()).hexdigest() == manifest['sha256'],
        'Tailscale installer checksum does not match bundle.json',
    )
    subprocess.run([sys.executable, str(ROOT/'tools/build_unova_agent.py'),
        '--output-dir',str(agent_build_dir),'--work-dir',str(agent_work_dir),
        *(['--pyinstaller-python',str(args.pyinstaller_python.resolve())] if args.pyinstaller_python else [])],
        check=True,cwd=ROOT)
    agent_executable=agent_build_dir/'Unova Agent Tools.exe'
    smoke = subprocess.run([str(agent_executable), '--project-root', str(repo), 'inventory'],
        cwd=WORKSPACE, check=True, capture_output=True, text=True, timeout=60)
    try:
        smoke_result = json.loads(smoke.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError('Standalone agent executable did not return valid inventory JSON.') from error
    project_version = smoke_result.get('result', {}).get('projectVersion')
    require_release_condition(smoke_result.get('ok') is True and
                              project_version in {version, f'Unova Together {version}'},
                              'Standalone agent executable failed its frozen-runtime inventory smoke test')
    license_parts = []
    for title, name in (('Python runtime', 'Python-LICENSE.txt'), ('PyInstaller bootloader', 'PyInstaller-COPYING.txt'),
                        ('ndspy', 'NDSpy-LICENSE.txt'), ('Pillow', 'Pillow-LICENSE.txt'),
                        ('TOMLKit', 'TOMLKit-LICENSE.txt')):
        path = launcher/name
        require_release_condition(path.is_file(), f'Missing agent-tool third-party notice: {name}')
        license_parts.append(f'## {title} ({name})\n\n{path.read_text(encoding="utf-8", errors="replace").strip()}\n')
    agent_licenses.write_text('# Notices for Unova Agent Tools.exe\n\n' + '\n'.join(license_parts), encoding='utf-8')
    asset_notices.write_text(asset_notice_doc.read_text(encoding='utf-8'), encoding='utf-8')
    with zipfile.ZipFile(runtime, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr('Unova-Together/VERSION.txt', f'{version}\n')
        z.write(current/'melonDS.exe', 'Unova-Together/builds/current/melonDS.exe')
        z.writestr('Unova-Together/builds/current/VERSION.txt', f'Unova Together {version}\nBy mvq1303 (GitHub: WhatWasMissing).\n')
        for path in sorted(current.rglob('*.dll')):
            if 'diagnostics' not in path.relative_to(current).parts:
                z.write(path, 'Unova-Together/builds/current/'+path.relative_to(current).as_posix())
        z.writestr('Unova-Together/builds/current/melonDS.toml', portable)
        for name in HELPERS:
            z.write(tool_source(name), 'Unova-Together/tools/'+name)
        z.write(agent_executable, 'Unova-Together/tools/Unova Agent Tools.exe')
        z.write(agent_licenses, 'Unova-Together/tools/Unova Agent Tools LICENSES.txt')
        for path in sorted((WORKSPACE/'tools/vendor').rglob('*')):
            if path.is_file() and path.suffix.lower() in {'.py','.txt','.md'}:
                z.write(path,'Unova-Together/tools/vendor/'+path.relative_to(WORKSPACE/'tools/vendor').as_posix())
        for path in sorted((ROOT/'tools/launcher_ui').rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                z.write(path,'Unova-Together/tools/launcher_ui/'+path.relative_to(ROOT/'tools/launcher_ui').as_posix())
        for name in COMMANDS:
            z.write(WORKSPACE/name, 'Unova-Together/'+name)
        z.writestr('Unova-Together/Start Emulator.cmd', '@echo off\r\ncd /d "%~dp0builds\\current"\r\nstart "" melonDS.exe\r\n')
        require_release_condition((launcher/'Pokemon Together.exe').is_file(), 'Launcher executable is missing')
        for path in sorted(launcher.rglob('*')):
            if path.is_file():z.write(path,'Unova-Together/launcher/'+path.relative_to(launcher).as_posix())
        z.writestr('Unova-Together/Start Unova Together.cmd','@echo off\r\ncd /d "%~dp0"\r\nstart "" "launcher\\Pokemon Together.exe" --home "%~dp0."\r\n')
        for name in DOCS:
            z.write(repo/'docs'/name, 'Unova-Together/docs/'+name)
        for path in sorted((repo/'patchnotes').glob('RELEASE_NOTES_*.md')):
            z.write(path, 'Unova-Together/patchnotes/'+path.name)
        z.write(repo/'patchnotes'/'index.json', 'Unova-Together/patchnotes/index.json')
        z.write(repo/'patchnotes'/'README.md', 'Unova-Together/patchnotes/README.md')
        for name in ('README.md', 'LICENSE', 'LICENSING.md', 'AUTHORSHIP.md'):
            z.write(repo/name, 'Unova-Together/'+name)
        z.writestr('Unova-Together/START HERE.md', '# Start here\n\nRun **Start Unova Together.cmd**, choose your own ROM and select Play. The launcher checks official GitHub releases and offers verified updates. Follow docs/PLAYER_GUIDE.md to connect. Both players need matching ROMs/builds and independent saves.\n')
        for name in (manifest['installer'], 'bundle.json', 'LICENSE.txt', 'README.txt'):
            z.write(tailscale/name, 'Unova-Together/setup/Tailscale/'+name)
    with zipfile.ZipFile(source, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name in ('check_follower_appearance.cpp','check_pokemon_follower.cpp','check_presence_rendering.cpp','test_presence_polling.py','test_party_stats.py','test_unova_storage.py'):
            z.write(tool_source(name),'Unova-Together-Source/tools/'+name)
        z.write(tool_source('test_launcher_migration.py'),'Unova-Together-Source/tools/test_launcher_migration.py')
        z.write(tool_source('test_launcher_versioning.py'),'Unova-Together-Source/tools/test_launcher_versioning.py')
        z.write(tool_source('test_presence_relay_version.py'),'Unova-Together-Source/tools/test_presence_relay_version.py')
        for path in sorted(source_root.rglob('*')):
            relative = path.relative_to(source_root)
            if not path.is_file() or any(part in {'.git', 'build', '__pycache__', 'test-fixtures', 'diagnostics'} for part in relative.parts):
                continue
            if relative.as_posix() == '.release-build-input' or relative.name.endswith('.latest.json'):
                continue
            if path.suffix.lower() in FORBIDDEN:
                raise RuntimeError(f'Private/game file in source: {relative}')
            z.write(path, 'Unova-Together-Source/source/melonDS/'+relative.as_posix())
        for name in HELPERS:
            z.write(tool_source(name), 'Unova-Together-Source/tools/'+name)
        z.write(agent_licenses, 'Unova-Together-Source/tools/Unova Agent Tools LICENSES.txt')
        for path in sorted((WORKSPACE/'tools/vendor').rglob('*')):
            if path.is_file() and path.suffix.lower() in {'.py','.txt','.md'}:
                z.write(path,'Unova-Together-Source/tools/vendor/'+path.relative_to(WORKSPACE/'tools/vendor').as_posix())
        for path in sorted((ROOT/'tools/launcher_ui').rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                z.write(path,'Unova-Together-Source/tools/launcher_ui/'+path.relative_to(ROOT/'tools/launcher_ui').as_posix())
        z.write(ROOT/'tools/package_unova_release.py','Unova-Together-Source/tools/package_unova_release.py')
        for name in ('test_unova_agent.py','test_emulator_agent.py'):
            z.write(tool_source(name),'Unova-Together-Source/tools/'+name)
        for name in ('test_unova_updater.py','test_unova_single_exe.py','unova_single_exe.py','build_unova_single_exe.py','test_launcher_ui.py','test_launcher_preferences.py','test_launcher_cheat_engine.py','test_launcher_services.py','test_ensure_presence_relay.py','test_release_input_bounds.py','test_overworld_companion.py','check_lan_player_list_validation.cpp','check_battle_presence.cpp','check_post_battle_presence.cpp','check_rival_agreement.cpp','test_rival_payload.py','test_coop_boss_payload.py','test_coop_story_return.py','test_coop_field_return.py','verify_coop_runtime.py','audit_native_enemy_setup.py','verify_rival_startups.py','test_field_zone_native.py','check_field_zone.cpp',):
            z.write(tool_source(name),'Unova-Together-Source/tools/'+name)
        for name in ('test_companion_interactions.py','test_companion_interactions_runner.py','test_follower_depth.py','check_follower_depth.cpp'):
            z.write(REPOSITORY_ROOT/'maintenance-tools/tools'/name,'Unova-Together-Source/tools/'+name)
        for name in ('check_launcher_tree_parity.py','test_launcher_tree_parity.py','test_release_validation.py'):
            z.write(ROOT/'tools'/name,'Unova-Together-Source/tools/'+name)
        for name in ('DEVELOPER_TESTING.md','AGENT_TOOLS.md','EMULATOR_AGENT_CONTROL.md',
                     'RELEASE_ASSET_NOTICES_2.0.32.md','AGENT_TOOLS_VERIFICATION_2.0.32.md',
                     'FOLLOWER_ART_CREDITS.md',
                     'FOLLOWER_ART_TERMS.md','FOLLOWER_VARIANTS.md','HGSS_FOLLOWER_IMPORT.md'):
            z.write(repo/'docs'/name,'Unova-Together-Source/docs/'+name)
        for name in ('ASSET_TERMS.md','CREDITS.md'):
            z.write(REPOSITORY_ROOT/'maintenance-tools/assets/followers'/name,
                    'Unova-Together-Source/ASSET_NOTICES/hg-engine/'+name)
        z.write(ROOT/'tools/test_patchnotes_feed.py','Unova-Together-Source/tools/test_patchnotes_feed.py')
        for name in ('test_player_models.py',):
            z.write(ROOT/'tools'/name, 'Unova-Together-Source/tools/'+name)
        for name in ('dialogue_preview.py', 'romhack_workflow.py', 'test_dialogue_preview.py', 'test_romhack_workflow.py'):
            z.write(repo/'maintenance-tools/tools'/name, 'Unova-Together-Source/maintenance-tools/tools/'+name)
        z.write(repo/'maintenance-tools/dialogue-demo/field_researcher.json', 'Unova-Together-Source/maintenance-tools/dialogue-demo/field_researcher.json')
        z.write(repo/'docs/ROMHACK_DIALOGUE_WORKFLOW.md', 'Unova-Together-Source/docs/ROMHACK_DIALOGUE_WORKFLOW.md')
        for name in COMMANDS:
            z.write(WORKSPACE/name, 'Unova-Together-Source/'+name)
        for name in ('AGENTS.md','skills.md','AUTHORSHIP.md'):
            z.write(repo/name, 'Unova-Together-Source/'+name)
        z.write(source_root/'LICENSE', 'Unova-Together-Source/LICENSE')
        z.writestr('Unova-Together-Source/README.md',
            f'Corresponding source for Unova Together {version}.\n\n'
            'Build the emulator using source/melonDS/README.md and HOWTO.md. '
            'CMake build files, native payload source and dependency notices are included. '
            'The connection and MCP agent helpers are Python source in tools/. Read docs/AGENT_TOOLS.md for client setup. '
            'Credited project artwork/audio and independent FreeBIOS replacements are included with their notices. '
            'No game ROM, user save or real firmware dump is included.\n')
    for archive in (runtime, source):
        with zipfile.ZipFile(archive) as z:
            require_release_condition(z.testzip() is None, f'Archive is corrupt: {archive.name}')
            require_release_condition(
                not any(Path(n).suffix.lower() in FORBIDDEN for n in z.namelist()),
                f'Archive contains a forbidden private file: {archive.name}',
            )
            require_release_condition(
                not any('/.git/' in n or '/test-fixtures/' in n or '/diagnostics/' in n for n in z.namelist()),
                f'Archive contains development-only files: {archive.name}',
            )
    with zipfile.ZipFile(runtime) as z:
        require_release_condition(
            z.read('Unova-Together/builds/current/melonDS.exe') == (current/'melonDS.exe').read_bytes(),
            'Packaged emulator differs from the staged emulator',
        )
        require_release_condition(
            z.read('Unova-Together/tools/Unova Agent Tools.exe') == agent_executable.read_bytes(),
            'Packaged agent executable differs from the verified standalone agent build',
        )
        runtime_notice=z.read('Unova-Together/docs/RELEASE_ASSET_NOTICES_2.0.32.md').decode('utf-8').replace('\r\n','\n')
        require_release_condition(
            runtime_notice == asset_notice_doc.read_text(encoding='utf-8') and freebios_notice_text in runtime_notice,
            'Runtime package is missing the full FreeBIOS binary redistribution notice',
        )
        require_release_condition(asset_notices.read_text(encoding='utf-8') == asset_notice_doc.read_text(encoding='utf-8'),
                                  'Standalone launcher notice sidecar differs from the full asset notice document')
        require_release_condition(z.read('Unova-Together/VERSION.txt').decode().strip() == version,
                                  'Packaged project version does not match the release')
        require_release_condition(
            z.read('Unova-Together/builds/current/VERSION.txt').startswith(f'Unova Together {version}'.encode()),
            'Packaged runtime version does not match the requested version',
        )
        packed = tomllib.loads(z.read('Unova-Together/builds/current/melonDS.toml').decode())
        require_release_condition(packed.get('Instance0', {}).get('Keyboard') == config['Instance0']['Keyboard'], 'Packaged keyboard controls differ from the staged configuration')
        require_release_condition(
            all(k in {'PauseLostFocus','LimitFPS','TargetFPS','MP','JIT'} or k.startswith('Instance') for k in packed),
            'Packaged configuration contains an unsupported top-level setting',
        )
        require_release_condition(not any('/source/' in n for n in z.namelist()), 'Runtime archive unexpectedly contains source files')
        note_files=[name for name in z.namelist() if name.startswith('Unova-Together/patchnotes/RELEASE_NOTES_') and name.endswith('.md')]
        patch_index = json.loads((repo/'patchnotes'/'index.json').read_text(encoding='utf-8'))
        require_release_condition(
            len(note_files)==len(patch_index['notes']) and f'Unova-Together/patchnotes/RELEASE_NOTES_{version}.md' in note_files,
            'Packaged patch notes do not match the release index/version',
        )
        require_release_condition(
            'Unova-Together/patchnotes/index.json' in z.namelist() and z.read('Unova-Together/patchnotes/index.json') == (repo/'patchnotes'/'index.json').read_bytes(),
            'Packaged patch-notes index is missing or stale',
        )
        launcher_info=json.loads(z.read('Unova-Together/launcher/BUILD_INFO.json'))
        require_release_condition(launcher_info['product']=='pokemon-together' and launcher_info['version']==version, 'Launcher build metadata does not match the release')
        require_release_condition(json.loads(z.read('Unova-Together/launcher/_internal/launcher_ui/build-info.json'))==launcher_info, 'Frozen launcher metadata differs from its build metadata')
        require_release_condition(z.read('Unova-Together/launcher/VERSION.txt').decode().strip()=='Pokemon Together Launcher '+version, 'Launcher VERSION.txt does not match the release')
    with zipfile.ZipFile(source) as z:
        names = set(z.namelist())
        require_release_condition('Unova-Together-Source/tools/test_launcher_migration.py' in names, 'Source archive is missing launcher migration coverage')
        require_release_condition('Unova-Together-Source/tools/test_launcher_versioning.py' in names, 'Source archive is missing launcher version coverage')
        require_release_condition('Unova-Together-Source/tools/test_companion_interactions.py' in names, 'Source archive is missing companion interaction coverage')
        require_release_condition('Unova-Together-Source/tools/test_overworld_companion.py' in names, 'Source archive is missing overworld companion coverage')
        require_release_condition('Unova-Together-Source/tools/test_companion_interactions_runner.py' in names, 'Source archive is missing companion test provenance checks')
        require_release_condition('Unova-Together-Source/tools/check_launcher_tree_parity.py' in names, 'Source archive is missing the launcher mirror checker')
        require_release_condition('Unova-Together-Source/tools/test_launcher_tree_parity.py' in names, 'Source archive is missing launcher mirror coverage')
        require_release_condition('Unova-Together-Source/tools/test_release_validation.py' in names, 'Source archive is missing optimized release-guard coverage')
        require_release_condition('Unova-Together-Source/docs/DEVELOPER_TESTING.md' in names, 'Source archive is missing test reproduction instructions')
        for required in ('Unova-Together-Source/tools/unova_agent.py', 'Unova-Together-Source/tools/emulator_agent.py',
                         'Unova-Together-Source/tools/build_unova_agent.py',
                         'Unova-Together-Source/tools/requirements-agent-tools.txt',
                         'Unova-Together-Source/tools/test_unova_agent.py',
                         'Unova-Together-Source/tools/test_emulator_agent.py',
                         'Unova-Together-Source/docs/AGENT_TOOLS.md',
                         'Unova-Together-Source/docs/EMULATOR_AGENT_CONTROL.md',
                         'Unova-Together-Source/docs/AGENT_TOOLS_VERIFICATION_2.0.32.md',
                         'Unova-Together-Source/docs/RELEASE_ASSET_NOTICES_2.0.32.md',
                         'Unova-Together-Source/source/melonDS/tools/test_emulator_agent_protocol.cpp'):
            require_release_condition(required in names, f'Source archive is missing agent tooling: {required}')
        require_release_condition(
            'Unova-Together-Source/docs/RELEASE_ASSET_NOTICES_2.0.32.md' in names and
            freebios_notice_text in z.read('Unova-Together-Source/docs/RELEASE_ASSET_NOTICES_2.0.32.md').decode('utf-8').replace('\r\n','\n') and
            'Unova-Together-Source/source/melonDS/freebios/drastic_bios_readme.txt' in names and
            'Unova-Together-Source/ASSET_NOTICES/hg-engine/ASSET_TERMS.md' in names and
            'Unova-Together-Source/ASSET_NOTICES/hg-engine/CREDITS.md' in names,
            'Source archive is missing included artwork permission records or notices',
        )
        require_release_condition(
            not any(n.endswith('.latest.json') or n.endswith('/.release-build-input') for n in names),
            'Source archive contains generated verification output or a build-input marker',
        )
    stage_root.mkdir(parents=True)
    (stage_root/'.disposable-release-stage').write_text('Temporary extracted release staging; final archives are in downloads/releases.\n', encoding='utf-8')
    with zipfile.ZipFile(runtime) as z:z.extractall(stage_root)
    subprocess.run([sys.executable,str(ROOT/'tools/build_unova_single_exe.py'),
        '--runtime-root',str(stage),'--work-dir',str(work_root),'--output-dir',str(standalone_dir),
        *(['--base-source-archive',str(args.base_source_archive.resolve())] if args.base_source_archive else []),
        '--native-source-root',str(source_root),
        *(['--pyinstaller-python',str(args.pyinstaller_python.resolve())] if args.pyinstaller_python else [])],check=True,cwd=ROOT)
    shutil.copy2(standalone_dir/'Unova Together.exe',standalone)
    shutil.copy2(agent_executable,agent_asset)
    shutil.copy2(launcher/'Pokemon Together Bootstrap.exe',repair)
    sums.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in (runtime,source,standalone,agent_asset,agent_licenses,asset_notices,repair)), encoding='utf-8')
    print(json.dumps({'version':version, 'exeSHA256':hashlib.sha256((current/'melonDS.exe').read_bytes()).hexdigest(),
        'assets':[{'name':p.name,'bytes':p.stat().st_size} for p in (runtime,source,standalone,agent_asset,agent_licenses,asset_notices,repair,sums)],
        'portableControlsVerified':True, 'privateFilesExcluded':True}, indent=2))

if __name__ == '__main__':
    main()
