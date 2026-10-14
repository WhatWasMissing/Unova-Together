# Unova Together features

Unova Together by **mvq1303 / WhatWasMissing**, built on melonDS. Current release: **1.0.11**. The wider regional Soaring view is included as an experimental test feature and remains off by default. Supported games are reviewed English Pokémon Black 2 and Blaze Black 2 Redux profiles on Windows x64. Every player supplies a matching ROM and uses an independent save.

## Explore and play together

| Feature | Where to use it | Scope and limits |
| --- | --- | --- |
| Shared exploration | Launcher **Co-op**, then **Unova → Players** | Teammate movement, followers and Ready/Busy/battle status. Player sharing and native wireless battles use separate connections. |
| Join a teammate's map | **Unova → Players → teammate → Join map / Teleport** | Available when field and destination checks allow it. This does not synchronise story progress. |
| Item offers | **Unova → Players → teammate → Give item** | Choose a quantity; the recipient accepts. Both players save after completion. |
| Party Pokémon trades | **Unova → Players → teammate → Pokémon trade** | Both players confirm. Eggs, held Mail and native trade evolutions are excluded; use the Union Room for those cases. |
| Friendly player battles | **Unova → Players → teammate → PvP battle** | Invite a teammate over the native multiplayer connection. |
| Trainer co-op | **Unova → Co-op → Trainer battles: Co-op** | Both players reach the matching trainer. Supported encounters use each player's party and original story script. Special events are not all verified. |
| Solo and practice battles | **Unova → Co-op → Practice battles** | Search the loaded ROM's NPC trainer list; selected party size and level range are shown. Practice gives no story rewards. Co-op XP remains disabled; supported solo battles award **1.25× XP**. |

## Following Pokémon and interactions

Your lead Pokémon follows roughly one tile behind you. All **649 base species** have directional sprites and idle movement. The development build includes **743 assets** with normal/shiny palettes and supported female/form variations; unsupported forms use base art. Larger art keeps its original dimensions. Eggs and fainted leads stay hidden. **Unova → Settings** contains **My follower**, **Teammate followers** and **Greet teammate's Pokémon**. Launcher Settings adds reduced follower motion. See [coverage and credits](FOLLOWER_VARIANTS.md).

Stop, face your follower and hold **R** while pressing **A**, or click/tap its sprite. A alone remains available to advance ordinary game text.

The ten actions are **Talk, Pet, Play, Praise, Tell a story, Ask about today, Sit together, Show a trick, Tell a joke** and **Sing together**. Each action has four rotating replies across five friendship bands. Nickname, health and nature influence the response; nature shows through tone and behavior. Reactions use hearts, question/exclamation marks, stars, notes and ellipses, with peeking, swaying, hopping, spinning and short runs.

Development dialogue also uses area, DS time/season, loaded-ROM Pokémon types and recent battles, with separate visit counts for each Pokémon/action. Weather and battle-result-specific dialogue remain future work.

Interactions are cosmetic and read-only. They do not raise friendship, heal Pokémon, award items or alter saves. They are blocked during movement, battles, native menus and co-op preparation. See the [interaction guide](COMPANIONS_AND_SOARING.md).

**Launcher update on main:** interactions are in **Settings → Following Pokémon**, enabled by default when no choice has been saved. An explicit off choice stays off. Following Pokémon themselves already default on in the game. The published v1.0.6 downloads still contain the earlier launcher: enable interactions under **Settings → Experimental** in those downloads. The updated source/local launcher does not replace existing release assets.

## Pokémon and field tools

| Feature | Where to use it | Scope and limits |
| --- | --- | --- |
| IVs and EVs | **Unova → Pokémon → IVs and EVs** | Read your party's stats. |
| Seasonal encounters | **Unova → Pokémon → Find wild Pokémon** | Ordinary grass, water and fishing tables from the loaded ROM. Gifts, scripted legendaries and Hidden Grottos are excluded. |
| Free move relearning | **Unova → Pokémon → Relearn moves** | Current species/form's level-up moves at or below its level. Save normally afterward. |
| Field HMs without learned move slots | Normal field interactions and native party menu | Own the HM and meet native story requirements. Fly needs a move slot without another field action. |
| Regional Soaring test feature | Enable **Settings → Experimental features → Soaring flight**; then open **Unova → Pokémon → Take flight** | Off by default. Choose a flying partner to enter a separate, local flight scene. Black 2's regional matrix streams real outdoor terrain up to 4,096 units around you, with smaller scene windows in dense areas and fog over gaps. Land only on verified clear ground, or return to take-off with B. The scene stays local and experimental. |
| Solo XP compensation | Automatic on supported profiles | **1.25×** newly awarded solo XP, with native rounding/caps. Existing XP is unchanged; co-op awards remain zero. |

See [field tools](FIELD_TOOLS.md), [party stats](PARTY_STATS.md) and [XP compensation](XP_COMPENSATION.md).

**Development shops:** Super Repels cost **₽10**, the lowest positive native price, and appear in active ordinary money-shop catalogs. Original ROM files remain unchanged.

## Presentation

- **Custom camera:** local tilt, rotation and zoom in **System → Multiplayer → Camera**.
- **Area battle scenery:** opt in through launcher **Settings**. Scenery is generated and cached locally from your ROM. These arenas are not exact overworld reconstructions; special scenes keep original backgrounds, and not every environment is playtested.

## Launcher and connections

- **Mod library:** one launcher with separate Unova Together and Pokémon X routes. Pokémon X is a separately prepared experimental prototype, not part of Unova's playable game package.
- **Games & saves:** separate save slots, automatically saved names, per-slot preferences, checksummed backups and restoration.
- **Co-op:** Host/Join/Retry, remembered role/address and embedded presence-relay hosting. Use Tailscale for different networks. Experimental UDP requires your group's server and Python; no public server is supplied.
- **Settings:** keyboard/controller navigation, menu music, display/audio/controls, searchable emulator options and reviewed optional cheats.
- **Gen 5 tools:** ROM compatibility checks, read-only copied-save comparison and Redux Challenge XP-budget estimates.
- **Maintenance:** SHA-256-verified updates, integrity checks, repair, old-installation cleanup and troubleshooting reports reviewed before sharing.

See the [launcher guide](LAUNCHER.md) and [player guide](PLAYER_GUIDE.md).

## Verification and proposed additions

The 1.0.6 interaction tests cover 5,000 nature/friendship/action/variation combinations, all 649 species and production input gates. The build and packaged launcher smoke test passed. These checks did **not** include a live ROM interaction session or a two-computer gameplay playtest. See [release checks](RELEASE_CHECKS_1.0.6.md).

Battle recovery, repeat encounters and latency remain priorities. Read [known limits](KNOWN_ISSUES.md) before playing and the [roadmap](ROADMAP.md) for proposed improvements. Roadmap entries are not shipped features.
