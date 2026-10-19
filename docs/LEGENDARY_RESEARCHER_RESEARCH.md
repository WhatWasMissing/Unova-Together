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

The proposed Nuvema position is stored as world grid `(778, 744)`, which resolves to map-matrix cell `(24, 23)` and local tile `(10, 8)` in `MAP_MODEL_OVERWORLD_2_MAP24_23`. The supported test ROM identifies Nuvema as zone ID `389` and event archive member `566`; `389` is the zone ID, not the event member. The local map renderer shows the candidate on the upper path, and the event table contains no NPC on that exact tile.

The new read-only audit checks the actual model terrain at that position. On the Cynthia-patched Redux test ROM, it finds one valid terrain plane with tile type `0x00800000` (class `0x0000`, flags `0x0080`). BW2's `MapTile_BlocksCollision` returns blocked for invalid tiles or when tile flags bit 0 is set, so this terrain cell does not block walking. The world-to-map conversion and collision predicate were cross-checked against the upstream BW2 decomp at commit [`81eea95`](https://github.com/fuddlesworth/pokebw2/tree/81eea95ee66e9ab41dedf5ead08ff1d3222cbef5). [`InitActorZoneNPCGridPositon`](https://github.com/fuddlesworth/pokebw2/blob/81eea95ee66e9ab41dedf5ead08ff1d3222cbef5/src/ov012/fldmmdl.c#L399-L430) shows how event coordinates become world positions, [`GetChunkCoordOfWorld`](https://github.com/fuddlesworth/pokebw2/blob/81eea95ee66e9ab41dedf5ead08ff1d3222cbef5/src/ov012/map_matrix.c#L118-L120) resolves the 32-tile matrix cell, and [`MapTile_BlocksCollision`](https://github.com/fuddlesworth/pokebw2/blob/81eea95ee66e9ab41dedf5ead08ff1d3222cbef5/src/ov036/map_attr.c#L29-L51) checks the terrain flags. This is static terrain evidence only: it does not verify prop collision, live map alignment, map-entry visibility, or that a new actor can be interacted with in-game.

Frost 5.0.1 parsed and exported the ROM without changing the input, but its map editor did not open in the inspection attempt. The map-editor and gameplay checks remain **BLOCKED / NOT RUN**. **No NPC, event script, text, or ROM patch has been added.** Implementation remains deferred until a compatible map-editor view or live-game test confirms the position and interaction path. The post-League gate and repeatable dialogue will also need artifact and gameplay checks, with the original ROM and save preserved.

### Additional map-editor evaluation

The official [SwissArmyKnife repository](https://github.com/PlatinumMaster/SwissArmyKnife) advertises B2W2 map-container, script/text, and zone-entity editing, including NPCs. Its README limits full support to retail Black 2/White 2, so Redux compatibility was not assumed. I checked out SwissArmyKnife `08c997485826f8fcd1e0dffbcafb205d1b32726b`, BeaterLibrary `a2a5267898361ae1e654edfe0cd82b1355ea1c0a`, Hotswap `70aacacc856dd5f1e383a0a7afb781f94c1802d4`, and NitroSharp `e1596712480970da755f9dbad7ba37b3c4cb5da5` from their official GitHub repositories. The local .NET 10.0.400 SDK restored dependencies, but the editor build stopped with 21 compile errors: the application expects `BeaterLibrary.GameInfo` and related types that are absent from the checked-out BeaterLibrary tree. No editor binary or map view was produced. The tool source stayed in a disposable local investigation folder and was not copied into this repository.

This second editor path therefore does not clear the placement gate. The candidate coordinate is still supported by ROM event-table and terrain/collision inspection only; prop collision, live map alignment, NPC interaction, and in-game post-League visibility remain unverified. No event patch should be created from the current evidence.

## Reproduce the audit

Run the production terrain-decoding tests with:

```powershell
python maintenance-tools/tools/test_legendary_researcher.py -v
```

All five map-position, collision-flag, invalid-tile, and bounds tests passed on the development PC.

Run this against a legally held disposable copy; it reads the ROM and only prints JSON:

```powershell
python maintenance-tools/tools/audit_legendary_researcher.py `
  --rom 'path\to\Blaze Black 2 Redux Complete v1.4.1.nds' `
  --decomp 'F:\gen5decomps\pokebw2-main'
```

The audit passed on two isolated ROM copies: the clean Redux input (SHA-256 `332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a`) and its Cynthia-patched target (SHA-256 `c34498dc807a83e3d5a5c85a341464c24f56a1ed515db6cfc7ef4e2a71dc3df7`). Encounter, unlock, and candidate terrain evidence matched between them. A negative-control Unova Together variant with a different SHA-256 was rejected. The audit output is ROM- and decomp-revision-specific; it does not establish behavior in the emulator.
