#!/usr/bin/env python3
"""Audit the Lake Trio encounter hints against a supported English B2 Redux ROM.

This is a read-only ROM inspection tool. It reports raw-script and event-table
evidence; it does not patch a ROM or claim that an in-game researcher exists.

Example:
  python maintenance-tools/tools/audit_legendary_researcher.py \
    --rom "path/to/Blaze Black 2 Redux Complete v1.4.1.nds" \
    --decomp "F:/gen5decomps/pokebw2-main"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import ndspy.narc
import ndspy.rom


HINTS = (
    ("Uxie", 480, "ZONE_NACRENE_CITY", 0x0396, 6, 0x4116, 5),
    ("Mesprit", 481, "ZONE_CELESTIAL_TOWER", 0x0397, 4, 0x4117, 3),
    ("Azelf", 482, "ZONE_ROUTE_23", 0x0398, 3, 0x4118, 2),
)
CAVE_WORK = {0x4115: 4, 0x4116: 1, 0x4117: 1, 0x4118: 1}
HALL_OF_FAME_FLAG = 0x0960
RESEARCHER_CANDIDATE = (778, 744)
SUPPORTED_ROM_SHA256 = {
    "332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a",  # clean Redux 1.4.1
    "c34498dc807a83e3d5a5c85a341464c24f56a1ed515db6cfc7ef4e2a71dc3df7",  # tested Cynthia-patched copy
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def event_flag(value: int | str) -> int:
    if isinstance(value, int):
        return value
    if value.startswith("EVENT_FLAG_0x"):
        return int(value.rsplit("x", 1)[1], 16)
    raise ValueError(f"Expected a raw event flag, got {value!r}")


def audit(rom_path: Path, decomp: Path) -> dict:
    sys.path[:0] = [str(decomp.resolve()), str((decomp / "tools/script").resolve()),
                    str((decomp / "tools/data").resolve())]
    from tools.data.event_data import events_json
    from tools.data.gen_constants import ordered_names
    from tools.data.zone_data import HEADER
    from tools.script.field_script import (ScriptFile, load_commands,
                                           plugin_of_files, script_header)

    rom = ndspy.rom.NintendoDSRom.fromFile(str(rom_path))
    if bytes(rom.idCode) != b"IREO":
        raise ValueError(f"Expected English Blaze Black 2 Redux (IREO), found {bytes(rom.idCode)!r}")
    input_hash = sha256(rom_path)
    if input_hash not in SUPPORTED_ROM_SHA256:
        raise ValueError("ROM SHA-256 is not one of the two locally reviewed Redux 1.4.1 inputs")

    zone_headers = ndspy.narc.NARC(rom.getFileByName("a/0/1/2")).files[0]
    script_files = ndspy.narc.NARC(rom.getFileByName("a/0/5/6")).files
    event_files = ndspy.narc.NARC(rom.getFileByName("a/1/2/6")).files
    zone_order = ordered_names("zones")
    event_order = json.loads((decomp / "data/events/order.json").read_text(encoding="utf-8"))
    base_commands, plugins, plugin_zones, global_scripts = load_commands()
    plugin_map = plugin_of_files(script_files, zone_headers, base_commands,
                                 plugins, plugin_zones, global_scripts)

    def decoded_script(file_index: int):
        data = script_files[file_index]
        header = script_header(data)
        if header is None:
            raise ValueError(f"Field-script member {file_index} has no valid script table")
        plugin_number = plugin_map.get(file_index, (None, None))[0]
        script = ScriptFile(data, base_commands, plugins.get(plugin_number))
        if not script.trace(header[0]):
            raise ValueError(f"Field-script member {file_index} has no traceable entry point")
        return script

    results = []
    prerequisite_vars = set()
    for species_name, species_id, zone_name, spawn_flag, npc_script, work_var, trigger_script in HINTS:
        zone_index = zone_order.index(zone_name)
        header = HEADER.unpack_from(zone_headers, zone_index * HEADER.size)
        script_index, matrix_index = header[4], header[3]
        script = decoded_script(script_index)
        battles = [
            {"offset": offset, "command": cmd.name, "args": args}
            for offset, (cmd, args, _) in script.instructions.items()
            if cmd.name in ("CallWildBattle", "CallWildBattleEx")
            and args and args[0] == species_id
        ]
        exact = [battle for battle in battles
                 if battle["command"] == "CallWildBattle" and battle["args"] == [species_id, 65, 1]]
        if len(exact) != 1:
            raise ValueError(f"Expected one level-65 {species_name} field encounter in {zone_name}; found {battles}")

        event_index = event_order.index(zone_name)
        events = events_json(event_files[event_index])
        actors = [actor for actor in events["npcs"]
                  if event_flag(actor["flag"]) == spawn_flag and actor["script"] == npc_script]
        triggers = [trigger for trigger in events["triggers"]
                    if trigger["script"] == trigger_script
                    and trigger["var"] == f"EVENT_WORK_0x{work_var:04x}"
                    and trigger["value"] == 1]
        if len(actors) != 1 or len(triggers) != 1:
            raise ValueError(f"{species_name} actor/trigger gate did not match the reviewed event table")
        prerequisite_vars.add(work_var)
        results.append({
            "species": species_name,
            "location": zone_name.removeprefix("ZONE_").replace("_", " ").title(),
            "level": 65,
            "zoneId": zone_index,
            "zoneEventMember": event_index,
            "fieldScriptMember": script_index,
            "mapMatrixId": matrix_index,
            "battleCommandOffset": exact[0]["offset"],
            "battleArgs": exact[0]["args"],
            "spawnFlag": f"0x{spawn_flag:04X}",
            "npcScript": npc_script,
            "trigger": {
                "script": trigger_script,
                "work": f"0x{work_var:04X}",
                "value": 1,
                "grid": triggers[0]["grid"],
            },
            "npcGrid": actors[0]["grid"],
        })

    cave_index = HEADER.unpack_from(zone_headers, zone_order.index("ZONE_CAVE_OF_BEING") * HEADER.size)[4]
    cave_script = decoded_script(cave_index)
    cave_work_steps = [
        (args[0], args[1])
        for _, (cmd, args, _) in cave_script.instructions.items()
        if cmd.name == "WorkSetConst" and len(args) == 2 and args[0] in CAVE_WORK
    ]
    if any((var, value) not in cave_work_steps for var, value in CAVE_WORK.items()):
        raise ValueError(f"Cave of Being does not establish the expected trio gates: {cave_work_steps}")

    nuvema_index = zone_order.index("ZONE_NUVEMA_TOWN")
    nuvema_header = HEADER.unpack_from(zone_headers, nuvema_index * HEADER.size)
    nuvema_script = decoded_script(nuvema_header[4])
    league_flag_reads = [offset for offset, (cmd, args, _) in nuvema_script.instructions.items()
                         if cmd.name == "VMStackPushFlag" and args == [HALL_OF_FAME_FLAG]]
    if not league_flag_reads:
        raise ValueError("Nuvema's existing postgame script no longer checks Hall of Fame flag 0x0960")
    nuvema_event_index = event_order.index("ZONE_NUVEMA_TOWN")
    nuvema_events = events_json(event_files[nuvema_event_index])
    occupied = [actor["grid"] for actor in nuvema_events["npcs"]]
    if any((point["x"], point["z"]) == RESEARCHER_CANDIDATE for point in occupied):
        raise ValueError("The candidate Nuvema tile has acquired an NPC")

    return {
        "rom": str(rom_path.resolve()),
        "romSha256": input_hash,
        "gameCode": bytes(rom.idCode).decode("ascii"),
        "decompPath": str(decomp.resolve()),
        "decompRevision": "local extraction; no Git metadata; source provenance not authenticated",
        "scriptDecodeWarnings": {
            "nacreneCity": str(decoded_script(32).errors),
            "celestialTower": str(decoded_script(684).errors),
            "route23": str(decoded_script(950).errors),
        },
        "lakeTrioPrerequisite": {
            "zone": "Cave of Being",
            "fieldScriptMember": cave_index,
            "workValuesSet": [
                {"work": f"0x{var:04X}", "value": value}
                for var, value in cave_work_steps
            ],
            "allEncounterGatesMatch": prerequisite_vars == {0x4116, 0x4117, 0x4118},
        },
        "leagueGateEvidence": {
            "zone": "Nuvema Town",
            "fieldScriptMember": nuvema_header[4],
            "hallOfFameFlag": f"0x{HALL_OF_FAME_FLAG:04X}",
            "readOffsets": league_flag_reads,
            "nuvemaEventMember": nuvema_event_index,
            "candidateNpcGrid": {"x": RESEARCHER_CANDIDATE[0], "z": RESEARCHER_CANDIDATE[1]},
            "candidateTileUnoccupied": True,
            "candidateTileCollisionVerified": False,
        },
        "encounters": results,
        "scope": "Read-only source/artifact evidence; no NPC patch generated and no gameplay claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--decomp", type=Path, default=Path(r"F:\gen5decomps\pokebw2-main"))
    args = parser.parse_args()
    print(json.dumps(audit(args.rom, args.decomp), indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Legendary Researcher audit failed: {error}", file=sys.stderr)
        raise
