# Unova Together 2.0.31 release checks

## Branch audit and scope

Remote main at intake: `698dca5c90d25baf1617afb8e89641817d19e101`.
Merged all three current forward branches: `0033fc8cb3bd562af8b8219c8991955e7b9833f1` (2.0.30 scenery launch fix), `aa7276ce3e77aa162b43db8931ef0e66dd57d3ea` (trainer outfit filter), and `3cbad2c294e2c597910a9cf980e41305231b5b58` (dialogue authoring workflow). Other active feature worktrees have no commits ahead of remote main. Two obsolete local 1.0.x branches have one divergent historical commit each and were excluded. Existing dirty worktrees were preserved.

## Checks

- PASS — SOURCE/UNIT VERIFIED: Windows 10, Python 3.12.8; `py -3.12 -B -m unittest discover -s launcher-source/tools -q`: 201 tests.
- PASS — SOURCE/UNIT VERIFIED: `py -3.12 -B -m unittest discover -s maintenance-tools/tools -q`: 277 tests, 10 optional skips. Expected negative-control CLI usage errors appeared; the suite finished OK.
- PASS — MIRROR: `py -3.12 -B launcher-source/tools/check_launcher_tree_parity.py`: 43 matching UI files.
- PASS — BUILD: PyInstaller 6.22.3 rebuilt the launcher and bootstrap with 2.0.31 metadata.
- PASS — LAUNCHER RUNTIME: isolated frozen launcher `--home <disposable-home> --self-test <result.json>` exited 0; window creation, no-ROM disabled Play, update control, settings, credits at three window sizes and cleanup entry all passed. No ROM or save was opened.
- NOT RUN — GAMEPLAY / TWO-CLIENT INTEGRATION: no live game or multiplayer session was run. Test the Trainer outfits filter, select a model and launch; check outdoor/indoor scenery with the optional setting on/off. Dialogue tools generate local previews/archives; they do not install an in-game event.

## Package provenance and cleanup policy

Reuse the unchanged 2.0.30 staged emulator, expected SHA-256 `84ad7d0d739d9bd38604162267a5bfca81c402f95c111923234b0c4c36bb684f`, with native corresponding source preserved from the official 2.0.30 source archive, SHA-256 `9ea54939188692f6c521c73568dc12234ac8ade4425bb3c6b9b09329c547f6d2`. The new source archive includes the outfit regression test, dialogue tools, demo and workflow guide.

After publication, verify all remote asset names, sizes and SHA-256 digests and latest-release discovery before cleanup. Retain v2.0.30 as rollback; remove superseded GitHub releases v2.0.25–v2.0.29 and v2.0.30-dialogue.1, keeping Git tags/history and local release archives. Remove only this task's verified disposable build/test work after recording results.

## Final local assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12217889 | `8c8124d9e822de7e43d978454b41b8de75d949e0894e837d6cfcc3083ee553bb` |
| `SHA256SUMS-Unova-Together-2.0.31.txt` | 378 | `c397ccb0237ca11ada03ddc83131edf9c8e11ac09ae6416ebef84eec7de1f673` |
| `Unova-Together-2.0.31-Source.zip` | 33042372 | `5ec9e9ff7dd6c2456bbb6e87cb69a67d56e673fa626376e4ad7351cefe931427` |
| `Unova-Together-2.0.31-Windows-x64.zip` | 207431262 | `9704551c1d3b0157a6e22a97e1336c5f680acea3158fe19911b1b23583e489ed` |
| `Unova-Together.exe` | 247998753 | `bb012af50e7ae6884704b937973741c4bbe20de895c31ec3af1f322c20e7677c` |

PASS — PACKAGE: both ZIPs passed integrity/private-file/version/control checks. All 2,388 native source files match the authenticated official 2.0.30 source archive; merged launcher code and all four dialogue tool/test files match this checkout. Frozen startup evidence is recorded above.

## Publication and final cleanup

- PASS — PUBLISHED: v2.0.31 targets reviewed remote commit `31420ff4d5c6e98d598780e40847017aba3dc7e6`. All five GitHub asset names, byte sizes and SHA-256 digests match local artifacts. `/releases/latest` returns v2.0.31.
- PASS — LIVE LAUNCHER FEED: the production `unova_updater.launcher_feed()` fetched public main patch notes and selected 2.0.31 for both newest News and latest update.
- PASS — OLD RELEASE CLEANUP: removed v2.0.25, v2.0.26, v2.0.27, v2.0.28, v2.0.29 and superseded v2.0.30-dialogue.1. The release list contains v2.0.31 and rollback v2.0.30 only. Git tags/history and local release artifacts remain. Public metadata and asset digests before removal are recorded in `docs/verification/RELEASE_2.0.31_PUBLICATION.json`.
- BLOCKED — LOCAL TEST CLEANUP: automatic approval review rejected the verified disposable-folder deletion command as “blocked by policy.” No retry or alternate deletion was attempted. This task's bootstrap, frozen launcher, isolated self-test and single-EXE build fixtures remain untracked. Generated release stages and launcher outputs also remain; they are excluded from commits and release ZIPs.
- NOT RUN — GAMEPLAY: source/unit, frozen launcher startup and package/publication verification do not establish live gameplay or two-client behavior.
