"""Execute compiled hook shims in Unicorn; game callees are intercepted stubs.

Requires Unicorn, Pillow, ndspy, and the ARM GNU toolchain. No ROM/save needed.
These tests establish register/stack/interworking behavior, not game rendering.
"""

import importlib.util
from pathlib import Path
import unittest
import struct

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_SP,
                               UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR)

spec = importlib.util.spec_from_file_location("dialogue_art_patch", Path(__file__).with_name("dialogue_art_patch.py"))
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)


class DialogueHookCpuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = patcher.ITCM_HELPER_BASE
        cls.code, cls.symbols = patcher.compile_hooks(patcher.HOOK_SOURCE, cls.base)

    def run_actor_hook(self, site):
        cpu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        cpu.mem_map(0x02000000, 0x400000)
        cpu.mem_map(patcher.ITCM_IMAGE_BASE, 0x8000)
        cpu.mem_write(self.base, self.code)
        cpu.mem_write(site, patcher.encode_thumb_bl(site, self.symbols["dialogue_hook_actor_lifecycle"]))
        cpu.mem_write(0x021551A4, bytes.fromhex("70 47"))  # Thumb bx lr
        cpu.mem_write(0x020787A8, bytes.fromhex("1e ff 2f e1"))  # ARM bx lr
        stack = 0x023E0000
        arguments = (0x02010000, 0x02020000, 0x34, 0x12345678)
        for register, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), arguments):
            cpu.reg_write(register, value)
        cpu.reg_write(UC_ARM_REG_R4, 0x12340000)
        cpu.reg_write(UC_ARM_REG_SP, stack)
        calls = []

        def hook(uc, address, size, user):
            if address == site + 4:
                uc.emu_stop()
            elif address in (0x021551A4, 0x020787A8):
                calls.append((address, bool(uc.reg_read(UC_ARM_REG_CPSR) & 32), tuple(
                    uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)
                )))

        cpu.hook_add(UC_HOOK_CODE, hook)
        try:
            cpu.emu_start(site | 1, 0, count=1000)
        except UcError as error:
            pc = cpu.reg_read(UC_ARM_REG_PC)
            self.fail(f"{error}; pc=0x{pc:08X}, bytes={bytes(cpu.mem_read(pc, 8)).hex()}, calls={calls}")
        self.assertEqual(cpu.reg_read(UC_ARM_REG_PC), site + 4)
        self.assertEqual(cpu.reg_read(UC_ARM_REG_SP), stack)
        self.assertEqual(cpu.reg_read(UC_ARM_REG_R4), 0x12340000)
        return calls, arguments

    def test_registration_dispatch_preserves_arguments_and_callee_saved_register(self):
        calls, args = self.run_actor_hook(patcher.ACTOR_CREATE_HOOK_ADDRESS)
        self.assertEqual(calls, [(0x021551A4, True, args)])

    def test_cleanup_calls_arm_memset_with_original_three_arguments(self):
        for site in patcher.ACTOR_CLEANUP_HOOK_ADDRESSES:
            with self.subTest(site=hex(site)):
                calls, args = self.run_actor_hook(site)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][:2], (0x020787A8, False))
                self.assertEqual(calls[0][2][:3], args[:3])

    def test_inline_background_store_preserves_stock_and_transparent_profiles(self):
        for marker, expected in ((0, 15), (3, 0)):
            with self.subTest(marker=marker):
                cpu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
                cpu.mem_map(0x02000000, 0x400000)
                cpu.mem_map(patcher.ITCM_IMAGE_BASE, 0x8000)
                cpu.mem_write(self.base, self.code)
                site = 0x0218B846
                cpu.mem_write(site, patcher.encode_thumb_bl(site, self.symbols["dialogue_hook_text_background"]))
                window, stack = 0x02030000, 0x023E0000
                cpu.mem_write(window + 3, bytes([marker]))
                cpu.reg_write(UC_ARM_REG_R4, window)
                cpu.reg_write(UC_ARM_REG_SP, stack)
                cpu.hook_add(UC_HOOK_CODE, lambda uc, address, size, user: uc.emu_stop() if address == site + 4 else None)
                cpu.emu_start(site | 1, 0, count=100)
                self.assertEqual(struct.unpack("<I", cpu.mem_read(stack + 20, 4))[0], expected)
                self.assertEqual(cpu.reg_read(UC_ARM_REG_SP), stack)
                self.assertEqual(cpu.reg_read(UC_ARM_REG_R4), window)

    def run_binding(self, zone=0xFFFF, fail_bitmap=False, uid=0xFFFF):
        code, symbols = patcher.compile_hooks(patcher.HOOK_SOURCE, self.base, speaker_profiles=[
            {"zone_id": zone, "actor_uid": uid, "ncgr": 14, "nclr": 15}
        ])
        cpu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        cpu.mem_map(0x02000000, 0x400000)
        cpu.mem_map(patcher.ITCM_IMAGE_BASE, 0x8000)
        cpu.mem_map(0x04000000, 0x1000)
        cpu.mem_write(self.base, code)
        win, talk, sys = 0x02030000, 0x02040000, 0x02050000
        custom, art = 0x020A0000, 0x020B0000
        cpu.mem_write(win + 8, struct.pack("<I", talk))
        cpu.mem_write(win + 0x14, struct.pack("<I", sys))
        cpu.mem_write(sys, struct.pack("<H", 3))
        cpu.mem_write(0x02060000, struct.pack("<H", 3))
        cpu.mem_write(0x02070008, struct.pack("<HH", 3, 460))
        cpu.mem_write(talk + 0x24, struct.pack("<I", 0x02090000))
        cpu.mem_write(0x04000050, struct.pack("<H", 0x3F44))
        returns = {0x021551CC: 0x02060000, 0x0215517C: 0x02080000,
                   0x02167A14: 0x02070000, 0x0218B518: 0x02090000,
                   0x02046F3C: 0 if fail_bitmap else 0x020C0000,
                   0x020484F4: 0x020D0000}
        targets = set(returns) | {0x020480C0, 0x0204B0F0, 0x0204713C, 0x02047008,
                                 0x0204826C, 0x02048244, 0x02044F90, 0x02046EDC,
                                 0x02048210, 0x020484B4}
        for target in targets:
            cpu.mem_write(target, bytes.fromhex("70 47"))
        creates, calls = [custom, art], []

        def hook(uc, address, size, user):
            if address == 0x0200F000:
                uc.emu_stop()
            elif address in targets:
                calls.append((address, uc.reg_read(UC_ARM_REG_R0)))
                if address == 0x020480C0:
                    uc.reg_write(UC_ARM_REG_R0, creates.pop(0))
                elif address in returns:
                    uc.reg_write(UC_ARM_REG_R0, returns[address])

        cpu.hook_add(UC_HOOK_CODE, hook)
        cpu.reg_write(UC_ARM_REG_R0, 0x02010000)
        cpu.reg_write(UC_ARM_REG_R1, win)
        cpu.reg_write(UC_ARM_REG_SP, 0x023E0000)
        cpu.reg_write(UC_ARM_REG_LR, 0x0200F001)
        cpu.emu_start(symbols["dialogue_actor_bind"] | 1, 0, count=10000)
        self.assertEqual(cpu.reg_read(UC_ARM_REG_PC), 0x0200F000)
        return cpu, symbols, calls, (win, talk, custom, art)

    def test_profile_binding_replaces_correct_window_and_cleanup_restores_blending(self):
        cpu, symbols, calls, (win, talk, custom, art) = self.run_binding(zone=460, uid=3)
        self.assertEqual(struct.unpack("<I", cpu.mem_read(talk + 0x24, 4))[0], custom)
        self.assertEqual(cpu.mem_read(talk + 0x1A, 2), bytes([1, 3]))
        self.assertEqual(struct.unpack("<I", cpu.mem_read(win + 0x28, 4))[0], art)
        self.assertEqual(struct.unpack("<H", cpu.mem_read(0x04000050, 2))[0], 0x3F40)
        self.assertIn((0x02048210, 0x02090000), calls)
        cpu.reg_write(UC_ARM_REG_R0, win)
        cpu.reg_write(UC_ARM_REG_LR, 0x0200F001)
        cpu.emu_start(symbols["dialogue_actor_cleanup"] | 1, 0, count=10000)
        self.assertEqual(struct.unpack("<I", cpu.mem_read(win + 0x28, 4))[0], 0)
        self.assertEqual(struct.unpack("<H", cpu.mem_read(0x04000050, 2))[0], 0x3F44)
        self.assertIn((0x02048210, art), calls)

    def test_unmatched_profile_and_failed_bitmap_preserve_original_text_window(self):
        for zone, uid, fail_bitmap in ((459, 3, False), (460, 4, False), (0xFFFF, 0xFFFF, True)):
            with self.subTest(zone=zone, uid=uid, fail_bitmap=fail_bitmap):
                cpu, _, calls, (win, talk, custom, art) = self.run_binding(zone, fail_bitmap, uid)
                self.assertEqual(struct.unpack("<I", cpu.mem_read(talk + 0x24, 4))[0], 0x02090000)
                self.assertEqual(struct.unpack("<I", cpu.mem_read(win + 0x28, 4))[0], 0)
                self.assertEqual(struct.unpack("<H", cpu.mem_read(0x04000050, 2))[0], 0x3F44)
                self.assertNotIn((0x02048210, 0x02090000), calls)
                if fail_bitmap:
                    self.assertIn((0x02048210, custom), calls)
                    self.assertIn((0x02048210, art), calls)


if __name__ == "__main__":
    unittest.main()
