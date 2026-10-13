"""Read-only Black 2 tools by mvq1303 / WhatWasMissing."""
import bisect, binascii, hashlib, itertools, struct
from pathlib import Path
import ndspy.code, ndspy.narc, ndspy.rom

REDUX='332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a'
GROWTH=['Medium Fast','Erratic','Fluctuating','Medium Slow','Fast','Slow']
BOSSES=[('Cheren',764,14),('Roxie',765,21),('Burgh',766,29),('Elesa',767,38),('Clay',768,45),('Skyla',769,55),('Drayden',770,64),('Marlon',771,68),('Ghetsis',345,72),('Elite Four',772,78),('Iris',776,79)]
FINGERPRINTS=[(0x021a8e10,'144b281c391c221ceb1805f0f7ff6868'),(0x021aee0c,'f0b58db000904068019102921d1ceff7'),(0x021af0be,'0db0f0bdc046331b0000a0860100'),(0x021a8e64,'0c1b0000')]

def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def load_rom(path):
    path=Path(path)
    if path.suffix.lower()!='.nds':raise ValueError('Choose a Nintendo DS .nds ROM.')
    return ndspy.rom.NintendoDSRom.fromFile(str(path))

def compatibility(path):
    rom=load_rom(path);lines=['English Black 2 / solo XP hook checks']
    identity=rom.idCode==b'IREO';lines.append(('PASS' if identity else 'FAIL')+': English Black 2 game code IREO')
    try:
        overlay=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda oid,fid:rom.files[fid])[167]
        matched=all(overlay.data[a-overlay.ramAddress:a-overlay.ramAddress+len(bytes.fromhex(h))]==bytes.fromhex(h) for a,h in FINGERPRINTS)
    except (KeyError,ValueError,IndexError):matched=False
    lines.append(('PASS' if matched else 'FAIL')+': XP caller, routine, return and context fingerprints')
    lines.append('Reviewed Redux 1.4.1: '+('exact ROM match' if digest(path)==REDUX else 'different ROM revision'))
    lines.append('These checks cover ROM identity and the XP hook. Test multiplayer and edited content in-game with the same ROM on both computers.')
    return '\n'.join(lines)

def progression(path,loss=0,growth=3):
    loss=float(loss)
    if not 0<=loss<=100:raise ValueError('Lost XP must be between 0 and 100 percent.')
    if digest(path)!=REDUX:raise ValueError('Challenge caps are verified for Redux Complete 1.4.1 only. Select the reviewed original ROM.')
    rom=load_rom(path);tables=ndspy.narc.NARC(rom.getFileByName('a/0/1/7')).files
    table=struct.unpack('<101I',tables[growth]);trainers=ndspy.narc.NARC(rom.getFileByName('a/0/9/1')).files;parties=ndspy.narc.NARC(rom.getFileByName('a/0/9/2')).files
    lines=[f'Redux Challenge • {GROWTH[growth]} • 1.25× solo XP • {loss:g}% earned XP lost to co-op','Checkpoint       Cap   XP-budget level   Stored trainer team']
    for name,tid,cap in BOSSES:
        xp=int(table[5]+(table[cap]-table[5])*1.25*(1-loss/100));level=min(100,bisect.bisect_right(table,xp)-1)
        record=trainers[tid];stride=8+(2 if record[0]&2 else 0)+(8 if record[0]&1 else 0)
        members=[f'#{struct.unpack_from("<H",parties[tid],i*stride+4)[0]&2047} L{struct.unpack_from("<H",parties[tid],i*stride+2)[0]}' for i in range(record[3])]
        lines.append(f'{name:16} {cap:3}   {level:3}               '+', '.join(members))
    lines+=['','Budget equivalent from level 5, not a playthrough prediction. Uses exact ROM growth thresholds and documented displayed Challenge caps. Stored team levels omit runtime difficulty shifts.','Lost XP is a share of earned XP, not battle count. Encounter choices, level-dependent award feedback, per-award rounding and the award cap are not simulated. 1.25× offsets about 20% missing XP.']
    return '\n'.join(lines)

def crypt(data,seed):
    result=bytearray(data)
    for offset in range(0,len(result),2):
        seed=(seed*0x41c64e6d+0x6073)&0xffffffff
        struct.pack_into('<H',result,offset,struct.unpack_from('<H',result,offset)[0]^(seed>>16))
    return result

def inspect_save(path):
    path=Path(path)
    if not 0x4c000<=path.stat().st_size<=16*1024*1024:raise ValueError('Not a supported Black 2 save size.')
    raw=path.read_bytes();banks=[]
    for bank in (0,0x26000):
        offset=bank+0x18e00
        if binascii.crc_hqx(raw[offset:offset+0x534],0xffff)!=struct.unpack_from('<H',raw,bank+0x19336)[0]:continue
        count=struct.unpack_from('<I',raw,offset+4)[0]
        if not 0<=count<=6:continue
        party=[]
        for i in range(count):
            record=raw[offset+8+i*220:offset+8+(i+1)*220];pid,flags,checksum=struct.unpack_from('<IHH',record);blocks=crypt(record[8:136],checksum)
            if flags or sum(struct.unpack('<64H',blocks))&65535!=checksum:raise ValueError('Party Pokémon checksum failed.')
            order=list(itertools.permutations(range(4)))[((pid>>13)&31)%24];canonical=b''.join(blocks[order.index(j)*32:order.index(j)*32+32] for j in range(4));ext=crypt(record[136:],pid)
            party.append(dict(pid=pid,species=struct.unpack_from('<H',canonical)[0],xp=struct.unpack_from('<I',canonical,8)[0],level=ext[4],hp=struct.unpack_from('<H',ext,6)[0],moves=list(struct.unpack_from('<4H',canonical,32))))
        banks.append(dict(bank=hex(bank),party=party))
    if not banks:raise ValueError('No checksum-valid Black 2 party block found. Other games and save states are unsupported.')
    return dict(name=path.name,sha256=hashlib.sha256(raw).hexdigest(),banks=banks)

def compare_saves(first,second):
    a,b=inspect_save(first),inspect_save(second)
    lines=['Read-only Black 2 party comparison. Party block and Pokémon checksums verified; this does not validate every save block.','Both bank snapshots are shown; differing banks are not assumed to be the latest.']
    for item in (a,b):
        lines+=['',item['name']+' • SHA-256 '+item['sha256']]
        for bank in item['banks']:
            lines.append('Bank '+bank['bank'])
            lines.extend(f"PID {p['pid']} • species #{p['species']} • level {p['level']} • XP {p['xp']} • HP {p['hp']} • moves {p['moves']}" for p in bank['party'])
    lines+=['','Byte-identical files: '+str(a['sha256']==b['sha256'])]
    return '\n'.join(lines)
