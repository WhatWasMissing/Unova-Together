# 1.0.20 release checks

## Mega Serperior battle crash fix

- Rebuilt the Windows emulator with the public roster enabled: Mega Serperior only.
- Replayed the user's exact Mega-armed slot 4 state against the supported Redux ROM in both JIT and interpreter modes.
- Both battle copies reached Mega form with stats `94 / 115 / 121 / 102 / 131`, Contrary, and 147/147 HP. The saved party was unchanged and battle teardown completed without a crash screen.
- The public-config Mega regression suite passes 7/7, including the full Redux ROM overlay test.
- A two-emulator live Mega battle remains a playtest item.

## Patch notes feed

- The launcher reads `patchnotes/index.json` from GitHub's `main` branch, independently of the GitHub Release list.
- Feed tests check that the newest note appears first and each version links to a file in `patchnotes/`.
- All 31 notes are retained in the folder; older GitHub Release entries are not required for displaying them.

## Art distribution

The user confirmed that the supplied Mega artwork may be used in the public mod provided it is not sold for monetary gain. This project is distributed free of charge; existing artwork and upstream notices are retained.


## Local package fingerprints

These hashes identify the published release artifacts. GitHub's asset digests were checked against every local file before publication.

- Runtime emulator: `builds/release-runtime-1.0.20/melonDS.exe` — SHA-256 `79f6e57ddfce8a86ea1b6c5d09e854256d7002bcdf20add280ef6b6b04e5aa35`
- Windows x64 runtime ZIP: `downloads/releases/release-1.0.20/Unova-Together-1.0.20-Windows-x64.zip` — SHA-256 `0e76095368f0d2691ddaf16061ce48587b35e086a096ae0960731028f2e4b225`
- Source ZIP: `downloads/releases/release-1.0.20/Unova-Together-1.0.20-Source.zip` — SHA-256 `ff60cd6126a48286d64591f8f4fc7cbd168e9d317c0108db82beb21101054470`
- Standalone launcher: `downloads/releases/release-1.0.20/Unova-Together.exe` — SHA-256 `0f9c8657f4b09c8fff88f38e467c6fca5edf6f2a7f97be0a9c08ad5748398358`
- Repair launcher: `downloads/releases/release-1.0.20/Repair-Launcher.exe` — SHA-256 `e2f2d2699aa6657ffcc3459269698364f769d80b5ceeb45bb65e8de751b628b3`
- The Windows runtime archive contains `patchnotes/index.json`; the source archive contains `Gen5MegaSpriteAssets.h`.

## Publication

- Published all five assets for [v1.0.20](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v1.0.20) on 15 October 2026. GitHub's latest-release endpoint selects this version.
- Publishing used the existing account credential without opening authentication UI. A stale repository-specific credential caused earlier HTTP 401 failures; the publisher now tries the cached account credential and disables interactive sign-in for every attempt.

## Public launcher download verification

- The production updater downloaded the public GitHub runtime ZIP, verified its checksum, and installed it into an isolated test home.
- Version selection, archived patch notes, the Windows Qt plugin, settings preservation, and a save sentinel all passed. No downloaded executable was run.
- Result: `{"downloadBytes": 179089509, "emulatorSha256": "79f6e57ddfce8a86ea1b6c5d09e854256d7002bcdf20add280ef6b6b04e5aa35", "newsSource": "patchnotes", "patchNotes": 31, "saveSentinelPreserved": true, "settingsPreserved": true, "version": "1.0.20", "windowsQtPluginPresent": true}`
- The generated download and extracted test installation were removed after recording these results.
