"""Regress native co-op defeat return using a private supported RAM capture.

Executes the generated ARM launcher and the actual native state-8 dispatcher
in Unicorn. Scene creation, peer count, allocation, event flags and division
use explicit reviewed helper contracts. This is not a live scene-resume test.
No ROM, save, capture or emulator process is modified.
"""
from pathlib import Path
import argparse
import re
import struct

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x02000000
CONTEXT = 0x023F0000
CODE = 0x03003000
EVENT = 0x03007000
DATA = 0x03007200
SYSTEM = 0x03007400
CHILD = 0x03007600
SETUP = 0x03008000
GAME_DATA = 0x03009000
FIELD = 0x0300A000
PARTY = 0x0300B000
SELECTED = 0x0300C000
BACKUP = 0x0300D000
STACK = 0x03010000
RETURN = 0x03020000
REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)
NATIVE_FIELD = 0x02168BAC


class Machine:
    def __init__(self, capture, payload, header):
        self.cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.cpu.mem_map(BASE, len(capture))
        self.cpu.mem_write(BASE, capture)
        self.cpu.mem_map(0x03000000, 0x30000)
        self.cpu.mem_write(CODE, payload)
        self.capture = capture
        self.payload = payload
        self.entries = {
            name: CODE + int(offset, 16)
            for name, offset in re.findall(r'(PokePlay\w+)Offset=0x([0-9a-f]+)', header)
        }
        self.adapter = struct.unpack_from('<I', capture, 0x021418B0-BASE)[0]
        assert BASE <= self.adapter <= BASE+len(capture)-0x350, 'Capture has no native adapter'
        self.cpu.mem_write(CONTEXT, bytes(0x7F0))
        self.put(CONTEXT, 0x12345678)
        self.put(CONTEXT+0x6C, GAME_DATA)
        self.put(CONTEXT+0x7D0, SETUP)
        self.put(self.adapter+0x34C, CONTEXT)
        self.put(SYSTEM+28, GAME_DATA)
        self.put(SYSTEM+32, FIELD)
        self.put(SETUP, 1)
        self.put(SETUP+8, 9)
        self.put(SETUP+0x9C, 0x4000)
        self.put(SETUP+0xA8, 2)  # Native defeat result.
        self.peers = 2
        self.allocate = True
        self.finished = False
        self.calls = []
        self.party_hp = None
        self.cpu.hook_add(UC_HOOK_CODE, self.code)
        self.cpu.hook_add(UC_HOOK_MEM_WRITE, self.write)

    def put(self, address, value):
        self.cpu.mem_write(address, struct.pack('<I', value))

    def word(self, address):
        return struct.unpack('<I', self.cpu.mem_read(address, 4))[0]

    def helper_return(self, value=None):
        if value is not None:
            self.cpu.reg_write(UC_ARM_REG_R0, value)
        self.cpu.reg_write(UC_ARM_REG_PC, self.cpu.reg_read(UC_ARM_REG_LR))

    def code(self, cpu, address, size, opaque):
        args = tuple(cpu.reg_read(reg) for reg in REGS)
        if address == RETURN:
            self.finished = True
            cpu.emu_stop()
        elif address == 0x02040474:
            self.calls.append(('peer-count', self.peers))
            self.helper_return(self.peers)
        elif address == 0x0201CCF8:
            if args[:3] == (PARTY+8, 0x4C, 0):
                self.calls.append(('native-egg-contract', args[:3]))
                self.helper_return(0);return
            assert self.party_hp is not None and args[:3] == (PARTY+8, 0xA0, 0), args
            self.calls.append(('native-current-hp', args[:3]))
            # Run the public native getter, including decrypt/re-encrypt.
        elif address == 0x02039D9C:
            assert args[:2] == (1, 0x534), args
            backup=any(c[0]=='allocate-selected-party' for c in self.calls)
            self.calls.append(('allocate-backup-party' if backup else 'allocate-selected-party', args[:2]))
            self.helper_return((BACKUP if backup else SELECTED) if self.allocate else 0)
        elif address == 0x0201FD34:
            assert args[0] in (SELECTED,BACKUP) and args[1]==6, args
            self.calls.append(('initialize-backup-party' if args[0]==BACKUP else 'initialize-selected-party', args[:2]))
            cpu.mem_write(args[0], bytes(0x534))
            self.put(args[0], 6)
            self.helper_return()
        elif address == 0x020200AC:
            assert args[:2]==(PARTY,BACKUP), args
            self.calls.append(('copy-full-party', args[:2]))
            cpu.mem_write(BACKUP,bytes(cpu.mem_read(PARTY,0x534)));self.helper_return()
        elif address == 0x0201FD6C:
            assert args[:2] == (SELECTED, PARTY+8), args
            assert self.word(SELECTED) == 6 and self.word(SELECTED+4) == 0
            self.calls.append(('copy-selected-pokemon', args[:2]))
            cpu.mem_write(SELECTED+8, bytes(cpu.mem_read(PARTY+8, 220)))
            self.put(SELECTED+4, 1)
            self.helper_return(1)
        elif address == 0x02016CB4:
            assert args == (SYSTEM, 0, self.entries['PokePlayCoopFieldEvent'] | 1, 48), args
            self.calls.append(('create-battle-event', args))
            if self.allocate:
                cpu.mem_write(EVENT, bytes(20))
                cpu.mem_write(DATA, bytes(48))
                self.put(EVENT+4, args[2])
                self.put(EVENT+12, DATA)
                self.put(EVENT+16, SYSTEM)
            self.helper_return(EVENT if self.allocate else 0)
        elif address == 0x02078658:
            # Native setup initializer calls MI_CpuFill8(value, dest, size).
            assert args[:3] == (0, DATA, 44), args
            self.calls.append(('initialize-battle-data', args[:3]))
            cpu.mem_write(DATA, bytes(44))
            self.helper_return()
        elif address == 0x02017D18:
            # Execute the actual native OR setter, rather than duplicating it.
            assert args[:2] == (SETUP, 0x100), args
            self.calls.append(('native-setup-flag', args[:2]))
        elif address == 0x02019494:
            assert args[0] == SYSTEM, args
            self.calls.append(('create-field-resume', SYSTEM))
            cpu.mem_write(CHILD, bytes(20))
            self.put(CHILD+4, 0x0201944D)
            self.put(CHILD+16, SYSTEM)
            self.helper_return(CHILD)
        elif address == 0x0216A274:
            # Native post-battle optional party-healing event flag 0x966.
            # Ordinary field return has this save event flag unset.
            assert args[0] == GAME_DATA, args
            self.calls.append(('optional-healing-flag', GAME_DATA))
            self.helper_return(0)
        elif address == 0x02016D68:
            # Execute native event chaining and GameSystem current-event store.
            assert args[:2] == (EVENT, CHILD), args
            self.calls.append(('chain-field-resume', args[:2]))
        elif address == 0x0208D868:
            # Native dispatcher integrity counter uses signed division.
            assert args[:2] == (0x013A1AB5, 0x1933), args
            self.calls.append(('division', args[:2]))
            quotient, remainder = divmod(args[0], args[1])
            cpu.reg_write(UC_ARM_REG_R1, remainder)
            self.helper_return(quotient)
        elif self.allowed(address):
            return
        else:
            raise AssertionError(f'Unreviewed native dependency {address:#x}')

    def allowed(self, address):
        ranges = (
            (CODE, CODE+len(self.payload)),
            (0x02016AD8, 0x02016ADC),  # GameSystem_GetGameData
            (0x02016AEC, 0x02016AF4),  # SetCurrentEvent/GetField
            (0x02016D68, 0x02016D74),  # Chain child event
            (0x02016EDC, 0x02016EE0),  # Event_GetData
            (0x02017D18, 0x02017D26),  # BattleSetup_ORFlags
            (0x0201735C, 0x02017364),  # GameData_GetParty
            (0x0201FDF8, 0x0201FDFC),  # Party_GetCount
            (0x0201FF08, 0x0201FF12),  # Party_GetPokemon
            (0x0201CCF8, 0x0201CD1C),  # Public Pokemon_GetValue
            (0x0201DDA4, 0x0201DEC8),  # Decrypt/get HP/re-encrypt wrappers
            (0x0201ECDC, 0x0201ED48),  # Native encryption and checksum
            (0x02168BAC, 0x02168BE0),  # Actual dispatcher state switch
            (0x02168C08, 0x02168C10),  # Advance dispatcher state
            (0x02168D9A, 0x02168DBC),  # Loss shortcut / normal return decision
            (0x02168DD6, 0x02168DF2),  # Normal field-resume creation
            (0x02168C00, 0x02168C08),  # Queue native child
            (0x02168E28, 0x02168E34),  # Reviewed integrity division
            (0x02168E46, 0x02168E4C),  # Return pending
            (0x021690A0, 0x021690C4),  # Native result/type predicate
            (0x021690D4, 0x021690E8),  # Read native battle result
            (0x0216911C, 0x02169154),  # Setup field data / retain setup
        )
        return any(start <= address < end for start, end in ranges)

    def write(self, cpu, access, address, size, value, opaque):
        ranges = (
            (CONTEXT, CONTEXT+0x7F0), (EVENT, EVENT+20), (DATA, DATA+48),
            (SYSTEM, SYSTEM+48), (CHILD, CHILD+20), (SETUP, SETUP+0x140),
            (PARTY+8, PARTY+8+220), (SELECTED, SELECTED+0x534),
            (BACKUP, BACKUP+0x534),
            (STACK, STACK+0x1000),
        )
        assert any(start <= address and address+size <= end for start, end in ranges), (
            f'Native write outside reviewed ownership: {address:#x}+{size}'
        )

    def run(self, entry, args):
        self.finished = False
        self.cpu.reg_write(UC_ARM_REG_SP, STACK+0x1000)
        self.cpu.reg_write(UC_ARM_REG_LR, RETURN | 1)
        for reg, value in zip(REGS, args):
            self.cpu.reg_write(reg, value)
        self.cpu.emu_start(entry | 1, RETURN+2, count=10000)
        assert self.finished, 'Native path failed to return within instruction budget'
        return self.cpu.reg_read(UC_ARM_REG_R0)

    def launch(self):
        return self.run(self.entries['PokePlayLaunchCoopBattle'], (
            CONTEXT, SYSTEM, self.entries['PokePlayCoopFieldEvent'] | 1,
            self.entries['PokePlayCoopSceneEvent'] | 1,
        ))

    def prepare_party(self, hp):
        # Copy a genuine private captured party record into this isolated
        # machine. Change only its encrypted current-HP tail for boundary
        # cases; boxed data, PID and checksum remain genuine and unchanged.
        word = lambda address: struct.unpack_from('<I', self.capture, address-BASE)[0]
        manager = word(0x02141858)
        process = word(manager+8)
        source = 0
        for _ in range(8):
            assert BASE <= process <= BASE+len(self.capture)-32
            if word(process) == 0x02090010 and word(process+4) == 0xFFFFFFFF:
                source = word(word(word(process+20)+28)+0x194)
                break
            process = word(process+24)
        assert BASE <= source <= BASE+len(self.capture)-0x534 and 1 <= word(source+4) <= 6
        pokemon = bytearray(self.capture[source-BASE+8:source-BASE+8+220])
        pid, flags = struct.unpack_from('<IH', pokemon)
        tail = bytearray(pokemon[0x88:])

        def crypt(data):
            seed = pid
            for offset in range(0, 84, 2):
                seed = (seed*0x41C64E6D+0x6073) & 0xFFFFFFFF
                value = struct.unpack_from('<H', data, offset)[0] ^ (seed >> 16)
                struct.pack_into('<H', data, offset, value)

        if not flags & 1:
            crypt(tail)
        maximum = struct.unpack_from('<H', tail, 8)[0]
        assert maximum > 0
        if hp is None:
            hp = maximum
        assert 0 <= hp <= maximum
        struct.pack_into('<H', tail, 6, hp)
        if not flags & 1:
            crypt(tail)
        pokemon[0x88:] = tail
        self.cpu.mem_write(PARTY, struct.pack('<II', 6, 1)+pokemon+bytes(0x534-228))
        self.cpu.mem_write(SELECTED, bytes([0xAA])*0x534)
        self.put(GAME_DATA+0x194, PARTY)
        self.put(CONTEXT+4, 1)
        self.party_hp = hp
        before_source = bytes(self.cpu.mem_read(PARTY, 0x534))
        result = self.run(self.entries['PokePlayPrepareCoopParty'], (CONTEXT, SYSTEM, 0, 0))
        assert bytes(self.cpu.mem_read(PARTY, 0x534)) == before_source, 'Getter modified source party'
        return result


