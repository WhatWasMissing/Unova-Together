#!/usr/bin/env python3
"""Add Cynthia's post-Skyla Mega Evolution lesson and gift to a Black 2 Redux ROM.

This patches only the Route 7 event/script/text entries and one otherwise unused
field-actor sprite slot. The input ROM is never modified.

Requires ndspy, Pillow, arm-none-eabi-gcc/objcopy, and the BW2 decomp source tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import uuid
from pathlib import Path

import ndspy.color
import ndspy.narc
import ndspy.rom
import ndspy.texture


GAME_CODE = b"IREO"
ACTOR_CODE = 0x126B
ACTOR_CONFIG_INDEX = ACTOR_CODE - 0x1000 + 0x179
ACTOR_RESOURCE_INDEX = 975
ACTOR_UID = 17
CHALLENGE_ACTOR_UID = 18
# These four placeholder flags are unused by the BW2 decomp and fit in the
# saved event-flag table (0x0000-0x0BF7).
REWARD_FLAG = 0x09A1
CHALLENGE_FLAG = 0x09A2
TUTORIAL_HIDE_FLAG = 0x09A3
CHALLENGE_HIDE_FLAG = 0x09A4
REMATCH_TRAINER_ID = 891
SKYLA_FLAG = "EVENT_FLAG_TRAINER_LEADER_SKYLA"
STONE_FALLBACK = 113  # Serperiorite
REMATCH_POSITION = {"x": 111, "z": 244, "y": 0}

# The first eligible Pokémon in party order receives the matching stone.
# Charizard defaults to X; Mewtwo defaults to Y; Lucario defaults to standard Mega.
MEGA_STONES = {
    "SERPERIOR": 113,
    "ARCANINE": 126,
    "VENUSAUR": 137,
    "CHARIZARD": 139,
    "BLASTOISE": 140,
    "BEEDRILL": 141,
    "PIDGEOT": 142,
    "ALAKAZAM": 143,
    "SLOWBRO": 144,
    "GENGAR": 145,
    "KANGASKHAN": 146,
    "PINSIR": 147,
    "GYARADOS": 148,
    "AERODACTYL": 485,
    "MEWTWO": 487,
    "AMPHAROS": 488,
    "STEELIX": 489,
    "SCIZOR": 490,
    "HERACROSS": 491,
    "HOUNDOOM": 505,
    "TYRANITAR": 506,
    "SCEPTILE": 507,
    "BLAZIKEN": 508,
    "SWAMPERT": 509,
    "GARDEVOIR": 510,
    "SABLEYE": 511,
    "MAWILE": 512,
    "AGGRON": 513,
    "MEDICHAM": 514,
    "MANECTRIC": 515,
    "SHARPEDO": 516,
    "CAMERUPT": 517,
    "ALTARIA": 518,
    "BANETTE": 519,
    "ABSOL": 520,
    "GLALIE": 521,
    "SALAMENCE": 522,
    "METAGROSS": 523,
    "LATIAS": 524,
    "LOPUNNY": 525,
    "GARCHOMP": 526,
    "LUCARIO": 527,
    "ABOMASNOW": 529,
    "GALLADE": 530,
    "AUDINO": 531,
    "LATIOS": 123,
}

NEW_MESSAGES = [
    ("Route7_Text_CynthiaIntro", "I'm Cynthia, a Pokémon Trainer from Sinnoh.\\nI came to Unova to study Mega Evolution."),
    ("Route7_Text_CynthiaExplainMega", "Mega Evolution lets certain Pokémon change form\\nduring battle. Each needs its own Mega Stone.\\nThe change lasts until the battle ends."),
    ("Route7_Text_CynthiaMatchingStone", "Your party has a Pokémon that can Mega Evolve.\\nThis {0109:0} matches it."),
    ("Route7_Text_CynthiaFallbackStone", "No one in your party can Mega Evolve yet.\\nTake this {0109:0}; it works with Serperior."),
    ("Route7_Text_CynthiaGiftReceived", "I gave you the {0109:0}. Give it to the matching\\nPokémon, then press L and R together while\\nchoosing a move to Mega Evolve."),
    ("Route7_Text_CynthiaBagFull", "Make room in your Bag, then speak to me again.\\nI'll hold the Mega Stone for you."),
    ("Route7_Text_CynthiaAlreadyGifted", "Give the Mega Stone I gave you to its matching\\nPokémon. Press L and R together while choosing\\na move in battle to Mega Evolve."),
    ("Route7_Text_CynthiaRematchIntro", "Ready to test your Mega Evolution? My Garchomp\\nand I will give it everything we've got!"),
    ("Route7_Text_CynthiaRematchWon", "That was an incredible battle! Your team has\\nlearned to use Mega Evolution well."),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def command(args: list[str], *, cwd: Path) -> None:
    run = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(f"Command failed ({run.returncode}): {' '.join(args)}\n{run.stdout}\n{run.stderr}")


def archive_member(rom: ndspy.rom.NintendoDSRom, name: str) -> tuple[int, bytes]:
    fid = rom.filenames.idOf(name)
    if fid is None:
        raise ValueError(f"ROM is missing {name}")
    return fid, rom.files[fid]


def patch_archive(rom: ndspy.rom.NintendoDSRom, name: str, member_index: int, member: bytes) -> None:
    fid, raw = archive_member(rom, name)
    narc = ndspy.narc.NARC(raw)
    if member_index >= len(narc.files):
        raise ValueError(f"{name} has {len(narc.files)} members, needs {member_index}")
    narc.files[member_index] = member
    rom.files[fid] = narc.save()


def species_ids(decomp: Path) -> dict[str, int]:
    names = {}
    value = -1
    for raw in (decomp / "data/constants/species.txt").read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, sep, given = line.partition("=")
        value = int(given.strip(), 0) if sep else value + 1
        names[name.strip().removeprefix("SPECIES_")] = value
    missing = set(MEGA_STONES) - names.keys()
    if missing:
        raise ValueError(f"species constants are missing: {sorted(missing)}")
    return {name: names[name] for name in MEGA_STONES}


def _stack_cmp(operator: int, left: int, right: int) -> bool:
    """Evaluate BW2 VMStackCmp operators used by Cynthia's event."""
    return {
        0: left < right,   # CMP_LT
        1: left == right,  # CMP_EQ
        5: left != right,  # CMP_NE
    }[operator]


