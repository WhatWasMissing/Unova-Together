# Pokémon Together launcher guide

Made by **mvq1303 / WhatWasMissing**, built on melonDS. The shared launcher opens **Mod library** on every launch. Choose **Unova Together** for Black 2/Redux, or the separately prepared **Pokémon X Together** experimental prototype. Each mod has its own pages. Use **Mod library** to switch.

Open **Start Unova Together.cmd** in the portable Unova folder, **Start Pokémon Together.cmd** in a shared-launcher installation, or the standalone **Unova-Together.exe** download. Choose your own supported ROM on **Play**.

## Games & saves

Select **Manage saves** on Play, or open **Games & saves**. Choose a slot or **New save slot** for a separate adventure. Slot names save automatically; new slots receive separate save folders. Existing slots retain their ROMs, settings and folders. **Advanced save options** contains custom folders, player names and slot removal. Changing folders does not move saves; removing a slot keeps its files and backups.

Save normally in-game, then choose **Back up now**. Select a dated entry and **Restore backup** with all melonDS instances closed. Restoration verifies checksums and backs up current files first. Backups preserve matching normal `.sav`, `.save` and `.dsv` files and numbered instance saves; they do not capture unsaved gameplay or savestates. Tools also offers backup and restore. Backups under `save-backups/<profile>` are not pruned automatically. See [Gen 5 tools](LAUNCHER_GEN5_TOOLS.md).

## Co-op connections

Choose **Local LAN**, **Tailscale backup**, **Internet UDP** or **Solo**. Player sharing uses a presence-relay address, port (usually 8765) and room. **Save connection** stores them; **Check relay** checks the sharing service. The compiled launcher can host that service without separate Python.

**Host & play** starts the selected ROM and a native LAN lobby; **Join & play** uses the host address. Launch the host first. The launcher remembers the role/address per save slot. **Retry** uses that role; save normally and close the running game before retrying. Lobby capacity is a native LAN setting, not a guarantee that every mod battle mode supports that many players.

For different networks, connect both PCs through Tailscale and use the host's Tailscale address. Experimental UDP uses its separate setup helper and needs your group's server, Python and dependencies. No public server is supplied. Do not combine UDP and Tailscale native LAN for one session.

Player sharing and native wireless are separate connections: seeing a teammate does not prove battles are ready. Match game/mod revisions, keep normal speed and C-Gear wireless off, and save independently after completed battles/trades. Solo disables automatic sharing/trainer co-op for that launch. See the [player guide](PLAYER_GUIDE.md) and [known limits](KNOWN_ISSUES.md).

## Following Pokémon

In the updated launcher source/local build, **Settings → Following Pokémon → Companion interactions** is enabled by default unless you saved an off choice. It applies on the next game launch. Followers themselves already default on; show or hide your own/teammates' followers in **Unova → Settings**.

Stop, face the follower and press **R+A**, or tap its sprite. A alone advances normal game text. There are ten interaction actions, friendship/nature-aware replies and short animated reactions. Interactions do not change HP, friendship, items or saves. See the [interaction guide](COMPANIONS_AND_SOARING.md).

The published v1.0.6 downloads include the preceding launcher and its **Settings → Experimental** toggle. Enable it and restart in those downloads. Main-branch/local launcher changes do not replace public release assets.

## Settings and controls

Settings contains per-slot volume, filtering, focus behavior and follower interactions. **Nearby battle scenery** remains explicitly experimental and off by default. It generates a local graphics cache from your ROM; it does not alter ROM/save files.

**All emulator settings** opens a searchable catalog and full configuration editor for controls/hotkeys, display, audio, firmware, networking and paths. Close the game before saving changes. Values use TOML syntax; before-edit backups are created. Pokémon's text speed and battle style remain in its native Options menu.

Reviewed optional cheats default off and are offered only for supported fingerprints. The catalog explains activation and effects; disabling a cheat does not undo already saved changes. Existing user codes are preserved. The Rare Candy option replaces the first medicine slot. Preserve backups before using it. Source attribution/license is shown in Settings.

Keyboard: **Tab/Shift+Tab** moves focus, **Enter** activates a button, **Ctrl+Tab/Ctrl+Shift+Tab** changes pages. Xbox-compatible controllers: D-pad/stick moves focus, A selects, B returns/closes an editor, LB/RB changes pages; left/right adjusts a focused dropdown/slider. Controller navigation runs only while the launcher/editor is focused. Addresses still need keyboard input.

## Features, guides and news

**Features** covers companion actions, exploration, trades, trainer/PvP battles, camera, followers, field tools, solo XP, scenery, saves and maintenance. Existing screenshots illustrate gameplay; they do not establish complete trainer or internet compatibility. **Feature guide**, **Known issues** and **Roadmap** open the detailed guides. Roadmap ideas are separate from shipped features.

**Setup → Refresh guides** downloads the official text guides independently of game updates and retains them for offline use. Failed refreshes preserve the previous complete set; bundled guides remain the fallback. **News** shows official GitHub release notes, cached offline.

## Updates, checks and repair

**Updates** downloads official Windows releases, verifies SHA-256 and installs beside the previous runtime. Updates/repairs back up existing save files first. Save normally and close the game before switching.

From launcher 1.0.8, update completion restarts into the new shared Pokémon Together launcher with the same profile/save home. Older compatible hub entry points forward to newer installed hubs without downgrading to legacy per-mod launchers. Release and Launcher labels describe the active game package and the running launcher build separately. Shared launchers older than 1.0.8 need the one-time restart described in [release notes](../RELEASE_NOTES_1.0.8.md).

From 1.0.9, a permanent entry follows the active update folder, keeping the original shortcut target. Existing 1.0.5 clients should install the game update and then run **Repair-Launcher.exe** once, selecting the old shared executable their shortcut opens. If the Unova home is separate from the shared hub, repair asks for that original folder. The original executable is retained as a backup; save/profile directories stay in place. See the [client migration instructions](../RELEASE_NOTES_1.0.9.md).

**Tools → Run launch checks** checks executable/ROM identity and frame/focus settings. It cannot pre-verify a teammate's game, live C-Gear or every multiplayer event. **Verify installed files** compares executables/DLLs with the integrity record. **Find repair download / Repair game files** restores a checksum-verified published package into a separate slot; published files replace local custom game changes when selected.

**Tools → Clean old installations** keeps the active and previous build, running builds and user data while pruning recognised older package files. Cleanup also runs at startup. Backups are retained. See [storage details](LAUNCHER_STORAGE.md).

## Reports and read-only tools

**Tools → Report a problem** creates a redacted troubleshooting ZIP and opens a review window. Inspect it and submit it yourself through GitHub issues. Reports include version/hash information and bounded text logs; ROMs, saves, RAM dumps and credentials are excluded. Nothing is uploaded automatically.

Gen 5 tools check ROM/XP-hook compatibility, compare copied save records and calculate Redux Challenge XP budgets using **1.25× solo XP**. These are read-only tools, not game editors or full compatibility certification.

See [Features](FEATURES.md), [release checks](RELEASE_CHECKS_1.0.6.md) and the [roadmap](ROADMAP.md) for capability, evidence and future work.

The development launcher adds **Co-op → Check readiness**, combining selected build/profile checks with the latest presence test result and explicit in-game requirements. **Settings → Following Pokémon → Reduced follower motion** applies on launch and preserves sprites and reaction symbols.
