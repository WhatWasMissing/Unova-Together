# Unova Together beta 0.3.8

Download **Unova-Together.exe**, or use **Updates → Check for updates** in the launcher. Update everyone before starting a new LAN game. Your ROM, saves and profiles are kept separately.

## Changes

- LAN games started from the launcher now allow up to 16 connected players. Change the lobby size under Co-op → Advanced.
- The host can pair with a later guest instead of only the first player who joined. Other connected players do not interfere with readiness, battle packets or recovery.
- Fixed stale co-op invitations after cleanup and improved recovery when the selected partner disconnects.
- High-level traded Pokémon obey in supported English Black 2 and Redux builds.

## Playing together

Use Local LAN or Tailscale for larger lobbies. A co-op battle still has **the host and one guest**; guest-to-guest battles and battles with more than two human players are not supported. The experimental internet UDP bridge remains limited to two players.

Keep fast-forward and C-Gear wireless off. Co-op experience remains disabled. See [known issues](docs/KNOWN_ISSUES.md) and [the lobby testing guide](docs/LAN_LOBBIES.md).

## Tested

Three local emulator instances connected, including pairing with the second guest. Native battle startup and checkpoint cancellation/recovery passed, with approximately 59–60 FPS during the measured battle. Matching results, mismatched results, partner changes and disconnect handling passed focused network tests. The obedience fix passed 728 ROM-backed cases across four local game builds.

Full NPC victory, badge awards and save persistence in a three-player lobby have not been verified. Cross-network testing of this larger-lobby change is still needed.

Made by mvq1303 / WhatWasMissing. Matching modified melonDS and launcher source is included in the Source ZIP. No ROMs, firmware or player saves are bundled.
