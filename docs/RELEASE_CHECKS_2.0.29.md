# Unova Together 2.0.29 release checks

## Scope

This is a launcher reliability release for the “Preparing Cynthia” launch stall. Optional area-scenery catalog generation now runs in the launch worker, and launch-handoff errors restore the launcher controls and polling. The game runtime is unchanged from 2.0.28; no ROM, gameplay, multiplayer, XP, or save-format changes are included.

## Verification

- **PASS — LAUNCHER TESTS:** `py -3.12 -B -m unittest test_launcher_ui -v` passed 49 tests in both `launcher-source/tools` and `maintenance-tools/tools`, including the area-catalog background-preparation, Cynthia preparation recovery, and unexpected handoff error paths.
- **PASS — FEED AND RELEASE GUARDS:** `py -3.12 -B -m unittest test_patchnotes_feed test_release_validation -v` passed 7 tests.
- **PASS — MIRROR:** `py -3.12 -B check_launcher_tree_parity.py` confirmed the launcher UI trees match across 43 files.
- **PASS — PACKAGE:** The 2.0.29 Windows and source archives passed integrity and private-file checks. The package contains the 2.0.29 launcher metadata and required player guides. Its corresponding native source matches all 2,388 native files from the official 2.0.28 source archive. The reused emulator executable matches the published 2.0.28 binary (SHA-256 `84ad7d0d739d9bd38604162267a5bfca81c402f95c111923234b0c4c36bb684f`).
- **PASS — PUBLISHED:** GitHub release [v2.0.29](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v2.0.29) points to commit `04d27f678d6dee1cbe5ebb1b77e65aba65b64a3f` and is returned by latest-release discovery. The patch-notes feed on `main` lists 2.0.29 first. All five release asset names, sizes, and SHA-256 digests match the uploaded assets.
- **NOT RUN — LIVE GAME:** The packaged launcher was not opened against a real ROM and no in-game launch was performed. The worker and recovery behavior is covered by automated launcher tests; a player-side launch test remains useful.

## Published assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12,216,501 | `8798dc0ab07ad222826266b29195d2dd1c2a55d04a23e799d9a56bde37b5726a` |
| `SHA256SUMS-Unova-Together-2.0.29.txt` | 378 | `cf9f49cb4c52ef00361f7d7abd5d3a5371c9f2ad8afb625ceb6b686561d9a03b` |
| `Unova-Together-2.0.29-Source.zip` | 33,017,113 | `744e22a1d8932161bca316db12cbdf397d9d066edfb814d3e61589d5283ccbe2` |
| `Unova-Together-2.0.29-Windows-x64.zip` | 207,425,423 | `50b82aed7544ee45699efab2f4c2d1a87369e29ede8dd303496c24700fba5281` |
| `Unova-Together.exe` | 247,992,015 | `b2a189df35908897d6b5ab37b120cc41b7ad475d5f83e7a32bd5ead91c2a67b6` |
