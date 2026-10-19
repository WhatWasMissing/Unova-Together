# Postgame Legendary Researcher research

The proposed guide is **not yet in the game**. This page records encounter data that was checked against a local English Blaze Black 2 Redux Complete v1.4.1 game-file copy and identifies what still prevents a safe event patch.

## Verified Lake Trio hints

The read-only audit tool checks the ROM's field-script archive (`a/0/5/6`), zone headers (`a/0/1/2`), and map event archive (`a/1/2/6`). For all three entries, it verifies a level-65 scripted encounter, the encounter NPC's visibility flag, and a map trigger that requires the corresponding work value to equal `1`.

| Pokémon | Verified location | Encounter | Unlock evidence |
| --- | --- | --- | --- |
| Uxie | Nacrene City | Level 65; field-script member 32, command at `0x02BF`; event member 16; spawn flag `0x0396` | Trigger requires work `0x4116 = 1`; Cave of Being script member 1034 sets it after the trio's departure sequence. |
| Mesprit | Celestial Tower | Level 65; field-script member 684, command at `0x0301`; event member 511; spawn flag `0x0397` | Trigger requires work `0x4117 = 1`; Cave of Being script member 1034 sets it after the trio's departure sequence. |
| Azelf | Route 23 | Level 65; field-script member 950, command at `0x011D`; event member 563; spawn flag `0x0398` | Trigger requires work `0x4118 = 1`; Cave of Being script member 1034 sets it after the trio's departure sequence. |

These are suitable hints for a postgame guide, phrased as locations and prerequisites rather than copied game dialogue. The three battle commands and event gates were decoded directly from the ROM. The local decomp tree helped decode them, but is a partial extraction without Git metadata; it is not treated as authenticated upstream source.

The parser reports two undecodable command sites in the Celestial Tower script archive member. The Mesprit encounter command and its matching event trigger were decoded, but those warnings leave the rest of that script's control flow unverified.

The existing Nuvema Town script also reads Hall of Fame flag `0x0960` (field-script member 778). The flag is set in field-script member 1242 at command offset `0x06DD`. This supports the proposed post-League gate, but does not itself implement or test a new NPC.

## Placement and implementation status

The Nuvema map renderer shows an unoccupied candidate at grid `(778, 744)` on the upper path, and the current event table has no NPC at that coordinate. The model-0 render and parser round-trip do not establish the game's collision behavior or prove an actor will spawn correctly on that tile. The available Frost check parsed and exported the ROM but did not open its map editor. **No NPC, event script, text, or ROM patch has been added.**

Before implementation, the candidate must be checked in a compatible map editor or exercised in the game so its collision, visual alignment, map-entry visibility, and interaction from an adjacent tile are confirmed. The post-League gate and repeatable dialogue also need artifact and gameplay checks, with the original ROM and save preserved.

## Reproduce the audit

Run this against a legally held disposable copy; it reads the ROM and only prints JSON:

```powershell
python maintenance-tools/tools/audit_legendary_researcher.py `
  --rom 'path\to\Blaze Black 2 Redux Complete v1.4.1.nds' `
  --decomp 'F:\gen5decomps\pokebw2-main'
```

The audit passed on two isolated ROM copies: the clean Redux input (SHA-256 `332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a`) and its Cynthia-patched target (SHA-256 `c34498dc807a83e3d5a5c85a341464c24f56a1ed515db6cfc7ef4e2a71dc3df7`). The encounter and unlock evidence matched between them. A negative-control Unova Together variant with a different SHA-256 was rejected. The audit output is ROM- and decomp-revision-specific; it does not establish behavior in the emulator.
