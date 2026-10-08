# Unova Together beta 0.3.5

Download **Unova-Together-0.3.5-Windows-x64.zip**, extract the entire folder and open **Start Unova Together.cmd**. Choose your own matching Black 2/Redux ROM and select **Play**. Update both players and restart the player-sharing relay.

## New and improved

- A Windows launcher with official GitHub release checks and checksum-verified updates. Updates install beside the existing build and retain your emulator settings; ROMs and saves are not overwritten. The launcher does not need a separate Python installation.
- Give item works while the idle co-op observer is enabled and from the custom trade overlay.
- Better battle-status recovery: a returned field can clear the battle badge even if the camera projection is temporarily unavailable. Field rebuilds switch tracking to the current owned player object.
- Different starter choices can agree at verified rival encounters. Both players use the host's matching ROM enemy variant while retaining their own story event and save.
- Remote trainer sprites are suppressed on local stock menu screens. Your menu status remains available to teammates.
- Hardened native wireless input, player-list handling and compressed/truncated ROM loading.

## Before playing

Back up your saves. Turn C-Gear wireless and fast-forward off. Co-op EXP gain remains disabled to prevent desynchronisation. The bundled Tailscale installer and setup guide remain available; the UDP bridge is experimental and has no default public server.

Native cleanup can time out after completion and discard recovered battle progress. An immediate second co-op battle can also fail to reconnect. Let recovery return both games to the field, then recreate native LAN before retrying. Intermittent rendering issues and unverified trainer events remain listed in [known issues](docs/KNOWN_ISSUES.md). Testing details are in [release checks](docs/RELEASE_CHECKS_0.3.5.md); they do not establish every rival story/save branch or reliable internet UDP battle completion.

Made by **mvq1303 / WhatWasMissing**, built on melonDS. The matching GPL source download and checksums are included. ROMs, saves and firmware are not included.
