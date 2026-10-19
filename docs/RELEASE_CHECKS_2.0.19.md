# Unova Together 2.0.19 release checks

Date: 2026-10-19. This release packages the Mega Stone shop crash fix, the field-zone relay data required by Teleport, and the optional co-op EXP suppression setting for testing.

## Verification

- **PASS — SOURCE/UNIT VERIFIED:** The complete launcher suite passed **169/169** tests. The maintenance suite passed **225** tests with **6 optional skips**. The launcher UI source trees match across all **48** files.
- **PASS — SOURCE/UNIT VERIFIED:** The Mega shop patch suite passed **7/7**. Presence relay tests ran as part of the maintenance suite, including field-zone forwarding and malformed-zone rejection. The opt-in co-op EXP source check passed all **6** conditions, and the C++ policy/guard fixture compiled and passed using the production headers.
- **PASS — TEST PROVENANCE:** The new portable tests accept `--source-root`; the C++ runner accepts `--compiler` and compiles the production `CoopRewardPolicy.h` and `CoopExperienceGuard.h`. The source root used here was extracted from the 1.0.6 corresponding-source archive (SHA-256 `c3833116062ed40811a252ae1945a23a7043694c1984d3c8ae3cc0ac6212dd25`). That digest identifies the baseline archive only. The working melonDS tree contains local changes and is **UNVERIFIED SOURCE** as proof of the released upstream build.
- **PASS — BUILD VERIFIED:** The Qt/SDL Windows emulator built in Release mode with MSYS2 UCRT64 GCC 16.2.0, CMake 4.4.1, Qt 6.11.2, and OpenGL enabled. The target completed all **209** build steps. The staged emulator reports product and file version **2.0.19**. Its embedded shop-patch fingerprint matches `Gen5ShopOverlayPatch.h` in the packaged source tree.
- **PASS — BUILD VERIFIED:** The 2.0.19 launcher and repair bootstrap were rebuilt with Python 3.12.8 and PyInstaller 6.22.3. The frozen launcher self-test showed **Release 2.0.19 · Launcher 2.0.19**, created its window, loaded 13 pages, 60 offline patch notes, and 11 artwork entries, and kept the Play button disabled without a ROM.
- **PASS — PACKAGE VERIFIED:** `package_unova_release.py` created and validated both ZIPs, the standalone download, repair launcher, and checksum file. Both archives pass ZIP integrity checks. The Windows archive contains the 2.0.19 patch notes; the source archive contains both new portable co-op tests. The source archive has **1,965** entries and contains no ROM, save, RAM dump, key, or firmware file extensions covered by the release scan.
- **PASS — STANDALONE INSTALL EXTRACTION:** Running the standalone download created an active 2.0.19 install slot. Its extracted `VERSION.txt`, emulator executable, and launcher executable were present. The standalone GUI self-test did not produce a report in this run, so this verifies extraction and version metadata, not normal launcher startup from the single-file download.
- **PASS — GITHUB RELEASE:** The `v2.0.19` release is the repository's latest release. GitHub reports the expected names, byte sizes, and SHA-256 digests for all five uploaded assets; each matches the prepared local asset and checksum file. See the [2.0.19 release](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v2.0.19).
- **PASS — LOCAL CHECKSUMS:** Every asset matches the release checksum file. Asset names, byte sizes, and SHA-256 values are listed below.
- **NOT RUN — GAMEPLAY/INTEGRATION:** The 2.0.19 package was not tested in a live game session. The merchant buy screen, Teleport with a freshly restarted relay, and co-op EXP suppression with two players remain unverified in-game. Source and relay tests do not establish those runtime behaviors.

## Reproduction commands

```powershell
py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'
py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'
py -3.12 -B maintenance-tools/tools/test_coop_experience_flow.py --source-root maintenance-tools/melonDS-source-1.1
py -3.12 -B maintenance-tools/tools/test_coop_reward_policy.py --source-root maintenance-tools/melonDS-source-1.1 --compiler C:\msys64\ucrt64\bin\g++.exe
py -3.12 -B launcher-source/tools/check_launcher_tree_parity.py
```

## Prepared assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12,216,717 | `22318cf6a45b475f6eb9c1545746f686fcdab7a0138c17a6ace01924ddcc49fb` |
| `SHA256SUMS-Unova-Together-2.0.19.txt` | 378 | `b998381dfb22736b311d1d95830390b59b8446e6951f43720a553db4d62c8ab5` |
| `Unova-Together-2.0.19-Source.zip` | 31,817,822 | `4e39b8ae044cb86e5ea48dac933b106a60d75a683d9ede2b457f62dbe03056cc` |
| `Unova-Together-2.0.19-Windows-x64.zip` | 206,521,564 | `162b3bd3e33abc655943089e8d7dc307855794b9f1de8339f8cc97f74da50da0` |
| `Unova-Together.exe` | 245,940,239 | `e1546d68266dcfebd4a1323118b1ac9c37cf745e634da991a232172b608a9370` |
