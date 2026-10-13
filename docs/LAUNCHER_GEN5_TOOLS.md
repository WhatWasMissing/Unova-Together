# Games, saves and Gen 5 tools

Original launcher contributions by mvq1303 / WhatWasMissing. These tools remain available in current builds; the verification below records the historical 1.0.3 pass.

Open **Start Unova Together.cmd** and choose **Unova Together** from **Mod library**. On Play, **Manage saves** opens **Games & saves**.

Choose a save slot, or select **New save slot** to start a separate adventure with the selected ROM. New slots get separate save folders automatically. Existing profiles keep their original folders and settings. Names save automatically. Custom save folders and player names are under **Advanced save options**; changing folders does not move existing saves. Removing a slot keeps its files and backups.

After saving in-game, select **Back up now**. Choose a dated backup and select **Restore backup** with all melonDS instances closed. Restore checks file sizes and SHA-256 hashes before writing and backs up current files first. Backup and restore preserve matching ROM-stem `.sav`, `.save` and `.dsv` files, including numbered instance files such as `Redux.2.save`. Saves for other ROM stems are excluded. `.save` support preserves opaque file contents; it does not convert formats. melonDS normally uses `.sav`.

**Tools** contains ROM compatibility checks, a read-only save comparison and a Redux Challenge progression calculator. The ROM checker covers the English Black 2 identity and the solo XP hook's code fingerprints; it does not certify every multiplayer feature or edited asset. The calculator reads exact growth tables and trainer teams from the reviewed Redux Complete 1.4.1 ROM, uses the current 1.25× multiplier and allows all six growth groups and a missing-XP percentage. It reports XP-budget equivalents from level 5, not predicted playthrough levels. Documented Challenge caps include runtime difficulty shifts. Save comparison verifies both party bank checksums and individual Pokémon checksums, showing species, identity, XP, level, HP and moves; it does not validate every save block or guess which differing bank is newest.

## Verification on 11 October 2026

The launcher buttons backed up and restored disposable copies of a real Redux battle save using `.save`, `.2.save`, `.sav` and `.dsv` filenames. All four restored files matched the source byte for byte. The automatically created before-restore archive contained the previous real save; another ROM's save and original input files remained unchanged.

The restored `.save` payload was copied to the emulator's normal `.sav` filename and loaded from a normal boot without a save state. Servine retained level 20 and 5,951 XP; Elekid retained level 1 and zero XP; the Cheren badge remained present. The restored SHA-256 was `52aeb1961ebd44531449114c2d04d8f2e2d8354484942498c240619edd798343`.

Reproduce the private real-data checks with `tools/verify_launcher_gen5_tools.py` using your local fixtures. Tests also cover save-slot isolation, automatic settings persistence, readable backup labels, corruption rejection and small-window navigation. No ROMs or player saves belong in source distributions.

The frozen launcher's `--self-test OUTPUT --gen5-self-test ROM --save-pair FIRST SECOND` options exercise the packaged read-only tools. Use a disposable `--home` directory for these checks. Release 1.0.3 retains the unchanged modified melonDS 1.0.2 executable. Older GitHub release assets are preserved.
