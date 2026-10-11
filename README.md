# Unova Together

**Current release: 1.0.2 — full release.** Made by mvq1303 / WhatWasMissing, built on melonDS.

Explore Unova with friends in supported English Pokémon Black 2 and Blaze Black 2 Redux. Each player uses their own matching ROM and independent save.

## Download and play

1. [Download version 1.0.2](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v1.0.2). Choose **Unova-Together.exe**, or extract the complete Windows x64 ZIP.
2. Open the EXE, or run **Start Unova Together.cmd** in the extracted folder. Choose your ROM and select **Play**.
3. Open launcher **Co-op** to configure your connection and host or join LAN. Follow the [player guide](docs/PLAYER_GUIDE.md).

The launcher and modified melonDS both ship as version **1.0.2**; the emulator is based on upstream melonDS **1.1**. Update every player and restart the presence relay. Existing ROMs and saves do not need conversion.

## Features

- **Explore together:** shared trainer movement, teammate locations and joining maps.
- **Trade and battle:** item offers, party Pokémon exchanges and friendly PvP from **Unova → Players**.
- **Trainer co-op:** supported story encounters, Solo/Co-op mode and practice rematches with independent saves.
- **Pokémon tools:** all 649 directional followers, optional companion interactions, IVs/EVs, seasonal encounters and free level-up move relearning.
- **Field HMs:** owned HMs work without taking learned battle move slots; native story requirements remain.
- **Presentation:** custom camera and optional nearby battle scenery built locally from your ROM.
- **Launcher:** profiles, LAN Host/Join/Retry, controller navigation, music, settings, optional cheats, save backups/restore, diagnostics, verified updates and repair.

## Guides and limits

[Release notes](RELEASE_NOTES_1.0.2.md) · [Release checks](docs/RELEASE_CHECKS_1.0.2.md) · [Known limits](docs/KNOWN_ISSUES.md)

[Launcher](docs/LAUNCHER.md) · [Co-op tools](docs/COOP_TOOLS.md) · [Field tools](docs/FIELD_TOOLS.md) · [Followers](docs/FOLLOWING_POKEMON.md) · [Companions](docs/COMPANIONS_AND_SOARING.md) · [Party stats](docs/PARTY_STATS.md)

For different networks use [Tailscale](docs/TAILSCALE_COOP.md). The optional [UDP bridge](docs/UDP_SERVER_GUIDE.md) remains experimental and needs your group's server; no public server is supplied. Co-op experience is disabled. Keep fast-forward and C-Gear wireless off during native multiplayer. Some special trainer events and network conditions remain unverified; interrupted battle recovery may discard that battle's progress.

Matching GPL source and checksums accompany the downloads. No ROMs, saves or firmware are bundled. [Authorship](AUTHORSHIP.md) · [Licensing](LICENSING.md). Playtesters: maxback221 and randomitem19.

Solo battles now award **1.65× XP**; co-op XP remains suppressed. See [XP compensation](docs/XP_COMPENSATION.md) and [measured battle results](docs/XP_COMPENSATION_BATTLE_TEST.md). Boosted XP save/reload remains unverified.
