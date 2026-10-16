# Release checks — 1.0.30

## Verified

- The follower regression passes. It checks the one-tile HeartGold trail plus a small 1/8-tile spacing cushion, smooth 60-fps movement between 50-ms samples, corner following, stop transitions, four facing directions and walk-cycle continuity.
- The full configured CTest suite passes 11/11, and the Windows Qt emulator frontend rebuilds successfully. The executable file and product versions are 1.0.30.
- The cross-area Soaring worker passes all 11 Python tests. It only joins outdoor areas when reciprocal, fly-enabled warps establish a consistent position.
- ROM analysis and scene exports on Black 2 and Black 2 Redux confirm 13 linked outdoor matrices. Renderer and landing behavior still need a live in-game check; see [Soaring design](SOARING_DESIGN.md).
- The release packager verifies ZIP integrity, source/runtime version agreement, the Windows Qt platform plug-in, saved controls, and exclusion of ROMs, saves, firmware and RAM dumps. The published SHA-256 sidecar lists each download's checksum.

## Please test in-game

Turn on Soaring under **Settings → Experimental features → Soaring flight**, then open **Unova → Pokémon → Take flight**. Try flying between routes and towns, land beside clear ground, and confirm the game returns to the expected map and tile. Mega Salamence's full-frame animation is also included; equip Salamencite and hold **L + R** while choosing a move to confirm it animates and stays centered.
