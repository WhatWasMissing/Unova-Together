# Unova Together 2.0.28 release checks

## Scope

This release moves Cynthia Route 7 ROM hashing and event-copy creation, plus optional player-model variant generation, off the launcher UI thread. It includes the already released 2.0.27 scenery and News-feed commits so `main` and the published release source stay aligned. No new gameplay, multiplayer, XP or save-format behavior is introduced.

Risk: **HIGH** (release and launcher ROM preparation). Base `main` at start: `9e53d01ef3ad8adade78f3fad8507046b06c4517`. Preserve original ROMs and saves. The launcher worker tests use a controlled placeholder ROM; live game startup and patching are not claimed as tested.

## Results

- **PASS — SOURCE/UNIT VERIFIED:** `py -3.12 -m unittest test_launcher_ui -v` — 47 passed. The blocking-worker test checks that Tk continues servicing events during ROM preparation; the error-path test checks Play controls recover after failure.
- **PASS — SOURCE/UNIT VERIFIED:** `py -3.12 -m unittest test_cynthia_event test_player_models test_launcher_preferences test_launcher_tree_parity test_patchnotes_feed test_release_validation -v` — 38 passed after merging the latest `main` News-feed changes. The launcher tree parity test confirms the two shipped UI trees match across 43 files.
- **PASS — NATIVE BUILD:** Configured the exact 2.0.27 corresponding-source tree with CMake 4.4.1, Ninja 1.13.2, GCC 16.2.0 and Qt 6.11.2; built target `melonDS` in Release mode with LTO disabled. The executable reports FileVersion and ProductVersion 2.0.28. SHA-256: `84ad7d0d739d9bd38604162267a5bfca81c402f95c111923234b0c4c36bb684f`.
- **PASS — LAUNCHER BUILD:** Python 3.12.8 and PyInstaller 6.22.3 built the launcher and bootstrap. Their executable version resources, `BUILD_INFO.json` and `VERSION.txt` identify 2.0.28.
- **PASS — SOURCE MATCH:** The source tree matched all 2,388 files in the published 2.0.27 source archive (SHA-256 `9f252681d0bf0100883b1a48efa83071126f0074720a7b9efc8d6bee48e95b96`) before release metadata changed. The packaged 2.0.28 source archive matches all 2,388 files in the build source tree.
- **PASS — PACKAGE:** `maintenance-tools/tools/package_unova_release.py` built and validated the Windows, corresponding-source, standalone, repair-launcher and checksum assets. It confirmed archive integrity, portable controls, launcher/emulator version metadata, source inclusion and exclusion of ROMs, saves, firmware, credentials and other private extensions.
- **NOT RUN — LIVE UI/GAMEPLAY:** No visible packaged-launcher session, real ROM preparation, Route 7 event, or multiplayer session was run. Automated launcher tests exercise the actual Tk event loop with a controlled worker and test doubles.

## Prepared assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12,217,412 | `47dada314bfdcbd3598b53b1f4398919b73b71993969df77d013ce8acd55148b` |
| `SHA256SUMS-Unova-Together-2.0.28.txt` | 378 | `51ecb702463dbffbcc5b428b9c73bff66009b0841a8afb4779228544ecba508d` |
| `Unova-Together-2.0.28-Source.zip` | 33,041,484 | `662797cd39b8848cdd2bf223d7f2b584b4a638f5e2ad6b3e3cf953be4d74422f` |
| `Unova-Together-2.0.28-Windows-x64.zip` | 207,420,114 | `9fd8df3f96d2bd95168b8c8afb3fe7ba1ef30918c666051366a0152514021328` |
| `Unova-Together.exe` | 247,906,692 | `8939a80d83e85078acca11aa5c570703acc2734bb005ff879d01dd641d6068ab` |

Prepared in `maintenance-tools/downloads/releases/release-2.0.28-final/`. The packaged News feed matches the repository's UTF-8 `patchnotes/index.json` byte-for-byte.

## Publication verification

- **PASS — MAIN:** Merged branch work was pushed to `main` at `b3235fa3e7fe0a39663c8f0fa3e021fa44eb92e3`.
- **PASS — RELEASE:** [GitHub release 2.0.28](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v2.0.28) points to that commit and is returned by GitHub's latest-release endpoint.
- **PASS — ASSETS:** All five uploaded assets match the prepared package's names, byte sizes and SHA-256 digests listed above. GitHub reports the same digest for each uploaded asset.
