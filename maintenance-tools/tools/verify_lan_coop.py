"""Private two-process native LAN battle check with a delayed UDP link."""
from pathlib import Path
import argparse,hashlib,heapq,json,os,re,select,shutil,socket,struct,subprocess,threading,time
ROOT=Path(__file__).resolve().parents[1]; FIX=ROOT/'test-fixtures/coop-launcher'
p=argparse.ArgumentParser();p.add_argument('--retry-after-cancel',action='store_true',help='Start a second battle after native checkpoint rollback');p.add_argument('--spectator',action='store_true',help='Connect an idle first guest before the active battle partner')
p.add_argument('--delay-ms',type=int,default=0);p.add_argument('--seconds',type=int,default=65);p.add_argument('--boss',type=int,default=156);p.add_argument('--port',type=int,default=17064);p.add_argument('--cancel-frame',type=int);p.add_argument('--forfeit-frame',type=int);p.add_argument('--baseline',action='store_true');p.add_argument('--pvp',action='store_true');p.add_argument('--rom',type=Path,default=FIX/'game/Redux.nds')
p.add_argument('--output-root',type=Path,help='Fresh private output directory; never reuse prior evidence')
p.add_argument('--runtime-dir',type=Path,default=FIX/'runtime')
p.add_argument('--save',type=Path,help='Disposable fixture save; source remains unchanged')
p.add_argument('--story-return',action='store_true',help='Retained synthetic parent; does not verify real NPC awards')
p.add_argument('--require-completion',action='store_true',help='Fail unless both games return an actual completed battle result')
p.add_argument('--move-slot',type=int,choices=(1,2,3,4),default=1,help='Real battle-menu move slot; use a damaging move for completion tests')
p.add_argument('--battle-delay-ms',type=int,help='Increase one-way delay only after both native battle scenes are running')
p.add_argument('--online-udp',action='store_true',help='Route native ENet through both encrypted UDP bridges and relay on loopback')
p.add_argument('--disconnect-guest',action='store_true',help='Terminate the private guest after both battles run; require host rollback and released allocations')
a=p.parse_args()
assert not a.disconnect_guest or not (a.cancel_frame or a.retry_after_cancel or a.require_completion or a.forfeit_frame), 'Guest loss is a separate recovery check'
assert not a.online_udp or (a.delay_ms == 0 and a.battle_delay_ms is None), 'UDP relay fixture does not inject delay'
a.runtime_dir=a.runtime_dir.resolve()
if a.output_root:a.output_root=a.output_root.resolve()
assert a.runtime_dir.resolve().is_relative_to(FIX.resolve())
if a.output_root:
    assert a.output_root.resolve().is_relative_to(FIX.resolve())
    a.output_root.mkdir(parents=True,exist_ok=False)
OUTPUT=a.output_root or FIX
assert not (a.story_return and a.pvp)
assert a.rom.resolve().is_relative_to(FIX.resolve()),'Use only a copied private fixture ROM'
if a.save: assert a.save.resolve().is_relative_to(FIX.resolve()),'Use only a copied private fixture save'
label=('sync' if a.baseline else 'async')+f'-{a.delay_ms}ms-'+('pvp' if a.pvp else f'boss{a.boss}')
if a.rom.name!='Redux.nds':label+='-'+a.rom.stem.lower()
if a.cancel_frame:label+='-cancel'
if a.online_udp:label+='-encrypted-relay'
if a.disconnect_guest:label+='-guest-loss'
if a.battle_delay_ms is not None:label+=f'-battle-delay-{a.battle_delay_ms}ms'
if a.retry_after_cancel:
    assert a.cancel_frame and not a.story_return
    label+='-retry'
if a.forfeit_frame:label+='-forfeit'
stop=threading.Event()
current_delay=a.delay_ms
delay_changed=False

def copy_runtime_file(source,destination):
    # Prior fixture libraries may share immutable archived DLL storage.
    # Replace the path atomically; never overwrite a shared library in place.
    source=Path(source);destination=Path(destination)
    if destination.exists() and os.path.samefile(source,destination):return str(destination)
    if destination.exists() and source.stat().st_size==destination.stat().st_size:
        with source.open('rb') as stream:source_hash=hashlib.file_digest(stream,'sha256').digest()
        with destination.open('rb') as stream:destination_hash=hashlib.file_digest(stream,'sha256').digest()
        if source_hash==destination_hash:return str(destination)
    temporary=destination.with_name(destination.name+'.incoming')
    assert not temporary.exists()
    shutil.copy2(source,temporary)
    os.replace(temporary,destination)
    return str(destination)
