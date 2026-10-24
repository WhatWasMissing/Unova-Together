#!/usr/bin/env python3
"""Build a private, exact-ROM dialogue-art test copy. Never patches the input ROM."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

from PIL import Image
import ndspy.narc
import ndspy.rom


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ART = ROOT / "maintenance-tools" / "assets" / "dialogue-art" / "field-guide-source.png"
HOOK_SOURCE = Path(__file__).with_name("dialogue_art_overlay_hook.c")
TARGET_ROM_SHA256 = "353fb0cf82c3e4eddfc8986efa8910b00eb1c4d6f106c220abef59d69d3a520a"
TARGET_GAME_CODE = "IREO"
OVERLAY_ID = 36
OVERLAY_CRC32 = 0xA7CF9125
FIELD_HEAP_CREATE_SITE = (0x0217F650, 0x0203A178, bytes.fromhex("ba f6 92 fd"))
FIELD_HEAP_SIZE_SETUP = (0x0217F64A, bytes.fromhex("21 48 39 04 89 22"))
FIELD_HEAP_ORIGINAL_SIZE = 0x10000
OVERLAY36_BSS_SIZE = 0x10040
OVERLAY36_CODE_CAVE = (0x021D5788, 24)  # Three 8-byte long-branch stubs.
ITCM_IMAGE_BASE = 0x01FF8000
ITCM_ORIGINAL_SIZE = 0x13A0
ITCM_HELPER_BASE = ITCM_IMAGE_BASE + ITCM_ORIGINAL_SIZE
ITCM_HELPER_MAX_SIZE = 0x2000
ARM9_RAM_BASE = 0x02004000
ARM9_MODULE_PARAMS_OFFSET = 0xFB0
ARM9_AUTOLOAD_SOURCE_OFFSET = 0x99740
ARM9_AUTOLOAD_TABLE_OFFSET = 0x9ABC0
ARM9_AUTOLOAD_TABLE_END = 0x9AC00
ARM9_ITCM_INSERT_OFFSET = ARM9_AUTOLOAD_SOURCE_OFFSET + ITCM_ORIGINAL_SIZE
ARM9_ITCM_ARENA_LITERAL_OFFSET = 0x77400
ARM9_AUTOLOAD_ENTRIES = (
    (ITCM_IMAGE_BASE, ITCM_ORIGINAL_SIZE, ITCM_IMAGE_BASE, 0),
    (0x02FE0000, 0xA0, 0x02FE0000, 0x20),
    (0x02400000, 0x20, 0x02400000, 0),
    (0x06898000, 0x20, 0x06898000, 0),
)
ROM_ARM9_FILE_OFFSET = 0x4000
ROM_ARM9_EXPECTED_SIZE = 0x9AC0C
ROM_ARM9_POSTDATA_EXPECTED = bytes.fromhex("21 06 c0 de d8 0a 00 00 00 00 00 00")
HOOK_ENTRY_NAMES = ("dialogue_hook_lifecycle", "dialogue_hook_fill_frame", "dialogue_hook_actor_lifecycle")
ACTOR_CREATE_HOOK_ADDRESS = 0x021A8D0E
ACTOR_CLEANUP_HOOK_ADDRESSES = frozenset((0x0218880A, 0x0218883C))
ACTOR_HOOK_MODES = {"full", "create-only", "cleanup-only", "disabled"}
FIELD_HOOK_ADDRESSES = frozenset((0x021884F2, 0x0218A070, 0x0218A082, 0x02188532))


def _active_branch_hooks(actor_hook_mode: str, enable_field_art: bool = False) -> dict[int, tuple[str, int, bytes]]:
    if actor_hook_mode not in ACTOR_HOOK_MODES:
        raise PatchError(f"unsupported actor hook mode: {actor_hook_mode}")
    active = {}
    for address, hook in BRANCH_HOOKS.items():
        if address in FIELD_HOOK_ADDRESSES and not enable_field_art:
            continue
        if address == ACTOR_CREATE_HOOK_ADDRESS and actor_hook_mode in {"full", "create-only"}:
            active[address] = hook
        elif address in ACTOR_CLEANUP_HOOK_ADDRESSES and actor_hook_mode in {"full", "cleanup-only"}:
            active[address] = hook
        elif address not in ACTOR_CLEANUP_HOOK_ADDRESSES and address != ACTOR_CREATE_HOOK_ADDRESS:
            active[address] = hook
    return active
WINFRAME_NARC = "a/0/0/5"
WINFRAME_MEMBER_COUNT = 12
ART_NCGR_ID = 12
ART_NCLR_ID = 13
SPEAKER_ART_NCGR_BASE = 14
SPEAKER_ART_NCLR_BASE = 15
MAX_SPEAKER_PROFILES = 64
ART_WIDTH = 256
ART_HEIGHT = 160
ART_BG_Y_TILES = 4
ART_BG_PALETTE = 15
ART_ASSET_DIR = ROOT / "maintenance-tools" / "assets" / "dialogue-art"
NAMEPLATE_LEFT = 12
NAMEPLATE_TOP = 94
NAMEPLATE_WIDTH = 70


class PatchError(RuntimeError):
    """Raised when the selected ROM or patch environment does not match the review."""


# The target addresses and expected callers are specific to the guarded IREO image.
BRANCH_HOOKS = {
    0x021884F2: ("dialogue_hook_lifecycle", 0x0218A57C, bytes.fromhex("02 f0 43 f8")),
    0x0218A070: ("dialogue_hook_fill_frame", 0x0204713C, bytes.fromhex("bd f6 64 f8")),
    0x0218A082: ("dialogue_hook_fill_frame", 0x02189F2C, bytes.fromhex("ff f7 53 ff")),
    0x02188532: ("dialogue_hook_lifecycle", 0x0203A24C, bytes.fromhex("b1 f6 8b fe")),
    # Register a newly created actor message window after its stock constructor
    # completes, so the hook never wraps or changes constructor arguments.
    0x021A8D0E: ("dialogue_hook_actor_lifecycle", 0x021551A4, bytes.fromhex("ac f7 49 fa")),
    0x0218880A: ("dialogue_hook_actor_lifecycle", 0x020787A8, bytes.fromhex("ef f6 ce ef")),
    0x0218883C: ("dialogue_hook_actor_lifecycle", 0x020787A8, bytes.fromhex("ef f6 b4 ef")),
    0x0218885C: ("dialogue_hook_actor_fill", 0x0204713C, bytes.fromhex("be f6 6e fc")),
    0x02188900: ("dialogue_hook_actor_cursor_clear", 0x02189D24, bytes.fromhex("01 f0 10 fa")),
    0x02188992: ("dialogue_hook_actor_cursor_clear", 0x02189D24, bytes.fromhex("01 f0 c7 f9")),
    0x02188952: ("dialogue_hook_actor_cursor_draw", 0x02189DE8, bytes.fromhex("01 f0 49 fa")),
    0x021889F2: ("dialogue_hook_actor_cursor_draw", 0x02189DE8, bytes.fromhex("01 f0 f9 f9")),
}
INLINE_HOOKS = {0x0218B846: ("dialogue_hook_text_background", bytes.fromhex("0f 20 05 90"))}
FIELD_WIN_SIZE_PATCH = (0x021884B0, bytes.fromhex("20 21"), bytes.fromhex("24 21"))
# These exact literal-pool references are the complete set of overlay-36 words that point into its BSS.
OVERLAY36_BSS_POINTERS = {
    0x000D0: 0x021D57A0,
    0x01400: 0x021E57A0,
    0x01408: 0x021E57A0,
    0x1AA8C: 0x021E57B0,
    0x1AA90: 0x021E57B0,
    0x2ADB0: 0x021E57BC,
    0x2AE80: 0x021E57BC,
    0x2C504: 0x021E57C0,
    0x2C544: 0x021E57C0,
    0x2E8D4: 0x021D6F6C,
    0x40310: 0x021DD940,
    0x4B65C: 0x021E0001,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _round_ds_color(channel: int) -> int:
    return round(channel * 31 / 255)


_NAME_FONT_3X5 = {
    "A": ("010", "101", "111", "101", "101"), "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"), "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"), "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"), "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"), "J": ("001", "001", "001", "101", "010"),
    "K": ("101", "101", "110", "101", "101"), "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "101", "101", "101"), "N": ("101", "111", "111", "111", "101"),
    "O": ("010", "101", "101", "101", "010"), "P": ("110", "101", "110", "100", "100"),
    "Q": ("010", "101", "101", "111", "011"), "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"), "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"), "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "101", "111", "101"), "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"), "Z": ("111", "001", "010", "100", "111"),
    "-": ("000", "000", "111", "000", "000"), " ": ("000", "000", "000", "000", "000"),
}


def draw_nameplate(indexed: bytearray, palette: list[tuple[int, int, int]], name: str) -> None:
    """Render a short profile name into the artwork's blank pixel nameplate."""
    normalized = name.upper()
    if not 1 <= len(normalized) <= 8 or any(char not in _NAME_FONT_3X5 for char in normalized):
        raise PatchError("speaker names must be 1-8 letters, spaces, or hyphens")
    scale = 2
    glyph_width = 3 * scale
    glyph_height = 5 * scale
    gap = scale
    text_width = len(normalized) * glyph_width + (len(normalized) - 1) * gap
    if text_width > NAMEPLATE_WIDTH or NAMEPLATE_TOP + glyph_height > ART_HEIGHT:
        raise PatchError("speaker name does not fit the reviewed art nameplate")

    text_x = NAMEPLATE_LEFT + (NAMEPLATE_WIDTH - text_width) // 2
    color_index = min(
        range(1, len(palette)),
        key=lambda index: sum((palette[index][channel] - target) ** 2
                              for channel, target in enumerate((247, 232, 207))),
    )
    for char_index, char in enumerate(normalized):
        glyph_x = text_x + char_index * (glyph_width + gap)
        for row, pattern in enumerate(_NAME_FONT_3X5[char]):
            for column, pixel in enumerate(pattern):
                if pixel != "1":
                    continue
                for dy in range(scale):
                    for dx in range(scale):
                        x = glyph_x + column * scale + dx
                        y = NAMEPLATE_TOP + row * scale + dy
                        indexed[y * ART_WIDTH + x] = color_index


