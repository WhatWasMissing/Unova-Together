"""Real two-core opening checks for all populated Redux rival records.
Does not claim story event eligibility, badge progression, or complete battles.
"""
from pathlib import Path
import argparse,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--trainers',help='Comma-separated subset, for fresh follow-up evidence');a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
ids=[161,162,163,166,167,168,368,369,370,378,379,380,588,589,590,684,685,686,693,694,695,696,697,698,701,702,703,794,795,796,853,854,855]
if a.trainers:ids=[int(x) for x in a.trainers.split(',')]
results=[]
for id in ids:
 report=a.output/f'rival-{id}.json';log=a.output/f'rival-{id}.log';started=time.monotonic()
 cmd=[sys.executable,'-X','utf8',str(ROOT/'tools/verify_coop_runtime.py'),'--rom',str(ROOT/'test-fixtures/coop-launcher/game/Redux.nds'),'--state',str(ROOT/'test-fixtures/coop-launcher/game/Redux.ml1'),'--report',str(report),'--runtime',str(a.runtime),'--pair','--opponents','--launch','--manual','--boss',str(id),'--handshake','--timeout','100','--observe-seconds','18']
 with log.open('w',encoding='utf-8') as out:done=subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
 ok=done.returncode==0
 if ok:
  cmd=[sys.executable,'-X','utf8',str(ROOT/'tools/audit_native_enemy_setup.py'),'--doubles-ai','--rom',str(ROOT/'test-fixtures/coop-launcher/game/Redux.nds'),'--dump',str(report)+'.ramdump','--dump',str(report)+'.instance-1.json.ramdump','--output',str(a.output/f'rival-{id}-teams.json')]
  with log.open('a',encoding='utf-8') as out:done=subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
  ok=done.returncode==0
 results.append({'trainer':id,'passed':ok,'seconds':round(time.monotonic()-started,1)})
 (a.output/'summary.json').write_text(json.dumps({'results':results,'allPassed':all(r['passed'] for r in results),'limits':__doc__},indent=2),encoding='utf-8')
 print(f'Rival #{id}: '+('native opening and ROM team audit passed' if ok else 'FAILED; see '+str(log)),flush=True)
print(f'{sum(r["passed"] for r in results)}/{len(results)} rival native openings passed',flush=True)
sys.exit(0 if all(r['passed'] for r in results) else 1)
