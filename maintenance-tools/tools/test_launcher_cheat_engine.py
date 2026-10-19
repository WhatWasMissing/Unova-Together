"""Compile the production AR executor against disposable copies of captured RAM."""
from pathlib import Path
import argparse, hashlib, json, os, struct, subprocess
from launcher_ui.preferences import CATALOG, identify, managed_codes
from inspect_inventory import inspect

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve()
    if out.exists():raise ValueError('Use a fresh output directory.')
    out.mkdir(parents=True)
    capture=ROOT/'test-fixtures/coop-launcher/release-035-final-completion-20261008/lifecycle-completion.json.final.ramdump'
    original=capture.read_bytes();digest=hashlib.sha256(original).hexdigest()
    inventory=inspect(capture,True);save=struct.unpack_from('<I',original,0x9a338)[0]
    assert save+0x19210==int(inventory['bag'],16)+0x7d8
    source=(ROOT/'melonDS-source-1.1/src/AREngine.cpp').read_text()
    macro=source[source.index('#define case16'):source.index('void AREngine::RunCheat')]
    body=source[source.index('void AREngine::RunCheat'):source.index('void AREngine::RunCheats()')]
    prefix=r"""
#include <cstdint>
#include <cstring>
#include <vector>
#include <fstream>
#include <cassert>
#include <string>
#include <iterator>
#include <stdexcept>
using u32=uint32_t;using u16=uint16_t;using u8=uint8_t;using s32=int32_t;
u32 ROR(u32 x,u32 n){return n?(x>>n)|(x<<(32-n)):x;}
enum class LogLevel{Warn,Error};template<class...T> void Log(LogLevel,const char*,T...){}
#include "ARCodeFile.h"
using namespace melonDS;
using FileHandle=FILE;enum class FileMode{ReadText};
FileHandle* OpenFile(const std::string& s,FileMode){return fopen(s.c_str(),"r");}
bool IsEndOfFile(FileHandle* f){return feof(f);}
bool FileReadLine(char* b,int n,FileHandle* f){return fgets(b,n,f)!=nullptr;}
void CloseFile(FileHandle* f){fclose(f);}
#define strncasecmp _strnicmp
struct Memory{
 std::vector<u8> ram;u16 keys=0x3ff;
 u8 ARM7Read8(u32 a){if(a==0x04000130)return keys&255;if(a==0x04000131)return keys>>8;return ram.at(a-0x02000000);}
 u16 ARM7Read16(u32 a){return ARM7Read8(a)|(ARM7Read8(a+1)<<8);}
 u32 ARM7Read32(u32 a){return ARM7Read16(a)|(u32(ARM7Read16(a+2))<<16);}
 void ARM7Write8(u32 a,u8 v){ram.at(a-0x02000000)=v;}
 void ARM7Write16(u32 a,u16 v){ARM7Write8(a,v);ARM7Write8(a+1,v>>8);}
 void ARM7Write32(u32 a,u32 v){ARM7Write16(a,v);ARM7Write16(a+2,v>>16);}
};
struct AREngine{Memory NDS;void RunCheat(const ARCode&);};
"""
    cases=[]
    for i,item in enumerate(CATALOG['codes']):
        cases.append('{ARCode c%d{nullptr,"Fixture","",true,{%s}}; e.NDS.ram=original;e.NDS.keys=0x3ff;e.RunCheat(c%d);assert(e.NDS.ram==original);e.NDS.keys=%s;e.RunCheat(c%d);assert(e.NDS.%s(save+%s)==%s);'%(
            i,','.join('0x'+x for x in item['words'].split()),i,'0xff' if item['id']=='candy' else '0x3fb',i,
            'ARM7Read8' if item['id']=='repel' else 'ARM7Read32',
            {'money':'0x21738','repel':'0x21f65','candy':'0x19210'}[item['id']],
            {'money':'9999999','repel':'255','candy':'0x03e70032'}[item['id']]))
        size=1 if item['id']=='repel' else 4;offset={'money':0x21738,'repel':0x21f65,'candy':0x19210}[item['id']]
        cases.append('for(size_t j=0;j<original.size();++j)if(j<save-0x02000000+%d||j>=save-0x02000000+%d)assert(e.NDS.ram[j]==original[j]);'%(offset,offset+size))
        cases.append('e.NDS.ram=original;e.NDS.ARM7Write32(0x0209a338,0);auto nullram=e.NDS.ram;e.RunCheat(c%d);assert(e.NDS.ram==nullram);}'%i)
    tail='int main(int argc,char**argv){assert(argc==2);std::ifstream f(argv[1],std::ios::binary);std::vector<u8> original((std::istreambuf_iterator<char>(f)),{});assert(original.size()==0x400000);AREngine e;e.NDS.ram=original;u32 save=e.NDS.ARM7Read32(0x0209a338);'+''.join(cases)+'}'
    native=(ROOT/'melonDS-source-1.1/src/ARCodeFile.cpp').read_text()
    parsing=native[native.index('ARCodeFile::ARCodeFile'):native.index('bool ARCodeFile::Save')]
    final=native[native.index('void ARCodeFile::FinalizeList()'):native.rfind('\n}')]
    parser_body='\nnamespace melonDS {\n'+parsing+final+'\n}\n'
    mch=out/'enabled.mch';mch.write_text(managed_codes('',{i['id']:True for i in CATALOG['codes']}))
    off=out/'disabled.mch';off.write_text(managed_codes(mch.read_text(),{i['id']:False for i in CATALOG['codes']}))
    tail=tail.replace('assert(argc==2);','assert(argc==4);ARCodeFile enabled(argv[2]);assert(!enabled.Error);auto parsed=enabled.GetCodes();assert(parsed.size()==3);for(auto& c:parsed){assert(c.Enabled);assert(c.Code.size()==10);}ARCodeFile disabled(argv[3]);assert(!disabled.Error);for(auto& c:disabled.GetCodes())assert(!c.Enabled);')
    cpp=out/'production_ar_fixture.cpp';cpp.write_text(prefix+macro+body+parser_body+tail)
    exe=out/'production_ar_fixture.exe'
    subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++20','-I',str(ROOT/'melonDS-source-1.1/src'),'-Wall','-Wextra',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe),str(capture),str(mch),str(off)],check=True)
    assert hashlib.sha256(capture.read_bytes()).hexdigest()==digest
    roms=[ROOT/'game-files/black2original/Pokemon - Black Version 2 (USA, Europe) (NDSi Enhanced).nds',ROOT/'game-files/rom-original/Pokemon Black 2 Redux Complete (v1.4.1).nds',ROOT/'game-files/unova-together/Pokemon Black 2 Redux Complete (v1.4.1) - Unova Together.nds']
    profiles=[identify(r) for r in roms];assert all(profiles)
    report={'codes':3,'checks':['inactive buttons write nothing','activation changes only intended bytes','null save pointer writes nothing','native bag getter/count and medicine offset','reviewed original/Redux/Unova Together ARM9 profiles','source capture unchanged','production .mch parser accepts individual enabled and disabled flags'], 'profiles':[p['profile'] for p in profiles],'limitations':'Captured-RAM executor tests, not a complete in-game co-op playtest.'}
    (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
