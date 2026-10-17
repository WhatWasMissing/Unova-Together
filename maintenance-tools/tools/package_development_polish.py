"""Publish a reproducible source delta; exclude ROMs, saves and private evidence."""
from pathlib import Path
import difflib, hashlib, json, shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT/'tools/unova-together-release'
SOURCE=ROOT/'melonDS-source-1.1'
BASE=ROOT/'downloads/releases/release-1.0.6-publish/Unova-Together-1.0.6-Source.zip'
PREFIX='Unova-Together-Source/source/melonDS/'
def main():
    delta=[];changed=[]
    with zipfile.ZipFile(BASE) as baseline:
        members=set(baseline.namelist())
        paths=[p for folder in ('src','res') for p in (SOURCE/folder).rglob('*') if p.is_file() and (p.suffix in ('.h','.cpp','.c','.qrc') or p.name=='melon.rc.in')]
        for path in sorted(paths):
            relative=path.relative_to(SOURCE).as_posix();member=PREFIX+relative
            previous=baseline.read(member).decode('utf-8-sig').replace('\r\n','\n') if member in members else ''
            current=path.read_text(encoding='utf-8-sig').replace('\r\n','\n')
            if previous==current:continue
            target='source/melonDS/'+relative
            delta.extend(difflib.unified_diff(previous.splitlines(True),current.splitlines(True),fromfile='a/'+target if previous else '/dev/null',tofile='b/'+target))
            changed.append(relative)
    patch=REPO/'maintenance-tools/patches/development-polish.patch';patch.write_text(''.join(delta),encoding='utf-8',newline='\n')
    assets=REPO/'maintenance-tools/assets/followers'
    shutil.copytree(SOURCE/'res/followers/variants',assets/'variants',dirs_exist_ok=True)
    for name in ('ASSET_TERMS.md','CREDITS.md'):
        if (SOURCE/'res/followers'/name).exists():shutil.copy2(SOURCE/'res/followers'/name,assets/name)
    references=REPO/'maintenance-tools/references/follower-completion-20261010';references.mkdir(parents=True,exist_ok=True)
    for name in ('hg-engine-tree.json','hg-species.h'):
        shutil.copy2(ROOT/'research/follower-completion-20261010'/name,references/name)
    for destination in (REPO/'launcher-source/tools/launcher_ui',REPO/'maintenance-tools/tools/launcher_ui'):
        shutil.copytree(ROOT/'tools/launcher_ui',destination,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    names=('build_follower_variants.py','test_follower_polish.py','test_super_repel_shops.py','check_super_repel_shops.cpp','check_pokemon_follower.cpp','check_presence_rendering.cpp','check_camera_continuity.cpp','check_battle_badge.cpp','test_party_stats.py','test_companion_interactions.py','test_coop_field_return.py','build_coop_payload.py','check_lan_group_pair.cpp','presence_server.py','test_presence_server.py','test_launcher_ui.py','test_launcher_services.py','test_launcher_preferences.py','build_unova_launcher.py','verify_lan_coop.py','package_development_polish.py')
    for name in names:shutil.copy2(ROOT/'tools'/name,REPO/'maintenance-tools/tools'/name)
    for name in ('build_unova_launcher.py','test_launcher_ui.py','test_launcher_services.py','test_launcher_preferences.py'):
        shutil.copy2(ROOT/'tools'/name,REPO/'launcher-source/tools'/name)
    metadata={'baseline':BASE.name,'baselineSha256':hashlib.file_digest(BASE.open('rb'),'sha256').hexdigest(),'changedNativeFiles':changed,'patchSha256':hashlib.sha256(patch.read_bytes()).hexdigest(),'spriteVariants':743,'build':'1.0.7-dev'}
    (REPO/'maintenance-tools/patches/development-polish.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata,indent=2))
if __name__=='__main__':main()
