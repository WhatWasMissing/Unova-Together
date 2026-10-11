"""Complete a solo NPC battle with ordinary input on a disposable save."""
from pathlib import Path
import argparse, binascii, hashlib, itertools, json, os, re, shutil, struct, subprocess, time
from heal_fixture_save import crypt
from inspect_npc_badge import inspect

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'test-fixtures/coop-launcher'

def decode(record):
    pid,flags,checksum=struct.unpack_from('<IHH',record)
    assert flags==0
    blocks=crypt(record[8:136],checksum)
    assert sum(struct.unpack('<64H',blocks))&65535==checksum
    order=list(itertools.permutations(range(4)))[((pid>>13)&31)%24]
    canonical=b''.join(blocks[order.index(i)*32:order.index(i)*32+32] for i in range(4))
    ext=crypt(record[136:],pid)
    return dict(pid=pid,species=struct.unpack_from('<H',canonical)[0],
                xp=struct.unpack_from('<I',canonical,8)[0],level=ext[4],
                hp=struct.unpack_from('<H',ext,6)[0],
                moves=list(struct.unpack_from('<4H',canonical,32)))

def ram_party(path):
    raw=path.read_bytes()
    def word(p):
        assert 0x02000000<=p<=0x023ffffc and not p&3
        return struct.unpack_from('<I',raw,p-0x02000000)[0]
    proc=word(word(0x02141858)+8)
    for _ in range(32):
        if word(proc)==0x02090010 and word(proc+4)==0xffffffff:
            data=word(word(proc+20)+28);party=word(data+0x194);count=word(party+4)
            assert 1<=count<=6
            return [decode(raw[party-0x02000000+8+i*220:party-0x02000000+8+(i+1)*220]) for i in range(count)]
        proc=word(proc+24)
    raise AssertionError('No validated party owner')

