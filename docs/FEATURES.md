# Unova Together features

Current release: **1.0.34**. Unova Together is made by **mvq1303 / WhatWasMissing** and built on melonDS. It supports reviewed English Pokémon Black 2 and Blaze Black 2 Redux profiles on Windows x64. Each player needs their own matching game file and save.

## Play with friends

- **Explore together:** see your friends move around, check their status, and join eligible maps.
- **Trade:** offer items or trade eligible party Pokémon from **Unova → Players**. Both players confirm before a trade completes.
- **Battle together:** invite a friend to a friendly battle or join supported story trainer battles in co-op mode.
- **Practice:** find supported trainers and rematch without changing story progress. Practice battles do not give story rewards.

Both players should use the same release and matching game revision. Co-op experience is disabled. Some special trainer events and slow or unstable connections still need more testing. See [co-op tools](COOP_TOOLS.md), the [player guide](PLAYER_GUIDE.md), and [known limits](KNOWN_ISSUES.md).

## Mega Evolution

This release includes **49 Mega forms**, each linked to its named Mega Stone. Buy stones at Pokémon Center Marts for **₽50,000**. Give a Pokémon its matching stone, then press **L + R together** at move selection in battle. Mega Evolution lasts until the battle ends.

Examples:

- **Mega Serperior** holds **Serperiorite** and gains **Adaptability** (BST 535 → 635).
- **Mega Charizard Y** holds **Charizardite Y** and gains **Drought** (BST 535 → 635).
- **Mega Salamence** holds **Salamencite** and has **Intimidate** (BST 600 → 700).
- **Mega Lucario Z** holds **Lucarionite Z** and gains **Adaptability**.

The roster is: **Serperior, Arcanine, Venusaur, Charizard Y, Charizard X, Blastoise, Beedrill, Pidgeot, Alakazam, Slowbro, Gengar, Kangaskhan, Pinsir, Gyarados, Aerodactyl, Mewtwo X, Mewtwo Y, Ampharos, Steelix, Scizor, Heracross, Houndoom, Tyranitar, Sceptile, Blaziken, Swampert, Gardevoir, Sableye, Mawile, Aggron, Medicham, Manectric, Sharpedo, Camerupt, Altaria, Banette, Absol, Glalie, Salamence, Metagross, Latias, Lopunny, Garchomp, Lucario, Lucario Z, Abomasnow, Gallade, Audino, and Latios.**

**46 of the 49 forms have animated battle artwork.** The supplied GIFs are converted to timed sprite frames; Mega Salamence uses all 67 front and back frames. Automated checks verify the clips and their timing, but they cannot replace checking how each animation looks in a live battle. The full stone, ability, stat, and animation list is in the [Mega Evolution guide](MEGA_EVOLUTION.md).

The roster is designed for the supported Black 2 Redux profile. Mega stats and some abilities are mod values; see the guide for details. Linked co-op Mega battles and every form still need individual live testing.

## Following Pokémon

Your lead Pokémon follows about 1¼ tiles behind and walks along your route. All **649 base species** have directional follower sprites and idle movement. Follower poses now align to their visible pixels so transparent image margins do not pull the artwork up and down between frames. The artwork pack also includes supported shiny, female, and form variations; other forms use the base sprite. Eggs and fainted Pokémon stay hidden. The latest alignment change has automated coverage and still needs a live visual check.

Interact by facing your follower and pressing **R + A**, or tap/click its sprite. Choose from ten friendly actions, including talking, petting, playing, and telling a story. These interactions are cosmetic: they do not change friendship, heal Pokémon, or award items. Use **Unova → Settings** to control your follower and your teammate's follower. Reduced motion is available in launcher settings.

See [Following Pokémon](FOLLOWING_POKEMON.md) and [companion interactions](COMPANIONS_AND_SOARING.md).

## Pokémon and field tools

- **IVs and EVs:** check your party's stats from **Unova → Pokémon**.
- **Wild encounters:** look up ordinary grass, water, and fishing encounters from the loaded game. Gifts, scripted legendaries, and Hidden Grottos are not included.
- **Move relearning:** restore eligible level-up moves for the Pokémon's current form.
- **Field HMs:** owned HMs can be used in the field without taking up a battle move slot. The game's story requirements still apply; Fly still needs a party member with the move.
- **Solo XP:** supported solo battles award 1.25× newly earned experience. Co-op experience is disabled.

## Optional Soaring preview

**Soaring is unfinished and experimental.** It is off by default and should be treated as a preview. Enable **Settings → Experimental features → Soaring flight**, then choose **Unova → Pokémon → Take flight**.

The current atlas connects 69 outdoor map areas, but some positions and routes are approximate. Only clear, checked ground is available for landing; **Marine Tube has no safe landing**, so return to take-off there. Flight is local to your game. Testing has covered map loading and simulated flight and landing, but a live playthrough still needs to confirm that travel and landings feel right on a player's save. Save normally before testing.

See [Soaring flight](SOARING_FLIGHT.md) for steps and current limits.

## Launcher and presentation

- **One launcher:** choose Unova Together, manage game and save slots, and start the emulator.
- **Save safety:** use backups, restore points, and integrity checks before changing installations.
- **Co-op setup:** host or join LAN, retry a connection, or follow the Tailscale guide for different networks. The optional UDP route needs a server run by your group; there is no public server.
- **Settings:** configure controls, display, audio, music, controller navigation, reduced motion, and optional reviewed cheats.
- **Gen 5 helpers:** check ROM compatibility, compare copied saves, and estimate Redux Challenge XP budgets.
- **Camera and battle scenery:** adjust the camera locally or enable optional scenery built from your own game data. Scenery is approximate, and some special battles keep their original backgrounds.
- **Verified updates:** the launcher checks release downloads and keeps saves while updating. Repair tools can restore a damaged launcher install.

For setup and troubleshooting, see the [launcher guide](LAUNCHER.md) and [known limits](KNOWN_ISSUES.md). The roadmap describes possible future work; it does not guarantee a feature is included.

