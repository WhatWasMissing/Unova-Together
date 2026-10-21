# Unova Together 2.0.24 release checks

This release packages the launcher navigation and settings improvements from
2.0.24. The emulator/gameplay changes from 2.0.23 are carried forward without
new gameplay or ROM-patch changes.

## Verification

- **Launcher tests:** 113 canonical launcher tests passed.
- **Release and patch-note tests:** 7 tests passed.
- **Launcher parity:** the canonical and maintenance UI trees match across 49
  files.
- **Launcher build:** the Windows launcher and bootstrap built with Python
  3.12.8 and PyInstaller 6.22.3. Both packaged build metadata files report
  version 2.0.24.
- **Emulator build:** the Windows Release build passed with CMake 4.4.1,
  Ninja 1.13.2, GCC 16.2.0 and Qt 6.11.2. Emulator FileVersion and
  ProductVersion are 2.0.24. Its SHA-256 is
  `6ae0608538d3f2717d4f0b3014bb6978e02072b7178611e1469ceb45f4ff809a`.
- **Packaging:** the Windows runtime, standalone emulator, repair launcher and
  corresponding-source archive were assembled. ZIP integrity, version
  metadata, keyboard settings, required Windows platform plugin and exclusion
  of ROMs and saves passed packaging validation. The standalone emulator
  matches the packaged runtime. The release source's melonDS files match the
  verified 2.0.24 source base; it contains no unrelated local decomp changes.
- **UI launch:** the built launcher opened as `Pokemon Together · Mod library`.
  Automated screenshot capture timed out on two attempts, so visual inspection
  of the live window could not be completed.
- **Gameplay:** no live gameplay check was run. This release changes launcher
  presentation and metadata only; it does not modify gameplay or ROM patches.

## Source provenance

The emulator source base came from the official 2.0.23 corresponding-source
archive (SHA-256
`311f271b5ebe1f97bee92f28fb01a15e73eeafd169802637e88c30d0490c5f37`). The
2.0.24 source-base archive was made by changing only the emulator's release
version metadata in `src/frontend/qt_sdl/ProjectCredits.h` and `res/melon.rc.in`
(SHA-256
`353b2d169494f4c6286f885606e8c8d5393bdd5d5e1a3a666895b7978fe5e6f8`). The
launcher changes were merged to `main` as commit
`907793a38127ebe4d025eb8883691aea44bcdec9`.

## Release assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12,216,331 | `8be1ed358f3fa452812ebdb9555c658e9b783a994da1998452fc5349933e5019` |
| `SHA256SUMS-Unova-Together-2.0.24.txt` | 378 | `8c4bbfa4f564a35f383965d0d47373ee562c406610c4c045e7d290e73fa59dcd` |
| `Unova-Together-2.0.24-Source.zip` | 33,096,004 | `9aaa56d6069458096c4cd889a974109368667d9bb943e6cd2220a97a3d4df3a3` |
| `Unova-Together-2.0.24-Windows-x64.zip` | 207,582,225 | `b7f488c9de7e5c59cf03e7522d1b188d1a2d508edc6fc49ab7c675057698fad7` |
| `Unova-Together.exe` | 248,243,679 | `6c5c84097544ff28eaa3fc1231f946952112f3acf31a01c8013f2f2040c6af19` |
