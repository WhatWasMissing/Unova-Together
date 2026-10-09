# Unova Together beta 0.3.7

Save in game and close the emulator. In the launcher, open **Updates → Check for updates**, install **0.3.7**, and restart. Update every player: older clients can still send incorrect map IDs.

## Fixes

- Outdoor map tracking now uses the zone under your player. Cached entry IDs could previously leave nearby teammates on different maps.
- Fixed the confirmed tracking failure that left positions unresolved and battle status stuck after returning to the field.
- Stock menus preserve the current zone instead of reverting to the map entered earlier.
- Same-map labels remain available during battles and field rebuilding when the location is verified.
- Teammates can remain visible behind the custom in-game menus when the live field camera is valid. Party and summary screens still hide the gameplay overlay.

## Checks and limits

Both reported RAM captures now resolve to the same zone with valid adjacent positions and clear a stale battle flag. The complete outdoor zone grid matches the loaded ROM. Recorded battle entry/exit, stale menu-map, invalid-grid, sprite motion/rendering, native menu and 12 relay tests pass.

These checks do not prove that all multiplayer desyncs are eliminated. A fresh multi-device replay of the reported incident is still needed. Co-op EXP remains disabled, and connection, trainer-event and cleanup limitations remain in **Setup → Known issues**. Keep C-Gear wireless and fast-forward off during co-op.

Download **Unova-Together.exe** for the bundled launcher and emulator, or use the portable ZIP. Matching GPL source and SHA-256 checksums are included. ROMs, saves and firmware are not included.

Made by **mvq1303 / WhatWasMissing**, built on melonDS.
