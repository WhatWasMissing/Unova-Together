"""Verify and collect the exact standalone payload as the 1.0.3 release assets."""
from pathlib import Path
import hashlib, json, shutil, tomllib, zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'downloads/releases/release-1.0.3-final'
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert not any(OUT.iterdir()), 'Fresh output directory required'
    work=ROOT/'test-fixtures/single-exe-build-20261009'
    runtime=work/'single-exe/runtime.zip'
    metadata=json.loads((work/'single-exe/bundle.json').read_text())
    assert metadata['version']=='1.0.3'
    assert hashlib.sha256(runtime.read_bytes()).hexdigest()==metadata['sha256']
    source=work/'Corresponding-Source.zip'
    stage=ROOT/'builds/release-1.0.3/Unova-Together'
    forbidden={'.nds','.gba','.sav','.save','.dsv','.ramdump','.ml1','.ml2','.ml3','.ml4','.ml5','.ml6','.ml7','.ml8','.pem','.key','.pyc'}
    for archive in (runtime,source):
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for name in z.namelist():
                assert Path(name).suffix.lower() not in forbidden,name
                assert not any(part in {'.git','diagnostics','trade-state','save-backups','play-profiles'} for part in Path(name).parts),name
                assert Path(name).name.lower() not in {'firmware.bin','bios7.bin','bios9.bin','wfcsettings.bin'},name
    with zipfile.ZipFile(runtime) as z:
        prefix='Unova-Together/'
        assert z.read(prefix+'builds/current/melonDS.exe')==(stage/'builds/current/melonDS.exe').read_bytes()
        assert z.read(prefix+'launcher/Unova Together.exe')==(stage/'launcher/Unova Together.exe').read_bytes()
        config=tomllib.loads(z.read(prefix+'builds/current/melonDS.toml').decode())
        original=tomllib.loads((ROOT/'builds/current/melonDS.toml').read_text(encoding='utf-8-sig'))
        assert config['Instance0']['Keyboard']==original['Instance0']['Keyboard']
        assert config['Instance0']['Joystick']==original['Instance0']['Joystick']
        assert 'SaveFilePath' not in str(config)
        assert z.read(prefix+'source/Corresponding-Source.zip')==source.read_bytes()
    with zipfile.ZipFile(source) as z:
        matched=0
        for name in z.namelist():
            if name=='tools/SCENERY_DEPENDENCIES.txt':continue
            if name.startswith('source/melonDS/'):
                local=ROOT/'melonDS-source-1.1'/name[len('source/melonDS/'):]
            elif name.startswith('tools/'):
                local=ROOT/name
            else:continue
            assert local.is_file() and z.read(name)==local.read_bytes(),name
            matched+=1
    assets=[OUT/'Unova-Together-1.0.3-Windows-x64.zip',OUT/'Unova-Together-1.0.3-Source.zip',OUT/'Unova-Together.exe']
    for src,dest in zip((runtime,source,ROOT/'builds/single-exe/Unova Together.exe'),assets):shutil.copy2(src,dest)
    checksums=OUT/'SHA256SUMS-Unova-Together-1.0.3.txt'
    checksums.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in assets),encoding='utf-8')
    report={'version':'1.0.3','fullRelease':True,'sourceFilesMatched':matched,'controlsPreserved':True,'privateFilesExcluded':True,'archiveIntegrityPassed':True,'assets':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in assets]}
    (ROOT/'test-fixtures/release-1.0.3/package.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