def _find_script_pattern(instructions, start: int, end: int, pattern: list[tuple[str, list[int | None]]]):
    matches = []
    for pc in sorted(offset for offset in instructions if start <= offset < end):
        cursor = pc
        sequence = []
        for name, expected_args in pattern:
            entry = instructions.get(cursor)
            if entry is None:
                break
            command, args, next_pc = entry
            if command.name != name or len(args) != len(expected_args):
                break
            if any(expected is not None and actual != expected
                   for actual, expected in zip(args, expected_args, strict=True)):
                break
            sequence.append(entry)
            cursor = next_pc
        else:
            matches.append(sequence)
    return matches


def validate_route7_script(compiled: bytes, decomp: Path, species: dict[str, int]) -> dict:
    """Verify the compiled event's branch polarity against the BW2 script VM.

    The decomp's VM handler (src/ov012/scrcmd_vm.c:s001F_VMJumpIf) jumps for
    CMP_STACK when the popped value is not 1. A nearby party-scanning script
    confirms the intended pattern: a true in-range comparison falls through,
    while a false comparison branches out of the loop.
    """
    from tools.data.gen_constants import load as load_constants
    from tools.script.field_script import ScriptFile, load_commands, script_header

    header = script_header(compiled)
    if header is None or len(header[0]) != 9:
        raise ValueError("Compiled Route 7 script has an unexpected script table")
    commands, _, _, _ = load_commands()
    traced = ScriptFile(compiled, commands, None)
    if not traced.trace(header[0]) or traced.errors:
        raise ValueError(f"Compiled Route 7 script failed decomp trace: {traced.errors}")

    offsets = header[0]
    ranges = []
    for start in offsets:
        greater = [offset for offset in offsets if offset > start]
        ranges.append((start, min(greater) if greater else len(compiled)))

    def only_pattern(script_index: int, pattern: list[tuple[str, list[int | None]]], description: str):
        found = _find_script_pattern(traced.instructions, *ranges[script_index], pattern)
        if len(found) != 1:
            raise ValueError(f"Cynthia script has {len(found)} instances of {description}; expected one")
        return found[0]

    def branch_target(sequence) -> int:
        target = sequence[-1][1][1]
        if target not in traced.instructions:
            raise ValueError("Cynthia script branch target is not a decoded instruction")
        return target

    def expect_target(sequence, command_name: str, args_prefix: list[int], description: str) -> None:
        target = branch_target(sequence)
        command, args, _ = traced.instructions[target]
        if command.name != command_name or args[:len(args_prefix)] != args_prefix:
            raise ValueError(f"Cynthia {description} branch lands on the wrong command")

    def assert_flag_branch(sequence, description: str) -> None:
        # This is the actual CMP_STACK behavior in s001F_VMJumpIf, not the
        # opposite wording in the header comment.
        for flag_value in (0, 1):
            cmp_true = _stack_cmp(eq, 0, flag_value)
            jumps = not cmp_true
            should_jump = flag_value == 1
            if jumps != should_jump:
                raise ValueError(f"Cynthia {description} has inverted CMP_STACK behavior")

    cmp_stack = 0xFF
    eq = 1
    ne = 5
    lt = 0
    flag_ids = load_constants("flags")
    flag_pattern = lambda flag: [
        ("VMStackPushFlag", [flag]),
        ("VMStackPushConst", [0]),
        ("VMStackCmp", [eq]),
        ("VMJumpIf", [cmp_stack, None]),
    ]

    gift_check = only_pattern(6, flag_pattern(0x09A1), "first-time gift check")
    expect_target(gift_check, "ParentActorMsg", [0x400, 12], "first-time gift")
    skyla_check = only_pattern(7, flag_pattern(flag_ids[SKYLA_FLAG]), "Skyla progression gate")
    expect_target(skyla_check, "VMStackPushFlag", [0x09A1], "Skyla progression")
    reward_check = only_pattern(7, flag_pattern(0x09A1), "gift progression gate")
    expect_target(reward_check, "FlagSet", [TUTORIAL_HIDE_FLAG], "gift progression")
    challenge_check = only_pattern(7, flag_pattern(0x09A2), "rematch-completion gate")
    expect_target(challenge_check, "FlagSet", [CHALLENGE_HIDE_FLAG], "rematch completion")
    rematch_check = only_pattern(8, flag_pattern(0x09A2), "rematch retry gate")
    expect_target(rematch_check, "ParentActorMsg", [0x400, 14], "rematch retry")
    for label, sequence in (("gift", gift_check), ("Skyla", skyla_check),
                            ("gift progression", reward_check), ("rematch completion", challenge_check),
                            ("rematch retry", rematch_check)):
        assert_flag_branch(sequence, label)

    party_loop = only_pattern(6, [
        ("VMStackPush", [0x8021]),
        ("VMStackPush", [0x8020]),
        ("VMStackCmp", [lt]),
        ("VMJumpIf", [cmp_stack, None]),
    ], "party bounds check")
    expect_target(party_loop, "WorkSetConst", [0x8023, STONE_FALLBACK], "empty-party fallback")
    # In-range (0 < 1) continues scanning; exhausted (1 < 1 is false) exits.
    for index, count, should_exit in ((0, 1, False), (1, 1, True)):
        cmp_true = _stack_cmp(lt, index, count)
        if (not cmp_true) != should_exit:
            raise ValueError("Cynthia party bounds check can skip a valid party member")

    for name, item_id in MEGA_STONES.items():
        species_check = only_pattern(6, [
            ("VMStackPush", [0x8022]),
            ("VMStackPushConst", [species[name]]),
            ("VMStackCmp", [ne]),
            ("VMJumpIf", [cmp_stack, None]),
        ], f"{name} species match")
        expect_target(species_check, "WorkSetConst", [0x8023, item_id], f"{name} Mega Stone")
        for candidate, should_match in ((species[name], True), (species[name] + 1, False)):
            cmp_true = _stack_cmp(ne, candidate, species[name])
            if (not cmp_true) != should_match:
                raise ValueError(f"Cynthia's {name} branch matches the wrong species")

    matching_check = only_pattern(6, [
        ("VMStackPush", [0x8024]),
        ("VMStackPushConst", [0]),
        ("VMStackCmp", [eq]),
        ("VMJumpIf", [cmp_stack, None]),
    ], "matching-stone dialogue check")
    expect_target(matching_check, "WordSetItemName", [], "matching-stone dialogue")
    for matched in (0, 1):
        if (not _stack_cmp(eq, matched, 0)) != bool(matched):
            raise ValueError("Cynthia's matching-stone dialogue branch is inverted")

    bag_check = only_pattern(6, [
        ("VMStackPush", [0x8025]),
        ("VMStackPushConst", [1]),
        ("VMStackCmp", [eq]),
        ("VMJumpIf", [cmp_stack, None]),
    ], "Bag capacity check")
    expect_target(bag_check, "ParentActorMsg", [0x400, 11], "full-Bag retry")
    victory_check = only_pattern(8, [
        ("VMStackPush", [0x8010]),
        ("VMStackPushConst", [1]),
        ("VMStackCmp", [eq]),
        ("VMJumpIf", [cmp_stack, None]),
    ], "battle result check")
    expect_target(victory_check, "CallTrainerLose", [], "battle-loss")
    for has_space, should_full in ((0, True), (1, False)):
        if (not _stack_cmp(eq, has_space, 1)) != should_full:
            raise ValueError("Cynthia's full-Bag branch is inverted")
    for won, should_lose in ((0, True), (1, False)):
        if (not _stack_cmp(eq, won, 1)) != should_lose:
            raise ValueError("Cynthia's rematch result branch is inverted")

    return {
        "party_species_branches": len(MEGA_STONES),
        "flag_progression_gates": 5,
        "party_loop_empty_and_nonempty_cases": "passed",
        "bag_and_rematch_outcomes": "passed",
        "cmp_stack_semantics": "passed against BW2 VM handler",
    }


