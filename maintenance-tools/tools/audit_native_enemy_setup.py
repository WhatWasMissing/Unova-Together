"""Compare retained native co-op enemy metadata/teams to the loaded Redux ROM.
Read-only. Seasonal Deerling forms may be adjusted by the native game loader.
"""
from pathlib import Path
import argparse,struct,itertools,json,ndspy.rom,ndspy.narc
p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--dump',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--doubles-ai',action='store_true',help='Require the additive co-op double-battle AI bit');a=p.parse_args()
rom=ndspy.rom.NintendoDSRom(a.rom.read_bytes());trainers=ndspy.narc.NARC(rom.getFileByName('a/0/9/1')).files;parties=ndspy.narc.NARC(rom.getFileByName('a/0/9/2')).files
u16=lambda b,o:struct.unpack_from('<H',b,o)[0]
def crypt(b,seed):
 out=bytearray(b)
 for o in range(0,len(b),2):
  seed=(seed*0x41c64e6d+0x6073)&0xffffffff;struct.pack_into('<H',out,o,u16(b,o)^(seed>>16))
 return out
def decode(p):
 assert len(p)==220 and u16(p,4)==0
 pid=struct.unpack_from('<I',p)[0];plain=crypt(p[8:136],u16(p,6));assert sum(struct.unpack('<64H',plain))&65535==u16(p,6)
 order=list(itertools.permutations(range(4)))[((pid>>13)&31)%24];blocks=bytearray(128)
 for i,j in enumerate(order):blocks[j*32:(j+1)*32]=plain[i*32:(i+1)*32]
 ext=crypt(p[136:],pid)
 return {'species':u16(blocks,0),'heldItem':u16(blocks,2),'moves':list(struct.unpack_from('<4H',blocks,32)),'level':ext[4],'ability':blocks[13],'form':blocks[56]>>3}
results=[]
for capture in a.dump:
 ram=capture.read_bytes();assert len(ram)==0x400000
 w=lambda adr:struct.unpack_from('<I',ram,adr-0x2000000)[0]
 valid=lambda adr,n:0x2000000<=adr<=0x2400000-n and adr%4==0
 found=[]
 for o in range(0,len(ram)-0x7f0,4):
  if ram[o:o+4]!=b'\x78\x56\x34\x12':continue
  setup=w(0x2000000+o+0x7d0)
  if not valid(setup,0x140) or w(setup)!=1 or w(setup+4)!=1:continue
  metas=[w(setup+0x48+slot*4) for slot in (1,3)]
  if not all(valid(m,40) and w(m)<len(trainers) for m in metas):continue
  same=w(metas[0])==w(metas[1]);slots=[]
  for index,slot in enumerate((1,3)):
   meta=metas[index];tid=w(meta);tr=trainers[tid];raw=parties[tid];typ=tr[0]&3;stride=8+bool(typ&2)*2+bool(typ&1)*8
   expected_ai=struct.unpack_from('<I',tr,12)[0] | (0x80 if a.doubles_ai else 0)
   assert w(meta+8)==expected_ai,f'AI mismatch {tid}'
   assert ram[meta-0x2000000+12:meta-0x2000000+20]==tr[4:12],f'Trainer item mismatch {tid}'
   expected=[]
   for j in range(tr[3]):
    row=raw[j*stride:(j+1)*stride]
    expected.append({'species':u16(row,4)&1023,'heldItem':u16(row,8) if typ&2 else 0,'moves':list(struct.unpack_from('<4H',row,8+bool(typ&2)*2)) if typ&1 else None,'level':u16(row,2),'form':u16(row,4)>>10})
   if same:expected=expected[index::2] if tr[3]>1 else expected
   party=w(setup+0x24+slot*4);assert valid(party,0x534) and w(party)==6 and w(party+4)==len(expected)
   actual=[decode(ram[party-0x2000000+8+j*220:party-0x2000000+8+(j+1)*220]) for j in range(w(party+4))]
   for want,got in zip(expected,actual):
    for key in ('species','heldItem','moves','level','form'):
     if key=='moves' and want[key] is None:continue
     if key=='form' and want['species'] in (585,586) and want[key]==0 and got[key] in range(4):continue
     assert want[key]==got[key],(tid,key,want,got)
   slots.append({'slot':slot,'trainer':tid,'aiFlags':hex(w(meta+8)),'trainerItemsPreserved':True,'expected':expected,'actual':actual})
  found.append({'context':hex(0x2000000+o),'setup':hex(setup),'enemySlots':slots})
 assert found,f'No retained native setup in {capture}'
 results.append({'capture':str(capture),'verifiedSetups':found})
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'passed':True,'results':results,'limits':'Checks setup metadata and explicit ROM team fields; does not grade AI choices or validate every encounter.'},indent=2),encoding='utf-8')
print(f'{len(results)} native captures match ROM AI masks, trainer items, species, levels, explicit moves and held items.')