def prepare_indexed_art(path: Path, name: str | None = None) -> tuple[bytes, list[tuple[int, int, int]]]:
    """Downsample the authored RGBA art and reserve palette index zero for transparency."""
    with Image.open(path) as source:
        source.load()
        rgba = source.convert("RGBA").resize((ART_WIDTH, ART_HEIGHT), Image.Resampling.NEAREST)

    pixels_rgba = list(rgba.getdata())
    opaque_positions = [index for index, pixel in enumerate(pixels_rgba) if pixel[3] >= 128]
    if not opaque_positions:
        raise PatchError("dialogue artwork has no opaque pixels")

    opaque = Image.new("RGB", (len(opaque_positions), 1))
    opaque.putdata([pixels_rgba[index][:3] for index in opaque_positions])
    reduced = opaque.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    reduced_indices = reduced.tobytes()
    reduced_palette = reduced.getpalette() or []

    palette: list[tuple[int, int, int]] = [(0, 0, 0)]
    for color_index in range(15):
        offset = color_index * 3
        color = tuple(reduced_palette[offset:offset + 3])
        palette.append(color if len(color) == 3 else (0, 0, 0))

    indexed = bytearray(ART_WIDTH * ART_HEIGHT)
    for position, color_index in zip(opaque_positions, reduced_indices, strict=True):
        indexed[position] = color_index + 1
    if name is not None:
        draw_nameplate(indexed, palette, name)
    return bytes(indexed), palette


def build_ncgr(indexed: bytes, width: int, height: int) -> bytes:
    """Build a sized, tiled 4bpp NCGR resource (RGCN/RAHC/SOPC)."""
    if width % 8 or height % 8 or len(indexed) != width * height:
        raise PatchError("NCGR pixels must be a complete 8x8-tile image")
    if max(indexed, default=0) > 15:
        raise PatchError("4bpp NCGR has a color index above 15")

    nibbles = bytearray()
    for tile_y in range(0, height, 8):
        for tile_x in range(0, width, 8):
            for row in range(8):
                start = (tile_y + row) * width + tile_x
                nibbles.extend(indexed[start:start + 8])
    characters = bytes(nibbles[index] | (nibbles[index + 1] << 4)
                       for index in range(0, len(nibbles), 2))

    width_tiles, height_tiles = width // 8, height // 8
    character_section = struct.pack(
        "<4sIHHIIIII", b"RAHC", 0x20 + len(characters), height_tiles, width_tiles,
        3, 0, 0, len(characters), 0x18,
    ) + characters
    size_section = struct.pack("<4sIHHHH", b"SOPC", 0x10, 0, 0, width_tiles, height_tiles)
    sections = character_section + size_section
    return struct.pack("<4sHHIHH", b"RGCN", 0xFEFF, 0x0101, 0x10 + len(sections), 0x10, 2) + sections


