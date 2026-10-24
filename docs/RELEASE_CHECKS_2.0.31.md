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
