# Unova Together

**Current release: 1.0.18.** Continues the experimental, battle-only Mega Serperior test: [downloads](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v1.0.18). Made by mvq1303 / WhatWasMissing, built on melonDS.

Explore Unova with friends in supported English Pokémon Black 2 and Blaze Black 2 Redux. Each player uses their own matching ROM and independent save.

## Download and play

1. [Download version 1.0.18](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v1.0.18). Choose **Unova-Together.exe**, or extract the complete Windows x64 ZIP.
2. Open the EXE, or run **Start Unova Together.cmd** in the extracted folder. Choose your ROM and select **Play**.
3. Open launcher **Co-op** to configure your connection and host or join LAN. Follow the [player guide](docs/PLAYER_GUIDE.md).

Version **1.0.18** includes matching launcher and emulator version labels and keeps Mega Serperior as the only playable Mega profile. The matching-overlay replay from 1.0.17 verified form 0→1, Contrary, stat updates and saved-party preservation; 1.0.18 adds the Serperior-only Release gate and ROM boot regressions. Other Mega drafts remain disabled in the public build. Existing ROMs and saves do not need conversion. Updates install beside the active build; the current game can remain open while the new build downloads. Play becomes available again after any game from that installation closes. Clients still running launcher 1.0.5 should install the game update, then run [Repair-Launcher.exe](https://github.com/WhatWasMissing/Unova-Together/releases/download/v1.0.18/Repair-Launcher.exe) once and select their old launcher. Subsequent updates follow the same entry automatically. See the [migration instructions](RELEASE_NOTES_1.0.10.md). Update every player and restart the presence relay.

## Features

- **Explore together:** shared trainer movement, teammate locations and joining maps.
- **Trade and battle:** item offers, party Pokémon exchanges and friendly PvP from **Unova → Players**.
- **Trainer co-op:** supported story encounters, Solo/Co-op mode and practice rematches with independent saves.
- **Pokémon tools:** all 649 directional followers, ten companion interaction scenes with nature-aware dialogue and animated reactions, IVs/EVs, seasonal encounters and free level-up move relearning.
- **Battle experiment:** Mega Serperior and Serperiorite for the supported Black 2 Redux profile. The form is battle-only; see the [Mega Evolution test guide](docs/MEGA_EVOLUTION.md) for setup and co-op limits.
- **Field HMs:** owned HMs work without taking learned battle move slots; native story requirements remain.
- **Presentation:** custom camera and optional nearby battle scenery built locally from your ROM.
- **Launcher:** simple save slots, Gen 5 ROM/save/XP tools, LAN Host/Join/Retry, controller navigation, music, settings, optional cheats, save backups/restore, diagnostics, verified updates and repair.

See the [complete feature guide](docs/FEATURES.md) for controls, menu paths and limitations, and the [roadmap](docs/ROADMAP.md) for proposed additions. Soaring remains optional and experimental; gaps use decorative regional terrain, and landings wait for the native map transition to settle before restoring game input.

Companion interactions are in **Settings → Following Pokémon** and enabled by default when no preference has been saved. Explicit off choices are preserved.

The release includes 743 normal/shiny follower variants, supported female/forms, sprite stability fixes, contextual dialogue, reduced motion, co-op compatibility/readiness checks, rematch filters and **₽10 Super Repels**. Practice completion passed a targeted local latency test; broader recovery/network playtesting remains required. The searchable trainer browser and experimental native-Fly shortcut from 1.0.7 are included; full free-flight Soaring is not implemented. See [changes, evidence and source reconstruction](docs/DEVELOPMENT_POLISH_2026-10-13.md).

## Guides and limits

[Release notes](RELEASE_NOTES_1.0.18.md) · [Release checks](docs/RELEASE_CHECKS_1.0.18.md) · [Known limits](docs/KNOWN_ISSUES.md)

[Launcher](docs/LAUNCHER.md) · [Co-op tools](docs/COOP_TOOLS.md) · [Field tools](docs/FIELD_TOOLS.md) · [Followers](docs/FOLLOWING_POKEMON.md) · [Companions](docs/COMPANIONS_AND_SOARING.md) · [Party stats](docs/PARTY_STATS.md)

For different networks use [Tailscale](docs/TAILSCALE_COOP.md). The optional [UDP bridge](docs/UDP_SERVER_GUIDE.md) remains experimental and needs your group's server; no public server is supplied. Co-op experience is disabled. Keep fast-forward and C-Gear wireless off during native multiplayer. Some special trainer events and network conditions remain unverified; interrupted battle recovery may discard that battle's progress.

Matching GPL source and checksums accompany the downloads. No ROMs, saves or firmware are bundled. [Authorship](AUTHORSHIP.md) · [Licensing](LICENSING.md). Playtesters: maxback221 and randomitem19.

Solo battles award **1.25× XP**; co-op XP remains suppressed. See [XP compensation](docs/XP_COMPENSATION.md) and [measured battle results](docs/XP_COMPENSATION_BATTLE_TEST.md). The current multiplier passed production-dispatch checks. The documented normal save/reload battle test used historical release 1.0.2's 1.65× multiplier; it is not a new 1.0.5/1.0.6 gameplay test.