def build_nclr(palette: list[tuple[int, int, int]]) -> bytes:
    """Build one 16-color BG NCLR resource (RLCN/TTLP)."""
    if len(palette) != 16:
        raise PatchError("the dialogue palette must contain exactly 16 colors")
    words = []
    for red, green, blue in palette:
        value = _round_ds_color(red) | (_round_ds_color(green) << 5) | (_round_ds_color(blue) << 10)
        words.append(struct.pack("<H", value))
    color_data = b"".join(words)
    palette_section = struct.pack("<4sIIIII", b"TTLP", 0x18 + len(color_data), 0, 0, len(color_data), 0x10) + color_data
    return struct.pack("<4sHHIHH", b"RLCN", 0xFEFF, 0x0100, 0x10 + len(palette_section), 0x10, 1) + palette_section


def decode_ncgr(raw: bytes) -> tuple[int, int, bytes]:
    """Strictly validate and decode the sized 4bpp NCGR format emitted above."""
    if len(raw) < 0x30 or raw[:4] != b"RGCN" or raw[16:20] != b"RAHC":
        raise PatchError("custom NCGR has an invalid RGCN/RAHC header")
    file_size = struct.unpack_from("<I", raw, 8)[0]
    section_size = struct.unpack_from("<I", raw, 20)[0]
    height_tiles, width_tiles, depth, _, _, data_size, data_offset = struct.unpack_from("<HHIIIII", raw, 24)
    if file_size != len(raw) or section_size + 16 > len(raw) or depth != 3 or data_offset != 0x18:
        raise PatchError("custom NCGR has inconsistent size or 4bpp metadata")
    width, height = width_tiles * 8, height_tiles * 8
    if width <= 0 or height <= 0 or data_size != width * height // 2:
        raise PatchError("custom NCGR dimensions do not match its character data")
    char_end = 24 + data_offset + data_size
    if raw[char_end:char_end + 4] != b"SOPC":
        raise PatchError("custom NCGR is missing its size section")
    out = bytearray(width * height)
    packed = raw[24 + data_offset:char_end]
    offset = 0
    for tile_y in range(0, height, 8):
        for tile_x in range(0, width, 8):
            for row in range(8):
                for column in range(0, 8, 2):
                    byte = packed[offset]
                    offset += 1
                    x = tile_x + column
                    y = tile_y + row
                    out[y * width + x] = byte & 15
                    out[y * width + x + 1] = byte >> 4
    return width, height, bytes(out)


def validate_nclr(raw: bytes) -> None:
    if len(raw) != 0x48 or raw[:4] != b"RLCN" or raw[16:20] != b"TTLP":
        raise PatchError("custom NCLR has an invalid RLCN/TTLP header")
    if struct.unpack_from("<I", raw, 8)[0] != len(raw) or struct.unpack_from("<I", raw, 32)[0] != 0x20:
        raise PatchError("custom NCLR must contain one 16-color palette")


def append_winframe_members(raw_narc: bytes, ncgr: bytes, nclr: bytes,
                            speaker_resources: list[tuple[bytes, bytes]] | None = None) -> bytes:
    archive = ndspy.narc.NARC(raw_narc)
    original = [bytes(member) for member in archive.files]
    if len(original) != WINFRAME_MEMBER_COUNT:
        raise PatchError(f"WinFrame NARC has {len(original)} members; expected {WINFRAME_MEMBER_COUNT}")
    if [member[:4] for member in original] != [b"RLCN"] * 5 + [b"RGCN"] * 7:
        raise PatchError("WinFrame NARC members do not match the reviewed five-palette/seven-character layout")
    additions = [ncgr, nclr]
    for profile_ncgr, profile_nclr in speaker_resources or []:
        additions.extend([profile_ncgr, profile_nclr])
    additions.append(build_nclr([(0, 0, 0), (247, 232, 207), (53, 31, 49)]
                                + [(247, 232, 207)] * 12 + [(43, 24, 42)]))
    archive.files.extend(additions)
    output = archive.save()
    verified = ndspy.narc.NARC(output)
    if len(verified.files) != WINFRAME_MEMBER_COUNT + len(additions):
        raise PatchError("the rebuilt WinFrame NARC does not contain every appended resource")
    if [bytes(member) for member in verified.files[:WINFRAME_MEMBER_COUNT]] != original:
        raise PatchError("rebuilding the WinFrame NARC changed an existing resource")
    for resource_id, resource in enumerate(additions, start=WINFRAME_MEMBER_COUNT):
        if bytes(verified.files[resource_id]) != resource:
            raise PatchError("a new WinFrame resource index does not match its renderer profile")
    return output


def load_speaker_profiles(path: Path, allow_wildcards: bool = False) -> list[dict]:
    """Validate speaker-to-art bindings without accepting assets outside the reviewed asset directory."""
    path = path.resolve(strict=True)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PatchError(f"could not read speaker profile manifest: {error}") from error
    if not isinstance(manifest, dict) or set(manifest) != {"profiles"} or not isinstance(manifest["profiles"], list):
        raise PatchError("speaker profile manifest must contain only a profiles array")
    if len(manifest["profiles"]) > MAX_SPEAKER_PROFILES:
        raise PatchError(f"speaker profile count exceeds the {MAX_SPEAKER_PROFILES}-profile limit")

    asset_root = ART_ASSET_DIR.resolve(strict=True)
    profiles = []
    identities = set()
    for index, raw in enumerate(manifest["profiles"]):
        if not isinstance(raw, dict) or set(raw) != {"name", "zone_id", "actor_uid", "art"}:
            raise PatchError(f"speaker profile {index} must contain name, zone_id, actor_uid, and art")
        name = raw["name"]
        zone_id = raw["zone_id"]
        actor_uid = raw["actor_uid"]
        art_value = raw["art"]
        if not isinstance(name, str) or not isinstance(art_value, str):
            raise PatchError(f"speaker profile {index} name and art must be strings")
        if any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFFFF
               for value in (zone_id, actor_uid)):
            raise PatchError(f"speaker profile {index} IDs must be 16-bit integers")
        if (zone_id == 0xFFFF or actor_uid == 0xFFFF) and not allow_wildcards:
            raise PatchError("wildcard speaker IDs are test-only; enable them explicitly for an isolated demo build")
        identity = (zone_id, actor_uid)
        if identity in identities:
            raise PatchError(f"speaker profile {index} duplicates an earlier zone/actor identity")
        identities.add(identity)
        art = (path.parent / art_value).resolve(strict=True)
        if not art.is_file() or not art.is_relative_to(asset_root):
            raise PatchError(f"speaker profile {index} art must be inside {asset_root}")
        profiles.append({
            "name": name,
            "zone_id": zone_id,
            "actor_uid": actor_uid,
            "art_path": art,
            "ncgr": SPEAKER_ART_NCGR_BASE + index * 2,
            "nclr": SPEAKER_ART_NCLR_BASE + index * 2,
        })
    return profiles


