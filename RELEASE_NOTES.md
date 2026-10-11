# Unova Together 1.0.0 — Full release

The feature-complete Windows release of Unova Together, including **launcher 1.0.0** and **modified melonDS 1.0.0**, based on upstream melonDS 1.1.

## Play

Download **Unova-Together.exe**, or extract **Unova-Together-1.0.0-Windows-x64.zip** and run **Start Unova Together.cmd**. Select your own supported Black 2 or Blaze Black 2 Redux ROM and press Play. Existing players can install this version through launcher Updates. Update every player and restart the presence relay.

## Included features

- Shared overworld exploration, teammate locations and joining maps.
- Item offers, direct party Pokémon trades and friendly player battles.
- Co-op trainer encounters, Solo/Co-op switching and practice rematches, with independent parties and story saves.
- Directional following Pokémon for all 649 base species and optional companion interactions.
- IV/EV viewing, seasonal encounter finder, free level-up move relearning and field HMs without learned battle move slots.
- Custom camera and optional nearby battle scenery generated locally from your ROM.
- Launcher profiles, LAN Host/Join/Retry, remembered connections, controller navigation, music, emulator settings and optional cheats.
- Save backups and restore, troubleshooting reports, verified updates and installation repair.

## Final polish

Both applications identify as 1.0.0. The launcher uses release wording, current in-game menu paths, a complete feature list and bundled 1.0.0 news. Setup and feature guides now describe the current build. The obsolete flight-preview instructions are removed: that prototype is absent from the current feature set. Upstream melonDS attribution and all project/dependency licenses are retained.

## Known limits

Co-op experience remains disabled to prevent desynchronisation. Saves and story progress remain independent; not every special trainer script has been verified. Keep fast-forward and C-Gear wireless off during native multiplayer. Interrupted battles may require returning to the field and recreating LAN; recovery can discard the interrupted battle's progress.

Tailscale is available for different networks. The optional UDP bridge remains experimental and requires your group's server and Python; there is no bundled public server. Nearby battle scenery and companion interactions remain optional. Companion interactions do not change friendship or HP. The encounter finder covers ordinary encounter tables, excluding gifts, scripted legendaries and Hidden Grottos. Direct Pokémon trades exclude eggs, held Mail and native trade evolutions; use the Union Room for those cases.

See [player guide](https://github.com/WhatWasMissing/Unova-Together/blob/main/docs/PLAYER_GUIDE.md), [known limits](https://github.com/WhatWasMissing/Unova-Together/blob/main/docs/KNOWN_ISSUES.md) and the included release checks for validation details. A full release does not imply every ROM hack, network or special event has been tested.

Made by **mvq1303 / WhatWasMissing**. Playtesters: **maxback221** and **randomitem19**. Built on melonDS; matching GPL source and SHA-256 checksums are included. No ROMs, saves or firmware are bundled.