def udp_proxy():
    import asyncio
    from types import SimpleNamespace
    from online_udp_relay import Relay
    from online_udp_bridge import bridge
    async def run():
        key=bytes(range(32));relay=Relay(key)
        transport,_=await asyncio.get_running_loop().create_datagram_endpoint(lambda:relay,local_addr=('127.0.0.1',0))
        server=await asyncio.start_server(relay.connection,'127.0.0.1',0)
        tasks=[]
        try:
            port=server.sockets[0].getsockname()[1]
            for role in ('host','guest'):
                args=SimpleNamespace(server='127.0.0.1',port=port,room='native-fixture',role=role,
                    access_key=key.hex(),ca=None,loopback_test=True,host_port=a.port,local_port=a.port+1)
                tasks.append(asyncio.create_task(bridge(args,lambda value:print('UDP',value,flush=True))))
            while not stop.is_set():
                for task in tasks:
                    if task.done():task.result();raise RuntimeError('UDP bridge exited')
                await asyncio.sleep(.05)
        finally:
            for task in tasks:task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
            server.close();await server.wait_closed();transport.close()
    asyncio.run(run())

def proxy():
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.bind(('127.0.0.1',a.port+1));sock.setblocking(False)
    server=('127.0.0.1',a.port);client=None;pending=[];serial=0
    try:
        while not stop.is_set():
            ready,_,_=select.select([sock],[],[],.001)
            if ready:
                try:data,address=sock.recvfrom(65536)
                except ConnectionResetError:continue
                if address==server: target=client
                else:client=address;target=server
                if target:
                    serial+=1;heapq.heappush(pending,(time.monotonic()+current_delay/1000,serial,target,data))
            while pending and pending[0][0]<=time.monotonic():
                _,_,target,data=heapq.heappop(pending);sock.sendto(data,target)
    finally:sock.close()
