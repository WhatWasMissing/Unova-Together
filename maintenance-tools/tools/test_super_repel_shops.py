"""Genuine Black 2/Redux catalogs and compiled production price policy; read-only."""
from pathlib import Path
import os,subprocess,tempfile
import ndspy.rom,ndspy.codeCompression
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_SP,UC_ARM_REG_LR
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'melonDS-source-1.1' if (ROOT/'melonDS-source-1.1').is_dir() else ROOT/'source/melonDS'
def main():
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env['PATH']
    with tempfile.TemporaryDirectory(prefix='unova-shops-') as folder:
        directory=Path(folder);exe=directory/'check.exe'
        subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-O2','-Wall','-Wextra','-Werror','-I'+str(SOURCE/'src'),str(ROOT/'tools/check_super_repel_shops.cpp'),'-o',str(exe)],env=env,check=True)
        for path in (ROOT/'game-files/black2original/Pokemon - Black Version 2 (USA, Europe) (NDSi Enhanced).nds',ROOT/'game-files/rom-original/Pokemon Black 2 Redux Complete (v1.4.1).nds'):
            rom=ndspy.rom.NintendoDSRom(path.read_bytes());arm=ndspy.codeCompression.decompress(rom.arm9)
            ram=bytearray(0x400000);start=rom.arm9RamAddress-0x02000000;ram[start:start+len(arm)]=arm
            item=directory/'super-repel.bin'
            subprocess.run([str(exe),str(path),str(item)],env=env,check=True)
            cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB);cpu.mem_map(0x02000000,0x400000);cpu.mem_write(0x02000000,bytes(ram))
            cpu.mem_map(0x03000000,0x20000);cpu.mem_write(0x02300000,item.read_bytes())
            cpu.reg_write(UC_ARM_REG_R0,0x02300000);cpu.reg_write(UC_ARM_REG_R1,0)
            cpu.reg_write(UC_ARM_REG_SP,0x0301f000);cpu.reg_write(UC_ARM_REG_LR,0x03001001)
            cpu.hook_add(UC_HOOK_CODE,lambda c,a,n,d:c.emu_stop() if a==0x03001000 else None)
            cpu.emu_start(0x02026821,0x03001002,count=1000)
            assert cpu.reg_read(UC_ARM_REG_R0)==10,'Actual native item getter must return the minimum positive 10-money price.'
            print('Actual ROM item-price routine returned 10; no instruction hook or forced return.',flush=True)
if __name__=='__main__':main()
