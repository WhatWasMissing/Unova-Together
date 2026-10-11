"""Normally boot a disposable saved game and compare its party/badge to disk evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

from verify_solo_xp_battle import ROOT, FIX, ram_party
from inspect_npc_badge import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', required=True, type=Path)
    parser.add_argument('--expected', required=True, type=Path, help='PKHeX inspector JSON')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--exe', required=True, type=Path)
    parser.add_argument('--seconds', type=int, default=90)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(FIX.resolve()) and not output.exists()
    expected = json.loads(args.expected.read_text(encoding='utf-8'))
    assert expected['checksumsValid'] and expected['sourceUnchanged']
    original = args.save.read_bytes()
    assert hashlib.sha256(original).hexdigest() == expected['sourceSha256']
    def copy(source, destination):
        if Path(source).suffix.lower() == '.dll':
            os.link(source, destination)
            return destination
        return shutil.copy2(source, destination)
    shutil.copytree(FIX/'maintenance-100-runtime', output, copy_function=copy,
                    ignore=shutil.ignore_patterns('melonDS.exe'))
    shutil.copy2(args.exe, output/'melonDS.exe')
    config = (output/'melonDS.toml').read_text(encoding='utf-8-sig')
    config = re.sub(r'SaveFilePath = "[^"]*"', 'SaveFilePath = '+json.dumps(output.as_posix()), config)
    config = re.sub(r'(?ms)^\[Instance\d+\.Audio\]\n.*?(?=^\[|\Z)', '', config)
    config += '\n[Instance0.Audio]\nVolume = 0\nDSiVolumeSync = false\n'
    (output/'melonDS.toml').write_text(config, encoding='utf-8')
    rom = FIX/'game/Redux-maintenance.nds'
    shutil.copy2(args.save, output/rom.with_suffix('.sav').name)
    script = output/'input.json'
    script.write_text(json.dumps([dict(frame=f, duration=4, keyMask=0xffe)
                                  for f in range(120, 7200, 30)]), encoding='utf-8')
    prefix = output/'reload'
    env = {k:v for k,v in os.environ.items() if not k.startswith('POKEPLAY_')}
    env.update(POKEPLAY_COOP_PREPARATION_CHECK='1', POKEPLAY_NPC_STORY_CHECK='1',
               POKEPLAY_NPC_BATTLE_MODE='solo', POKEPLAY_COOP_PREPARATION_STATE='',
               POKEPLAY_COOP_PREPARATION_REPORT=str(prefix), POKEPLAY_COOP_BATTLE_SCRIPT=str(script))
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    with (output/'reload.log').open('w', encoding='utf-8') as log:
        proc = subprocess.Popen([str(output/'melonDS.exe'), str(rom)], cwd=output, env=env,
                                startupinfo=startup, stdout=log, stderr=log)
        try:
            deadline = time.monotonic()+args.seconds
            while time.monotonic() < deadline:
                assert proc.poll() is None, 'Emulator exited'
                try:
                    state = json.loads(Path(str(prefix)+'.npc.json').read_text(encoding='utf-8'))
                    position = state.get('npcFixturePosition', {})
                    capture = Path(str(prefix)+'.npc.ramdump')
                    if position.get('status') != 'Experimental match' or not capture.exists():
                        time.sleep(.2)
                        continue
                    party = ram_party(capture)
                    badge = inspect(capture)
                except (OSError, json.JSONDecodeError, AssertionError):
                    time.sleep(.2)
                    continue
                # Check identity, accumulated XP, level and moves; HP may change after dialogue.
                keys = ('pid', 'species', 'xp', 'level', 'moves')
                actual = [{k:p[k] for k in keys} for p in party]
                wanted = [{k:p[k] for k in keys} for p in expected['party']]
                assert actual == wanted, 'Restarted party differs from the actual saved party'
                assert badge['cherenBadge'] == bool(expected['badgeMask'] & 1), 'Reloaded badge differs'
                assert args.save.read_bytes() == original, 'Source save changed'
                report = dict(normalBoot=True, savestateUsed=False, reloadVerified=True,
                              party=party, badge=badge, sourceSha256=expected['sourceSha256'],
                              exeSha256=hashlib.sha256(args.exe.read_bytes()).hexdigest())
                (output/'summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
                print(json.dumps(report, indent=2))
                return
            raise AssertionError('Saved-game reload did not reach a validated field party')
        finally:
            if proc.poll() is None:
                proc.terminate()
            proc.wait(timeout=10)


if __name__ == '__main__':
    main()