def save_parties(raw):
    result=[]
    for bank in (0,0x26000):
        offset=bank+0x18e00
        if binascii.crc_hqx(raw[offset:offset+0x534],0xffff)!=struct.unpack_from('<H',raw,bank+0x19336)[0]:continue
        count=struct.unpack_from('<I',raw,offset+4)[0]
        assert 1<=count<=6
        result.append(dict(bank=hex(bank),badgeMask=raw[bank+0x21104],
                           party=[decode(raw[offset+8+i*220:offset+8+(i+1)*220]) for i in range(count)]))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--exe',type=Path,default=ROOT/'builds/current/melonDS.exe')
    p.add_argument('--runtime',type=Path,default=FIX/'maintenance-100-runtime')
    p.add_argument('--save',type=Path,default=FIX/'npc-dialogue-20261007/boosted-inputs/Redux.sav')
    p.add_argument('--seconds',type=int,default=300)
    p.add_argument('--fps',type=int,default=60,help='Private fixture frame limit; does not change game data')
    a=p.parse_args();a.output=a.output.resolve()
    assert a.output.is_relative_to(FIX.resolve()) and not a.output.exists()
    before=a.save.read_bytes();rom=FIX/'game/Redux-maintenance.nds'
    def copy(source,destination):
        if Path(source).suffix.lower()=='.dll':os.link(source,destination);return destination
        return shutil.copy2(source,destination)
    shutil.copytree(a.runtime,a.output,copy_function=copy,ignore=shutil.ignore_patterns('melonDS.exe'))
    shutil.copy2(a.exe,a.output/'melonDS.exe')
    config=(a.output/'melonDS.toml').read_text(encoding='utf-8-sig')
    config=re.sub(r'SaveFilePath = "[^"]*"','SaveFilePath = '+json.dumps(a.output.as_posix()),config)
    assert 30<=a.fps<=240
    config=re.sub(r'TargetFPS = [^\n]+',f'TargetFPS = {float(a.fps)}',config)
    config=re.sub(r'(?ms)^\[Instance\d+\.Audio\]\n.*?(?=^\[|\Z)','',config)
    config+='\n[Instance0.Audio]\nVolume = 0\nDSiVolumeSync = false\n'
    (a.output/'melonDS.toml').write_text(config,encoding='utf-8')
    shutil.copy2(a.save,a.output/rom.with_suffix('.sav').name)
    script=a.output/'input.json';prefix=a.output/'battle'
    script.write_text(json.dumps([dict(frame=f,duration=4,keyMask=0xffe) for f in range(120,7200,30)]))
    env={k:v for k,v in os.environ.items() if not k.startswith('POKEPLAY_')}
    env.update(POKEPLAY_COOP_PREPARATION_CHECK='1',POKEPLAY_NPC_STORY_CHECK='1',
               POKEPLAY_NPC_BATTLE_MODE='solo',POKEPLAY_COOP_PREPARATION_STATE='',
               POKEPLAY_COOP_PREPARATION_REPORT=str(prefix),POKEPLAY_COOP_BATTLE_SCRIPT=str(script))
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    history=[];battle=False;returned=None;saved=None;initial=None;disk_candidate=None
    with (a.output/'battle.log').open('w',encoding='utf-8') as log:
        proc=subprocess.Popen([str(a.output/'melonDS.exe'),str(rom)],cwd=a.output,env=env,startupinfo=startup,stdout=log,stderr=log)
        try:
            deadline=time.monotonic()+a.seconds;last=None
            while time.monotonic()<deadline:
                assert proc.poll() is None,'Emulator exited'
                try:d=json.loads(Path(str(prefix)+'.npc.json').read_text(encoding='utf-8'))
                except (OSError,json.JSONDecodeError):time.sleep(.2);continue
                frame=d['npcFixtureFrames'];pos=d.get('npcFixturePosition',{});in_battle=pos.get('inBattle',False)
                if not history or history[-1]['npcFixtureFrames']!=frame:history.append(d)
                if initial is None and not in_battle and pos.get('status')=='Experimental match':
                    capture=Path(str(prefix)+'.npc.ramdump')
                    if capture.exists():
                        try:initial=ram_party(capture);shutil.copy2(capture,a.output/'before.ramdump')
                        except (AssertionError,struct.error):pass
                if in_battle and not battle:
                    battle=True;print('Genuine solo NPC battle began at frame',frame,flush=True)
                    steps=[]
                    for f in range(frame+180,frame+40000,180):
                        steps.extend([dict(frame=f,duration=4,keyMask=0xffe),dict(frame=f+30,duration=4,x=128,y=100),
                                      dict(frame=f+60,duration=4,x=62,y=110),dict(frame=f+90,duration=4,keyMask=0xffd),
                                      dict(frame=f+120,duration=4,keyMask=0xffd),dict(frame=f+150,duration=4,keyMask=0xffd)])
                    script.write_text(json.dumps(steps))
                if battle and not in_battle and pos.get('status')=='Experimental match' and returned is None:
                    returned=frame;print('Returned from battle at frame',frame,flush=True)
                    # Cheren's post-victory dialogue needs A before the field menu opens.
                    script.write_text(json.dumps([dict(frame=f,duration=4,keyMask=0xffe) for f in range(frame+60,frame+3600,30)]))
                status=(in_battle,pos.get('map'),frame//600)
                if status!=last:print('Progress',frame,'battle',in_battle,'map',pos.get('map'),flush=True);last=status
                if returned is not None and frame>=returned+600 and saved is None:
                    capture=Path(str(prefix)+'.npc.ramdump')
                    final=ram_party(capture);badge=inspect(capture)
                    if badge['cherenBadge']:
                        shutil.copy2(capture,a.output/'after.ramdump')
                        saved=frame
                        steps=[]
                        for f in range(frame+120,frame+3600,90):
                            # Walk away as soon as story dialogue finishes so
                            # repeated A inputs cannot reopen Cheren's conversation.
                            steps.extend([dict(frame=f,duration=4,keyMask=0xffe),dict(frame=f+30,duration=30,keyMask=0xf7f)])
                        steps.extend([dict(frame=frame+3840,duration=4,keyMask=0xbff),dict(frame=frame+4080,duration=4,x=64,y=143)])
                        steps.extend(dict(frame=f,duration=4,keyMask=0xffe) for f in range(frame+4200,frame+6000,30))
                        script.write_text(json.dumps(steps));print('Victory badge verified; saving through game UI',flush=True)
                if saved is not None and frame>=saved+6000:
                    disk=(a.output/rom.with_suffix('.sav').name).read_bytes()
                    saved_parties=save_parties(disk)
                    normal_save=any(b['badgeMask']&1 and b['party']==final for b in saved_parties)
                    if not normal_save:
                        # Saving takes multiple stages; keep the emulator alive
                        # until validated party data and the real badge reach disk.
                        time.sleep(.2)
                        continue
                    disk_hash=hashlib.sha256(disk).hexdigest()
                    if disk_candidate is None or disk_candidate[0]!=disk_hash:
                        disk_candidate=(disk_hash,frame)
                        time.sleep(.2)
                        continue
                    if frame<disk_candidate[1]+600:
                        # Let the complete flash-save transaction settle before shutdown.
                        time.sleep(.2)
                        continue
                    evidence=dict(initialParty=initial,finalParty=final,badge=badge,history=history,
                                  battleCompleted=True,normalSaveVerified=normal_save,diskParties=saved_parties,
                                  sourceSaveSha256=hashlib.sha256(before).hexdigest(),exeSha256=hashlib.sha256(a.exe.read_bytes()).hexdigest(),
                                  copiedSaveSha256=hashlib.sha256(disk).hexdigest())
                    (a.output/'summary.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
                    assert initial and final[0]['xp']>initial[0]['xp'],'No real XP gained'
                    assert a.save.read_bytes()==before,'Source save changed'
                    print(json.dumps({k:v for k,v in evidence.items() if k!='history'}),flush=True)
                    assert normal_save,'Battle passed, but the normal-save input did not write the actual result'
                    return
                time.sleep(.2)
            (a.output/'timeout.json').write_text(json.dumps(dict(history=history,initialParty=initial,battle=battle,returned=returned),indent=2),encoding='utf-8')
            raise AssertionError('Battle/save test timed out')
        finally:
            if proc.poll() is None:proc.terminate()
            proc.wait(timeout=10)

if __name__=='__main__':main()
