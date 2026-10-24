# Ordinary battle scenery context — 2026-10-24

## Defect and fix

Wild and ordinary trainer battles switched `OverworldTracker::Sample()` to `status="In battle"` before the scenery hook sampled the game. `AreaBattleScenes::update()` accepted only an `Experimental match` with an owned field position, so it returned during battle and kept using the native background. The tracker now carries the last verified map, field zone, and world coordinates with an `areaFieldContext` marker while preserving the public battle status and leaving `fieldPositionOwned` false. The scenery hook accepts that context only when battle ownership is known and the location passes bounds checks. Invalid or missing battle context clears an existing asset patch and falls back to original scenery.

The change is derived from the official 2.0.34 source archive, SHA-256 `de592d351d8e2ea24f8b79769bf4d7ebdb6445e1ebc23183c95c0421902ac0bb`. The reproducible patch and file hashes are in `maintenance-tools/patches/area-battle-scenery-context.json`.

## Verification

- **PASS — source/unit:** `python -m unittest test_battle_scenery_context_patch -v` passed 5/5 checks, including applying the patch to the exact source archive and matching every changed output file hash.
- **PASS — focused native checks:** `check_battle_scenery_context.cpp` compiled with C++17, `-Wall -Wextra -Werror`; its ten verified, retained, invalid, unknown, and catalog-state cases passed.
- **PASS — build:** the complete Windows `melonDS` target compiled from the matching 2.0.34 source with the 2.0.36 changes. Build configuration and executable hash are recorded in the release verification document.
- **NOT RUN — gameplay:** the active desktop game session was left untouched; the MCP reports no isolated emulator session. No new emulator was launched, and no ROM, save, launcher profile, or installed runtime was changed.
- **Dialogue check:** custom dialogue art remains an opt-in ROM patch. The main profile ROM is intentionally unchanged, so it shows stock dialogue. Follow `docs/DIALOGUE_ART_TESTING.md` to build a separate ROM and test it with a copied save in a muted isolated session. The prior exact-build live renderer check remains scoped to its recorded Redux ROM and NPC.

## Reproduction

From `maintenance-tools/tools`, with the official 2.0.34 source archive available:

```powershell
$env:UNOVA_BATTLE_SCENERY_BASELINE_SOURCE_ZIP = "<path to Unova-Together-2.0.34-Source.zip>"
python -m unittest test_battle_scenery_context_patch -v
```

Compile the focused native check with the same C++17 flags shown above. For the complete emulator build, see `CMakeCache.txt` from the release build input or use the Windows UCRT64 CMake configuration documented in `skills.md`.
