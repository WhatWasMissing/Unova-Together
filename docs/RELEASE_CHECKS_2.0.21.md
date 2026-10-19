# Unova Together 2.0.21 release checks

This release enables co-op EXP suppression by default while keeping the launcher setting switchable. The EV reset prompt now names both choices clearly and selects **No, keep them** first.

## Verification

- **PASS — LAUNCHER TESTS:** `py -3.12 -B -m unittest test_launcher_ui test_launcher_preferences` passed **48/48** from `launcher-source/tools`. Coverage includes the default-on setting, profile persistence, and both values passed to the game.
- **PASS — PATCH/FEED TESTS:** `py -3.12 -B maintenance-tools/tools/test_gen5_shop_overlay_patch.py` passed **7/7**. `py -3.12 -B -m unittest test_patchnotes_feed test_release_validation` passed **7/7**. Launcher UI parity matched **49 files**.
- **PASS — EMULATOR BUILD:** Built all **209** steps with MSYS2 UCRT64 GCC **16.2.0**, CMake **4.4.1**, and Qt **6.11.2** on Windows 10 build **19045**. The executable reports ProductVersion and FileVersion **2.0.21**; its SHA-256 is `52668417fde1402961ee90464fa95293039e4b1aa6639838c20942ff6732bfc7`.
- **SOURCE PROVENANCE:** The build source tree was based on the published 2.0.20 corresponding-source archive, whose SHA-256 is `6733323db3aa0e5121c2ea43c17ba10b800491257938eef8d68ad16ecd07224b`. Before editing, `MultiplayerPanel.cpp` matched the archived file byte-for-byte. The release source archive contains the changed EV prompt and version metadata used for this build. This records the source bytes used; it does not claim an upstream source signature.
- **PASS — LAUNCHER SMOKE TESTS:** The packaged launcher and standalone download both opened in isolated test homes and reported **Release 2.0.21 · Launcher 2.0.21**. They loaded the launcher pages and artwork and kept Play disabled without a ROM.
- **PASS — PACKAGE:** Both ZIP archives passed integrity checks. The package script verified the runtime fingerprint against the source header and found no ROM, save, RAM dump, key, or firmware files.
- **NOT RUN — GAMEPLAY:** The EV confirmation was compiled and checked in the source patch, but was not exercised with a controller in a live game. Co-op EXP behavior was not tested with two clients.
- **PASS — GITHUB RELEASE:** [v2.0.21](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v2.0.21) is non-draft and the latest release. Its tag resolves to commit `cc892a890511861f5e8bd043d6b8893afbe941a2`, now on `main`. GitHub asset sizes and digests match the prepared files.

## Release assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12,216,749 | `4b9565d5a2eaaa7ac939808855ba2cb9f63217562ce60b273cd050cef5e4ffac` |
| `SHA256SUMS-Unova-Together-2.0.21.txt` | 378 | `f6d177d4af1a5fb3a91d7eba7738765ff590e63e58ce012b8f72b5feca8c345b` |
| `Unova-Together-2.0.21-Source.zip` | 31,821,556 | `a118bf1a85e7525d85a8c0fe3fb30b9da5c43ced766884bdb4eee8b580f78a34` |
| `Unova-Together-2.0.21-Windows-x64.zip` | 206,532,244 | `805d0bd6dd7fafae1bc9eb0b9a23c299a730f159af2aa7f939d1765071aab8df` |
| `Unova-Together.exe` | 245,949,212 | `140d559e753bf703c52972d994f88d12b3d5a5044f14995a6f1d33488c87e1e0` |
