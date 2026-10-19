#!/usr/bin/env python3
# Unova Together contributions: Copyright (C) 2026 mvq1303.
# GitHub: WhatWasMissing - https://github.com/WhatWasMissing/Unova-Together
# GPL-3.0-or-later. Preserve all upstream notices.
"""Build the ROM-specific delta for the heap-backed BW2 shop overlay.

Only the shop UI routine span is copied, keeping the original overlay size and
RAM allocation. Replacing the full overlay also replaces the main field engine
with a separately rebuilt binary and can stall when continuing a save.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import zlib
from pathlib import Path


RAM_BASE = 0x0217F600
OVERLAY_ID = 36
EXPECTED_GAME_CODE = b"IREO"
SHOP_UI_START = 0x021ABB70  # s0149_CallFriendlyShopBuy
SHOP_UI_END = 0x021ADC6A    # end of GetMoveTutorShopSortimentBits
SHOP_UI_START_SYMBOL = ("s0149_CallFriendlyShopBuy", 0x021ABB70, 0x150)
SHOP_UI_END_SYMBOL = ("GetMoveTutorShopSortimentBits", 0x021ADC1C, 0x4E)

# (symbol, object, baseline VA, rebuilt VA, changed bytes within symbol)
# These are the Redux 1.4.1 deltas found when comparing its overlay 36 with the
# clean decomp build. The linker maps are checked before any delta is applied.
REDUX_SYMBOL_DELTAS = (
    ("hollowSet", "fieldmap_event.o", 0x021824E0, 0x021824E0, ((0x26, 2), (0x4A, 2))),
    ("UpdatePhenomenon", "effect_encount.o", 0x021A206C, 0x021A206C, ((0xBE, 2), (0xD9, 1))),
    ("EffectEncount_GenDustCloudItem", "effect_encount.o", 0x021A28E4, 0x021A28E4,
     ((0x62, 1), (0x64, 1), (0x84, 2))),
    ("EventBattleCall_DecideEnvTrainer", "enceff.o", 0x021C618C, 0x021C62D0,
     ((0x14, 8), (0x1E, 16), (0x80, 2), (0x88, 3))),
    ("generateHollow", "scrcmd_hidden_hollow.o", 0x021C8C34, 0x021C8D78,
     ((0x2C, 1), (0x32, 1), (0x34, 2))),
    ("DUST_CLOUD_ITEMS_NORMAL", "effect_encount.o", 0x021D02DC, 0x021D0420,
     ((0x12, 1),),),
)

MAP_ROW = re.compile(
    r"^\s*([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})\s+\.\w+\s+"
    r"(\S+)\s+\(([^()]*)\)\s*$"
)


def map_symbol(path: Path, name: str, obj: str, expected: int) -> None:
    for line in path.read_text(errors="replace").splitlines():
        match = MAP_ROW.match(line)
        if match and match.group(3) == name and match.group(4) == obj:
            if int(match.group(1), 16) == expected:
                return
    raise ValueError(f"{path.name} does not map {name} ({obj}) at {expected:#010x}")


def map_symbol_range(path: Path, name: str, expected_start: int, expected_size: int) -> None:
    matches = []
    for line in path.read_text(errors="replace").splitlines():
        match = MAP_ROW.match(line)
        if match and match.group(3) == name:
            start, end = int(match.group(1), 16), int(match.group(2), 16)
            matches.append((start, end - start))
    if matches != [(expected_start, expected_size)]:
        raise ValueError(
            f"{path.name} must map {name} at {expected_start:#010x} "
            f"with size {expected_size:#x}; found {matches}"
        )


def filter_shop_ui_overlay(source: bytes, rebuilt: bytes) -> bytes:
    """Keep only the shop UI section inside the original overlay allocation."""
    start = SHOP_UI_START - RAM_BASE
    end = SHOP_UI_END - RAM_BASE
    if len(source) != Gen5ShopOverlayPatchSourceSize:
        raise ValueError("Redux overlay 36 has an unexpected source size")
    if len(rebuilt) < len(source) or end > len(source) or start >= end:
        raise ValueError("Rebuilt overlay 36 does not contain the expected shop UI range")

    filtered = bytearray(source)
    filtered[start:end] = rebuilt[start:end]
    return bytes(filtered)


def get_runs(source: bytes, target: bytes) -> list[tuple[int, bytes]]:
    runs: list[tuple[int, bytes]] = []
    at = 0
    common = min(len(source), len(target))
    while at < common:
        if source[at] == target[at]:
            at += 1
            continue
        start = at
        while at < common and source[at] != target[at]:
            at += 1
        runs.append((start, target[start:at]))
    if len(target) > common:
        runs.append((common, target[common:]))
    return runs


def render_header(output: Path, source_crc: int, target_crc: int,
                  source_size: int, target_size: int,
                  encoded: bytes, run_count: int) -> None:
    values = ",\n".join(
        "    " + ", ".join(f"0x{byte:02X}" for byte in encoded[i:i + 16])
        for i in range(0, len(encoded), 16)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "/*\n"
        " * Unova Together contributions: Copyright (C) 2026 mvq1303.\n"
        " * GitHub: WhatWasMissing - https://github.com/WhatWasMissing/Unova-Together\n"
        " * GPL-3.0-or-later.\n"
        " * Generated from the matching Redux overlay and heap-backed shop build.\n"
        " * Only the shop UI routine span is copied; overlay size is preserved.\n"
        " */\n"
        "#pragma once\n#include <array>\n#include <cstdint>\n"
        "namespace Gen5ShopOverlayPatch {\n"
        f"inline constexpr uint32_t SourceOverlayCrc32 = 0x{source_crc:08X};\n"
        f"inline constexpr uint32_t TargetOverlayCrc32 = 0x{target_crc:08X};\n"
        f"inline constexpr uint32_t SourceOverlaySize = {source_size};\n"
        f"inline constexpr uint32_t TargetOverlaySize = {target_size};\n"
        f"inline constexpr uint32_t DeltaRunCount = {run_count};\n"
        f"inline constexpr std::array<uint8_t, {len(encoded)}> EncodedDelta{{{{\n"
        f"{values}\n}}}};\n"
        "}\n",
        encoding="ascii",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path, help="Redux v1.4.1 source ROM")
    parser.add_argument("--baseline", required=True, type=Path, help="clean decomp overlay 36")
    parser.add_argument("--rebuilt", required=True, type=Path, help="heap-backed overlay 36")
    parser.add_argument("--baseline-map", required=True, type=Path)
    parser.add_argument("--rebuilt-map", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parents[1] / "src" / "Gen5ShopOverlayPatch.h")
    args = parser.parse_args()

    try:
        import ndspy.rom  # type: ignore[import-not-found]

        rom = ndspy.rom.NintendoDSRom.fromFile(args.rom)
        if args.rom.read_bytes()[0x0C:0x10] != EXPECTED_GAME_CODE:
            raise ValueError("Expected a Black 2 ROM with game code IREO")
        overlay = rom.loadArm9Overlays({OVERLAY_ID})[OVERLAY_ID]
        source = bytes(overlay.data)
        baseline = args.baseline.read_bytes()
        target = bytearray(args.rebuilt.read_bytes())
        if len(source) != len(baseline) or len(source) != Gen5ShopOverlayPatchSourceSize:
            raise ValueError("Redux overlay 36 does not match the expected decomp baseline size")

        covered = bytearray(len(source))
        for name, obj, old_va, new_va, deltas in REDUX_SYMBOL_DELTAS:
            map_symbol(args.baseline_map, name, obj, old_va)
            map_symbol(args.rebuilt_map, name, obj, new_va)
            old_start = old_va - RAM_BASE
            new_start = new_va - RAM_BASE
            for relative, length in deltas:
                src = old_start + relative
                dst = new_start + relative
                if src + length > len(source) or dst + length > len(target):
                    raise ValueError(f"Redux delta {name} falls outside the overlay")
                if source[src:src + length] == baseline[src:src + length]:
                    raise ValueError(f"Expected Redux delta in {name} at {src:#x} was absent")
                target[dst:dst + length] = source[src:src + length]
                covered[src:src + length] = b"\x01" * length

        for offset, (left, right) in enumerate(zip(source, baseline)):
            if left != right and not covered[offset]:
                raise ValueError(f"Unmapped Redux-only overlay difference at {offset:#x}")

        for path in (args.baseline_map, args.rebuilt_map):
            map_symbol_range(path, *SHOP_UI_START_SYMBOL)
            map_symbol_range(path, *SHOP_UI_END_SYMBOL)

        target = bytearray(filter_shop_ui_overlay(source, bytes(target)))
        runs = get_runs(source, bytes(target))
        encoded = bytearray()
        previous_end = 0
        for offset, payload in runs:
            if offset > 0xFFFFFF or len(payload) > 0xFFFF:
                raise ValueError("Overlay delta record exceeds its compact encoding")
            encoded.extend(offset.to_bytes(3, "little"))
            encoded.extend(len(payload).to_bytes(2, "little"))
            encoded.extend(payload)
            previous_end = offset + len(payload)
        if previous_end > len(target):
            raise AssertionError("Delta generation escaped target overlay")

        render_header(args.output, zlib.crc32(source) & 0xFFFFFFFF,
                      zlib.crc32(target) & 0xFFFFFFFF, len(source), len(target),
                      bytes(encoded), len(runs))
        print(f"Wrote {args.output}: {len(runs)} changed runs, "
              f"{sum(len(data) for _, data in runs)} changed bytes, "
              f"{len(encoded)} encoded bytes")
        print(f"Overlay CRC32: {zlib.crc32(source) & 0xFFFFFFFF:08x} -> "
              f"{zlib.crc32(target) & 0xFFFFFFFF:08x}")
        return 0
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


# Kept explicit so the build script cannot silently map a different base ROM.
Gen5ShopOverlayPatchSourceSize = 352672

if __name__ == "__main__":
    raise SystemExit(main())
