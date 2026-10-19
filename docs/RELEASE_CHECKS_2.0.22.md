# Unova Together 2.0.22 release checks

This release puts item trades under **Unova → Players → Give item** and restores the game’s normal **Options** entry in the pause menu.

## Verification

- **PASS — SOURCE / UNIT:** `py -3.12 -B maintenance-tools/tools/test_native_options_menu.py` passed **2/2**. The test structurally checks the native menu hook in the development patch and confirms the Unova Players action still opens item trade. It does not execute the game.
- **PASS — REGRESSION TESTS:** `py -3.12 -B maintenance-tools/tools/test_gen5_shop_overlay_patch.py` passed **7/7**; `py -3.12 -B maintenance-tools/tools/test_cynthia_practice_catalog_patch.py` passed **3/3**; `py -3.12 -B -m unittest test_patchnotes_feed test_launcher_versioning test_release_validation` passed **21/21** from `launcher-source/tools`; `py -3.12 -B check_launcher_tree_parity.py` matched **49 files**.
- **PASS — EMULATOR BUILD:** Incrementally rebuilt the Windows `melonDS` target from the 2.0.21 corresponding source tree with the menu change. CMake 4.4.2, Ninja 1.13.2, MSYS2 UCRT64 GCC 16.2.0, and Qt 6.11.2; Windows 10 build 19045. The command was `$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH; & 'C:\msys64\ucrt64\bin\cmake.exe' --build maintenance-tools/builds/release-2.0.21-cmake --target melonDS --parallel 4`. The executable reports ProductVersion and FileVersion **2.0.22**. SHA-256: `60dafbeea5647abe8ddc957084b7af4b0269d6e2b4289d4f5f656ad6a7cc4f45`.
- **SOURCE PROVENANCE:** The source base was the 2.0.21 corresponding-source release archive, SHA-256 `a118bf1a85e7525d85a8c0fe3fb30b9da5c43ced766884bdb4eee8b580f78a34`. Comparing the build tree against that archive found only the intended menu hook and the 2.0.22 version-resource/fallback labels. The menu regression test checks source text; the emulator build compiles the modified `ARM.cpp` but does not prove the menu hook in live gameplay.
- **PASS — PACKAGE:** `py -3.12 maintenance-tools/tools/package_unova_release.py --version 2.0.22 --runtime-root maintenance-tools/builds/release-runtime-2.0.22 --launcher-root "maintenance-tools/builds/release-launcher-2.0.22/Pokemon Together" --artifact-dir maintenance-tools/downloads/releases/release-2.0.22 --pyinstaller-python C:/Users/novel/AppData/Local/Programs/Python/Python312/python.exe` produced the Windows ZIP, corresponding-source ZIP, standalone EXE, repair launcher, and checksum file. The package builder verified ZIP integrity, launcher/emulator versions, source inclusion, and excluded ROMs, saves, firmware, and other private files. The emulator, launcher, bootstrap, repair launcher, and standalone executable all report version **2.0.22**.
- **PASS — GITHUB RELEASE:** [v2.0.22](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v2.0.22) is published and is the latest release. Its tag resolves to `3d71a2e08d8ded5554800e188adabc8ac543bb26` on `main`; GitHub-reported asset names, sizes, and SHA-256 digests match the table below.
- **NOT RUN — GAMEPLAY:** The pause menu and item trade were not exercised in a live game after this build. The menu change is compiled and packaged; in-game behavior remains to be confirmed by a player.

## Release assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12,216,609 | `c6725b30f88e1d97ead5323e42fc6fb7db255faad02a4e8c6cf2800833752f7a` |
| `SHA256SUMS-Unova-Together-2.0.22.txt` | 378 | `37a51c00fb1afa53597d2ea2a15a9ce7e30052c007c64456dfe2d2ecc97ead2b` |
| `Unova-Together-2.0.22-Source.zip` | 31,822,740 | `e0b423733748efe8dbe5297a6c21e66d54908c36071ccb14bf7727621b7a1c50` |
| `Unova-Together-2.0.22-Windows-x64.zip` | 206,531,553 | `65c59c72379d382be9690b6f9ae6969caf1cb5cebd2d74547be0b87979035fa8` |
| `Unova-Together.exe` | 245,951,216 | `1d867117cc7b7e202ad57592a2bc7b6be7af93f2ba841eb65bc53cc52dc5b892` |
