# Unova Together 2.0.25 release checks

This release adds a launcher picker for animated overworld characters available
in the selected game profile. No emulator gameplay code or ROM patches were
changed for this feature.

## Verification

- **Launcher tests:** 41 launcher UI tests passed; 74 model, preferences,
  services, versioning, patch-note and release-validation tests passed.
- **Launcher parity:** canonical and maintenance launcher trees match across
  51 files.
- **Launcher builds:** standalone launcher and bootstrap built with Python
  3.12.8 and PyInstaller 6.22.3. Both launcher and repair executable report
  version 2.0.25.
- **Emulator build:** Windows Release build succeeded with CMake 4.4.2, Ninja
  1.13.2, GCC 16.2.0 and Qt 6.11.2. The emulator reports FileVersion and
  ProductVersion 2.0.25. Existing Mega shop-overlay source fingerprint is
  present in the built runtime.
- **Packaging:** runtime and corresponding-source ZIP integrity passed; the
  package validator confirmed the Windows Qt platform plugin, release versions,
  controls configuration, patch-note index, source inclusion and required
  checksums. ROMs, saves, firmware, credentials and forbidden private file
  extensions were absent. The corresponding-source archive includes the
  player-model catalog and its tests.
- **Source provenance:** the source base is the official 2.0.24 corresponding
  source archive (SHA-256
  `9aaa56d6069458096c4cd889a974109368667d9bb943e6cd2220a97a3d4df3a3`). All
  2,385 source files other than the two version-metadata files match that
  archive byte-for-byte. `ProjectCredits.h` and `res/melon.rc.in` identify
  version 2.0.25.
- **Not run:** visual inspection of the packaged launcher and live gameplay
  checks. Automated launcher tests and packaging checks passed; the feature
  changes the launcher selection and relies on the game's existing field
  model resources.

## Release assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12,216,511 | `1ff534665834974e3f7f1027a52fead3807ce1453c23d379003a976223f34ef4` |
| `SHA256SUMS-Unova-Together-2.0.25.txt` | 378 | `2671ad3bc28a84732b2cfc640bf1b1b812cdb77f1a9aae2f42ee044376073d10` |
| `Unova-Together-2.0.25-Source.zip` | 33,129,605 | `b6f5d1e708b9baf7c4a89547b5839b21fd8a91f73f9d7b5cbf0b25622a359ac5` |
| `Unova-Together-2.0.25-Windows-x64.zip` | 207,625,011 | `9a0b190a8fd1df14789c44b1594a034f9fb1b618aa6738a601e813d8477ff38a` |
| `Unova-Together.exe` | 248,200,136 | `56e4836801e539247b46b3820fcc775f91fc7e2b9b0ea88a673506abed403c73` |
