# Release 2.0.35 verification

This release adds the exact-build actor dialogue-art authoring tool and its sample artwork to the standard Windows and corresponding-source packages. It does not change the launcher or emulator gameplay binary. The new tool is verified for one exact English Redux v1.4.1 ROM fingerprint; its compatibility limits and live scenario are documented in [the renderer verification record](verification/ROM_DIALOGUE_ART_RENDERER_2026-10-24.md).

## Dialogue renderer evidence

- PASS: focused patcher and compiled CPU suite, 15 tests.
- PASS: exact-profile nurse interaction rendered the portrait, nameplate, frame, and native text; page advance, Yes/No, close/reopen, stock fallback for an unconfigured NPC, and leaving the map were exercised.
- PASS: tested source ROM and save were unchanged; the public packages exclude private ROMs and saves.
- NOT RUN: DSi mode, real hardware, two-client co-op, and all NPC/window styles.

Reproduce the source and CPU tests from the repository root with the packages in `maintenance-tools/tools/rom/requirements.txt` and ARM GNU tools available:

```powershell
py -3 -m unittest maintenance-tools.tools.rom.test_dialogue_art_patch maintenance-tools.tools.rom.test_dialogue_art_hook_cpu -v
```

The CPU suite compiles production C and runs it in Unicorn with explicit stubs for game rendering/allocation calls. It does not replace the separate live-game evidence.

## Release-source checks

- PASS: 70 launcher UI, versioning, patch-note feed, and release-guard tests with CPython 3.12.8.
- PASS: launcher UI mirror check; all 43 files match.
- PASS: the reused melonDS executable's embedded shop-patch fingerprint matches the 2.0.34 source archive's `Gen5ShopOverlayPatch.h`. The archive SHA-256 is `de592d351d8e2ea24f8b79769bf4d7ebdb6445e1ebc23183c95c0421902ac0bb`; the executable SHA-256 is `f8a6b7071f13bd151e714327c7f00a22c94fefe6e763d1b8b09307a88524d9ca`.
- Package creation is validated separately by `launcher-source/tools/package_unova_release.py`; the post-build release record reports archive, private-file, version/feed, and publication checks.

## Release integration

The Windows ZIP and corresponding-source archive include the patcher, native helper source, dependencies, example profile, original artwork and credit, testing instructions, and verification record. The standard app downloads remain ROM/save-free. Release build/package checks and remote asset verification are reported in the final release record.