def decode_thumb_bl(source_address: int, encoded: bytes) -> int:
    if len(encoded) != 4:
        raise PatchError("Thumb BL instruction must be four bytes")
    first, second = struct.unpack("<HH", encoded)
    if first & 0xF800 != 0xF000 or second & 0xD000 != 0xD000:
        raise PatchError(f"0x{source_address:08X} is not a Thumb BL instruction")
    sign = (first >> 10) & 1
    imm10 = first & 0x03FF
    j1 = (second >> 13) & 1
    j2 = (second >> 11) & 1
    imm11 = second & 0x07FF
    i1 = 1 ^ (j1 ^ sign)
    i2 = 1 ^ (j2 ^ sign)
    immediate = (sign << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if immediate & (1 << 24):
        immediate -= 1 << 25
    return source_address + 4 + immediate


def decode_thumb_call(source_address: int, encoded: bytes) -> int:
    """Decode an immediate Thumb BL or BLX call from the reviewed overlay."""
    if len(encoded) != 4:
        raise PatchError("Thumb call instruction must be four bytes")
    first, second = struct.unpack("<HH", encoded)
    if first & 0xF800 != 0xF000:
        raise PatchError(f"0x{source_address:08X} is not a Thumb BL/BLX instruction")
    if second & 0xD000 == 0xD000:
        return decode_thumb_bl(source_address, encoded)
    if second & 0xD001 != 0xC000:
        raise PatchError(f"0x{source_address:08X} is not an immediate Thumb BLX instruction")

    sign = (first >> 10) & 1
    imm10 = first & 0x03FF
    j1 = (second >> 13) & 1
    j2 = (second >> 11) & 1
    imm10_low = (second >> 1) & 0x03FF
    i1 = 1 ^ (j1 ^ sign)
    i2 = 1 ^ (j2 ^ sign)
    immediate = (sign << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm10_low << 2)
    if immediate & (1 << 24):
        immediate -= 1 << 25
    aligned_pc = (source_address + 4) & ~3
    return aligned_pc + immediate


def decode_thumb_call_target(source_address: int, encoded: bytes) -> int:
    """Use the exact call decoder shared by the patch gate and source tests."""
    return decode_thumb_call(source_address, encoded)


def encode_thumb_bl(source_address: int, target_address: int) -> bytes:
    target_address &= ~1
    displacement = target_address - (source_address + 4)
    if displacement & 1 or not -(1 << 22) <= displacement < (1 << 22):
        raise PatchError("Thumb BL target is unaligned or outside ARM946 Thumb-1 branch range")
    immediate = displacement & 0x01FFFFFF
    sign = (immediate >> 24) & 1
    i1 = (immediate >> 23) & 1
    i2 = (immediate >> 22) & 1
    j1 = 1 ^ (i1 ^ sign)
    j2 = 1 ^ (i2 ^ sign)
    first = 0xF000 | (sign << 10) | ((immediate >> 12) & 0x03FF)
    second = 0xD000 | (j1 << 13) | (j2 << 11) | ((immediate >> 1) & 0x07FF)
    return struct.pack("<HH", first, second)


def _resolve_tool(explicit: str | None, exe_name: str) -> Path:
    candidates = [Path(explicit)] if explicit else []
    located = shutil.which(exe_name)
    if located:
        candidates.append(Path(located))
    candidates.append(Path(r"C:\SysGCC\arm-eabi\bin") / exe_name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise PatchError(f"required ARM toolchain executable is unavailable: {exe_name}")


def compile_hooks(source: Path, base_address: int, gcc_path: str | None = None,
                  objcopy_path: str | None = None, nm_path: str | None = None,
                  speaker_profiles: list[dict] | None = None) -> tuple[bytes, dict[str, int]]:
    gcc = _resolve_tool(gcc_path, "arm-none-eabi-gcc.exe")
    objcopy = _resolve_tool(objcopy_path, "arm-none-eabi-objcopy.exe")
    nm = _resolve_tool(nm_path, "arm-none-eabi-nm.exe")
    if not source.is_file():
        raise PatchError(f"renderer hook source is missing: {source}")

    with tempfile.TemporaryDirectory(prefix="unova-dialogue-art-build-") as temp_name:
        temp = Path(temp_name)
        linker_script = temp / "dialogue_art.ld"
        profile_include = temp / "dialogue_speaker_profiles.inc"
        elf = temp / "dialogue_art.elf"
        raw = temp / "dialogue_art.bin"
        profiles = speaker_profiles or []
        profile_lines = [f"#define DIALOGUE_SPEAKER_PROFILE_COUNT {len(profiles)}"]
        profile_lines.append(f"#define DIALOGUE_TEXT_NCLR {14 + len(profiles) * 2}")
        profile_lines.append(
            "static const DialogueSpeakerProfile dialogue_speaker_profiles[%d] = {" % max(1, len(profiles))
        )
        if profiles:
            for profile in profiles:
                profile_lines.append(
                    "    { 0x%04x, 0x%04x, %d, %d }," % (
                        profile["zone_id"], profile["actor_uid"], profile["ncgr"], profile["nclr"]
                    )
                )
        else:
            profile_lines.append("    { 0xffff, 0xffff, 0, 0 },")
        profile_lines.append("};")
        profile_include.write_text("\n".join(profile_lines) + "\n", encoding="ascii")
        linker_script.write_text(
            "ENTRY(dialogue_hook_lifecycle)\n"
            "SECTIONS {\n"
            f"  . = 0x{base_address:08X};\n"
            "  .text : ALIGN(4) { KEEP(*(.text.dialogue_hook_alpha)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) *(.ARM.attributes*) }\n"
            "}\n",
            encoding="ascii",
        )
        build = subprocess.run(
            [str(gcc), "-std=c11", "-mcpu=arm946e-s", "-mthumb", "-Os", "-ffreestanding", "-fno-builtin",
             "-fno-common", "-fno-stack-protector", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
             "-nostdlib", "-I", str(temp), f"-Wl,-T,{linker_script}", "-Wl,--build-id=none", "-Wl,--no-undefined",
             "-o", str(elf), str(source)],
            capture_output=True, text=True, check=False,
        )
        if build.returncode:
            raise PatchError("ARM hook compilation failed: " + (build.stderr or build.stdout).strip())
        symbol_result = subprocess.run([str(nm), "-n", "--defined-only", str(elf)],
                                        capture_output=True, text=True, check=False)
        if symbol_result.returncode:
            raise PatchError("could not read ARM hook symbols: " + symbol_result.stderr.strip())
        symbols: dict[str, int] = {}
        for line in symbol_result.stdout.splitlines():
            match = re.fullmatch(r"([0-9a-fA-F]+)\s+\w\s+(\S+)", line.strip())
            if match:
                symbols[match.group(2)] = int(match.group(1), 16)
        required = {name for name, _, _ in BRANCH_HOOKS.values()} | {name for name, _ in INLINE_HOOKS.values()} | {
            "dialogue_attach_art", "dialogue_actor_bind", "dialogue_actor_cleanup"
        }
        missing = required - symbols.keys()
        if missing:
            raise PatchError("ARM hook build is missing symbols: " + ", ".join(sorted(missing)))
        undefined = subprocess.run([str(nm), "-u", str(elf)], capture_output=True, text=True, check=False)
        if undefined.returncode or undefined.stdout.strip():
            raise PatchError("ARM hook build has unresolved symbols: " + undefined.stdout.strip())
        extraction = subprocess.run([str(objcopy), "-O", "binary", str(elf), str(raw)],
                                    capture_output=True, text=True, check=False)
        if extraction.returncode:
            raise PatchError("could not extract ARM hook bytes: " + extraction.stderr.strip())
        code = raw.read_bytes()

    if not code or len(code) > 0x2000:
        raise PatchError(f"compiled ARM hook image has unexpected size: {len(code)} bytes")
    code += b"\x00" * ((-len(code)) % 4)
    return code, symbols


def _overlay_slice(overlay, address: int, size: int) -> slice:
    start = address - overlay.ramAddress
    end = start + size
    if start < 0 or end > len(overlay.data):
        raise PatchError(f"hook address 0x{address:08X} is outside overlay {OVERLAY_ID}")
    return slice(start, end)


def _check_bss_sites(data: bytes, bss_start: int, bss_size: int) -> None:
    expected = dict(OVERLAY36_BSS_POINTERS)
    actual = {}
    for offset in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, offset)[0]
        if bss_start <= (value & ~1) < bss_start + bss_size:
            actual[offset] = value
    if actual != expected:
        missing = sorted(set(expected.items()) - set(actual.items()))
        extra = sorted(set(actual.items()) - set(expected.items()))
        raise PatchError(f"overlay 36 BSS references differ from the reviewed set (missing={missing}, extra={extra})")


def _verify_base_rom(path: Path, rom) -> object:
    digest = sha256_file(path)
    if digest.lower() != TARGET_ROM_SHA256:
        raise PatchError(f"unsupported base ROM SHA-256: {digest}")
    game_code = bytes(rom.idCode).decode("ascii", errors="replace")
    if game_code != TARGET_GAME_CODE:
        raise PatchError(f"unsupported game code: {game_code}")
    with path.open("rb") as source:
        header = source.read(0x40)
    if len(header) != 0x40 or struct.unpack_from("<I", header, 0x20)[0] != ROM_ARM9_FILE_OFFSET:
        raise PatchError("ARM9 ROM offset differs from the reviewed build")
    if len(rom.arm9) != ROM_ARM9_EXPECTED_SIZE or bytes(rom.arm9PostData) != ROM_ARM9_POSTDATA_EXPECTED:
        raise PatchError("ARM9 image or post-data differs from the reviewed autoload layout")
    overlays = rom.loadArm9Overlays({OVERLAY_ID})
    if OVERLAY_ID not in overlays:
        raise PatchError("ARM9 overlay 36 is missing")
    overlay = overlays[OVERLAY_ID]
    actual_crc = zlib.crc32(overlay.data) & 0xFFFFFFFF
    if actual_crc != OVERLAY_CRC32:
        raise PatchError(f"overlay 36 CRC32 mismatch: {actual_crc:08X}")
    if len(overlay.data) != overlay.ramSize:
        raise PatchError("overlay 36 decompressed length does not match its RAM size")
    for address, (hook_name, expected_target, expected_bytes) in BRANCH_HOOKS.items():
        actual = bytes(overlay.data[_overlay_slice(overlay, address, 4)])
        if actual != expected_bytes or decode_thumb_call(address, actual) != expected_target:
            raise PatchError(f"0x{address:08X} no longer calls the reviewed function for {hook_name}")
    for address, (_, expected_bytes) in INLINE_HOOKS.items():
        if bytes(overlay.data[_overlay_slice(overlay, address, 4)]) != expected_bytes:
            raise PatchError(f"inline print-background site 0x{address:08X} changed")
    address, old, _ = FIELD_WIN_SIZE_PATCH
    if bytes(overlay.data[_overlay_slice(overlay, address, 2)]) != old:
        raise PatchError("FieldMsgWin allocation-size instruction does not match the reviewed build")
    bss_start = overlay.ramAddress + overlay.ramSize
    _check_bss_sites(bytes(overlay.data), bss_start, overlay.bssSize)
    heap_site, heap_target, heap_expected = FIELD_HEAP_CREATE_SITE
    heap_actual = bytes(overlay.data[_overlay_slice(overlay, heap_site, 4)])
    if heap_actual != heap_expected or decode_thumb_bl(heap_site, heap_actual) != heap_target:
        raise PatchError("field heap creation call no longer matches the reviewed build")
    cave_address, cave_size = OVERLAY36_CODE_CAVE
    if any(overlay.data[_overlay_slice(overlay, cave_address, cave_size)]):
        raise PatchError("overlay 36 long-branch trampoline cave is no longer empty")
    if overlay.bssSize != OVERLAY36_BSS_SIZE:
        raise PatchError("overlay 36 BSS size differs from the reviewed field heap layout")
    size_setup_address, size_setup_expected = FIELD_HEAP_SIZE_SETUP
    if bytes(overlay.data[_overlay_slice(overlay, size_setup_address, len(size_setup_expected))]) != size_setup_expected:
        raise PatchError("field root heap initializer no longer passes the reviewed 0x10000-byte size")
    return overlay


def _extend_itcm_image(original: bytes, payload: bytes) -> bytes:
    """Extend the exact TwlSDK four-word ITCM autoload entry and its arena floor.

    ndspy's generic MainCodeFile parser assumes three-word entries. This ROM's
    boot copy loop at 0x02004BDC reads destination/size/BSS-address/BSS-size.
    Keep all other autoload data, static BSS, and executable bytes intact.
    """
    if len(original) != ROM_ARM9_EXPECTED_SIZE:
        raise PatchError("ARM9 length does not match the reviewed autoload image")
    params = struct.unpack_from("<6I", original, ARM9_MODULE_PARAMS_OFFSET)
    expected = (ARM9_RAM_BASE + ARM9_AUTOLOAD_TABLE_OFFSET,
                ARM9_RAM_BASE + ARM9_AUTOLOAD_TABLE_END,
                ARM9_RAM_BASE + ARM9_AUTOLOAD_SOURCE_OFFSET,
                0x0209D740, 0x0214F500, 0)
    entries = tuple(struct.unpack_from("<4I", original, offset)
                    for offset in range(ARM9_AUTOLOAD_TABLE_OFFSET, ARM9_AUTOLOAD_TABLE_END, 16))
    if params != expected or entries != ARM9_AUTOLOAD_ENTRIES:
        raise PatchError("ARM9 module parameters or four-word autoload entries changed")
    if struct.unpack_from("<I", original, ARM9_ITCM_ARENA_LITERAL_OFFSET)[0] != ITCM_HELPER_BASE:
        raise PatchError("ITCM arena floor does not match the reviewed end of initialized ITCM")
    if not payload or len(payload) > ITCM_HELPER_MAX_SIZE:
        raise PatchError("ITCM renderer payload is empty or exceeds the reserved extension limit")
    extension = payload + bytes((-len(payload)) % 32)
    out = bytearray(original[:ARM9_ITCM_INSERT_OFFSET] + extension + original[ARM9_ITCM_INSERT_OFFSET:])
    for offset in (ARM9_MODULE_PARAMS_OFFSET, ARM9_MODULE_PARAMS_OFFSET + 4):
        struct.pack_into("<I", out, offset, struct.unpack_from("<I", original, offset)[0] + len(extension))
    struct.pack_into("<I", out, ARM9_AUTOLOAD_TABLE_OFFSET + len(extension) + 4,
                     ITCM_ORIGINAL_SIZE + len(extension))
    struct.pack_into("<I", out, ARM9_ITCM_ARENA_LITERAL_OFFSET, ITCM_HELPER_BASE + len(extension))
    return bytes(out)


def _patch_rom(rom, overlay, hook_code: bytes, hook_ram_address: int,
               symbols: dict[str, int], ncgr: bytes, nclr: bytes,
               speaker_resources: list[tuple[bytes, bytes]],
               actor_hook_mode: str = "full", enable_field_art: bool = False) -> dict:
    old_ram_size, old_bss_size = overlay.ramSize, overlay.bssSize
    old_memory_end = overlay.ramAddress + old_ram_size + old_bss_size
    helper_symbols = [value & ~1 for name, value in symbols.items()
                      if name.startswith("dialogue_hook_") or name in {
                          "dialogue_attach_art", "dialogue_actor_bind", "dialogue_actor_cleanup"
                      }]
    if not helper_symbols or min(helper_symbols) < hook_ram_address or max(helper_symbols) >= hook_ram_address + len(hook_code):
        raise PatchError("linker placed renderer symbols outside the ITCM hook payload")
    if hook_ram_address != ITCM_HELPER_BASE:
        raise PatchError("renderer payload must be linked at the reviewed ITCM extension")

    narc_raw = bytes(rom.getFileByName(WINFRAME_NARC))
    updated_narc = append_winframe_members(narc_raw, ncgr, nclr, speaker_resources)

    code = bytearray(overlay.data)
    bss_start = overlay.ramAddress + overlay.ramSize
    _check_bss_sites(bytes(code), bss_start, overlay.bssSize)

    active_branch_hooks = _active_branch_hooks(actor_hook_mode, enable_field_art)
    for address, (hook_name, _, expected) in active_branch_hooks.items():
        site = _overlay_slice(overlay, address, 4)
        if bytes(code[site]) != expected:
            raise PatchError(f"branch patch site at 0x{address:08X} changed during patch preparation")
        code[site] = encode_thumb_bl(address, symbols[hook_name])
    for address, (hook_name, expected) in INLINE_HOOKS.items():
        site = _overlay_slice(overlay, address, 4)
        if bytes(code[site]) != expected:
            raise PatchError("inline print-background site changed during preparation")
        code[site] = encode_thumb_bl(address, symbols[hook_name])

    alloc_address, old_instruction, new_instruction = FIELD_WIN_SIZE_PATCH
    alloc_site = _overlay_slice(overlay, alloc_address, 2)
    if bytes(code[alloc_site]) != old_instruction:
        raise PatchError("FieldMsgWin size patch site changed during patch preparation")
    if enable_field_art:
        code[alloc_site] = new_instruction

    _check_bss_sites(bytes(code), bss_start, overlay.bssSize)
    overlay.data = code
    overlay.compressed = True
    rom.files[overlay.fileID] = overlay.save(compress=True)

    rom.arm9 = _extend_itcm_image(bytes(rom.arm9), hook_code)
    table = bytearray(rom.arm9OverlayTable)
    matches = [offset for offset in range(0, len(table), 32)
               if struct.unpack_from("<I", table, offset)[0] == OVERLAY_ID]
    if len(matches) != 1:
        raise PatchError("ARM9 overlay table does not have one unique entry for overlay 36")
    entry = matches[0]
    struct.pack_into("<I", table, entry + 28, overlay.compressedSize | (overlay.flags << 24))
    rom.arm9OverlayTable = bytes(table)
    rom.setFileByName(WINFRAME_NARC, updated_narc)
    if (overlay.ramSize != old_ram_size or overlay.bssSize != old_bss_size
            or overlay.ramAddress + overlay.ramSize + overlay.bssSize != old_memory_end):
        raise PatchError("dialogue renderer changed overlay 36's loaded RAM or BSS layout")
    return {"hook_address": hook_ram_address, "hook_size": len(hook_code),
            "hook_storage": "ARM9 ITCM autoload extension", "field_heap_size": FIELD_HEAP_ORIGINAL_SIZE,
            "field_heap_reduction": 0,
            "winframe_members": WINFRAME_MEMBER_COUNT + 3 + len(speaker_resources) * 2,
            "actor_hook_mode": actor_hook_mode,
            "field_system_art": enable_field_art,
            "speaker_profile_count": len(speaker_resources), "rom_size": len(rom.save())}


def build_patch(base_rom_path: Path, art_path: Path, output_path: Path, gcc: str | None = None,
                objcopy: str | None = None, nm: str | None = None,
                speaker_profile_manifest: Path | None = None,
                allow_wildcard_speakers: bool = False,
                actor_hook_mode: str = "full", enable_field_art: bool = False) -> dict:
    base_rom_path = base_rom_path.resolve(strict=True)
    art_path = art_path.resolve(strict=True)
    output_path = output_path.resolve()
    if output_path.exists():
        raise PatchError(f"output already exists; refusing to overwrite: {output_path}")
    if output_path == base_rom_path:
        raise PatchError("output path must not be the selected source ROM")
    if not output_path.parent.is_dir():
        raise PatchError("output directory must already exist")
    if not art_path.is_file() or not HOOK_SOURCE.is_file():
        raise PatchError("dialogue art or hook source is missing")

    rom = ndspy.rom.NintendoDSRom.fromFile(str(base_rom_path))
    overlay = _verify_base_rom(base_rom_path, rom)
    indexed, palette = prepare_indexed_art(art_path)
    ncgr = build_ncgr(indexed, ART_WIDTH, ART_HEIGHT)
    nclr = build_nclr(palette)
    validate_nclr(nclr)
    decoded_width, decoded_height, decoded = decode_ncgr(ncgr)
    if (decoded_width, decoded_height, decoded) != (ART_WIDTH, ART_HEIGHT, indexed):
        raise PatchError("NCGR round-trip did not preserve the indexed art")

    speaker_profiles = load_speaker_profiles(speaker_profile_manifest, allow_wildcard_speakers) \
        if speaker_profile_manifest is not None else []
    speaker_resources: list[tuple[bytes, bytes]] = []
    for profile in speaker_profiles:
        profile_pixels, profile_palette = prepare_indexed_art(profile["art_path"], profile["name"])
        profile_ncgr = build_ncgr(profile_pixels, ART_WIDTH, ART_HEIGHT)
        profile_nclr = build_nclr(profile_palette)
        validate_nclr(profile_nclr)
        if decode_ncgr(profile_ncgr) != (ART_WIDTH, ART_HEIGHT, profile_pixels):
            raise PatchError(f"speaker profile {profile['name']} NCGR round-trip failed")
        speaker_resources.append((profile_ncgr, profile_nclr))

    with base_rom_path.open("rb") as source:
        source.seek(0x20)
        arm9_file_offset_bytes = source.read(4)
    if len(arm9_file_offset_bytes) != 4:
        raise PatchError("selected ROM has a truncated Nintendo DS header")
    arm9_file_offset = struct.unpack("<I", arm9_file_offset_bytes)[0]
    hook_base = ITCM_HELPER_BASE
    original_arm9 = bytes(rom.arm9)
    original_arm9_postdata = bytes(rom.arm9PostData)
    hook_code, symbols = compile_hooks(HOOK_SOURCE, hook_base, gcc, objcopy, nm, speaker_profiles)
    original_ram_size, original_bss_size = overlay.ramSize, overlay.bssSize
    original_winframe = [bytes(member) for member in ndspy.narc.NARC(rom.getFileByName(WINFRAME_NARC)).files]
    result = _patch_rom(rom, overlay, hook_code, hook_base, symbols, ncgr, nclr, speaker_resources,
                        actor_hook_mode, enable_field_art)
    output_bytes = rom.save()
    with tempfile.TemporaryDirectory(prefix="unova-dialogue-art-output-", dir=output_path.parent) as temp_name:
        temp_path = Path(temp_name) / output_path.name
        temp_path.write_bytes(output_bytes)
        output_rom = ndspy.rom.NintendoDSRom.fromFile(str(temp_path))
        output_overlay = output_rom.loadArm9Overlays({OVERLAY_ID})[OVERLAY_ID]
        if output_overlay.ramSize != original_ram_size or output_overlay.bssSize != original_bss_size:
            raise PatchError("saved ROM changed overlay 36's reviewed RAM or BSS size")
        if (output_overlay.ramAddress + output_overlay.ramSize + output_overlay.bssSize
                != overlay.ramAddress + original_ram_size + original_bss_size):
            raise PatchError("saved ROM changed overlay 36's overall memory endpoint")
        _check_bss_sites(bytes(output_overlay.data), output_overlay.ramAddress + output_overlay.ramSize,
                         output_overlay.bssSize)
        if bytes(output_rom.arm9) != _extend_itcm_image(original_arm9, hook_code) or bytes(output_rom.arm9PostData) != original_arm9_postdata:
            raise PatchError("saved ROM does not preserve the reviewed ARM9 autoload transformation")
        output_arm9_offset = struct.unpack_from("<I", output_bytes, 0x20)[0]
        output_arm9_size = struct.unpack_from("<I", output_bytes, 0x2C)[0]
        helper_file_offset = ROM_ARM9_FILE_OFFSET + ARM9_ITCM_INSERT_OFFSET
        if (output_arm9_offset != ROM_ARM9_FILE_OFFSET or output_arm9_size != len(rom.arm9)
                or output_bytes[helper_file_offset:helper_file_offset + len(hook_code)] != hook_code):
            raise PatchError("saved ROM does not contain the complete helper in the ITCM autoload source")
        arm9_overlay_table_offset = struct.unpack_from("<I", output_bytes, 0x50)[0]
        if helper_file_offset + len(hook_code) > arm9_overlay_table_offset:
            raise PatchError("ROM hook payload overlaps the ARM9 overlay table")
        if zlib.crc32(output_overlay.data) & 0xFFFFFFFF == OVERLAY_CRC32:
            raise PatchError("saved overlay 36 is unchanged")
        output_narc = ndspy.narc.NARC(output_rom.getFileByName(WINFRAME_NARC))
        expected_resource_count = WINFRAME_MEMBER_COUNT + 3 + len(speaker_resources) * 2
        if len(output_narc.files) != expected_resource_count:
            raise PatchError("saved ROM does not contain every new WinFrame art resource")
        if [bytes(member) for member in output_narc.files[:WINFRAME_MEMBER_COUNT]] != original_winframe:
            raise PatchError("saved ROM changed one or more original WinFrame members")
        expected_resources = [ncgr, nclr]
        for profile_ncgr, profile_nclr in speaker_resources:
            expected_resources.extend([profile_ncgr, profile_nclr])
        expected_resources.append(build_nclr([(0, 0, 0), (247, 232, 207), (53, 31, 49)]
                                             + [(247, 232, 207)] * 12 + [(43, 24, 42)]))
        if [bytes(output_narc.files[index]) for index in range(WINFRAME_MEMBER_COUNT, expected_resource_count)] \
                != expected_resources:
            raise PatchError("saved ROM has missing or reordered dialogue art resources")
        active_branch_hooks = _active_branch_hooks(actor_hook_mode, enable_field_art)
        for address, (hook_name, _, _) in active_branch_hooks.items():
            actual = bytes(output_overlay.data[_overlay_slice(output_overlay, address, 4)])
            target = symbols[hook_name] & ~1
            if decode_thumb_bl(address, actual) != target:
                raise PatchError(f"saved ROM does not branch to the ITCM {hook_name} entry")
        for address, (hook_name, _) in INLINE_HOOKS.items():
            if decode_thumb_bl(address, bytes(output_overlay.data[_overlay_slice(output_overlay, address, 4)])) != symbols[hook_name]:
                raise PatchError("saved ROM has an invalid inline print-background branch")
        heap_call, _, _ = FIELD_HEAP_CREATE_SITE
        heap_site = bytes(output_overlay.data[_overlay_slice(output_overlay, heap_call, 4)])
        if heap_site != FIELD_HEAP_CREATE_SITE[2] or decode_thumb_bl(heap_call, heap_site) != FIELD_HEAP_CREATE_SITE[1]:
            raise PatchError("saved ROM changed the field root-heap initialization call")
        size_setup_address, size_setup_expected = FIELD_HEAP_SIZE_SETUP
        if bytes(output_overlay.data[_overlay_slice(output_overlay, size_setup_address, len(size_setup_expected))]) != size_setup_expected:
            raise PatchError("saved ROM changed the field root-heap capacity")
        if output_path.exists():
            raise PatchError(f"output appeared while the build was running; refusing to replace it: {output_path}")
        os.rename(temp_path, output_path)

    result.update({
        "base_rom_sha256": TARGET_ROM_SHA256,
        "patched_rom_sha256": hashlib.sha256(output_bytes).hexdigest(),
        "patched_rom_path": str(output_path),
        "art_source_sha256": sha256_file(art_path),
        "art_dimensions": [ART_WIDTH, ART_HEIGHT],
        "speaker_profiles": [
            {"name": item["name"], "zone_id": item["zone_id"], "actor_uid": item["actor_uid"],
             "ncgr": item["ncgr"], "nclr": item["nclr"], "art_sha256": sha256_file(item["art_path"])}
            for item in speaker_profiles
        ],
        "helper_ram_address": f"0x{hook_base:08X}",
        "helper_rom_file_offset": f"0x{helper_file_offset:08X}",
        "overlay36_crc32": f"{zlib.crc32(output_overlay.data) & 0xFFFFFFFF:08X}",
        "overlay36_ram_size": output_overlay.ramSize,
        "overlay36_bss_size": output_overlay.bssSize,
        "helper_symbols": {name: f"0x{address:08X}" for name, address in symbols.items()
                           if name.startswith("dialogue_hook_") or name in {
                               "dialogue_attach_art", "dialogue_actor_bind", "dialogue_actor_cleanup"
                           }},
        "source_toolchain": str(_resolve_tool(gcc, "arm-none-eabi-gcc.exe")),
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-rom", required=True, type=Path, help="exact supported user-provided IREO ROM")
    parser.add_argument("--art", type=Path, default=DEFAULT_ART, help="original transparent dialogue-art PNG")
    parser.add_argument("--output-rom", required=True, type=Path, help="new isolated output path; must not exist")
    parser.add_argument("--gcc", help="arm-none-eabi-gcc executable")
    parser.add_argument("--objcopy", help="arm-none-eabi-objcopy executable")
    parser.add_argument("--nm", help="arm-none-eabi-nm executable")
    parser.add_argument("--speaker-profiles", type=Path,
                        help="JSON manifest mapping exact map-zone/actor-UID pairs to portrait/name art")
    parser.add_argument("--allow-wildcard-speaker-profiles", action="store_true",
                        help="test-only: allow profiles to match any zone or actor UID")
    parser.add_argument("--actor-hook-mode", choices=sorted(ACTOR_HOOK_MODES), default="full",
                        help="diagnostic actor hook selection; use full for the normal profile renderer")
    parser.add_argument("--field-system-art", action="store_true",
                        help="experimental: also replace bottom system-message framing with fixed narrator art")
    args = parser.parse_args()
    try:
        result = build_patch(args.base_rom, args.art, args.output_rom, args.gcc, args.objcopy, args.nm,
                             args.speaker_profiles, args.allow_wildcard_speaker_profiles,
                             args.actor_hook_mode, args.field_system_art)
    except (OSError, ValueError, PatchError) as error:
        parser.exit(2, f"dialogue art patch failed: {error}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
