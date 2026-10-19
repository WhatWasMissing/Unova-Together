"""Run compiled story callback and actual native defeat/victory return branches.

Helper contracts and private RAM are isolated in Unicorn. This does not award
a badge or claim an actual NPC script has been playtested.
"""
from pathlib import Path
import os
import unittest
from test_coop_field_return import Machine, CONTEXT, DATA, EVENT, SETUP, SYSTEM, CHILD, GAME_DATA, REGS

ROOT=Path(__file__).resolve().parents[1]

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

def run_story_return_cases(capture, payload, header):
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
    return cases


class CoopStoryReturnTests(unittest.TestCase):
    def test_native_story_return_branches(self):
        capture_path=Path(os.environ.get('UNOVA_COOP_STORY_CAPTURE', ROOT/'research/co-op/multibattle/pc-guest-multi-command.ramdump'))
        payload_path=Path(os.environ.get('UNOVA_COOP_CONTEXT', ROOT/'research/co-op/CoopContext.bin'))
        source_root=Path(os.environ.get('UNOVA_MELONDS_SOURCE_ROOT', ROOT/'melonDS-source-1.1'))
        header_path=source_root/'src/frontend/qt_sdl/NativeCoopPayload.h'
        required=(capture_path,payload_path,header_path)
        missing=[str(path) for path in required if not path.is_file()]
        if missing:
            configured_missing=(
                ('UNOVA_COOP_STORY_CAPTURE' in os.environ and not capture_path.is_file()) or
                ('UNOVA_COOP_CONTEXT' in os.environ and not payload_path.is_file()) or
                ('UNOVA_MELONDS_SOURCE_ROOT' in os.environ and not header_path.is_file())
            )
            if configured_missing:
                self.fail('Configured co-op story test prerequisites are missing: '+', '.join(missing))
            self.skipTest('private RAM/payload/source fixtures are unavailable; configure UNOVA_COOP_STORY_CAPTURE, UNOVA_COOP_CONTEXT, and UNOVA_MELONDS_SOURCE_ROOT')
        capture=capture_path.read_bytes()
        payload=payload_path.read_bytes()
        header=header_path.read_text(encoding='utf-8')
        self.assertEqual(run_story_return_cases(capture,payload,header),4)


if __name__ == '__main__':
    unittest.main()
