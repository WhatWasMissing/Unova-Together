"""Build one EXE with reviewed runtime and corresponding source. mvq1303."""
from pathlib import Path
from importlib import metadata as package_metadata
import argparse, hashlib, json, os, subprocess, sys, zipfile
import unova_updater as updates
from launcher_ui import versioning

ROOT=Path(__file__).resolve().parents[1]
PRIVATE={'.nds','.gba','.sav','.save','.dsv','.ramdump','.ml1','.ml2','.ml3','.ml4','.ml5','.ml6','.ml7','.ml8','.pem','.key','.pyc'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runtime-root',type=Path);parser.add_argument('--work-dir',type=Path);parser.add_argument('--output-dir',type=Path);parser.add_argument('--pyinstaller-python',type=Path)
    parser.add_argument('--launcher-source',type=Path,help='Matching source archive for a retained frozen launcher')
    args=parser.parse_args()
    installed=args.runtime_root.resolve() if args.runtime_root else ROOT/'builds/unova-together-0.3.5/Unova-Together'
    if not installed.is_relative_to(ROOT/'builds'):raise ValueError('Runtime must be staged under builds')
    work=(args.work_dir.resolve() if args.work_dir else ROOT/'test-fixtures/single-exe-build-20261009')
    if not work.is_relative_to(ROOT/'test-fixtures'):raise ValueError('Single-EXE work directory must stay within test-fixtures')
    if args.work_dir and work.exists() and any(work.iterdir()):raise FileExistsError('Single-EXE work directory must be fresh')
    work.mkdir(parents=True,exist_ok=True)
    assets=work/'single-exe';assets.mkdir(exist_ok=True)
    source=work/'Corresponding-Source.zip'
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as bundle:
        for name in ('launcher_migration.py','unova_launcher_bootstrap.py','build_unova_bootstrap.py','test_launcher_migration.py'):
            bundle.write(ROOT/'tools'/name,'tools/'+name)
        bundle.write(ROOT/'tools/test_launcher_versioning.py','tools/test_launcher_versioning.py')
        primary=ROOT/'melonDS-source-1.1'
        for directory,dirs,names in os.walk(primary):
            dirs[:]=[d for d in dirs if d not in {'.git','build','__pycache__','test-fixtures','diagnostics'}]
            for name in sorted(names):
                path=Path(directory)/name
                if path.is_symlink() or path.suffix.lower() in PRIVATE|{'.exe','.dll','.obj','.o','.a','.log'}:continue
                relative=path.relative_to(primary).as_posix()
                bundle.write(path,'source/melonDS/'+relative)
        for path in sorted((ROOT/'tools/launcher_ui').rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:bundle.write(path,'tools/launcher_ui/'+path.relative_to(ROOT/'tools/launcher_ui').as_posix())
        for name in ('unova_launcher.py','unova_updater.py','unova_single_exe.py','build_unova_launcher.py','build_unova_single_exe.py','generate_launcher_settings.py','test_launcher_all_settings.py','test_launcher_ui.py','test_launcher_services.py','test_launcher_preferences.py','test_unova_updater.py','test_unova_single_exe.py','verify_launcher_native_lan.py','verify_lan_coop.py','check_battle_presence.cpp','check_field_zone.cpp','check_presence_rendering.cpp','test_presence_server.py','presence_server.py','check_lan_group_pair.cpp','test_gen5_obedience.py','check_obedience_patch.cpp'):
            bundle.write(ROOT/'tools'/name,'tools/'+name)
        for name in ('test_overworld_companion.py','test_companion_and_soaring.py','check_pokemon_follower.cpp','probe_native_item_menu.py','test_party_stats.py','test_field_tools.py','test_field_hms.py','probe_native_field_hms.py','complete_follower_assets.py','verify_complete_followers.py'):
            bundle.write(ROOT/'tools'/name,'tools/'+name)
        for name in ('coop_social.py','test_coop_social.py','item_trading_relay.py','pokemon_trading_relay.py'):
            bundle.write(ROOT/'tools'/name,'tools/'+name)
        for name in ('verify_npc_story_live.py','verify_npc_save_reload.py','inspect_npc_badge.py',
                     'heal_fixture_save.py','record_maintenance_100.py','check_release_101.py',
                     'stage_release_101.py','package_release_101.py','prepare_release_101.py',
                     'check_release_100_native.py','test_coop_experience_suppression.py',
                     'check_coop_experience_guard.cpp'):
            bundle.write(ROOT/'tools'/name,'tools/'+name)
        bundle.write(ROOT/'docs/MAINTENANCE_REVIEW_2026-10-11.md','docs/MAINTENANCE_REVIEW_2026-10-11.md')
        for name in ('test_gen5_experience_boost.py','verify_solo_xp_battle.py',
                     'analyze_redux_xp.py','prepare_release_102.py','check_release_102.py',
                     'stage_release_102.py','package_release_102.py','verify_release_102.py'):
            bundle.write(ROOT/'tools'/name,'tools/'+name)
        for name in ('XP_COMPENSATION.md','XP_COMPENSATION_BATTLE_TEST.md','LAUNCHER_GEN5_TOOLS.md','LAUNCHER_STORAGE.md'):
            bundle.write(ROOT/'docs'/name,'docs/'+name)
        bundle.write(ROOT/'tools/verify_launcher_gen5_tools.py','tools/verify_launcher_gen5_tools.py')
        for name in ('unova_storage.py','test_unova_storage.py'):
            bundle.write(ROOT/'tools'/name,'tools/'+name)
        for name in ('area_scene_cache.py','build_area_battle_scene.py','build_area_battle_catalog.py','install_area_battle_fixture.py','test_area_battle_scene.py','check_rom_asset_overlay.cpp'):
            bundle.write(ROOT/'tools'/name,'tools/'+name)
        for name in ('extract_battle_surroundings.py','field_scene_geometry.py','build_battle_surroundings.py','battle_surroundings_worker.py','test_battle_surroundings.py','verify_battle_surroundings.py','playtest_battle_surroundings.py'):
            bundle.write(ROOT/'tools'/name,'tools/'+name)
        for path in sorted((ROOT/'tools/vendor/nsbmd_writer').rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                bundle.write(path,'tools/vendor/nsbmd_writer/'+path.relative_to(ROOT/'tools/vendor/nsbmd_writer').as_posix())
        bundle.writestr('tools/SCENERY_DEPENDENCIES.txt','ndspy 4.2.0 (GPL-3.0-or-later): https://github.com/RoadrunnerWMC/ndspy\nPillow 12.3.0: https://github.com/python-pillow/Pillow\nCLI geometry previews additionally use NumPy; gameplay/cache generation does not require it.\n')
        # The launcher freezes GPL ndspy bytecode; ship its matching Python
        # source and license alongside our own corresponding source.
        dependency=package_metadata.distribution('ndspy')
        for entry in dependency.files:
            if str(entry).startswith('ndspy/') and str(entry).endswith('.py'):
                bundle.write(dependency.locate_file(entry),'dependencies/'+str(entry))
            elif str(entry).endswith('/LICENSE'):
                bundle.write(dependency.locate_file(entry),'dependencies/ndspy-LICENSE')
        bundle.writestr('README.md','Unova Together by mvq1303 / WhatWasMissing. Corresponding modified melonDS source is in source/melonDS; use its BUILD.md/CMake files. Launcher/bootstrap source is in tools. Keep GPL/upstream notices. Runtime helpers are also distributed as Python source in the installed tools folder. No game ROMs, firmware or user saves are included.\n')
    if args.launcher_source:
        # Keep the retained frozen launcher and its corresponding source aligned.
        revised=source.with_suffix('.reviewed.zip')
        with zipfile.ZipFile(source) as current, zipfile.ZipFile(args.launcher_source) as baseline, zipfile.ZipFile(revised,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as target:
            replacements={n for n in baseline.namelist() if n.startswith('tools/launcher_ui/') or n in {'tools/unova_launcher.py','tools/build_unova_launcher.py'}}
            for name in current.namelist():
                if name not in replacements and not name.startswith('tools/launcher_ui/'):
                    target.writestr(name,current.read(name))
            for name in sorted(replacements):target.writestr(name,baseline.read(name))
        revised.replace(source)
    archive=assets/'runtime.zip';entries=[]
    def add(bundle,path,relative):
        if path.suffix.lower() in PRIVATE:raise ValueError('Private/game file cannot be bundled: '+relative)
        if path.is_symlink():raise ValueError('Linked file cannot be bundled.')
        bundle.write(path,'Unova-Together/'+relative);entries.append(relative)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as bundle:
        for directory in ('launcher','docs','setup','tools'):
            for path in sorted((installed/directory).rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and not any(p.startswith('.') for p in path.relative_to(installed).parts):add(bundle,path,path.relative_to(installed).as_posix())
        runtime=installed/'builds/current'
        for path in sorted(runtime.rglob('*')):
            if path.is_file() and path.suffix.lower() in {'.exe','.dll'} and 'diagnostics' not in path.relative_to(runtime).parts:add(bundle,path,path.relative_to(installed).as_posix())
        add(bundle,runtime/'VERSION.txt','builds/current/VERSION.txt')
        # The reviewed stage supplies a sanitized config with packaged controls.
        add(bundle,runtime/'melonDS.toml','builds/current/melonDS.toml')
        for path in sorted(installed.iterdir()):
            if path.is_file() and (path.suffix.lower() in {'.md','.cmd'} or path.name=='LICENSE'):add(bundle,path,path.name)
        if (installed/'.launcher-integrity.json').is_file():
            add(bundle,installed/'.launcher-integrity.json','.launcher-integrity.json')
        add(bundle,source,'source/Corresponding-Source.zip')
        bundle.writestr('Unova-Together/docs/SINGLE_EXE.md','Run the single EXE. The runtime is unpacked once to %LOCALAPPDATA%/UnovaTogether/Standalone. Saves/profiles/backups persist outside the temporary EXE unpack directory. Updates and repair remain available. Choose your own ROM; no ROM, firmware or user save is bundled. Corresponding GPL source: source/Corresponding-Source.zip. Internet helpers retain their documented setup requirements.\n')
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:raise ValueError('Bundle failed ZIP integrity check.')
        assert not any(Path(n).suffix.lower() in PRIVATE for n in bundle.namelist())
        assert not any('/.updates/' in n or '/diagnostics/' in n or '/save-backups/' in n for n in bundle.namelist())
    metadata={'version':'.'.join(map(str,updates.local_version(installed))),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'launcher_revision':int((installed/'launcher/BUILD_REVISION.txt').read_text().strip())}
    (assets/'bundle.json').write_text(json.dumps(metadata))
    versioning.write_windows_version(ROOT/'tools/launcher_ui/windows-version.txt',work/'windows-version.txt',metadata['version'])
    (work/'package-report.json').write_text(json.dumps({**metadata,'archive_bytes':archive.stat().st_size,'files':len(entries),'source_included':True,'private_files_excluded':True},indent=2))
    output=(args.output_dir.resolve() if args.output_dir else ROOT/'builds/single-exe')
    if not output.is_relative_to(ROOT/'builds'):raise ValueError('Single-EXE output must stay within builds')
    if args.output_dir and output.exists() and any(output.iterdir()):raise FileExistsError('Single-EXE output directory must be fresh')
    output.mkdir(parents=True,exist_ok=True)
    pyinstaller_python=args.pyinstaller_python.resolve() if args.pyinstaller_python else Path(sys.executable)
    if not pyinstaller_python.is_file():raise FileNotFoundError('PyInstaller Python executable does not exist')
    subprocess.run([str(pyinstaller_python),'-m','PyInstaller','--noconfirm','--onefile','--windowed','--noupx',
        '--name','Unova Together','--icon',str(ROOT/'tools/launcher_ui/assets/launcher.ico'),
        '--version-file',str(work/'windows-version.txt'),
        '--add-data',str(assets)+';single-exe','--distpath',str(output),
        '--workpath',str(work/'pyinstaller'),'--specpath',str(work),str(ROOT/'tools/unova_single_exe.py')],check=True,cwd=ROOT)
    executable=output/'Unova Together.exe'
    (output/'SHA256SUMS.txt').write_text(hashlib.sha256(executable.read_bytes()).hexdigest()+'  '+executable.name+'\n')
    print(json.dumps({'exe':str(executable),'bytes':executable.stat().st_size,'runtime_sha256':metadata['sha256'],'source_included':True}))

if __name__=='__main__':main()
