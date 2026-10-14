# Unova Together 1.0.13 — Launcher update recovery

This release fixes launcher update blocking and duplicate-game state after an update.

- Updates and repairs install into separate versioned folders, so they can download and stage while a game is open. The running build and its save files remain in place.
- The launcher detects `melonDS.exe` processes by their executable path across legacy and versioned folders for the same install. An unrelated melonDS installation no longer blocks Play or a repair.
- After switching to a new build, Play stays disabled while any game from the previous version of that install is still running, then becomes available once it exits.
- Fixed the local NSBMD writer package initializer used by optional Soaring and battle-scene generation.

Existing ROMs, profiles and saves need no conversion. Keep every player's game build and launcher version matched. No ROMs, saves, firmware or RAM captures are included.

Made by **mvq1303 / WhatWasMissing**, built on melonDS. Upstream and dependency notices are retained.
