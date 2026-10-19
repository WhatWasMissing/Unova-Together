"""Compiled native setup coverage for every populated named Redux rival record."""
from pathlib import Path
import ndspy.rom,ndspy.narc
from test_coop_boss_payload import check
ROOT=Path(__file__).resolve().parents[1]
ids=[161,162,163,166,167,168,368,369,370,378,379,380,588,589,590,684,685,686,693,694,695,696,697,698,701,702,703,794,795,796,853,854,855]
r=ndspy.rom.NintendoDSRom((ROOT/'game-files/rom-original/Pokemon Black 2 Redux Complete (v1.4.1).nds').read_bytes())
t=ndspy.narc.NARC(r.getFileByName('a/0/9/1')).files
cases=0;used=[];empty=[]
for id in ids:
 count=t[id][3]
 if not 1<=count<=6:empty.append((id,count));continue
 for slot in (0,2):
  for n in (1,2,3):check(count,trainer=id,ally=slot,selected_count=n);cases+=1
 used.append(id)
print(f'{cases} compiled native cases across {len(used)} populated rival records. Empty records: {empty}')
