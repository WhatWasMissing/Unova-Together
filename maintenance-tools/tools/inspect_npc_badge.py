"""Read actual native Misc-save ownership from a copied Black 2 RAM capture.

Execute the ROM-backed read-only getter in isolated Unicorn memory. Writes
are allowed only to the private scratch stack, never to captured game RAM.
This observes a badge award; it does not prove normal saving or reload.
"""
from pathlib import Path
import argparse,json,struct
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC

def inspect(path):
    ram=path.read_bytes();assert len(ram)==0x400000
    def word(p):
        assert 0x02000000<=p<=0x023ffffc and not p&3
        return struct.unpack_from('<I',ram,p-0x02000000)[0]
    manager=word(0x02141858);proc=word(manager+8);system=0
    for _ in range(8):
        if word(proc)==0x02090010 and word(proc+4)==0xffffffff:system=word(proc+20);break
        proc=word(proc+24)
    assert system;game=word(system+28)
    assert ram[0x17974:0x1797c]==bytes.fromhex('0068014b1847c046')
    assert word(0x0216b538+0xd7*4)==0x02155851 # reviewed badge-count script handler
    cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB);cpu.mem_map(0x02000000,0x400000);cpu.mem_write(0x02000000,ram)
    cpu.mem_map(0x03000000,0x20000)
    def write(_cpu,_access,address,_size,_value,_opaque):
        assert 0x03000000<=address<0x03020000,'Native getter attempted to mutate captured game RAM'
    cpu.hook_add(UC_HOOK_MEM_WRITE,write)
    cpu.reg_write(UC_ARM_REG_R0,game);cpu.reg_write(UC_ARM_REG_SP,0x03010000);cpu.reg_write(UC_ARM_REG_LR,0x03011001)
    cpu.emu_start(0x02017975,0x03011000,count=10000)
    assert cpu.reg_read(UC_ARM_REG_PC)==0x03011000
    misc=cpu.reg_read(UC_ARM_REG_R0);mask=word(misc+4);assert mask<=255
    return dict(capture=str(path),gameData=hex(game),miscSave=hex(misc),badgeMask=mask,cherenBadge=bool(mask&1))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('captures',type=Path,nargs='+');a=p.parse_args()
    print(json.dumps([inspect(x) for x in a.captures],indent=2))
