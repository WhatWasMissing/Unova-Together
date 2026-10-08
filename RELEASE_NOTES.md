# Unova Together beta 0.3.2

Explore Unova with a friend, share items, and take on trainers together in Pokémon Black 2 and Blaze Black 2 Redux. This Windows beta packages the current build with embedded **mvq1303 / WhatWasMissing** credits and the updated release presentation.

## Download and start

1. Download **Unova-Together-0.3.2-Windows-x64.zip** and extract the entire folder.
2. Run **Start Emulator.cmd** and load your own ROM and save. Both players need the same build and game revision.
3. Follow **docs/PLAYER_GUIDE.md**. The package includes preset controls, connection helpers, the Tailscale installer and guides.
4. For different networks, use the Tailscale guide first. The UDP option is experimental and requires a server supplied by your group. No public server is included.

## What is included

- Shared exploration and in-game item trading.
- Experimental NPC-triggered co-op trainer battles, with independent saves and a Solo/Co-op toggle.
- Camera tilt, rotation and zoom controls in the Camera tab.
- Existing recovery controls and Debug tools.
- Complete matching source as a separate optional download, plus SHA-256 checksums. ROMs, saves and firmware are excluded.

## Before playing

Back up saves and keep fast-forward off while connected. Co-op XP remains disabled to prevent desynchronisation. Internet UDP battle completion, special trainer events and all story/save outcomes have not been exhaustively verified. Teammate rendering can flicker, and unstable connections can interrupt battles. Rapid retries after cancelling a trade can fail; wait for both players to show Ready. See **docs/KNOWN_ISSUES.md** for limitations and recovery.

This is a beta packaging/credits update, not a claim that the remaining performance and networking issues have been fixed.

Made by **mvq1303**, GitHub **WhatWasMissing**. Built on melonDS; upstream credits and GPL licensing are preserved.
