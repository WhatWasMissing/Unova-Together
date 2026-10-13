"""Compile production sprite/renderer contracts against local, read-only ROMs."""
from pathlib import Path
import os, shlex, subprocess
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'melonDS-source-1.1' if (ROOT/'melonDS-source-1.1').is_dir() else ROOT/'source/melonDS'
def main():
    out=ROOT/'test-fixtures/follower-polish-20261013';out.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,QT_QPA_PLATFORM='offscreen');env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env['PATH']
    front=SOURCE/'src/frontend/qt_sdl'
    flags=shlex.split(subprocess.check_output(['C:/msys64/ucrt64/bin/pkg-config.exe','--cflags','--libs','Qt6Gui'],env=env,text=True))
    for name in ('check_presence_rendering','check_camera_continuity','check_battle_badge'):
        exe=out/(name+'.exe')
        subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-O2','-I'+str(front),str(ROOT/'tools'/(name+'.cpp')),str(front/'PresenceOverlay.cpp'),'-o',str(exe),*flags],env=env,check=True)
        subprocess.run([str(exe)],env=env,check=True)
    rcc=out/'followers.cpp'
    subprocess.run(['C:/msys64/ucrt64/share/qt6/bin/rcc.exe',str(SOURCE/'res/followers.qrc'),'-o',str(rcc)],env=env,check=True)
    exe=out/'followers.exe'
    subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-O2','-I'+str(front),str(ROOT/'tools/check_pokemon_follower.cpp'),str(front/'TrainerSprites.cpp'),str(rcc),'-o',str(exe),*flags],env=env,check=True)
    for rom in ('game-files/black2original/Pokemon - Black Version 2 (USA, Europe) (NDSi Enhanced).nds','game-files/rom-original/Pokemon Black 2 Redux Complete (v1.4.1).nds'):
        subprocess.run([str(exe),str(ROOT/rom)],env=env,check=True)
if __name__=='__main__':main()