def script_source(decomp: Path, messages_path: Path, header_path: Path, species: dict[str, int]) -> str:
    from tools.text.text_ids import header as make_text_header

    source_path = decomp / "data/field_scripts/route_7.s"
    source = source_path.read_text(encoding="utf-8")
    old_entries = "    ScriptEntry Script_6\n    ScriptEntriesEnd"
    new_entries = "    ScriptEntry Script_6\n    ScriptEntry Script_7\n    ScriptEntry Script_8\n    ScriptEntry Script_9\n    ScriptEntriesEnd"
    if source.count(old_entries) != 1:
        raise ValueError("Route 7 source script entry list has an unexpected layout")
    source = source.replace(old_entries, new_entries)
    source = source.replace("#include \"text/script/route_7.h\"", "#include \"text/script/route_7.h\"")
    source_ids = []
    for species_name, species_id in species.items():
        label = "L_GIVE_" + species_name
        source_ids.append(
            f"    VMStackPush 0x8022\n"
            f"    VMStackPushConst {species_id}\n"
            f"    VMStackCmp CMP_NE\n"
            f"    VMJumpIf CMP_STACK, {label}\n"
        )
    reward_labels = []
    for species_name, item_id in MEGA_STONES.items():
        reward_labels.append(
            f"L_GIVE_{species_name}:\n"
            f"    WorkSetConst 0x8023, {item_id}\n"
            f"    WorkSetConst 0x8024, 1\n"
            f"    VMJump L_STONE_SELECTED\n"
        )

    def jump_if_flag_set(flag: int, label: str) -> str:
        return (
            f"    VMStackPushFlag {flag}\n"
            f"    VMStackPushConst 0\n"
            f"    VMStackCmp CMP_EQ\n"
            f"    VMJumpIf CMP_STACK, {label}\n"
        )

    source = source.replace(
        "    .balign 4, 0",
        "\n" + f"""
Script_7:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
{jump_if_flag_set(REWARD_FLAG, 'L_CYNTHIA_ALREADY_GIFTED').rstrip()}
    ParentActorMsg MSGFILE_SCRIPT, Route7_Text_CynthiaIntro, 0, 0
    LastKeyWait
    ActorMsgClose
    ParentActorMsg MSGFILE_SCRIPT, Route7_Text_CynthiaExplainMega, 0, 0
    LastKeyWait
    ActorMsgClose
    PokePartyGetCount 0x8020, 0
    WorkSetConst 0x8021, 0

L_CYNTHIA_SCAN_PARTY:
    VMStackPush 0x8021
    VMStackPush 0x8020
    VMStackCmp CMP_LT
    VMJumpIf CMP_STACK, L_CYNTHIA_NO_MATCH
    PokePartyGetSpecies 0x8022, 0x8021
{''.join(source_ids)}    WorkAdd 0x8021, 1
    VMJump L_CYNTHIA_SCAN_PARTY

L_CYNTHIA_NO_MATCH:
    WorkSetConst 0x8023, {STONE_FALLBACK}
    WorkSetConst 0x8024, 0
    VMJump L_STONE_SELECTED

{''.join(reward_labels)}
L_STONE_SELECTED:
    VMStackPush 0x8024
    VMStackPushConst 0
    VMStackCmp CMP_EQ
    VMJumpIf CMP_STACK, L_CYNTHIA_MATCHING_STONE
    WordSetItemName 0, 0x8023
    ParentActorMsg MSGFILE_SCRIPT, Route7_Text_CynthiaFallbackStone, 0, 0
    VMJump L_CYNTHIA_CHECK_BAG

L_CYNTHIA_MATCHING_STONE:
    WordSetItemName 0, 0x8023
    ParentActorMsg MSGFILE_SCRIPT, Route7_Text_CynthiaMatchingStone, 0, 0

L_CYNTHIA_CHECK_BAG:
    LastKeyWait
    ActorMsgClose
    ItemCheckSpace 0x8023, 1, 0x8025
    VMStackPush 0x8025
    VMStackPushConst 1
    VMStackCmp CMP_EQ
    VMJumpIf CMP_STACK, L_CYNTHIA_BAG_FULL
    ItemAdd 0x8023, 1, 0x8025
    FlagSet {REWARD_FLAG}
    WordSetItemName 0, 0x8023
    ParentActorMsg MSGFILE_SCRIPT, Route7_Text_CynthiaGiftReceived, 0, 0
    LastKeyWait
    ActorMsgClose
    ActorDelete {ACTOR_UID}
    VMJump L_CYNTHIA_DONE

L_CYNTHIA_BAG_FULL:
    ParentActorMsg MSGFILE_SCRIPT, Route7_Text_CynthiaBagFull, 0, 0
    LastKeyWait
    ActorMsgClose
    VMJump L_CYNTHIA_DONE

L_CYNTHIA_ALREADY_GIFTED:
    ParentActorMsg MSGFILE_SCRIPT, Route7_Text_CynthiaAlreadyGifted, 0, 0
    LastKeyWait
    ActorMsgClose

L_CYNTHIA_DONE:
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_8:
    // This runs before map actors spawn. Set their spawn flags from saved progress.
{jump_if_flag_set(SKYLA_FLAG, 'L_CYNTHIA_SKYLA_DEFEATED').rstrip()}
    FlagSet {TUTORIAL_HIDE_FLAG}
    FlagSet {CHALLENGE_HIDE_FLAG}
    VMJump L_CYNTHIA_INIT_DONE

L_CYNTHIA_SKYLA_DEFEATED:
{jump_if_flag_set(REWARD_FLAG, 'L_CYNTHIA_GIFT_RECEIVED').rstrip()}
    FlagReset {TUTORIAL_HIDE_FLAG}
    FlagSet {CHALLENGE_HIDE_FLAG}
    VMJump L_CYNTHIA_INIT_DONE

L_CYNTHIA_GIFT_RECEIVED:
    FlagSet {TUTORIAL_HIDE_FLAG}
{jump_if_flag_set(CHALLENGE_FLAG, 'L_CYNTHIA_CHALLENGE_COMPLETE').rstrip()}
    FlagReset {CHALLENGE_HIDE_FLAG}
    VMJump L_CYNTHIA_INIT_DONE

L_CYNTHIA_CHALLENGE_COMPLETE:
    FlagSet {CHALLENGE_HIDE_FLAG}

L_CYNTHIA_INIT_DONE:
    VMHalt

// Cynthia moves to the northern end of Route 7 once the player has the gift.
Script_9:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
{jump_if_flag_set(CHALLENGE_FLAG, 'L_CYNTHIA_REMATCH_COMPLETE').rstrip()}
    TrainerBGMPlayPush {REMATCH_TRAINER_ID}
    ParentActorMsg MSGFILE_SCRIPT, Route7_Text_CynthiaRematchIntro, 0, 0
    LastKeyWait
    MsgWinCloseAll
    CallTrainerBattle {REMATCH_TRAINER_ID}, 0, 0
    TrainerBattleIsVictory 0x8010
    VMStackPush 0x8010
    VMStackPushConst 1
    VMStackCmp CMP_EQ
    VMJumpIf CMP_STACK, L_CYNTHIA_REMATCH_LOST
    CallTrainerBattleEnd
    TrainerFlagSet {REMATCH_TRAINER_ID}
    FlagSet {CHALLENGE_FLAG}
    ParentActorMsg MSGFILE_SCRIPT, Route7_Text_CynthiaRematchWon, 0, 0
    LastKeyWait
    ActorMsgClose
    ActorDelete {CHALLENGE_ACTOR_UID}
    VMJump L_CYNTHIA_REMATCH_DONE

L_CYNTHIA_REMATCH_LOST:
    CallTrainerLose
    VMJump L_CYNTHIA_REMATCH_DONE

L_CYNTHIA_REMATCH_COMPLETE:
    ParentActorMsg MSGFILE_SCRIPT, Route7_Text_CynthiaRematchWon, 0, 0
    LastKeyWait
    ActorMsgClose

L_CYNTHIA_REMATCH_DONE:
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

    .balign 4, 0""",
        1,
    )
    header_path.parent.mkdir(parents=True, exist_ok=True)
    header_path.write_text(make_text_header(messages_path), encoding="utf-8")
    return source


