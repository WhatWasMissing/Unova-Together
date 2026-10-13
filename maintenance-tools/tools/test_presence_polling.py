"""Exercise production polling methods with a deliberately stalled core."""
from pathlib import Path
import os, shlex, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'melonDS-source-1.1' if (ROOT/'melonDS-source-1.1').is_dir() else ROOT/'source/melonDS'
source=(SOURCE/'src/frontend/qt_sdl/EmuThread.cpp').read_text(encoding='utf-8')
start=source.index('QVariantMap EmuThread::sampleOverworldPresence(')
end=source.index('QVariantMap EmuThread::loadOverworldTrainerSprites()',start)
cpp=r'''
#include <QVariantMap>
#include <QMutex>
#include <QMutexLocker>
#include <atomic>
#include <cassert>
#include <iostream>
class EmuThread {
public:
 enum Type {msg_OverworldPresenceSample,msg_FollowerSample};
 struct Message {Type type;QVariant param;};
 bool running=true;int requests=0;
 QMutex presenceSampleMutex;
 QVariantMap presenceSampleResult,followerSampleResult;
 std::atomic<bool> presenceSamplePending{false},followerSamplePending{false};
 bool isRunning() const{return running;}
 void sendMessage(Message){++requests;}
 void sendMessage(Type type){sendMessage({type,{}});}
 QVariantMap sampleOverworldPresence(bool resetTracker=false);
 QVariantMap sampleFollowerAppearance();
};
'''+source[start:end]+r'''
int main() {
 EmuThread core;
 // A slow core cannot block the renderer or accumulate polling requests.
 for(int i=0;i<10000;++i) {core.sampleOverworldPresence();core.sampleFollowerAppearance();}
 assert(core.requests==2);
 core.presenceSampleResult={{"map",191}};
 core.followerSampleResult={{"species",531},{"shiny",true}};
 core.presenceSamplePending=false;core.followerSamplePending=false;
 assert(core.sampleOverworldPresence().value("map").toInt()==191);
 assert(core.sampleFollowerAppearance().value("shiny").toBool());
 assert(core.requests==4);
 core.running=false;
 assert(core.sampleOverworldPresence().value("status")=="Emulator stopped");
 assert(core.sampleFollowerAppearance().isEmpty());assert(core.requests==4);
 std::cout<<"Stalled-core polling checks passed: 20,000 reads, two requests, no waits.\n";
}
'''
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env['PATH']
flags=shlex.split(subprocess.check_output(['C:/msys64/ucrt64/bin/pkg-config.exe','--cflags','--libs','Qt6Core'],env=env,text=True))
with tempfile.TemporaryDirectory(prefix='unova-presence-poll-') as temporary:
    path=Path(temporary)/'poll.cpp';path.write_text(cpp)
    exe=path.with_suffix('.exe')
    subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++17',str(path),'-o',str(exe),*flags],env=env,check=True)
    subprocess.run([str(exe)],env=env,check=True)
