# Unova Together beta 0.3.9

Save in game and close the emulator before updating. In the launcher, open **Updates → Check for updates** and install **0.3.9**, or download **Unova-Together.exe** below. Update everyone playing together. Back up your saves first.

## New and improved

- **Area battle scenery:** enable **Settings → Area battle scenery (experimental)** before launching. The launcher builds native 3D arenas using assets from your own English Black 2 ROM. The first launch prepares a local cache; subsequent launches reuse it. Turn the option off to restore standard backgrounds. Your ROM and save files are not edited.
- **Following Pokémon:** corrected follower identities and animation selection. Pokémon without native directional artwork use a party-icon fallback; not all species have complete walking sprites.
- **Game menus:** fixed the Options shortcut opening the player card.
- Includes the latest launcher and automatic restart after updates.

## Tested and known limits

The local Redux Complete v1.4.1 / Unova Together ROM generated **137 area scenes covering 617 map headers**. Every generated model passed parsing and resource-size checks. A two-emulator Cheren co-op battle displayed the new scenery, completed on both instances and returned to Ready at approximately **59–60 FPS**. Launcher cache generation/reuse and focused native menu checks passed.

Scenery remains experimental. These are generated arenas, not exact reconstructions of maps. Only standard battle-background resources are replaced; Pokéstar cinematic scenes remain original. Seasonal/time lighting and animated water are not implemented, and not every encounter has been playtested. Co-op EXP remains disabled. Keep C-Gear wireless and fast-forward off during co-op. Other connection and rendering limitations are listed in [Known issues](https://github.com/WhatWasMissing/Unova-Together/blob/main/docs/KNOWN_ISSUES.md).

Download the single EXE for the bundled launcher and emulator, or use the portable ZIP. Matching GPL source and SHA-256 checksums are provided. ROMs, saves and firmware are not included. Scenery graphics are generated locally from your own ROM.

Made by **mvq1303 / WhatWasMissing**, built on melonDS.
