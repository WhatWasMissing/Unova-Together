# Unova Together 1.0.15 — Mega Serperior test

This launcher and emulator release adds an experimental, battle-only Mega Evolution for Serperior in the supported English Pokémon Black 2 Redux v1.4.1 ROM (`IREO`). It adds the custom Serperiorite stone, Mega stats and typing, battle transformation and restoration, and a paired co-op event path. Open **Fight** and press **L + R** at move selection. The Multiplayer panel's **Debug** tab can grant Serperiorite while the player is idle in the overworld and C-Gear wireless is off.

Focused native and ROM-overlay regressions pass in Debug and Release. Two LAN instances pass the event transport test, and paired in-memory battle tests verify both native handlers. A live two-emulator battle and natural battle-end restoration remain unverified, so treat co-op Mega Evolution as a test feature and save normally before trying it. See [the Mega Evolution test guide](docs/MEGA_EVOLUTION.md).

Launcher and emulator labels both report **1.0.15**. Existing ROMs and saves are kept. No ROMs, saves, firmware or RAM captures are included. Made by **mvq1303 / WhatWasMissing**, built on melonDS; upstream and dependency notices are retained.
