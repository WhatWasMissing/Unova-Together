"""Heal copied Black 2 party HP/status; never edit progression or the source.

Layout and mirrored CRCs reviewed against PKHeX SAV5/SaveBlockAccessor5B2W2.
Only the encrypted party extension and its two affected block CRCs change.
"""
from pathlib import Path
import argparse,binascii,hashlib,itertools,json,struct

ROOT=Path(__file__).resolve().parents[1]
def crypt(data,seed):
    result=bytearray(data)
    for i in range(0,len(result),2):
        seed=(seed*0x41c64e6d+0x6073)&0xffffffff
        struct.pack_into('<H',result,i,struct.unpack_from('<H',result,i)[0]^(seed>>16))
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--battle-stats',type=int,help='optional disposable-fixture combat stats; never used in a normal build')
    a=p.parse_args();assert a.output.resolve().is_relative_to((ROOT/'test-fixtures').resolve())
    assert not a.output.exists();raw=a.source.read_bytes();assert len(raw)==0x80000
    out=bytearray(raw);records=[];allowed=set()
    for bank in (0,0x26000):
        party=bank+0x18e00
        crc=binascii.crc_hqx(raw[party:party+0x534],0xffff)
        if any(struct.unpack_from('<H',raw,bank+x)[0]!=crc for x in (0x19336,0x25f34)):continue
        count=raw[party+4];assert 1<=count<=6
        for slot in range(count):
            pos=party+8+slot*220;record=raw[pos:pos+220]
            pid,flags,checksum=struct.unpack_from('<IHH',record);assert flags==0
            blocks=crypt(record[8:136],checksum)
            assert sum(struct.unpack('<64H',blocks))&0xffff==checksum
            order=list(itertools.permutations(range(4)))[((pid>>13)&31)%24]
            canonical=b''.join(blocks[order.index(i)*32:order.index(i)*32+32] for i in range(4))
            extension=crypt(record[136:],pid);hp,maxhp=struct.unpack_from('<HH',extension,6)
            assert 1<=extension[4]<=100 and 0<=hp<=maxhp<=714 and maxhp>0
            records.append(dict(bank=hex(bank),slot=slot+1,hp=hp,maxHp=maxhp,
                                moves=struct.unpack_from('<4H',canonical,32)))
            struct.pack_into('<I',extension,0,0);struct.pack_into('<H',extension,6,maxhp)
            if a.battle_stats is not None:
                assert 1<=a.battle_stats<=600
                struct.pack_into('<5H',extension,10,*([a.battle_stats]*5))
            out[pos+136:pos+220]=crypt(extension,pid)
            allowed.update(range(pos+136,pos+220))
        crc=binascii.crc_hqx(out[party:party+0x534],0xffff)
        for x in (0x19336,0x25f34):struct.pack_into('<H',out,bank+x,crc)
        crc=binascii.crc_hqx(out[bank+0x25f00:bank+0x25f94],0xffff)
        struct.pack_into('<H',out,bank+0x25fa2,crc)
        for x in (0x19336,0x25f34,0x25fa2):allowed.update((bank+x,bank+x+1))
    assert records,'No valid party bank found'
    changed={i for i,(before,after) in enumerate(zip(raw,out)) if before!=after}
    assert changed<=allowed,'Unexpected change outside party extension/checksums'
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(out)
    assert a.source.read_bytes()==raw
    report=dict(sourceSha256=hashlib.sha256(raw).hexdigest(),outputSha256=hashlib.sha256(out).hexdigest(),battleStats=a.battle_stats,party=records)
    a.output.with_suffix('.healing.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
