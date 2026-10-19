# Unova Together 2.0.18 release checks

Date: 2026-10-19. Prepared from the current Unova Together repository and the matching maintained emulator source. This release includes the completed launcher reliability changes since 2.0.17, the corrected Center-entry runtime, and Cynthia's Practice catalog fix. No Legendary Researcher NPC was added.

## Verification

- **PASS — SOURCE/UNIT VERIFIED:** `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` ran 168 tests successfully. The corresponding maintenance-tools discovery ran 221 tests successfully with six optional checks skipped.
- **PASS — SOURCE/UNIT VERIFIED:** The launcher UI mirrors match all 48 files. The entry, bootstrap, standalone, updater, storage and migration module mirrors are byte-identical.
- **PASS — SOURCE/BUILD VERIFIED:** The source patch applies to the 1.0.6 source baseline (SHA-256 `c3833116062ed40811a252ae1945a23a7043694c1984d3c8ae3cc0ac6212dd25`). All 88 modified native files match the build source after newline normalization. The release patch SHA-256 is `f01ce7a3d4e6977b7dfc16bcc71f4a3511c82365e6dd4d30bbd0ef06a415e110`. Git reported three existing added blank-line-at-EOF warnings; patch application and file comparisons passed.
- **PASS — BUILD VERIFIED:** The emulator, launcher, permanent bootstrap and standalone download built on Windows 10 build 19045 with Python 3.12.8, PyInstaller 6.22.3, CMake 4.4.1, MSYS2 GCC 16.2.0 and Qt 6.11.2. Emulator, launcher and bootstrap PE product versions are 2.0.18. The initial standalone packaging attempt rejected a nonnumeric launcher revision; the prepared build metadata was corrected to revision 2026101901 before the final package was built.
- **PASS — GAMEPLAY VERIFIED FOR CENTER ENTRY:** The final emulator SHA-256 is `3134719eda6aa2a421bffd4142c6f4de05fb69dcfd4730f4bed4964fad9db30c`. The exact-save Center-entry probe ran for 75 seconds / 4,440 observer frames, reached map 460 at `(7, 19)`, and reported input unblocked. Both captured DS screens were visually inspected and showed the normal Center and C-Gear. The supplied source save and its disposable test copy retained SHA-256 `4336e7e447fa88cd39dce2b7eef44324fa43f87c5722dca1f00dc84d85635ac7`.
- **PASS — PACKAGED LAUNCHER VERIFIED:** The frozen launcher self-test created its window, loaded 13 pages and 11 artwork entries, exposed update checks, disabled Play without a ROM, and displayed `Release 2.0.18 · Launcher 2.0.18`. Credits remained visible and fit the tested window sizes.
- **PASS — STANDALONE INSTALL VERIFIED:** The final downloadable `Unova-Together.exe` installed into a fresh disposable data directory and completed its child launcher self-test. A second run reused one installation slot and again displayed release/launcher 2.0.18. No user installation, ROM or save was used for this installation test.
- **PASS — PACKAGE VERIFIED:** Both ZIP integrity checks passed. The packaged emulator matches the gameplay-tested executable. All 88 modified native files in the source ZIP match the build source byte-for-byte. Packaged README, Features, patch-note feed and attribution/license files match the repository. Scans found no ROM, save, RAM dump, private key or named proprietary BIOS/firmware files. The source ZIP and corresponding source embedded in the standalone are included.
- **PASS — LOCAL CHECKSUMS VERIFIED:** Every entry in the checksum file matches its asset. The expected upload identities are listed below. GitHub asset size/digest and latest-release discovery are checked after upload.
- **NOT RUN — NEW TWO-CLIENT REGRESSION MATRIX:** Release packaging did not rerun the full co-op battle matrix. Existing battle evidence and the unverified Gym Leader Mega AI limits remain documented in `DEVELOPER_TESTING.md`; this release does not claim those limits were resolved.

## Build and packaging commands

```powershell
$env:PATH = 'C:\msys64\ucrt64\bin;C:\msys64\ucrt64\share\qt6\bin;' + $env:PATH
cmake --build maintenance-tools/test-fixtures/center-runtime-rebuild-20261019/build --target melonDS --parallel 4
py -3.12 -B maintenance-tools/tools/package_unova_release.py --version 2.0.18 --runtime-root maintenance-tools/builds/release-runtime-2.0.18 --launcher-root 'maintenance-tools/builds/release-launcher-2.0.18/Pokemon Together' --artifact-dir maintenance-tools/downloads/releases/release-2.0.18-verified
```

The gameplay probe requires a private, marked disposable ROM/save fixture as described in `DEVELOPER_TESTING.md`; game files are not distributed. The release packager uses the current repository's documentation rather than the stale nested repository mirror. Its source-fingerprint guard rejects the old 2.0.17 emulator.

## Prepared assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| Repair-Launcher.exe | 12217764 | `ddbb43b95cfa9bd16cec24c450ff7f7452d56fefd0a0675f3504de5cd996eeb0` |
| SHA256SUMS-Unova-Together-2.0.18.txt | 378 | `4e00f61b6f86677df2136cfd3221a0dc4145a6a839143172878136fdce0e2567` |
| Unova-Together-2.0.18-Source.zip | 31809697 | `c875d2c904a84c129f571f40c227d46e3a0cabf383f9162410dc230aac6a1153` |
| Unova-Together-2.0.18-Windows-x64.zip | 206531737 | `057fcdce1c3af23c59767d097cf19c69f9d023f9d413146c2cd29a0ab4d79268` |
| Unova-Together.exe | 245942324 | `b16e01a039a8e4fdb1bfbfebc820af59d0b1428205ab1868ffb0191ed76d98b6` |
