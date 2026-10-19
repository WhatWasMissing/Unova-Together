"""Publish a reproducible source delta; exclude ROMs, saves and private evidence."""
from pathlib import Path
import argparse
import difflib, hashlib, json, shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT/'tools/unova-together-release'
SOURCE=ROOT/'melonDS-source-1.1'
BASE=ROOT/'downloads/releases/release-1.0.6-publish/Unova-Together-1.0.6-Source.zip'
PREFIX='Unova-Together-Source/source/melonDS/'

def unified_diff_lines(before, after, fromfile, tofile):
    """Emit valid Git patch records even when source files lack final newlines."""
    lines=difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=fromfile,tofile=tofile)
    records=[]
    for index,line in enumerate(lines):
        if line.endswith(('\n','\r')):
            records.append(line)
        elif index >= 3 and line[:1] in (' ','+','-'):
            records.extend((line+'\n','\\ No newline at end of file\n'))
        else:
            records.append(line+'\n')
    return records

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--patch-only',action='store_true',help='regenerate the source patch and metadata without copying assets or mirrored tools')
    parser.add_argument('--base-zip',type=Path,default=BASE,help='verified 1.0.6 source archive used as the patch baseline')
    parser.add_argument('--output-root',type=Path,default=REPO,help='repository root that receives generated patch and assets')
    args=parser.parse_args()
    base_archive=args.base_zip
    output_root=args.output_root
    delta=[];changed=[]
    with zipfile.ZipFile(base_archive) as baseline:
        members=set(baseline.namelist())
        paths=[p for folder in ('src','res') for p in (SOURCE/folder).rglob('*') if p.is_file() and (p.suffix in ('.h','.cpp','.c','.qrc') or p.name in ('CMakeLists.txt','melon.rc.in'))]
        for path in sorted(paths):
            relative=path.relative_to(SOURCE).as_posix();member=PREFIX+relative
            previous=baseline.read(member).decode('utf-8-sig').replace('\r\n','\n') if member in members else ''
            current=path.read_text(encoding='utf-8-sig').replace('\r\n','\n')
            if previous==current:continue
            target='source/melonDS/'+relative
            delta.extend(unified_diff_lines(previous,current,fromfile='a/'+target if previous else '/dev/null',tofile='b/'+target))
            changed.append(relative)
    patch=output_root/'maintenance-tools/patches/development-polish.patch';patch.write_text(''.join(delta),encoding='utf-8',newline='\n')
    with base_archive.open('rb') as baseline_file:
        baseline_sha256=hashlib.file_digest(baseline_file,'sha256').hexdigest()
    version_file=output_root/'VERSION.txt'
    build_label=version_file.read_text(encoding='utf-8-sig').strip().removeprefix('Unova Together ') if version_file.is_file() else 'development'
    metadata={'baseline':base_archive.name,'baselineSha256':baseline_sha256,'changedNativeFiles':changed,'patchSha256':hashlib.sha256(patch.read_bytes()).hexdigest(),'spriteVariants':743,'build':build_label}
    (output_root/'maintenance-tools/patches/development-polish.json').write_text(json.dumps(metadata,indent=2)+'\n')
    if args.patch_only:
        print(json.dumps(metadata,indent=2))
        return
    assets=output_root/'maintenance-tools/assets/followers'
    shutil.copytree(SOURCE/'res/followers/variants',assets/'variants',dirs_exist_ok=True)
    for name in ('ASSET_TERMS.md','CREDITS.md'):
        if (SOURCE/'res/followers'/name).exists():shutil.copy2(SOURCE/'res/followers'/name,assets/name)
    references=output_root/'maintenance-tools/references/follower-completion-20261010';references.mkdir(parents=True,exist_ok=True)
    for name in ('hg-engine-tree.json','hg-species.h'):
        shutil.copy2(ROOT/'research/follower-completion-20261010'/name,references/name)
    for destination in (output_root/'launcher-source/tools/launcher_ui',output_root/'maintenance-tools/tools/launcher_ui'):
        shutil.copytree(ROOT/'tools/launcher_ui',destination,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    names=('build_follower_variants.py','test_follower_polish.py','test_super_repel_shops.py','check_super_repel_shops.cpp','check_pokemon_follower.cpp','check_presence_rendering.cpp','check_camera_continuity.cpp','check_battle_badge.cpp','test_party_stats.py','test_companion_interactions.py','test_coop_field_return.py','build_coop_payload.py','check_lan_group_pair.cpp','presence_server.py','test_presence_server.py','test_launcher_ui.py','test_launcher_services.py','test_launcher_preferences.py','build_unova_launcher.py','verify_lan_coop.py','package_development_polish.py')
    for name in names:shutil.copy2(ROOT/'tools'/name,output_root/'maintenance-tools/tools'/name)
    for name in ('build_unova_launcher.py','test_launcher_ui.py','test_launcher_services.py','test_launcher_preferences.py'):
        shutil.copy2(ROOT/'tools'/name,output_root/'launcher-source/tools'/name)
    print(json.dumps(metadata,indent=2))
if __name__=='__main__':main()
