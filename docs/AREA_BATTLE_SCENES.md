# Area battle scenery

Enable **Settings → Area battle scenery (experimental)** in the launcher, then launch your game. The first launch generates scenery from your own English Black 2 ROM. Later launches reuse its local cache. Disable the option to use the original backgrounds. This option does not edit ROM or save files.

The emulator chooses the area in the overworld and holds that choice through the battle. Each scene uses the area's floor, wall/fence and detail textures in a native 3D arena, with scenery around all four sides for the rotating camera. Original Pokémon platforms, move effects, battle logic and save handling remain game-owned. Incompatible assets fall back to the original background.

## Coverage

The local Redux Complete v1.4.1 / Unova Together ROM has **617 map headers** referencing **137 area groups**. All 137 groups export successfully. The overlay replaces the 35 standard `batt_bg` resources used by ordinary environments. Each scene has 44 quads and fits the existing resource slots. Shared area groups share scenery: these are procedural arenas, not exact map reconstructions.

Pokéstar's scripted cinematic resources are retained. Special scenes outside standard backgrounds, seasonal/time lighting and animated water are not implemented. Not every battle screen has been playtested.

## Verification

All 137 generated models were parsed and checked against every replacement slot. Focused tests cover texture selection, bounds, refusing to overwrite outputs, and partial/overlapping cartridge reads. A private two-emulator Cheren co-op battle displayed generated scenery on both instances at approximately 60 / 59 FPS. Both instances completed the battle and returned to a ready state, with their native allocations released. Other environments have not all been playtested. Tests use copied saves and muted instances.

Generated ROM graphics remain in the local cache and are not distributed. Implementation by **mvq1303 / WhatWasMissing**, GPL-3.0-or-later. The vendored NSBMD writer retains its MIT notice; ndspy and Pillow licenses accompany the launcher.

Developer tools: `build_area_battle_scene.py`, `build_area_battle_catalog.py`, `test_area_battle_scene.py`, and `check_rom_asset_overlay.cpp` in `tools`.
