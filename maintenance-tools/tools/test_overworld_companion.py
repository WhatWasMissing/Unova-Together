"""Compile production follower-facing and A-button interception code; no saves."""
from pathlib import Path
import os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'melonDS-source-1.1'
if not source.is_dir():source=ROOT/'source/melonDS'
front=source/'src/frontend/qt_sdl'
s=(front/'MultiplayerPanel.cpp').read_text(encoding='utf-8',errors='replace');a=s.index('bool MultiplayerPanel::companionActive() const');b=s.index('void MultiplayerPanel::interactWithCompanion',a);active=s[a:b]
a=s.index('bool MultiplayerPanel::facingCompanion() const');b=s.index('void MultiplayerPanel::openCompanionDialogue',a);facing=s[a:b]
s=(front/'EmuInstanceInput.cpp').read_text(encoding='utf-8',errors='replace');a=s.index('    if(!(buttons&1)) companionChordHeld=false;');b=s.index('\n\n    joyHotkeyMask',a);gate=s[a:b].replace('SDL_GetTicks64()','now')
cpp=r'''#include "FollowerInteraction.h"
#include "PokemonFollower.h"
#include <QMap>
#include <atomic>
#include <cassert>
#include <iostream>
struct Check {bool on=true;bool isChecked() const {return on;}};
struct MultiplayerPanel {
 bool companionInteractionsEnabled=true;Check control;Check* followerEnabled=&control;
 QVariantMap companion{{"ok",true},{"species",25},{"hp",20}};
 QVariantMap currentSample{{"status","Experimental match"},{"fieldPositionOwned",true},{"smoothX",10},{"smoothZ",10},{"worldY",0},{"facing","North"}};
 struct {bool inBattle=false;} battlePresence;
 QString menuMode;QMap<QString,PokemonFollowerTrail> followerTrails;
 bool companionActive() const;bool facingCompanion() const;
};
'''+active+facing+r'''
struct Input {
 std::atomic<bool> menuInputBlocked{false},waitForNeutralInput{false},companionInteractionPress{false};
 std::atomic<unsigned long long> companionInteractionUntil{0};std::atomic<unsigned> menuButtonPress{0};
 std::atomic<unsigned> menuButtons{0};bool companionChordHeld=false;unsigned inputMask=0;unsigned joyHotkeyMask=0;
 void sample(unsigned buttons,unsigned previousButtons,unsigned long long now) {unsigned rawMask=0xfff&~buttons;
'''+gate+r'''
 }
};
int main() {
 MultiplayerPanel p;auto& trail=p.followerTrails["local"];trail.visible=true;trail.position={10,9};
 assert(p.facingCompanion());p.currentSample["facing"]="South";assert(!p.facingCompanion());
 trail.position={10,11};assert(p.facingCompanion());trail.height=9;assert(!p.facingCompanion());trail.height=0;
 trail.moving=true;assert(!p.facingCompanion());trail.moving=false;
 p.currentSample["moving"]=true;assert(!p.facingCompanion());p.currentSample["moving"]=false;
 p.currentSample["inMenu"]=true;assert(!p.facingCompanion());p.currentSample["inMenu"]=false;
 p.menuMode="players";assert(!p.facingCompanion());p.menuMode.clear();
 p.battlePresence.inBattle=true;assert(!p.facingCompanion());p.battlePresence.inBattle=false;
 p.currentSample["nativeCoopCanCancel"]=true;assert(!p.facingCompanion());p.currentSample["nativeCoopCanCancel"]=false;
 p.currentSample["fieldPositionOwned"]=false;assert(!p.facingCompanion());p.currentSample["fieldPositionOwned"]=true;
 p.companionInteractionsEnabled=false;assert(!p.facingCompanion());
 Input i;i.companionInteractionUntil=200;
 i.sample(1,0,100);assert(!(i.inputMask&1) && !i.companionInteractionPress); // A still advances game text.
 i.sample(0,1,105);const unsigned chord=1|(1<<8);i.sample(chord,0,110);assert(i.inputMask&1);assert(i.companionInteractionPress.exchange(false));
 i.sample(chord,chord,120);assert(i.inputMask&1);assert(!i.companionInteractionPress);
 i.sample(1<<8,chord,121);assert(!(i.inputMask&(1<<8)) && !i.companionChordHeld);
 i.sample(chord,1<<8,122);assert(i.inputMask&1);assert(i.companionInteractionPress.exchange(false));
 i.sample(0,chord,123);
 i.sample(chord,0,201);assert(!(i.inputMask&1) && !i.companionInteractionPress); // Expired chord reaches game.
 i.companionInteractionUntil=300;i.sample(chord|16,0,220);assert(!(i.inputMask&1) && !i.companionInteractionPress);
 i.menuInputBlocked=true;i.sample(1,0,221);assert(i.inputMask==0xfff && !i.companionInteractionPress);
 std::cout<<"Production facing gates and A interception: idle, menus, battles, opt-in, expiry, held buttons, D-pad and ordinary game input passed.\n";
}
'''
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env['PATH']
with tempfile.TemporaryDirectory(prefix='unova-field-companion-') as folder:
 cppfile=Path(folder)/'test.cpp';cppfile.write_text(cpp,encoding='utf-8');exe=cppfile.with_suffix('.exe')
 subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Wall','-Wextra','-Werror',str(cppfile),'-I'+str(front),'-IC:/msys64/ucrt64/include/qt6','-IC:/msys64/ucrt64/include/qt6/QtCore','-LC:/msys64/ucrt64/lib','-lQt6Core','-o',str(exe)],env=env,check=True)
 subprocess.run([str(exe)],env=env,check=True)
