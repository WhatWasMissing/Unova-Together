"""Run native preparation in an isolated emulator fixture and check its report.

Uses the private fixture state and report paths. An optional in-project emulator
and the dedicated courtyard ROM can be supplied for integration validation.
"""
from pathlib import Path
import argparse
import json
import os
import subprocess
import time
import struct

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'test-fixtures/coop-launcher'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, default=FIXTURE/'runtime/melonDS.exe')
    parser.add_argument('--registration', action='store_true')
    parser.add_argument('--pair', action='store_true', help='Test automatic native group establishment in two local cores')
    parser.add_argument('--opponents', action='store_true', help='Load test opponents from the native ROM trainer data; requires --pair')
    parser.add_argument('--launch', action='store_true', help='Observe private battle-event startup only; requires --opponents')
    parser.add_argument('--boss', type=int, help='Private same-ROM boss team check; requires --manual')
    parser.add_argument('--manual', action='store_true', help='Exercise the panel request path in the isolated launcher test')
    parser.add_argument('--handshake', action='store_true', help='Require native opening exchange, remote party and running battle scene')
    parser.add_argument('--timeout', type=float, default=20)
    parser.add_argument('--observe-seconds', type=float, default=10, help='Observe the launched battle beyond startup')
    args = parser.parse_args()
    if args.opponents and not args.pair:
        parser.error('--opponents requires --pair')
    if args.launch and not args.opponents:
        parser.error('--launch requires --opponents')
    if args.manual and not args.launch:
        parser.error('--manual requires --launch')
    if args.boss and not args.manual: parser.error('--boss requires --manual')
    if args.handshake and not args.launch:
        parser.error('--handshake requires --launch')
    runtime = args.runtime.resolve()
    fixture_root=FIXTURE.resolve()
    runtime_roots=(fixture_root,(ROOT/'builds/current').resolve())
    if not runtime.is_file() or not any(runtime.is_relative_to(root) for root in runtime_roots):
        raise ValueError(f'Integration runtime must be the isolated fixture or local current build: {runtime}')
    for path in (args.state,args.report):
        if not path.resolve().is_relative_to(fixture_root):
            raise ValueError(f'Integration state and report must stay inside the fixture: {path}')
    rom=args.rom.resolve()
    allowed_courtyard=(ROOT/'game-files/test-courtyard/Coop Courtyard.nds').resolve()
    if not rom.is_relative_to(fixture_root) and rom!=allowed_courtyard:
        raise ValueError(f'Integration ROM must be the private fixture or installed courtyard ROM: {rom}')
    args.report.unlink(missing_ok=True)
    env = os.environ.copy()
    env['POKEPLAY_COOP_PREPARATION_CHECK'] = '1'
    env['POKEPLAY_COOP_PREPARATION_STATE'] = str(args.state.resolve())
    env['POKEPLAY_COOP_PREPARATION_REPORT'] = str(args.report.resolve())
    if args.boss: env['POKEPLAY_COOP_BOSS_CHECK']=str(args.boss)
    else: env.pop('POKEPLAY_COOP_BOSS_CHECK', None)
    if args.manual:
        env['POKEPLAY_COOP_MANUAL_CHECK']='1'
    else:
        env.pop('POKEPLAY_COOP_MANUAL_CHECK',None)
    if args.launch:
        env['POKEPLAY_COOP_LAUNCH_CHECK']='1'
    else:
        env.pop('POKEPLAY_COOP_LAUNCH_CHECK',None)
    if args.opponents:
        env['POKEPLAY_COOP_OPPONENT_CHECK'] = '1'
    else:
        env.pop('POKEPLAY_COOP_OPPONENT_CHECK', None)
    if args.registration:
        env['POKEPLAY_COOP_REGISTRATION_CHECK'] = '1'
    else:
        env.pop('POKEPLAY_COOP_REGISTRATION_CHECK', None)
    reports = [args.report]
    if args.pair:
        env['POKEPLAY_COOP_REGISTRATION_CHECK'] = '1'
        env['POKEPLAY_COOP_GROUP_CHECK'] = '1'
        env['POKEPLAY_COOP_PAIR_CHECK'] = '1'
        reports.append(Path(str(args.report) + '.instance-1.json'))
    else:
        env.pop('POKEPLAY_COOP_GROUP_CHECK', None)
        env.pop('POKEPLAY_COOP_PAIR_CHECK', None)
    for report in reports:
        report.unlink(missing_ok=True)
    if args.manual:
        for name in ('POKEPLAY_COOP_REGISTRATION_CHECK','POKEPLAY_COOP_GROUP_CHECK','POKEPLAY_COOP_OPPONENT_CHECK'):
            env.pop(name,None)
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    results = [{} for _ in reports]
    with Path(str(args.report)+'.stdout').open('w') as out, Path(str(args.report)+'.stderr').open('w') as err:
        process = subprocess.Popen([str(runtime), str(rom)],
                                   cwd=runtime.parent, env=env, stdout=out,
                                   stderr=err, startupinfo=startup)
        try:
            deadline = time.monotonic() + args.timeout
            while process.poll() is None and time.monotonic() < deadline:
                for i, report in enumerate(reports):
                    if report.exists():
                        try:
                            results[i] = json.loads(report.read_text())
                        except (OSError, json.JSONDecodeError):
                            pass
                if all(result.get('final') for result in results):
                    break
                if args.launch and all(result.get('nativeCoopBattleEventQueued') for result in results):
                    observeUntil=time.monotonic()+args.observe_seconds
                    while time.monotonic()<observeUntil:
                        try:results=[json.loads(report.read_text()) for report in reports]
                        except (OSError,json.JSONDecodeError):time.sleep(.1);continue
                        def sceneReady(path):
                            try:
                                ram=Path(str(path)+'.ramdump').read_bytes()
                                def w(address):
                                    if not 0x02000000<=address<=0x023ffffc:raise ValueError('pointer not live')
                                    return struct.unpack_from('<I',ram,address-0x02000000)[0]
                                scene=w(w(0x0223b288)+8)
                                return w(scene+4)==167 and w(scene+8)==2
                            except (OSError,ValueError,struct.error):return False
                        if args.handshake and all("Native opening exchange complete; battle scene running" in result.get("nativeCoopPreparation","") for result in results) and all(sceneReady(path) for path in reports):
                            break
                        time.sleep(.1)
                    results=[json.loads(report.read_text()) for report in reports]
                    break
                time.sleep(0.1)
            for details in results:
                if args.launch:
                    assert details.get('nativeCoopBattleEventQueued'), details.get('nativeCoopPreparation')
                    if args.handshake:
                        capture=reports[details.get('instance',0)].with_name(reports[details.get('instance',0)].name+'.ramdump').read_bytes()
                        def word(address):
                            assert 0x02000000<=address<=0x023ffffc, hex(address)
                            return struct.unpack_from('<I',capture,address-0x02000000)[0]
                        net=word(0x021db06c)
                        assert 0x02000000<=net<=0x023ffffc, f'Native opening exchange has no valid session pointer: {net:#x}'
                        assert capture[net-0x02000000+7]!=40, 'Native opening exchange is still blocked'
                        assert capture[net-0x02000000+10]==1, 'Native exchange did not complete'
                        table=word(0x021418a0)
                        assert tuple(word(table+i) for i in (16,20,28))==(0x021d7448,9,0x100)
                        scene=word(word(0x0223b288)+8)
                        assert word(scene+4)==167 and word(scene+8)==2, 'Battle scene did not reach its native main loop'
                        setup=word(word(word(0x021418b0)+0x34c)+0x7d0)
                        if args.boss:
                            counts=[word(word(setup+0x24+i*4)+4) for i in range(4)]
                            expected=max(2,details['nativeCoopBossTeamSize'])
                            assert counts[0]>0 and counts[2]>0, 'Remote player party was not imported'
                            assert counts[1]+counts[3]==expected and counts[1]==(expected+1)//2 and counts[3]==expected//2, counts
                            print(f'Boss {args.boss}: team {expected}, AI slots {counts[1]}/{counts[3]}')
                        else:
                            assert all(word(word(setup+0x24+i*4)+4)>0 for i in range(4)), 'Remote party was not imported'
                        print(f'Instance {details.get("instance",0)}: opening exchange, remote party and native battle main loop passed')
                    print(f'Instance {details.get("instance",0)}: native battle event queued; gameplay and cleanup remain unverified')
                    continue
                assert details.get('final'), f'Native test did not finish: {details.get("nativeCoopPreparation", "no report")}'
                assert details.get('passed') and details.get('allocationsReleased'), details.get('nativeCoopPreparation')
                assert details.get('nativeCoopBridgeVerified') and details.get('nativeCoopContextPrepared')
                if args.registration or args.pair:
                    assert all(details.get(k) for k in ('nativeCoopRegistrationVerified',
                        'nativeCoopUnregisterVerified', 'nativeCoopSelectedPartyVerified', 'nativeCoopSetupPrepared'))
                if args.pair:
                    assert details.get('nativeCoopGroupVerified') and details.get('nativeCoopConnectedPeers') == 2
                if args.opponents:
                    setup=details['setupInspection']
                    assert 1<=setup['count1']<=6 and 1<=setup['count3']<=6
            # Continue ordinary game execution after removing the native hook.
            time.sleep(0.5)
            assert process.poll() is None, 'Emulator exited after preparation'
            for details in results:
                print(f'Instance {details.get("instance",0)}: {details["nativeCoopPreparation"]}')
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)

if __name__ == '__main__':
    main()
