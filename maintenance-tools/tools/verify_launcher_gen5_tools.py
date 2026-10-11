"""Exercise launcher tools and byte-exact backups with disposable real save copies."""
from pathlib import Path
import json, tempfile, time, zipfile
from unittest.mock import patch
from launcher_ui.app import Launcher
from launcher_ui import services, gen5_tools

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-fixtures/launcher-gen5-tools-20261011'
ROM=ROOT/'game-files/rom-original/Pokemon Black 2 Redux Complete (v1.4.1).nds'
OLD=ROOT/'test-fixtures/coop-launcher/npc-dialogue-20261007/boosted-inputs/Redux.sav'
NEW=ROOT/'test-fixtures/coop-launcher/xp-102-save-reload-02/Redux-maintenance.sav'

def main():
    OUT.mkdir(parents=True,exist_ok=True);before={str(p):gen5_tools.digest(p) for p in (ROM,OLD,NEW)}
    with tempfile.TemporaryDirectory() as folder:
        home=Path(folder);runtime=home/'builds/current';runtime.mkdir(parents=True);(runtime/'VERSION.txt').write_text('1.0.2');(runtime/'melonDS.exe').write_bytes(b'fixture')
        app=Launcher(home,testing=True)
        try:
            item=app._active_profile();item.update(rom=str(ROM),save_dir=str(home/'saves'));saves=Path(item['save_dir']);saves.mkdir()
            names=[ROM.stem+'.save',ROM.stem+'.2.save',ROM.stem+'.sav',ROM.stem+'.dsv']
            for name in names:(saves/name).write_bytes(NEW.read_bytes())
            (saves/'different-profile.save').write_bytes(OLD.read_bytes())
            app.show_page('Tools');app.update();app._backup_now();archive=app.backup_paths[0]
            with zipfile.ZipFile(archive) as bundle:
                assert set(json.loads(bundle.read('manifest.json'))['files'][i]['name'] for i in range(4))==set(names)
                assert all(bundle.read(name)==NEW.read_bytes() for name in names)
            for name in names:(saves/name).write_bytes(OLD.read_bytes())
            app.backup_picker.current(0)
            with patch('launcher_ui.app.prefs.any_running',return_value=False):app._restore_backup()
            assert 'Restored 4' in app.status.get(),app.status.get()
            assert all((saves/name).read_bytes()==NEW.read_bytes() for name in names)
            retained=next(p for p in app.backup_paths if 'before-restore' in p.name)
            with zipfile.ZipFile(retained) as bundle:assert all(bundle.read(name)==OLD.read_bytes() for name in names)
            assert (saves/'different-profile.save').read_bytes()==OLD.read_bytes()
            restored=OUT/'restored.save';restored.write_bytes((saves/names[0]).read_bytes())
            for task in (app._check_rom,app._calculate_progression):
                task();deadline=time.monotonic()+60
                while app.busy and time.monotonic()<deadline:app.update();time.sleep(.02)
                assert not app.busy and app.status.get()=='Read-only inspection complete.',app.status.get()
                output=app.tool_text.get('1.0','end');assert ('PASS: XP' in output if task==app._check_rom else 'Iris' in output)
            comparison=gen5_tools.compare_saves(OLD,restored);assert '5951' in comparison and '5144' in comparison
            app._worker('tool-result',lambda:comparison)
            while app.busy:app.update();time.sleep(.02)
            app.update();(OUT/'comparison.txt').write_text(comparison,encoding='utf-8')
            report=dict(backupRestoreByteExact=True,formats=names,previousSavePreserved=True,otherProfileUntouched=True,restoredSha256=gen5_tools.digest(restored),romCheck=gen5_tools.compatibility(ROM),progression=gen5_tools.progression(ROM,25),party=gen5_tools.inspect_save(restored))
        finally:app.destroy()
    assert all(gen5_tools.digest(p)==value for p,value in before.items())
    report['originalInputsUnchanged']=True;(OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ('romCheck','progression','party')},indent=2))

if __name__=='__main__':main()