thread=threading.Thread(target=udp_proxy if a.online_udp else proxy);thread.start();processes=[];spectators=[];logs=[];samples=[[],[]];original_parties=[None,None]
try:
    reports=[]
    for i,role in enumerate(('host','guest')):
        folder=OUTPUT/f'lan-{label}-{role}';folder.mkdir(exist_ok=True)
        for source in a.runtime_dir.iterdir():
            if source.is_file() and (source.suffix.lower() in ('.dll','.exe') or source.name=='VERSION.txt'):copy_runtime_file(source,folder/source.name)
        for name in ('platforms','imageformats','styles','tls','networkinformation','multimedia','generic','iconengines'):
            source=a.runtime_dir/name
            if source.is_dir():shutil.copytree(source,folder/name,dirs_exist_ok=True,copy_function=copy_runtime_file)
        config=(a.runtime_dir/'melonDS.toml').read_text(encoding='utf-8-sig')
        config=re.sub(r'MAC = "[^"]*"',f'MAC = "00:09:BF:11:22:{34+i:02X}"',config)
        config=re.sub(r'(\[Instance\d+\.Firmware\]\n)',r'\1OverrideSettings = true\n',config)
        config=re.sub(r'Volume = \d+','Volume = 0',config)
        config=re.sub(r'RecvTimeout = \d+','RecvTimeout = 150',config)
        config=re.sub(r'SaveFilePath = "[^"]*"', 'SaveFilePath = '+json.dumps(folder.as_posix()),config)
        shutil.copy2(a.save or ROOT/'game-files/rom-original/Pokemon Black 2 Redux Complete (v1.4.1).sav',folder/(a.rom.stem+'.sav'))
        (folder/'melonDS.toml').write_text(config,encoding='utf-8')
        report=folder/'report.json';report.unlink(missing_ok=True);reports.append(report)
        Path(str(report)+'.ramdump').unlink(missing_ok=True)
        Path(str(report)+'.final.ramdump').unlink(missing_ok=True)
        script=folder/'input.json';steps=[]
        for frame in range(300,20000,120):
            if a.forfeit_frame and i==0 and frame>=a.forfeit_frame:
                steps.extend([{'frame':frame,'duration':4,'keyMask':0xffd},{'frame':frame+20,'duration':4,'x':216,'y':160}]+[{'frame':frame+n,'duration':4,'keyMask':0xffe} for n in (40,60,80)])
            else:
                move_x=62 if a.move_slot in (1,3) else 192
                move_y=63 if a.move_slot in (1,2) else 110
                steps.extend([{'frame':frame,'duration':4,'keyMask':0xffe},{'frame':frame+20,'duration':4,'x':128,'y':100},{'frame':frame+40,'duration':4,'x':move_x,'y':move_y},{'frame':frame+60,'duration':4,'x':62,'y':63},{'frame':frame+80,'duration':4,'keyMask':0xffe}])
        if a.cancel_frame:steps.append({'frame':a.cancel_frame,'duration':1200,'cancel':True})
        script.write_text(json.dumps(steps))
        env={k:v for k,v in os.environ.items() if not k.startswith('POKEPLAY_')}
        env.update(POKEPLAY_COOP_PREPARATION_CHECK='1',POKEPLAY_COOP_MANUAL_CHECK='1',POKEPLAY_COOP_LAUNCH_CHECK='1',POKEPLAY_COOP_LAN_FIXTURE=role,POKEPLAY_COOP_TEST_PORT=str(a.port if a.spectator else a.port+i),POKEPLAY_COOP_PREPARATION_STATE="",POKEPLAY_COOP_PREPARATION_REPORT=str(report),POKEPLAY_COOP_BATTLE_SCRIPT=str(script),POKEPLAY_COOP_BOSS_CHECK=str(a.boss))
        if a.baseline:env['POKEPLAY_COOP_SYNC_BASELINE']='1'
        if a.story_return:
            env['POKEPLAY_COOP_STORY_FIXTURE']='1'
            env['POKEPLAY_COOP_BOSS_CHECK']=str(a.boss|0x80000000)
        if a.retry_after_cancel:env['POKEPLAY_COOP_RETRY_CHECK']='1'
        if a.pvp:
            env['POKEPLAY_PLAYER_BATTLE_CHECK']='1'
            env['POKEPLAY_COOP_BOSS_CHECK']='0'
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
        log=(folder/'run.log').open('w');logs.append(log)
        processes.append(subprocess.Popen([str(folder/'melonDS.exe'),str(a.rom.resolve())],cwd=folder,env=env,startupinfo=startup,stdout=log,stderr=log))
        if i==0:
            time.sleep(1)
            if a.spectator:
                spectator=OUTPUT/'idle-first-guest';shutil.copytree(folder,spectator)
                (spectator/'melonDS.toml').write_text(config.replace(folder.as_posix(),spectator.as_posix()).replace('00:09:BF:11:22:22','00:09:BF:11:22:24'))
                request=os.urandom(16).hex()
                idle_env={k:v for k,v in os.environ.items() if not k.startswith(('POKEPLAY_','UNOVA_'))}
                idle_env.update(POKEPLAY_LAN_START_CHECK='1',POKEPLAY_COOP_TEST_PORT=str(a.port),UNOVA_LAN_ACTION='join',UNOVA_LAN_HOST='127.0.0.1:'+str(a.port),UNOVA_LAN_REQUEST=request,UNOVA_PLAYER_NAME='Idle first guest',UNOVA_TRAINER_COOP='0',UNOVA_AUTO_CONNECT='0')
                idle_log=(spectator/'idle.log').open('w');logs.append(idle_log)
                spectators.append(subprocess.Popen([str(spectator/'melonDS.exe'),str(a.rom.resolve())],cwd=spectator,env=idle_env,startupinfo=startup,stdout=idle_log,stderr=idle_log))
                deadline=time.monotonic()+30
                while time.monotonic()<deadline:
                    try:
                        idle=json.loads((spectator/'launcher-lan-status.json').read_text())
                        if idle.get('request')==request and idle.get('ok') and idle.get('role')==2:break
                    except (FileNotFoundError,json.JSONDecodeError):pass
                    time.sleep(.1)
                else:raise RuntimeError('Idle first guest did not connect')

    deadline=time.monotonic()+a.seconds
    last_status=[None,None]
    guest_disconnected=False
    while time.monotonic()<deadline:
        for i,report in enumerate(reports):
            if i==1 and guest_disconnected:continue
            if processes[i].poll() is not None:raise RuntimeError(f'{i} exited {processes[i].returncode}')
            try:d=json.loads(report.read_text(encoding='utf-8-sig'))
            except (OSError,json.JSONDecodeError):continue
            if not samples[i] or d.get('fixtureFrames')!=samples[i][-1].get('fixtureFrames'):samples[i].append(d)
            if a.pvp and original_parties[i] is None and d.get('contextAddress') not in (None,'0'):
                try:
                    import struct
                    ram=Path(str(report)+'.ramdump').read_bytes();context=int(d['contextAddress'],16)
                    pointer=struct.unpack_from('<I',ram,context-0x02000000+0x7a8)[0]
                    if 0x02000000<=pointer<=0x023ffacc:
                        count=struct.unpack_from('<I',ram,pointer-0x02000000+4)[0]
                        if 1<=count<=6:original_parties[i]=ram[pointer-0x02000000+8:pointer-0x02000000+8+count*220]
                except (OSError,ValueError,struct.error):pass
            status=d.get('nativeCoopPreparation')
            if status!=last_status[i]:print(i,status,flush=True);last_status[i]=status
        time.sleep(.2)
        if a.disconnect_guest and not guest_disconnected and all(sum(d.get('nativeCoopPreparation','').startswith('Native opening exchange complete; battle scene running') for d in h)>=6 for h in samples):
            processes[1].terminate();processes[1].wait(timeout=10)
            guest_disconnected=True
            print('Private guest terminated after both native battles were running',flush=True)
        if guest_disconnected and samples[0] and samples[0][-1].get('nativeCoopRecovered') and samples[0][-1].get('nativeCoopRecoveryFieldIdle'):break
        if a.battle_delay_ms is not None and not delay_changed and all(sum(d.get('nativeCoopPreparation','').startswith('Native opening exchange complete; battle scene running') for d in h)>=6 for h in samples):
            current_delay=a.battle_delay_ms;delay_changed=True
            print(f'Injected in-battle one-way delay {current_delay} ms (nominal RTT {current_delay*2} ms)',flush=True)
        if a.retry_after_cancel and all(h and h[-1].get('final') and h[-1].get('nativeCoopAttempt')==2 for h in samples):break
        if (a.forfeit_frame or a.require_completion) and all(h and h[-1].get('final') for h in samples):break
    output=[]
    for i,history in enumerate(samples):
        active=[d for d in history if d.get('nativeCoopPreparation','').startswith('Native opening exchange complete; battle scene running')]
        frames=0;fps=0
        if len(active)>1:
            frames=active[-1]['fixtureFrames']-active[0]['fixtureFrames'];elapsed=active[-1]['fixtureElapsedMs']-active[0]['fixtureElapsedMs'];fps=frames*1000/elapsed if elapsed else 0
        output.append({'role':i,'battle_samples':len(active),'fps':round(fps,2),'last':history[-1] if history else {}})
    target=OUTPUT/f'lan-{label}-summary.json';target.write_text(json.dumps(output,indent=2));print(target,flush=True)
    for d in output:print('RESULT',d['role'],'battle samples',d['battle_samples'],'FPS',d['fps'],flush=True)
    assert all(d['battle_samples']>5 for d in output),'Both processes must import the party and reach running battle'
    if a.disconnect_guest:
        final=output[0]['last']
        assert guest_disconnected,'Never reached both running battles before guest disconnect'
        assert final.get('nativeCoopRecovered') and final.get('nativeCoopRecoveryFieldIdle'),'Host did not restore its field checkpoint after guest loss'
        assert final.get('allocationsReleased') and final.get('nativeCoopCanStart'),'Host retained allocations or cannot start again after guest loss'
    if a.battle_delay_ms is not None:
        assert delay_changed,'Never reached both running battles before latency injection'
        assert all(not d['last'].get('nativeCoopRecovered') for d in output),'Latency injection caused native battle rollback'
    if a.require_completion:
        for d in output:
            final=d['last']
            assert final.get('final') and final.get('nativeCoopBattleCompleted') and final.get('passed') and not final.get('nativeCoopRecovered'), 'No completed native result: '+final.get('nativeCoopPreparation','No report')
            if a.story_return:
                assert final.get('nativeCoopStoryAttached') and final.get('nativeCoopStoryReleased')
                assert final['nativeCoopStoryResult']==final['setupInspection']['storyParentResult']
        if a.story_return:assert output[0]['last']['nativeCoopStoryResult']==output[1]['last']['nativeCoopStoryResult'],'Story outcomes differ'
    def assert_party_restored(index):
        assert original_parties[index] is not None,'No original full-party capture'
        ram=Path(str(reports[index])+'.final.ramdump').read_bytes()
        word=lambda address:struct.unpack_from('<I',ram,address-0x02000000)[0]
        manager=word(0x02141858);system=word(word(manager+8)+20);party=word(word(system+28)+0x194)
        returned=ram[party-0x02000000+8:party-0x02000000+8+word(party+4)*220]
        assert returned==original_parties[index],'Friendly PvP changed/truncated the original full party'
        assert word(0x021418b0)==0 and word(system+24)==0,'Native event/adapter retained after field return'
    if a.cancel_frame:
        for i,d in enumerate(output):
            final=d['last']
            if a.retry_after_cancel:assert final.get('nativeCoopAttempt')==2,'Second battle never started'
            assert final.get('nativeCoopRecovered') and final.get('nativeCoopRecoveryFieldIdle'),final['nativeCoopPreparation']
            assert final.get('allocationsReleased') and final.get('nativeCoopCanStart'),final['nativeCoopPreparation']
            if a.pvp:assert_party_restored(i)
    if a.forfeit_frame:
        for i,d in enumerate(output):
            final=d['last']
            assert final.get('nativeCoopBattleCompleted') and final.get('passed') and not final.get('nativeCoopRecovered'),final['nativeCoopPreparation']
            assert final.get('allocationsReleased') and final.get('nativeCoopCanStart'),final['nativeCoopPreparation']
            if a.pvp:assert_party_restored(i)
finally:
    for process in processes+spectators:
        if process.poll() is None:process.terminate()
        process.wait(timeout=10)
    stop.set();thread.join(timeout=5)
    for log in logs:log.close()