def verify_profile(capture, payload, header):
    assert len(capture) == 0x400000, 'Expected a 4 MiB main RAM snapshot'
    expected = re.search(r'Code=\{(.*?)\n\};', header, re.S)[1]
    assert payload == bytes(int(x, 16) for x in re.findall(r'0x([0-9a-f]{2})', expected)), (
        'Payload differs from generated source header'
    )
    addresses = {0x02016AD8, 0x02016AEC, 0x02016EDC, 0x02017D18,
                 0x02168BAC, 0x0216911C, 0x0201CCF8}
    checked = set()
    for address, data in re.findall(r'\{0x([0-9a-f]+), \{([^}]+)\}\}', header):
        address = int(address, 16)
        if address in addresses:
            expected = bytes(int(x, 16) for x in re.findall(r'0x([0-9a-f]{2})', data))
            assert capture[address-BASE:address-BASE+len(expected)] == expected, hex(address)
            checked.add(address)
    assert checked == addresses, 'Generated profile lacks a reviewed native helper'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('payload', type=Path)
    args = parser.parse_args()
    capture, payload = args.capture.read_bytes(), args.payload.read_bytes()
    header = (ROOT/'melonDS-source-1.1/src/frontend/qt_sdl/NativeCoopPayload.h').read_text()
    verify_profile(capture, payload, header)
    cases = 0

    for hp in (0, 1, None):
        machine = Machine(capture, payload, header)
        result = machine.prepare_party(hp)
        names = [call[0] for call in machine.calls]
        assert names[:2] == ['native-egg-contract','native-current-hp']
        if hp == 0:
            assert result == 0 and machine.word(CONTEXT+0x7CC) == 0
            assert machine.word(CONTEXT+0x7E4) == 1
            assert names == ['native-egg-contract','native-current-hp'], 'Fainted party allocated/copied/registered'
            assert bytes(machine.cpu.mem_read(SELECTED, 0x534)) == bytes([0xAA])*0x534
        else:
            assert result == SELECTED and machine.word(CONTEXT+0x7CC) == SELECTED
            assert machine.word(CONTEXT+0x7E4) == 0
            assert names == ['native-egg-contract','native-current-hp', 'allocate-selected-party',
                             'initialize-selected-party', 'copy-selected-pokemon',
                             'allocate-backup-party','initialize-backup-party','copy-full-party']
            assert machine.word(SELECTED) == 6 and machine.word(SELECTED+4) == 1
            assert bytes(machine.cpu.mem_read(SELECTED+8, 220)) == bytes(machine.cpu.mem_read(PARTY+8, 220))
        cases += 1

    machine = Machine(capture, payload, header)
    assert machine.launch() == EVENT
    assert machine.word(SETUP+0x9C) == 0x4100, 'Native no-blackout flag missing or old flags lost'
    assert machine.word(DATA+20) == machine.word(DATA+24) == machine.word(DATA+32) == 1
    assert machine.word(DATA+40) == CONTEXT+0x74C
    assert machine.word(DATA+44) == machine.entries['PokePlayCoopSceneEvent'] | 1
    assert machine.word(CONTEXT+0x7DC) == EVENT
    assert machine.word(SYSTEM+24) == EVENT
    assert sum(call[0] == 'native-setup-flag' for call in machine.calls) == 1
    cases += 1

    # Guard launch ownership before allocation or mutation of a foreign game.
    for guard in ('foreign-context', 'foreign-game-data', 'wrong-peer-count',
                  'busy-field-event', 'missing-field', 'missing-setup', 'allocation-failure'):
        machine = Machine(capture, payload, header)
        if guard == 'foreign-context': machine.put(machine.adapter+0x34C, CONTEXT+4)
        elif guard == 'foreign-game-data': machine.put(SYSTEM+28, GAME_DATA+4)
        elif guard == 'wrong-peer-count': machine.peers = 1
        elif guard == 'busy-field-event': machine.put(SYSTEM+24, CHILD)
        elif guard == 'missing-field': machine.put(SYSTEM+32, 0)
        elif guard == 'missing-setup': machine.put(CONTEXT+0x7D0, 0)
        elif guard == 'allocation-failure': machine.allocate = False
        machine.cpu.mem_write(CONTEXT+0x74C, bytes([0xAA])*0x80)
        before_context = bytes(machine.cpu.mem_read(CONTEXT, 0x7F0))
        before_setup = bytes(machine.cpu.mem_read(SETUP, 0x140))
        assert machine.launch() == 0, guard
        assert bytes(machine.cpu.mem_read(SETUP, 0x140)) == before_setup, guard
        assert not any(call[0] == 'native-setup-flag' for call in machine.calls), guard
        if guard != 'allocation-failure':
            assert bytes(machine.cpu.mem_read(CONTEXT, 0x7F0)) == before_context, guard
        cases += 1

    # Actual captured native dispatcher: the former defeat shortcut returns
    # done without recreating a field, explaining the terminated GameSystem.
    for no_blackout, result, expected_done in ((False, 2, 1), (True, 2, 0), (True, 1, 0)):
        machine = Machine(capture, payload, header)
        assert machine.launch() == EVENT
        machine.calls.clear()
        machine.put(EVENT+8, 8)
        machine.put(SETUP+0xA8, result)
        machine.put(DATA+24, int(no_blackout))
        done = machine.run(machine.entries['PokePlayCoopFieldEvent'], (EVENT, EVENT+8, DATA, 0))
        assert done == expected_done
        resume = [call for call in machine.calls if call[0] == 'create-field-resume']
        if no_blackout:
            assert resume == [('create-field-resume', SYSTEM)]
            assert ('chain-field-resume', (EVENT, CHILD)) in machine.calls
            assert machine.word(CHILD) == EVENT and machine.word(SYSTEM+24) == CHILD
            assert machine.word(EVENT+8) == 9, 'Field return failed to advance'
            assert bytes(machine.cpu.mem_read(CONTEXT+0x7D8, 1)) == b'\0', 'Premature completion'
        else:
            assert not resume, 'Regression no longer represents the original loss shortcut'
            assert machine.word(EVENT+8) == 8
            assert bytes(machine.cpu.mem_read(CONTEXT+0x7D8, 1)) == b'\1'
        cases += 1

    # Practice completion must hold the native parent/radio until the peers
    # agree. PvP deliberately opts out because opposing outcomes differ.
    for barrier,agreed in ((True,False),(True,True),(False,False)):
        machine=Machine(capture,payload,header);assert machine.launch()==EVENT
        machine.cpu.mem_write(CONTEXT+0x7D9,bytes([int(barrier)]))
        machine.cpu.mem_write(CONTEXT+0x7D7,b'\1')
        machine.put(CONTEXT+0x7BC,2 if agreed else 0)
        machine.put(EVENT+8,8);machine.calls.clear()
        result=machine.run(machine.entries['PokePlayCoopFieldEvent'],(EVENT,EVENT+8,DATA,0))
        if barrier and not agreed:
            assert result==0 and machine.word(EVENT+8)==8
            assert machine.word(CONTEXT+0x7B4)==2
            assert bytes(machine.cpu.mem_read(CONTEXT+0x7DA,1))==b'\1'
            assert not machine.calls,'Unagreed completion reached native dispatcher'
        else:
            assert any(call[0]=='create-field-resume' for call in machine.calls)
        cases+=1

    print(f'{cases} co-op field-return cases passed: native HP preflight, flag pair, '
          'guarded launch, old defeat shortcut, and actual defeat/victory field resume.')


if __name__ == '__main__':
    main()