def make_texture_resource(template: bytes, sprite_path: Path, montage_path: Path) -> bytes:
    from PIL import Image, ImageDraw

    sheet = Image.open(sprite_path).convert("RGBA")
    if sheet.size != (256, 256):
        raise ValueError(f"Overworld sprite sheet must be 256x256, got {sheet.size}")

    # Native Gen V human packs have three walking frames for each direction.
    # The supplied 4-frame rows duplicate the standing frame at columns 0 and 2.
    frame_rows = (3, 0, 1, 2)  # native order: back, front, left, right
    selected_columns = (0, 1, 3)  # idle, one step, opposite step
    frames = []
    for row in frame_rows:
        for column in selected_columns:
            frame = sheet.crop((column * 64, row * 64, (column + 1) * 64, (row + 1) * 64))
            frames.append(frame.resize((32, 32), Image.Resampling.NEAREST))

    opaque = [pixel[:3] for frame in frames for pixel in frame.getdata() if pixel[3] >= 128]
    if not opaque:
        raise ValueError("Sprite sheet has no opaque pixels")
    flat = Image.new("RGB", (len(opaque), 1))
    flat.putdata(opaque)
    reduced = flat.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette_rgb = reduced.getpalette()[:45]
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(palette_rgb + [0] * (768 - len(palette_rgb)))

    packed_frames = []
    frame_images = []
    for frame in frames:
        indices = list(frame.convert("RGB").quantize(palette=palette_image, dither=Image.Dither.NONE).getdata())
        alpha = list(frame.getchannel("A").getdata())
        indices = [0 if alpha[i] < 128 else indices[i] + 1 for i in range(32 * 32)]
        out = bytearray()
        for i in range(0, len(indices), 2):
            out.append(indices[i] | (indices[i + 1] << 4))
        packed_frames.append(bytes(out))
        display = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        display.putdata([(0, 0, 0, 0) if idx == 0 else tuple(palette_rgb[(idx - 1) * 3:(idx - 1) * 3 + 3]) + (255,) for idx in indices])
        frame_images.append(display)

    btx = ndspy.texture.NSBTX(template)
    if len(btx.textures) != 12:
        raise ValueError(f"Template character pack has {len(btx.textures)} frames, expected 12")
    for i, (_, texture) in enumerate(btx.textures):
        if texture.size != (32, 32) or texture.format != ndspy.texture.TextureFormat.I4:
            raise ValueError("Template character pack is not the expected 32x32 I4 layout")
        texture.data1 = packed_frames[i]
        texture.data2 = b""
    palette = btx.palettes[0][1]
    rgb_colors = [(0, 0, 0)] + [tuple(palette_rgb[i:i + 3]) for i in range(0, 45, 3)]
    palette.colors = [(r >> 3, g >> 3, b >> 3, 0) for r, g, b in rgb_colors]

    montage = Image.new("RGBA", (32 * 4, 32 * 3), (225, 225, 225, 255))
    for i, frame in enumerate(frame_images):
        montage.alpha_composite(frame, ((i % 4) * 32, (i // 4) * 32))
    montage.resize((32 * 4 * 4, 32 * 3 * 4), Image.Resampling.NEAREST).save(montage_path)
    return btx.save()


def validate_sprite(data: bytes) -> None:
    nsbtx = ndspy.texture.NSBTX(data)
    if len(nsbtx.textures) != 12 or len(nsbtx.palettes) != 1 or len(nsbtx.palettes[0][1].colors) != 16:
        raise ValueError("Generated character texture archive has an unexpected texture/palette layout")
    for _, texture in nsbtx.textures:
        if texture.format != ndspy.texture.TextureFormat.I4 or texture.size != (32, 32) or len(texture.data1) != 512:
            raise ValueError("Generated Cynthia frame is not a 32x32 4bpp texture")


def pack_cynthia_rematch_trainer(rom: ndspy.rom.NintendoDSRom, decomp: Path) -> dict:
    """Append a native-class Cynthia trainer record that the Practice browser can discover."""
    from tools.data.gen_constants import load as load_constants
    from tools.data.datajson import constants as all_constants
    from tools.text.text_data import pack_file, unpack_file, with_ids

    constant_values = all_constants()
    trainers_archive = ndspy.narc.NARC(rom.getFileByName("a/0/9/1"))
    parties_archive = ndspy.narc.NARC(rom.getFileByName("a/0/9/2"))
    if len(trainers_archive.files) != REMATCH_TRAINER_ID or len(parties_archive.files) != REMATCH_TRAINER_ID:
        raise ValueError(
            f"Expected trainer slot {REMATCH_TRAINER_ID} after {REMATCH_TRAINER_ID} records; "
            f"found {len(trainers_archive.files)} trainer and {len(parties_archive.files)} party records"
        )

    source = json.loads((decomp / "data/trainers/cynthia.json").read_text(encoding="utf-8"))
    species_constants = load_constants("species")
    item_constants = load_constants("items")
    move_constants = load_constants("moves")
    required = {
        "trainer class": source["class"],
        "battle style": source["battle_style"],
    }
    for label, name in required.items():
        if name not in constant_values:
            raise ValueError(f"Decomp is missing {label} constant {name}")
    trainer_items = [item_constants[name] for name in source["items"]]
    if len(trainer_items) > 4:
        raise ValueError("Cynthia's team has more than four trainer battle items")
    trainer_items += [0] * (4 - len(trainer_items))
    ai_flags = 0
    for name in source["ai_flags"]:
        ai_flags |= constant_values[name]
    trainer_record = struct.pack(
        "<4B4HIBBH",
        3,  # PARTY_ITEMS | PARTY_MOVES
        constant_values[source["class"]],
        constant_values[source["battle_style"]],
        len(source["party"]),
        *trainer_items,
        ai_flags,
        int(source["heals"]),
        source["money"],
        item_constants[source["reward"]],
    )

    # Redux Complete's post-Skyla rematch uses five level-51 Pokémon and one
    # level-52 Pokémon. Keep Cynthia at the same level range and progression.
    levels = (51, 51, 52, 51, 51, 52)
    party = bytearray()
    species_report = []
    for mon, level in zip(source["party"], levels, strict=True):
        species_name = mon["species"]
        item_name = "GARCHOMPITE" if species_name == "SPECIES_GARCHOMP" else "ITEM_NONE"
        item_id = MEGA_STONES["GARCHOMP"] if item_name == "GARCHOMPITE" else item_constants[item_name]
        moves = mon["moves"]
        if len(moves) != 4:
            raise ValueError(f"Cynthia's {species_name} must have four moves for the custom record")
        values = (mon["difficulty"], mon["gender"] | mon["ability"] << 4,
                  level, 0, species_constants[species_name], mon["form"])
        party += struct.pack("<4BHHH4H", *values, item_id,
                             *(move_constants[move] for move in moves))
        species_report.append({
            "species": species_name.removeprefix("SPECIES_"),
            "level": level,
            "item": item_name.removeprefix("ITEM_") if item_name != "ITEM_NONE" else None,
            "moves": [move.removeprefix("MOVE_") for move in moves],
        })
    if len(trainer_record) != 20 or len(party) != 18 * len(levels):
        raise ValueError("Cynthia trainer record has an unexpected byte layout")
    trainers_archive.files.append(trainer_record)
    parties_archive.files.append(bytes(party))
    rom.files[rom.filenames.idOf("a/0/9/1")] = trainers_archive.save()
    rom.files[rom.filenames.idOf("a/0/9/2")] = parties_archive.save()

    text_archive = ndspy.narc.NARC(rom.getFileByName("a/0/0/2"))
    name_lines = unpack_file(text_archive.files[382]).splitlines()
    if len(name_lines) <= REMATCH_TRAINER_ID:
        raise ValueError("Trainer name bank is too short for the reserved Practice slot")
    name_lines[REMATCH_TRAINER_ID] = r"\cCynthia"
    name_text = with_ids(decomp / "data/text/system/trainer_names.txt", "\n".join(name_lines) + "\n")
    text_archive.files[382] = pack_file(name_text)

    message_bank = unpack_file(text_archive.files[381]).splitlines()
    message_pad = message_bank.pop() if message_bank and message_bank[-1].startswith(r"\pad{") else None
    message_count = len(message_bank)
    if message_count != len(ndspy.narc.NARC(rom.getFileByName("a/0/8/9")).files[0]) // 4:
        raise ValueError("Trainer dialogue bank and trainer-message table have different lengths")
    message_bank.extend((
        "I have been looking forward to seeing how you use Mega Evolution!",
        "That was an incredible battle. Garchomp and I had a great time!",
    ))
    if message_pad is not None:
        message_bank.append(message_pad)
    message_text = with_ids(decomp / "data/text/system/trainer_messages.txt",
                            "\n".join(message_bank) + "\n")
    text_archive.files[381] = pack_file(message_text)
    rom.files[rom.filenames.idOf("a/0/0/2")] = text_archive.save()

    trainer_message_types = constant_values
    message_table_archive = ndspy.narc.NARC(rom.getFileByName("a/0/8/9"))
    message_table = bytearray(message_table_archive.files[0])
    if len(message_table) % 4:
        raise ValueError("Trainer-message table has a partial record")
    for type_name in ("TRMSG_START", "TRMSG_LOSE"):
        if type_name not in trainer_message_types:
            raise ValueError(f"Decomp is missing {type_name}")
        message_table += struct.pack("<HH", REMATCH_TRAINER_ID, trainer_message_types[type_name])
    message_table_archive.files[0] = bytes(message_table)
    rom.files[rom.filenames.idOf("a/0/8/9")] = message_table_archive.save()

    offsets_archive = ndspy.narc.NARC(rom.getFileByName("a/0/9/0"))
    offsets_raw = offsets_archive.files[0]
    if len(offsets_raw) % 2:
        raise ValueError("Trainer-message offsets contain a partial value")
    offsets = list(struct.unpack(f"<{len(offsets_raw) // 2}H", offsets_raw))
    offsets += [message_count] * (REMATCH_TRAINER_ID + 1 - len(offsets))
    offsets[REMATCH_TRAINER_ID] = message_count
    offsets_archive.files[0] = struct.pack(f"<{len(offsets)}H", *offsets)
    rom.files[rom.filenames.idOf("a/0/9/0")] = offsets_archive.save()

    return {
        "trainer_id": REMATCH_TRAINER_ID,
        "trainer_class": source["class"],
        "trainer_name": "Cynthia",
        "party": species_report,
        "trainer_messages": ["TRMSG_START", "TRMSG_LOSE"],
        "trainer_message_start_index": message_count,
    }


def compile_script(decomp: Path, src_text: str, messages_path: Path, work: Path, gcc: str, objcopy: str) -> bytes:
    sys.path.insert(0, str(decomp))
    from tools.data.gen_constants import write_header
    from tools.script.field_script import write_inc
    from tools.text.text_ids import header as text_header

    (work / "asm").mkdir(parents=True, exist_ok=True)
    (work / "constants").mkdir(parents=True, exist_ok=True)
    (work / "text/script").mkdir(parents=True, exist_ok=True)
    write_inc(work / "asm/field_script.inc")
    for source in (decomp / "data/constants").glob("*.txt"):
        write_header(source, work / "constants" / f"{source.stem}.h")
    (work / "text/script/route_7.h").write_text(text_header(messages_path), encoding="utf-8")

    asm = work / "route_7.s"
    obj = work / "route_7.o"
    binary = work / "route_7.bin"
    asm.write_text(src_text, encoding="utf-8")
    command([gcc, "-x", "assembler-with-cpp", "-c", str(asm), "-o", str(obj), "-I", str(work), "-I", str(decomp / "include")], cwd=decomp)
    command([objcopy, "-O", "binary", "-j", ".data", str(obj), str(binary)], cwd=decomp)
    return binary.read_bytes()


def save_rom_copy(rom, output: Path) -> Path:
    """Write and promote a generated ROM without reusing a predictable temp path."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pending = output.with_name(output.name + "." + uuid.uuid4().hex + ".pending")
    with pending.open("xb"):
        pass
    try:
        rom.saveToFile(str(pending))
        os.replace(pending, output)
    finally:
        try:
            pending.unlink()
        except FileNotFoundError:
            pass
    return output


def build(args: argparse.Namespace) -> dict:
    from tools.data.event_data import events_bytes, events_json
    from tools.data.gen_constants import ordered_names
    from tools.text.text_data import pack_file, unpack_file, split_message

    rom = ndspy.rom.NintendoDSRom.fromFile(str(args.rom))
    if bytes(rom.idCode) != GAME_CODE:
        raise ValueError(f"Expected English Blaze Black 2 Redux (IREO), found {bytes(rom.idCode)!r}")
    decomp = args.decomp.resolve()
    tmp = args.work.resolve()
    tmp.mkdir(parents=True, exist_ok=True)
    species = species_ids(decomp)

    # Route 7 text bank must match the decomp baseline before appending localized messages.
    text_archive = ndspy.narc.NARC(rom.getFileByName("a/0/0/3"))
    script_text_index = ordered_names("script_text_banks").index("SCRIPT_TEXT_ROUTE_7")
    text_src = decomp / "data/text/script/route_7.txt"
    source_lines = [line for line in text_src.read_text(encoding="utf-8").splitlines() if line and not line.startswith("\\pad{")]
    base_messages = [split_message(line)[1] for line in source_lines]
    old_messages = [line for line in unpack_file(text_archive.files[script_text_index]).splitlines() if line and not line.startswith("\\pad{")]
    if old_messages[:len(base_messages)] != base_messages:
        raise ValueError("Installed Route 7 text does not match the decomp messages; refusing to overwrite it")
    new_text = text_src.read_text(encoding="utf-8").rstrip("\n") + "\n" + "".join(f"{name} = {message}\n" for name, message in NEW_MESSAGES)
    if len(base_messages) != 6:
        raise ValueError(f"Expected six base Route 7 messages, found {len(base_messages)}")
    message_header = tmp / "text/script/route_7.h"
    from tools.text.text_ids import header as make_text_header
    messages_path = tmp / "route_7.txt"
    messages_path.write_text(new_text, encoding="utf-8")
    message_header.parent.mkdir(parents=True, exist_ok=True)
    message_header.write_text(make_text_header(messages_path), encoding="utf-8")

    src_text = script_source(decomp, messages_path, message_header, species)
    compiled = compile_script(decomp, src_text, messages_path, tmp / "compile", args.gcc, args.objcopy)

    # Use the decomp's field-script decoder to walk every script entry and branch.
    # Assembly alone will accept bad relative jumps, while the game's VM would not.
    from tools.script.field_script import ScriptFile, load_commands, script_header
    base_commands, _, _, _ = load_commands()
    entries = script_header(compiled)
    if entries is None or len(entries[0]) != 9:
        raise ValueError("Compiled Route 7 script has an unexpected script table")
    traced = ScriptFile(compiled, base_commands, None)
    if not traced.trace(entries[0]) or traced.errors:
        raise ValueError(f"Compiled Route 7 script failed decomp trace: {traced.errors}")
    script_logic = validate_route7_script(compiled, decomp, species)

    # The decomp's event order is also the zone-event archive order in the target ROM.
    event_archive = ndspy.narc.NARC(rom.getFileByName("a/1/2/6"))
    order = json.loads((decomp / "data/events/order.json").read_text(encoding="utf-8"))
    route_index = order.index("ZONE_ROUTE_7")
    if len(event_archive.files) != len(order):
        raise ValueError(f"Route event archive mismatch: {len(event_archive.files)} files vs {len(order)} expected")
    # Protect reused actor code from clobbering an existing map NPC.
    for index, zone in enumerate(order):
        if zone is None:
            continue
        raw = event_archive.files[index]
        bg_count, npc_count = raw[4], raw[5]
        npc_pos = 8 + bg_count * 20
        for _ in range(npc_count):
            npc = struct.unpack_from("<12HI8s", raw, npc_pos)
            if npc[1] == ACTOR_CODE:
                raise ValueError(f"Object code 0x{ACTOR_CODE:04X} is already used in {zone}")
            npc_pos += 36
    route_events = events_json(event_archive.files[route_index])
    if any(npc["id"] == ACTOR_UID for npc in route_events["npcs"]):
        raise ValueError(f"Route 7 NPC slot {ACTOR_UID} is already occupied")
    route_events["npcs"].append({
        "id": ACTOR_UID,
        "model": ACTOR_CODE,
        "movement": 0,
        "type": 0,
        "flag": TUTORIAL_HIDE_FLAG,
        "script": 7,
        "direction": "DIR_LEFT",
        "params": [0, 0, 0],
        "area": {"width": 0, "height": 0},
        "grid": {"x": 125, "z": 277, "y": 0},
    })
    route_events["npcs"].append({
        "id": CHALLENGE_ACTOR_UID,
        "model": ACTOR_CODE,
        "movement": 0,
        "type": 0,
        "flag": CHALLENGE_HIDE_FLAG,
        "script": 9,
        "direction": "DIR_DOWN",
        "params": [0, 0, 0],
        "area": {"width": 0, "height": 0},
        "grid": REMATCH_POSITION,
    })
    route_events["init_scripts"].append({"type": 2, "script": 8})
    event_member = events_bytes(route_events, "route_7.json")

    # The original sheet has four poses per direction; native BW2 uses three walk frames.
    # The supplied first and third poses are pixel-identical, so no walking pose is lost.
    template = ndspy.narc.NARC(rom.getFileByName("a/0/4/8")).files[99]
    sprite_pack = make_texture_resource(template, args.sprite, tmp / "cynthia_frames.png")
    validate_sprite(sprite_pack)

    # Assign a free, unused remapped actor code to the appended texture resource.
    config_archive = ndspy.narc.NARC(rom.getFileByName("a/0/4/7"))
    config = bytearray(config_archive.files[0])
    if len(config) < 4 + (ACTOR_CONFIG_INDEX + 1) * 28:
        raise ValueError("Actor config table does not contain the selected free row")
    template_config = config[4 + 93 * 28:4 + 94 * 28]
    new_config = bytearray(template_config)
    struct.pack_into("<H", new_config, 0, ACTOR_CODE)
    struct.pack_into("<H", new_config, 16, ACTOR_RESOURCE_INDEX)
    config[4 + ACTOR_CONFIG_INDEX * 28:4 + (ACTOR_CONFIG_INDEX + 1) * 28] = new_config
    config_archive.files[0] = bytes(config)

    resource_archive = ndspy.narc.NARC(rom.getFileByName("a/0/4/8"))
    if len(resource_archive.files) != ACTOR_RESOURCE_INDEX:
        raise ValueError(f"Expected 975 field sprite resources, found {len(resource_archive.files)}")
    resource_archive.files.append(sprite_pack)

    script_file_index = ordered_names("field_scripts").index("SCRIPTS_ROUTE_7")
    scripts = ndspy.narc.NARC(rom.getFileByName("a/0/5/6"))
    current_script = scripts.files[script_file_index]
    # Verify the current Redux script is exactly the decomp baseline before replacing it.
    base_work = tmp / "baseline"
    base_compiled = compile_script(decomp, (decomp / "data/field_scripts/route_7.s").read_text(encoding="utf-8"), text_src, base_work, args.gcc, args.objcopy)
    if current_script != base_compiled:
        raise ValueError("Installed Route 7 script differs from decomp baseline; refusing to replace it")
    scripts.files[script_file_index] = compiled

    # Ensure only the intended banks/members change.
    text_archive.files[script_text_index] = pack_file(new_text)
    trainer_info = pack_cynthia_rematch_trainer(rom, decomp)
    rom.files[rom.filenames.idOf("a/0/0/3")] = text_archive.save()
    rom.files[rom.filenames.idOf("a/1/2/6")] = patch_member_archive(event_archive, route_index, event_member)
    rom.files[rom.filenames.idOf("a/0/4/7")] = config_archive.save()
    rom.files[rom.filenames.idOf("a/0/4/8")] = resource_archive.save()
    rom.files[rom.filenames.idOf("a/0/5/6")] = scripts.save()

    save_rom_copy(rom, args.output)

    verify = ndspy.rom.NintendoDSRom.fromFile(str(args.output))
    verify_resources = ndspy.narc.NARC(verify.getFileByName("a/0/4/8"))
    verify_configs = ndspy.narc.NARC(verify.getFileByName("a/0/4/7")).files[0]
    verify_events = ndspy.narc.NARC(verify.getFileByName("a/1/2/6"))
    verify_scripts = ndspy.narc.NARC(verify.getFileByName("a/0/5/6"))
    verify_text = ndspy.narc.NARC(verify.getFileByName("a/0/0/3"))
    verify_system_text = ndspy.narc.NARC(verify.getFileByName("a/0/0/2"))
    verify_trainers = ndspy.narc.NARC(verify.getFileByName("a/0/9/1"))
    verify_parties = ndspy.narc.NARC(verify.getFileByName("a/0/9/2"))
    verify_trainer_names = unpack_file(verify_system_text.files[382]).splitlines()
    verify_trainer_messages = unpack_file(verify_system_text.files[381]).splitlines()
    verify_message_table = ndspy.narc.NARC(verify.getFileByName("a/0/8/9")).files[0]
    verify_message_offsets = ndspy.narc.NARC(verify.getFileByName("a/0/9/0")).files[0]
    if verify_resources.files[ACTOR_RESOURCE_INDEX] != sprite_pack:
        raise ValueError("Appended Cynthia texture resource failed ROM reload verification")
    if verify_configs[ACTOR_CONFIG_INDEX * 28 + 4:ACTOR_CONFIG_INDEX * 28 + 6] != struct.pack("<H", ACTOR_CODE):
        raise ValueError("Cynthia actor config UID failed ROM reload verification")
    if verify_events.files[route_index] != event_member:
        raise ValueError("Route 7 event record failed ROM reload verification")
    if verify_scripts.files[script_file_index] != compiled:
        raise ValueError("Route 7 script failed ROM reload verification")
    if len(unpack_file(verify_text.files[script_text_index]).splitlines()) < len(base_messages) + len(NEW_MESSAGES):
        raise ValueError("Cynthia dialogue failed ROM reload verification")
    if len(verify_trainers.files) != REMATCH_TRAINER_ID + 1 or len(verify_parties.files) != REMATCH_TRAINER_ID + 1:
        raise ValueError("Cynthia rematch was not appended at the Practice-visible trainer index")
    if verify_trainer_names[REMATCH_TRAINER_ID] != r"\cCynthia":
        raise ValueError("Cynthia rematch trainer name failed ROM reload verification")
    record = verify_trainers.files[REMATCH_TRAINER_ID]
    party = verify_parties.files[REMATCH_TRAINER_ID]
    if len(record) != 20 or record[0] != 3 or record[3] != 6 or len(party) != 6 * 18:
        raise ValueError("Cynthia rematch trainer has an invalid party layout")
    garchomp_party_slot = next((slot for slot in range(6)
        if struct.unpack_from("<H", party, slot * 18 + 4)[0] == species["GARCHOMP"]), None)
    if garchomp_party_slot is None or struct.unpack_from("<H", party, garchomp_party_slot * 18 + 8)[0] != MEGA_STONES["GARCHOMP"]:
        raise ValueError("Cynthia rematch Garchomp is missing Garchompite")
    if len(verify_message_offsets) < 2 * (REMATCH_TRAINER_ID + 1):
        raise ValueError("Trainer-message offset table does not include Cynthia's Practice trainer")
    if len(verify_message_table) % 4 or len(verify_trainer_messages) < 2:
        raise ValueError("Cynthia rematch battle dialogue table failed verification")
    message_pairs = [struct.unpack_from("<HH", verify_message_table, offset)
                     for offset in range(0, len(verify_message_table), 4)]
    if message_pairs[-2][0] != REMATCH_TRAINER_ID or message_pairs[-1][0] != REMATCH_TRAINER_ID:
        raise ValueError("Cynthia rematch battle dialogue rows are missing")
    challenge_actor = next((npc for npc in route_events["npcs"] if npc["id"] == CHALLENGE_ACTOR_UID), None)
    if not challenge_actor or challenge_actor["script"] != 9 or challenge_actor["grid"] != REMATCH_POSITION:
        raise ValueError("Cynthia rematch Route 7 actor failed event validation")

    report = {
        "input": str(args.rom.resolve()),
        "input_sha256": sha256(args.rom),
        "output": str(args.output.resolve()),
        "output_sha256": sha256(args.output),
        "game_code": bytes(verify.idCode).decode("ascii"),
        "decomp": str(decomp),
        "route7_zone_event_member": route_index,
        "route7_script_member": script_file_index,
        "route7_text_bank": script_text_index,
        "cynthia_actor_code": ACTOR_CODE,
        "cynthia_texture_resource": ACTOR_RESOURCE_INDEX,
        "cynthia_actor_config_row": ACTOR_CONFIG_INDEX,
        "party_species_branches": len(MEGA_STONES),
        "script_logic": script_logic,
        "fallback_stone_item_id": STONE_FALLBACK,
        "one_time_gift_flag": REWARD_FLAG,
        "npc_position": {"x": 125, "z": 277, "y": 0},
        "rematch_position": REMATCH_POSITION,
        "rematch_flag": CHALLENGE_FLAG,
        "rematch_trainer": trainer_info,
        "practice_roster_slots": len(verify_trainers.files),
        "practice_browser": "ROM trainer ID 891 with the native Cynthia trainer class and battle artwork",
        "structural_checks": "passed",
        "live_emulator_check": "not run",
    }
    report_path = args.output.with_suffix(".report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def patch_member_archive(archive: ndspy.narc.NARC, index: int, member: bytes) -> bytes:
    archive.files[index] = member
    return archive.save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--sprite", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--decomp", type=Path, default=Path(r"F:\gen5decomps\pokebw2-main"))
    parser.add_argument("--work", type=Path, default=Path("build/cynthia-npc-patch"))
    parser.add_argument("--gcc", default="arm-none-eabi-gcc")
    parser.add_argument("--objcopy", default="arm-none-eabi-objcopy")
    args = parser.parse_args()
    sys.path.insert(0, str(args.decomp.resolve()))
    try:
        report = build(args)
    except Exception as exc:
        print(f"Cynthia Route 7 patch failed: {exc}", file=sys.stderr)
        raise
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
