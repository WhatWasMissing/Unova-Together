# Unova Together 2.0.30 release checks

## Scope

The launcher now builds optional area-scenery catalogs from the final prepared ROM it passes to melonDS, after Cynthia-event and player-model variants are applied. The emulator checks the catalog against the loaded cartridge's header and asset digest; using the original selected ROM made catalogs for prepared copies fail that check and left native battle backgrounds in place. The emulator binary, ROM patching behavior, multiplayer, XP, and save format are unchanged.

## Verification

- **PASS — SOURCE/UNIT:** The focused area-catalog launch-preparation test passed in both launcher trees. It substitutes separate source, event-patched, and player-model ROM paths and verifies that catalog generation uses the final path, while still running on the launch worker.
- **PASS — FULL LAUNCHER TESTS:** Python 3.12.8 discovery passed with **199/199** tests in `launcher-source/tools` and **256 tests, 10 optional skips** in `maintenance-tools/tools`.
- **PASS — RELEASE METADATA:** The patch-note feed and release-validation tests passed **7/7**; launcher UI parity passed across **43 files**. Both release archives include the 2.0.30 launcher metadata and patch-note entry.
- **PASS — PACKAGE:** Windows and source packages passed ZIP and private-file checks. The runtime `melonDS.exe` is unchanged from the published 2.0.28 binary (SHA-256 `84ad7d0d739d9bd38604162267a5bfca81c402f95c111923234b0c4c36bb684f`). The corresponding-source archive starts from the authenticated v2.0.29 source archive (SHA-256 `744e22a1d8932161bca316db12cbdf397d9d066edfb814d3e61589d5283ccbe2`) and includes this launch-path regression test.
- **PASS — MIRROR:** `py -3.12 -B check_launcher_tree_parity.py` confirmed launcher UI trees match.
- **PASS — RUNTIME SOURCE REVIEW:** The matching v2.0.29 source archive was fetched from the official GitHub release and inspected in memory. Its `AreaBattleScenes.h` validates the catalog against the loaded cartridge's header and post-secure-area asset digest.
- **NOT RUN — GAMEPLAY:** A packaged game battle was not used to visually confirm the replacement background. Check an outdoor and indoor battle with **Area battle scenery** enabled, then disable it and confirm the original backgrounds return. Special battles can retain their native scenes.

## Regression test provenance

The changed test executes the real launcher launch-preparation path with stubbed ROM-variant and catalog functions; it verifies which file path is passed through, not ROM bytes or native background rendering. It ran with Python 3.12 using the production modules in this repository revision. The native-loader compatibility premise was independently confirmed from the official v2.0.29 source release archive; no user ROM, save, or test installation was opened or changed.

## Prepared release assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12,217,137 | `f82c1673ad23280c279fbf089110d647a94fd01fe0eb2e558661e81297b546f1` |
| `SHA256SUMS-Unova-Together-2.0.30.txt` | 378 | `aa460eb97e4f6a07b1c9cc23537a93df2d91b222cf550e8bf697075fa8d8557f` |
| `Unova-Together-2.0.30-Source.zip` | 33,017,404 | `9ea54939188692f6c521c73568dc12234ac8ade4425bb3c6b9b09329c547f6d2` |
| `Unova-Together-2.0.30-Windows-x64.zip` | 207,427,301 | `dc5826d8eb953e520fb736d26cb9bf759df1c0d33176b4da7e5164cd9ee00d27` |
| `Unova-Together.exe` | 247,993,907 | `9e30cb59ab750052889b87b24441002987792837f54a7c889352d45191b95aad` |
