# Unova Together 1.0.12 — Safer Soaring landings

This full release updates the emulator and launcher together. Soaring remains optional, local to the player and disabled by default; enable it in **Settings → Experimental features**.

- Regional flight scenery now fills open areas with deep ocean, context-based forest islets and lightweight visual flyways. Generated scenery is decorative and cannot be landed on.
- The optional **Show Soaring collision data (debug)** setting marks verified ground, blockers, special tiles and the rider's position.
- Landing candidates avoid authored NPC event positions. After a landing, emulator input stays locked until the requested map and tile have loaded and the player's position has settled, preventing NPC dialogue from interrupting the warp. A timeout reports its status and returns control instead of leaving the flight menu stuck.
- Returning to the take-off point now asks for confirmation.
- Flight timing uses fixed simulation steps, and the cached flight frame remains visible during speedup instead of flashing between the field and flight scene.

Soaring still uses verified coordinates from the take-off map matrix. Separate map matrices do not yet share a verified regional transform, and generated scenery does not add collision or landing locations. See [Soaring design and limits](docs/SOARING_DESIGN.md) and [release checks](docs/RELEASE_CHECKS_1.0.12.md).

The Windows x64 ZIP, standalone launcher, repair utility, matching GPL source and SHA-256 checksums are provided. Update all players to 1.0.12. Existing ROMs and saves need no conversion. No ROMs, saves, firmware or RAM captures are included.

Made by **mvq1303 / WhatWasMissing**, built on melonDS. Upstream and dependency notices are retained.
