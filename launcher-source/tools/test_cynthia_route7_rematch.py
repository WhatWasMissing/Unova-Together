#!/usr/bin/env python3
"""Check that the Cynthia Route 7 rematch is readable by the Practice catalog."""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import ndspy.narc
import ndspy.rom
from build_cynthia_route7 import species_ids, validate_route7_script


TRAINER_ID = 891
GARCHOMPITE = 526
REWARD_FLAG = "EVENT_FLAG_0x09a1"
REMATCH_FLAG = "EVENT_FLAG_0x09a2"
TUTORIAL_HIDE_FLAG = "EVENT_FLAG_0x09a3"
CHALLENGE_HIDE_FLAG = "EVENT_FLAG_0x09a4"
REMATCH_POSITION = {"x": 111, "z": 244, "y": 0}
SKYLA_TRAINER_ID = 155
SKYLA_LEVELS = [51, 51, 51, 51, 52, 51]
EXPECTED_LEVELS = [51, 51, 52, 51, 51, 52]


def verify(rom_path: Path, decomp: Path) -> dict:
    sys.path.insert(0, str(decomp.resolve()))
    from tools.data.event_data import events_json
    from tools.data.gen_constants import load as load_constants, ordered_names
    from tools.text.text_data import unpack_file

    rom = ndspy.rom.NintendoDSRom.fromFile(str(rom_path))
    if bytes(rom.idCode) != b"IREO":
        raise ValueError("Practice test requires an English Blaze Black 2 Redux game file")
    trainer_records = ndspy.narc.NARC(rom.getFileByName("a/0/9/1")).files
    parties = ndspy.narc.NARC(rom.getFileByName("a/0/9/2")).files
    names = unpack_file(ndspy.narc.NARC(rom.getFileByName("a/0/0/2")).files[382]).splitlines()

    skyla_record = trainer_records[SKYLA_TRAINER_ID]
    skyla_kind = skyla_record[0] & 3
    skyla_stride = 8 + (2 if skyla_kind & 2 else 0) + (8 if skyla_kind & 1 else 0)
    skyla_party = parties[SKYLA_TRAINER_ID]
    skyla_levels = [skyla_party[index * skyla_stride + 2] for index in range(skyla_record[3])]
    if names[SKYLA_TRAINER_ID] != r"\cSkyla" or skyla_levels != SKYLA_LEVELS:
        raise ValueError("Redux Skyla's reference team changed; refresh Cynthia's level comparison")

    # This mirrors Gen5Menu::npcTrainers/trainerSummary eligibility: the ID is
    # in range, the record has 1-6 party members, and each level/species is valid.
    limit = min(1024, len(trainer_records), len(parties))
    if not TRAINER_ID < limit or not TRAINER_ID < len(names):
        raise ValueError("The rematch trainer is outside the Practice catalog's ROM bounds")
    record = trainer_records[TRAINER_ID]
    if len(record) < 18 or record[3] != 6:
        raise ValueError("Practice cannot read Cynthia's six-Pokémon party")
    if names[TRAINER_ID] != r"\cCynthia":
        raise ValueError("Practice will not display Cynthia's trainer name")

    constants = load_constants("species")
    class_id = load_constants("trainer_classes")["TRAINER_CLASS_PKMN_TRAINER_CYNTHIA"]
    class_id_from_record = struct.unpack_from("<H", record, 1)[0]
    if class_id_from_record != class_id:
        raise ValueError("Cynthia's rematch is not using her native trainer class")
    party = parties[TRAINER_ID]
    kind = record[0] & 3
    stride = 8 + (2 if kind & 2 else 0) + (8 if kind & 1 else 0)
    if kind != 3 or len(party) != 6 * stride:
        raise ValueError("Cynthia's Practice party has an invalid item/move layout")

    species = []
    levels = []
    garchomp_item = None
    for index in range(6):
        offset = index * stride
        level = party[offset + 2]
        mon_species, form = struct.unpack_from("<HH", party, offset + 4)
        held_item = struct.unpack_from("<H", party, offset + 8)[0]
        if not level or level > 100 or not mon_species:
            raise ValueError(f"Practice rejected team member {index}")
        levels.append(level)
        species.append(mon_species)
        if mon_species == constants["SPECIES_GARCHOMP"]:
            garchomp_item = held_item
    expected_species = [constants[name] for name in (
        "SPECIES_SPIRITOMB", "SPECIES_MILOTIC", "SPECIES_TOGEKISS",
        "SPECIES_LUCARIO", "SPECIES_GLACEON", "SPECIES_GARCHOMP",
    )]
    if species != expected_species or levels != EXPECTED_LEVELS:
        raise ValueError("Cynthia's Practice roster or Skyla-matched levels changed")
    if any(abs(cynthia - skyla) > 1 for cynthia, skyla in zip(levels, skyla_levels, strict=True)):
        raise ValueError("Cynthia's team is no longer close to Redux Skyla's level curve")
    if garchomp_item != GARCHOMPITE:
        raise ValueError("Cynthia's Garchomp is missing Garchompite")

    order = json.loads((decomp / "data/events/order.json").read_text(encoding="utf-8"))
    route_index = order.index("ZONE_ROUTE_7")
    event_archive = ndspy.narc.NARC(rom.getFileByName("a/1/2/6"))
    events = events_json(event_archive.files[route_index])
    actor = next((npc for npc in events["npcs"] if npc["id"] == 18), None)
    if not actor or actor["script"] != 9 or actor["grid"] != REMATCH_POSITION:
        raise ValueError("Cynthia's rematch NPC is missing from northern Route 7")
    tutorial = next((npc for npc in events["npcs"] if npc["id"] == 17), None)
    if not tutorial or tutorial["script"] != 7 or tutorial["type"] != 0:
        raise ValueError("Cynthia's lesson NPC is missing or is not a talkable map actor")
    if actor["type"] != 0:
        raise ValueError("Cynthia's rematch NPC is not a talkable map actor")
    if tutorial["flag"] != TUTORIAL_HIDE_FLAG or actor["flag"] != CHALLENGE_HIDE_FLAG:
        raise ValueError("Cynthia's Route 7 actors are missing their spawn flags")
    if not any(init["type"] == 2 and init.get("script") == 8 for init in events["init_scripts"]):
        raise ValueError("Route 7 is missing the pre-spawn progress initializer")
    script_index = ordered_names("field_scripts").index("SCRIPTS_ROUTE_7")
    route_scripts = ndspy.narc.NARC(rom.getFileByName("a/0/5/6"))
    script_logic = validate_route7_script(route_scripts.files[script_index], decomp, species_ids(decomp))
    for init in events["init_scripts"]:
        if init["type"] != 1:
            continue
        for condition in init.get("conditions", []):
            var = condition.get("var", 0)
            if (isinstance(var, int) and var < 0x4000) or (
                isinstance(var, str) and var.startswith("EVENT_FLAG_")
            ):
                raise ValueError("A Route 7 type-1 condition uses a flag ID instead of an event-work ID")
    flag_ids = load_constants("flags")
    if any(flag_ids[flag] >= 0x0BF8
           for flag in (REWARD_FLAG, REMATCH_FLAG, TUTORIAL_HIDE_FLAG, CHALLENGE_HIDE_FLAG)):
        raise ValueError("Cynthia's event uses flags outside the saved event-flag table")

    return {
        "rom": str(rom_path.resolve()),
        "practice_catalog_id": TRAINER_ID,
        "practice_name": "Cynthia",
        "trainer_class": "TRAINER_CLASS_PKMN_TRAINER_CYNTHIA",
        "team_species": ["Spiritomb", "Milotic", "Togekiss", "Lucario", "Glaceon", "Garchomp"],
        "levels": levels,
        "redux_skyla_levels": skyla_levels,
        "garchomp_held_item": "Garchompite",
        "route7_rematch_position": REMATCH_POSITION,
        "route7_script_logic": script_logic,
        "catalog_checks": "passed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--decomp", type=Path, default=Path(r"F:\gen5decomps\pokebw2-main"))
    args = parser.parse_args()
    print(json.dumps(verify(args.rom, args.decomp), indent=2))


if __name__ == "__main__":
    main()
