"""Execute production follower resources and compare preserved appearances.

Unova Together: Copyright (C) 2026 mvq1303. GPL-3.0-or-later.
"""
from pathlib import Path
import argparse
import json
import os
import shlex
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--snapshot',type=Path,required=True)
    p.add_argument('--baseline',type=Path)
    args=p.parse_args()
    out=ROOT/'test-fixtures/hgss-followers';out.mkdir(parents=True,exist_ok=True)
    (out/'.disposable-test-output').write_text('Follower loader compilation outputs.\n')
    env=dict(os.environ,QT_QPA_PLATFORM='offscreen')
    env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env['PATH']
    front=args.source.resolve()/'src/frontend/qt_sdl'
    flags=shlex.split(subprocess.check_output(['C:/msys64/ucrt64/bin/pkg-config.exe','--cflags','--libs','Qt6Gui'],env=env,text=True))
    rcc=out/'followers.cpp'
    subprocess.run(['C:/msys64/ucrt64/share/qt6/bin/rcc.exe',str(args.source.resolve()/'res/followers.qrc'),'-o',str(rcc)],check=True,env=env)
    exe=out/'check.exe'
    subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-O2','-I'+str(front),str(ROOT/'tools/check_hgss_followers.cpp'),
                    str(front/'TrainerSprites.cpp'),str(rcc),'-o',str(exe),*flags],check=True,env=env)
    result=json.loads(subprocess.check_output([str(exe)],env=env,text=True))
    args.snapshot.parent.mkdir(parents=True,exist_ok=True)
    args.snapshot.write_text(json.dumps(result,indent=2)+'\n')
    if args.baseline:
        original=json.loads(args.baseline.read_text(encoding='utf-8'))
        if set(original)!=set(result): raise AssertionError('Variant roster changed')
        manifest=json.loads((ROOT/'assets/followers/official-hgss/manifest.json').read_text(encoding='utf-8'))
        imported={v['asset'].removesuffix('.png') for v in manifest['variants']}
        for key,entry in result.items():
            if entry['shiny']!=original[key]['shiny']:
                raise AssertionError('Shiny artwork changed: '+key)
            if key not in imported and entry['normal']!=original[key]['normal']:
                raise AssertionError('Uncovered artwork changed: '+key)
        print(f'PASS: {len(result)} shiny appearances unchanged; {len(result)-len(imported)} uncovered normal appearances unchanged; {len(imported)} imported variants decoded.')
    else:
        print(f'Captured {len(result)} verified baseline normal/shiny appearances.')

if __name__=='__main__':main()
