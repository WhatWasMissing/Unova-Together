"""Compiled native setup coverage for every populated named Redux rival record."""
from pathlib import Path
import os
import unittest
import ndspy.rom,ndspy.narc
from launcher_ui.preferences import identify
from test_coop_boss_payload import check
ROOT=Path(__file__).resolve().parents[1]
ids=[161,162,163,166,167,168,368,369,370,378,379,380,588,589,590,684,685,686,693,694,695,696,697,698,701,702,703,794,795,796,853,854,855]


class RivalPayloadTests(unittest.TestCase):
 def test_native_setup_for_populated_redux_rival_records(self):
  configured=os.environ.get('UNOVA_TEST_REDUX_ROM')
  rom_path=Path(configured) if configured else ROOT/'game-files/rom-original/Pokemon Black 2 Redux Complete (v1.4.1).nds'
  payload_path=Path(os.environ.get('UNOVA_COOP_CONTEXT',ROOT/'research/co-op/CoopContext.bin'))
  source_root=Path(os.environ.get('UNOVA_MELONDS_SOURCE_ROOT',ROOT/'melonDS-source-1.1'))
  header_path=source_root/'src/frontend/qt_sdl/NativeCoopPayload.h'
  missing=[str(path) for path in (rom_path,payload_path,header_path) if not path.is_file()]
  if missing:
   configured_missing=(
    (configured is not None and not rom_path.is_file()) or
    ('UNOVA_COOP_CONTEXT' in os.environ and not payload_path.is_file()) or
    ('UNOVA_MELONDS_SOURCE_ROOT' in os.environ and not header_path.is_file())
   )
   if configured_missing:self.fail('Configured rival-payload test prerequisites are missing: '+', '.join(missing))
   self.skipTest('private Redux ROM/co-op payload/source fixtures are unavailable; configure UNOVA_TEST_REDUX_ROM, UNOVA_COOP_CONTEXT, and UNOVA_MELONDS_SOURCE_ROOT')
  profile=identify(rom_path)
  self.assertIsNotNone(profile,'ROM does not match the supported English Redux v1.4.1 profile')
  self.assertEqual(profile['profile'],'Blaze Black 2 Redux Complete v1.4.1 / Unova Together')
  r=ndspy.rom.NintendoDSRom(rom_path.read_bytes())
  t=ndspy.narc.NARC(r.getFileByName('a/0/9/1')).files
  cases=0;used=[];empty=[]
  for id in ids:
   count=t[id][3]
   if not 1<=count<=6:empty.append((id,count));continue
   for slot in (0,2):
    for n in (1,2,3):check(count,trainer=id,ally=slot,selected_count=n);cases+=1
   used.append(id)
  self.assertGreater(cases,0,'No populated rival records were found')
  self.assertGreater(len(used),0,'No populated rival records were found')
  self.cases=cases
  print(f'{cases} compiled native cases across {len(used)} populated rival records. Redux ARM9 SHA-256: {profile["digest"]}. Empty records: {empty}')


if __name__ == '__main__':
 unittest.main()
