"""Run compiled story callback and actual native defeat/victory return branches.

Helper contracts and private RAM are isolated in Unicorn. This does not award
a badge or claim an actual NPC script has been playtested.
"""
from pathlib import Path
from test_coop_field_return import Machine, CONTEXT, DATA, EVENT, SETUP, SYSTEM, CHILD, GAME_DATA, REGS

ROOT=Path(__file__).resolve().parents[1]
capture=(ROOT/'research/co-op/multibattle/pc-guest-multi-command.ramdump').read_bytes()
payload=(ROOT/'research/co-op/CoopContext.bin').read_bytes()
header=(ROOT/'melonDS-source-1.1/src/frontend/qt_sdl/NativeCoopPayload.h').read_text(encoding='utf-8')

class StoryMachine(Machine):
    def code(self,cpu,address,size,opaque):
        if address==0x02017c84:
            assert cpu.reg_read(REGS[0])==SETUP+0x180
            self.calls.append(('free-original',SETUP+0x180));self.helper_return();return
        super().code(cpu,address,size,opaque)
    def allowed(self,address):
        return 0x02168e1c<=address<0x02168e28 or super().allowed(address)
    def write(self,cpu,access,address,size,value,opaque):
        assert not DATA+44<=address<DATA+48, '44-byte story event overflow'
        super().write(cpu,access,address,size,value,opaque)

cases=0
for result in (1,2,3,4):
    m=StoryMachine(capture,payload,header)
    # Establish equivalent retained data without invoking the 48-byte launcher.
    m.put(EVENT+16,SYSTEM);m.put(EVENT+12,DATA);m.put(DATA,SYSTEM);m.put(DATA+4,GAME_DATA)
    m.put(DATA+8,SETUP);m.put(DATA+20,1);m.put(DATA+24,1);m.put(DATA+32,1);m.put(DATA+40,CONTEXT+0x74c)
    m.put(CONTEXT+0x7dc,EVENT);m.put(CONTEXT+0x7e8,0x53544f52)
    m.put(CONTEXT+0x7e0,SETUP+0x180);m.put(CONTEXT+0x7b8,m.entries['PokePlayCoopSceneEvent']|1)
    m.put(DATA+44,0xfeed1234);m.put(EVENT+8,8);m.put(SETUP+0xa8,result)
    entry=m.entries['PokePlayCoopStoryFieldEvent'];args=(EVENT,EVENT+8,DATA,0)
    assert m.run(entry,args)==0 and m.word(EVENT+8)==8 and not m.calls
    m.put(CONTEXT+0x7bc,1)
    assert m.run(entry,args)==0 and m.word(EVENT+8)==9
    assert len([c for c in m.calls if c[0]=='free-original'])==1
    assert m.word(CHILD)==EVENT and m.word(SYSTEM+24)==CHILD
    # Model completed native field-resume child; execute actual final dispatch.
    m.put(SYSTEM+24,EVENT);m.put(EVENT+8,11)
    assert m.run(entry,args)==0 and m.word(CONTEXT+0x7b4)==result
    assert bytes(m.cpu.mem_read(CONTEXT+0x7d8,1))==b'\1'
    before=list(m.calls)
    assert m.run(entry,args)==0 and m.calls==before # No repeated native free/writeback.
    m.put(CONTEXT+0x7bc,2)
    assert m.run(entry,args)==1 and m.calls==before
    assert m.word(DATA+44)==0xfeed1234
    cases+=1
print(f'{cases} compiled story return cases pass: 44-byte bounds, native victory/defeat resume, one free, result barrier and parent release.')
