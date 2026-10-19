"""Execute compiled boss setup: exact team conservation and failure cleanup."""
from pathlib import Path
import re
import struct
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

ROOT = Path(__file__).resolve().parents[1]
CODE, CONTEXT, SYSTEM, DATA, RECORD, SETUP = 0x03003000, 0x03005000, 0x03006000, 0x03006400, 0x03006800, 0x03007000
SELECTED, FIRST, SECOND, COPY, LOCAL = 0x03008000, 0x03009000, 0x0300a000, 0x0300b000, 0x0300c000
STACK, RETURN = 0x03018000, 0x03020000
META_FIRST, META_SECOND = 0x03014000, 0x03014100
REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3]

def check(count, trainer=156, fail_alloc=False, fail_add=False, ally=0, selected_count=1, secondary=0, second_count=2):
    payload = (ROOT / 'research/co-op/CoopContext.bin').read_bytes()
    header = (ROOT / 'melonDS-source-1.1/src/frontend/qt_sdl/NativeCoopPayload.h').read_text()
    entry = CODE + int(re.search(r'PokePlayPrepareCoopSetupOffset=0x([0-9a-f]+)', header)[1], 16)
    cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    cpu.mem_map(0x02000000, 0x400000)
    cpu.mem_map(0x03000000, 0x30000)
    cpu.mem_write(CODE, payload)
    cpu.mem_write(CONTEXT, struct.pack('<II', 0x12345678, 1))
    cpu.mem_write(CONTEXT + 0x6c, struct.pack('<I', DATA))
    cpu.mem_write(CONTEXT + 0x7cc, struct.pack('<I', SELECTED))
    original = [bytes([i + 1]) * 220 for i in range(count)]
    parties = {SELECTED: [bytes([99+i]) * 220 for i in range(selected_count)], FIRST: original[:], SECOND: original[:], LOCAL: [], COPY: []}
    other = [bytes([70+i]) * 220 for i in range(second_count)]
    if secondary: parties[SECOND] = other[:]
    pokemon = {}
    frees = []
    finished = False
    def code(c, address, size, opaque):
        nonlocal finished
        if address == RETURN:
            finished = True; c.emu_stop(); return
        if CODE <= address < CODE + len(payload): return
        args = tuple(c.reg_read(r) for r in REGS)
        result = 0
        if address == 0x02016ad8:
            assert args[0] == SYSTEM; result = DATA
        elif address == 0x0201fdf8: result = len(parties[args[0]])
        elif address == 0x02040440: result = RECORD
        elif address == 0x02017c60: result = SETUP
        elif address == 0x0201848c:
            assert args == (SETUP, DATA, RECORD, 1)
            stack = struct.unpack('<IIII', c.mem_read(c.reg_read(UC_ARM_REG_SP), 16))
            assert stack == (ally, trainer, secondary or trainer, 1), stack
            for offset, pointer in [(0x24, LOCAL), (0x28, FIRST), (0x30, SECOND)]:
                c.mem_write(SETUP + offset, struct.pack('<I', pointer))
            for offset,pointer,mask in ((0x4c,META_FIRST,0x7),(0x54,META_SECOND,0x403)):
                c.mem_write(SETUP+offset,struct.pack('<I',pointer))
                c.mem_write(pointer+8,struct.pack('<I',mask))
        elif address == 0x02039d9c:
            assert args[:2] == (1, 0x534); result = 0 if fail_alloc else COPY
        elif address == 0x0201fd34:
            assert args[1] == 6; parties[args[0]] = []
        elif address == 0x020200ac: parties[args[1]] = parties[args[0]][:]
        elif address == 0x0201ff08:
            result = 0x0300d000 + args[1] * 220
            pokemon[result] = parties[args[0]][args[1]]
        elif address == 0x0201fd6c:
            if not fail_add:
                parties[args[0]].append(pokemon[args[1]]); result = 1
        elif address in (0x02039e2c, 0x02017c84): frees.append(args[0])
        else: raise AssertionError(f'Unreviewed native dependency {address:#x}')
        c.reg_write(UC_ARM_REG_R0, result)
        c.reg_write(UC_ARM_REG_PC, c.reg_read(UC_ARM_REG_LR))
    cpu.hook_add(UC_HOOK_CODE, code)
    for reg, value in zip(REGS, (CONTEXT, SYSTEM, ally, (secondary << 16) | (trainer << 1) | 1)): cpu.reg_write(reg, value)
    cpu.reg_write(UC_ARM_REG_SP, STACK + 0x1000)
    cpu.reg_write(UC_ARM_REG_LR, RETURN | 1)
    cpu.emu_start(entry | 1, RETURN + 2, count=30000)
    assert finished
    result = cpu.reg_read(UC_ARM_REG_R0)
    if selected_count not in (1,2,3):
        assert result==0 and not frees
    elif (not secondary and (fail_alloc or fail_add)) or count < 1 or count > 6 or (secondary and not 1 <= second_count <= 6):
        assert result == 0 and SETUP in frees
        assert struct.unpack('<I', cpu.mem_read(CONTEXT + 0x7d0, 4))[0] == 0
        if fail_add: assert COPY in frees
    else:
        assert result == SETUP and frees == ([] if secondary else [COPY])
        assert struct.unpack('<I',cpu.mem_read(META_FIRST+8,4))[0]==0x87
        assert struct.unpack('<I',cpu.mem_read(META_SECOND+8,4))[0]==0x483
        effective=original*2 if count==1 and not secondary else original
        assert parties[FIRST] == (original if secondary else effective[::2]) and parties[SECOND] == (other if secondary else effective[1::2])
        assert parties[LOCAL] == parties[SELECTED]
        assert sorted(parties[FIRST] + parties[SECOND]) == sorted(effective + (other if secondary else []))
        assert struct.unpack('<I', cpu.mem_read(CONTEXT + 0x7ec, 4))[0] == len(effective) + (second_count if secondary else 0)

if __name__ == '__main__':
    cases = 0
    for ally in (0, 2):
        for trainer in (156, 764, 345):
            for selected_count in (1,2,3):
                for count in range(1, 7): check(count, trainer=trainer, ally=ally,selected_count=selected_count); cases += 1
        for selected_count in (0,4):check(6,ally=ally,selected_count=selected_count);cases+=1
        for extra in ({'fail_alloc': True}, {'fail_add': True}):
            check(6, ally=ally, **extra); cases += 1
        for count in (0, 1, 7): check(count, ally=ally); cases += 1
    for ally in (0,2):
        for count in range(1,7):
            for second_count in range(1,7):
                for selected_count in (1,2,3):
                    check(count,trainer=850,secondary=851,second_count=second_count,ally=ally,selected_count=selected_count);cases+=1
        for second_count in (0,7):check(2,trainer=850,secondary=851,second_count=second_count,ally=ally);cases+=1
    print(f'{cases} compiled boss cases passed: 1–3 human Pokemon, both ally slots, exact boss team conservation and failure cleanup.')
