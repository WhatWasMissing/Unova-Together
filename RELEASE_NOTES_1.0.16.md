# Unova Together 1.0.16 — Mega Serperior battle verification

This launcher and emulator update strengthens the experimental Mega Evolution test for the supported English Pokémon Black 2 Redux v1.4.1 ROM (`IREO`). A full-state battle replay now verifies Mega Serperior's native ChangeForm command, battle stats and ability in both battle copies. The replay also drives battle-end cleanup and confirms the saved party record remains unchanged.

Open **Fight** with Serperior holding Serperiorite and press **L + R together** at move selection. If you need the stone, use the Multiplayer panel's **Debug** tab while idle in the overworld and C-Gear wireless is off. Save normally before testing.

The local regression uses an isolated copy of the emulator with the supplied battle state; it does not write to the ROM, save or state. A live two-emulator co-op battle and failure recovery still need playtesting. Treat the feature as experimental and have every player use the same build.

Launcher and emulator version labels both report **1.0.16**. Existing ROMs and saves need no conversion. No ROMs, saves, firmware or RAM captures are included. Matching source and SHA-256 checksums accompany the downloads. Made by **mvq1303 / WhatWasMissing**, built on melonDS; upstream and dependency notices are retained.
