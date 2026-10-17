"""Compile the actual read-only companion interactions; no user saves."""
from pathlib import Path
import os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'melonDS-source-1.1'
if not source.is_dir():source=ROOT/'source/melonDS'
CPP=r'''#include "FollowerInteraction.h"
#include <cassert>
#include <iostream>
#include <set>
int main() {
 qunsetenv("UNOVA_COMPANION_INTERACTIONS");qunsetenv("UNOVA_EXPERIMENTAL_COMPANION");
 assert(FollowerInteraction::enabledByEnvironment());
 qputenv("UNOVA_EXPERIMENTAL_COMPANION","0");assert(!FollowerInteraction::enabledByEnvironment());
 qputenv("UNOVA_EXPERIMENTAL_COMPANION","1");assert(FollowerInteraction::enabledByEnvironment());
 qputenv("UNOVA_COMPANION_INTERACTIONS","0");assert(!FollowerInteraction::enabledByEnvironment());
 qputenv("UNOVA_EXPERIMENTAL_COMPANION","0");qputenv("UNOVA_COMPANION_INTERACTIONS","1");
 assert(FollowerInteraction::enabledByEnvironment());
 qunsetenv("UNOVA_COMPANION_INTERACTIONS");qunsetenv("UNOVA_EXPERIMENTAL_COMPANION");
 QVariantMap p{{"ok",true},{"species",381},{"name","Latios"},{"hp",80},{"maxHp",100},{"friendship",240}};
 const auto unchanged=p;
 assert(FollowerInteraction::available(p));
 assert(FollowerInteraction::reaction(p,"talk").contains("happy"));
 assert(FollowerInteraction::reaction(p,"talk",1).contains("close"));
 assert(FollowerInteraction::reaction(p,"pet").contains("hand"));
 assert(FollowerInteraction::reaction(p,"play").contains("hops"));
 assert(FollowerInteraction::reaction(p,"play",1).contains("turns"));
 assert(p==unchanged);
 p["hp"]=25;assert(FollowerInteraction::reaction(p,"play").contains("tired"));
 p["hp"]=0;assert(FollowerInteraction::reaction(p,"pet").contains("rest"));
 p["hp"]=100;p["friendship"]=20;assert(FollowerInteraction::reaction(p,"talk").contains("carefully"));
 p["friendship"]=100;for(unsigned i=0;i<6;++i)assert(!FollowerInteraction::reaction(p,"talk",i).isEmpty());
 const QStringList actions{"talk","pet","play","praise","story","ask","sit","trick","joke","sing"};
 const std::array<unsigned,5> bonds{{0,50,100,150,220}};
 const QStringList motions{"bounce","run","peek","sway","hop","spin"};
 const QStringList emotes{"?","!","heart","...","star","music"};
 unsigned combinations=0;bool sawRun=false;
 for(unsigned nature=0;nature<25;++nature) {
  p["nature"]=nature;
  for(unsigned band=0;band<bonds.size();++band) {
   p["friendship"]=bonds[band];
   for(const auto& action:actions) {
    std::set<QString> variants;
    for(unsigned variation=0;variation<4;++variation) {
     const auto before=p;
     const auto line=FollowerInteraction::reaction(p,action,variation);
     const auto cue=FollowerInteraction::visualCue(p,action,variation);
     assert(line.startsWith("Latios ") && !line.isEmpty());
     assert(motions.contains(cue.motion) && emotes.contains(cue.emote));
     assert(cue.durationMs==1700 || (cue.motion=="run" && cue.durationMs==2400));
     variants.insert(line);sawRun=sawRun || cue.motion=="run";++combinations;
     assert(p==before);
    }
    assert(variants.size()==4);
   }
  }
 }
 assert(combinations==5000 && sawRun);
 for(unsigned nature=0;nature<25;++nature) {
  p["nature"]=nature;p["friendship"]=240;std::set<QString> lines;
  for(unsigned i=0;i<60;++i) lines.insert(FollowerInteraction::reaction(p,"talk",i));
  assert(lines.size()>=16);
 }
 p["type1"]=10;p["type2"]=10;
 const QVariantMap context{{"area","Undella Bay"},{"hour",23},{"month",4},{"recentBattle",true}};
 const auto beforeContext=p;std::set<QString> contexts;
 for(unsigned i=1;i<80;i+=2) contexts.insert(FollowerInteraction::contextNote(p,context,i));
 assert(contexts.size()>=10 && p==beforeContext);
 bool water=false,night=false,battle=false;
 for(const auto& line:contexts) {water|=line.contains("water");night|=line.contains("night");battle|=line.contains("battle");}
 assert(water && night && battle);
 assert(FollowerInteraction::contextNote(p,context,0).isEmpty());
 p["nature"]=0;const auto firstNature=FollowerInteraction::reaction(p,"talk");
 p["nature"]=1;assert(FollowerInteraction::reaction(p,"talk")!=firstNature);
 p["egg"]=true;assert(!FollowerInteraction::available(p));
 p["egg"]=false;p["species"]=650;assert(!FollowerInteraction::available(p));
 assert(!FollowerInteraction::available({}));
 for(unsigned n=1;n<=649;++n) {p["species"]=n;assert(FollowerInteraction::available(p));}
 std::cout<<"Companion interaction matrix: "<<combinations<<" nature/action/friendship/variation combinations passed; all 649 species, read-only data, cues and running reactions passed.\n";
}
'''
def main():
 env=os.environ.copy();env['PATH']=r'C:\msys64\ucrt64\bin'+os.pathsep+env.get('PATH','')
 with tempfile.TemporaryDirectory(prefix='unova-companion-') as folder:
  cpp=Path(folder)/'test.cpp';exe=Path(folder)/'test.exe';cpp.write_text(CPP,encoding='utf-8')
  subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-I'+str(source/'src/frontend/qt_sdl'),'-IC:/msys64/ucrt64/include/qt6','-IC:/msys64/ucrt64/include/qt6/QtCore','-LC:/msys64/ucrt64/lib','-lQt6Core','-o',str(exe)],env=env,check=True)
  subprocess.run([str(exe)],env=env,check=True)
if __name__=='__main__': main()
