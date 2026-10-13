# Unova Together 1.0.10 — Follower colours and smooth movement

- Removes synchronous multiplayer polling and full-RAM follower copies from the rendering thread. Requests coalesce while the emulator is busy, preventing polling backlogs and frame-delivery stalls.
- Keeps the last verified follower through temporary party-read failures while the owned field remains valid. Battles, unloading, party changes, eggs and fainted leads still update visibility.
- Bobs the complete follower sprite at pixel-aligned offsets instead of stretching its height.
- Detects the loaded game's verified native shiny threshold. Shiny Audino and other followers use Redux's increased shiny odds, while the original game's rule remains supported.
- Hosted relay startup uses the current shared launcher executable, preserving follower shiny and gender metadata.
- Cleanup detects the shared launcher, bootstrap and repair utility as running installations.

The author confirmed smooth walking/running, idle followers remaining visible, bobbing and shiny Audino in the local gameplay build. Automated decoder, renderer, polling, relay and updater checks passed. This does not claim every species or network configuration has received a new two-PC playtest.

Install through launcher Updates. Restart the game and hosted relay after updating; both players should use the same release. Launcher and emulator report 1.0.10. Saves, ROMs and settings are preserved by the updater.

Includes the Windows runtime, matching GPL source, standalone installer, repair utility and SHA-256 checksums. No ROM, firmware, save or private RAM capture is included. Original contributions by mvq1303 / WhatWasMissing, built on melonDS; attribution and dependency notices are preserved.
