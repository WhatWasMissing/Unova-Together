# Maintenance tool source snapshots

**Client migration 1.0.9:** `launcher-source/tools/launcher_migration.py` and `unova_launcher_bootstrap.py` implement the permanent entry and repair utility. Build the bootstrap with `build_unova_bootstrap.py`, then pass its executable through `build_unova_launcher.py --bootstrap`. The 1.0.9 native patch contains version/credit labels only and records the 1.0.8 source baseline checksum. Existing 1.0.5 clients run the repair utility once; subsequent launches follow their active update slot.

**Launcher 1.0.8:** the current launcher overlay fixes update handoff and reads the running build's embedded identity. `patches/launcher-version-1.0.8.patch` updates only the native resource/credit labels on the published 1.0.7 source; its JSON records the baseline archive checksum. Use the complete 1.0.8 source download for a direct rebuild. Older shared launchers need the one-time startup step in `../patchnotes/RELEASE_NOTES_1.0.8.md`.

**Current development delta:** `patches/development-polish.patch` supersedes the companion-defaults patch and applies directly to the published 1.0.6 source ZIP. Copy `assets/followers/variants` to `source/melonDS/res/followers/variants` and overlay the tools. See `docs/DEVELOPMENT_POLISH_2026-10-13.md` in the repository for reconstruction, validation and limitations. Asset credits/terms remain beside the variant folder.

Unova Together maintenance by mvq1303 / WhatWasMissing, built on melonDS. These helper sources are covered by the repository GPL license. Preserve upstream attribution. Frost and PKHeX are separate tools downloaded from their official projects; their binaries and source are not vendored here.

These are follow-up helpers developed after the immutable 1.0.2 release assets. Copy this `tools` directory over the corresponding-source workspace `tools` directory to use the updated helpers. ROMs, saves and private fixtures are deliberately excluded. The native battle/reload runners require the private fixture layout documented in the matching source and are not general-purpose player utilities.

See `docs/GEN5_EDITOR_WORKFLOW.md`, `docs/GEN5_SAVE_INSPECTION.md` and `docs/XP_COMPENSATION_BATTLE_TEST.md` in the repository. Python requires ndspy for ROM inspection and Unicorn for the read-only badge getter. The save inspector requires .NET 10 and the official PKHeX.Core build at the documented commit. Download/install provenance is retained locally.

Frost: https://github.com/FrostFalcon/FrostsGen5Editor
PKHeX: https://github.com/kwsch/PKHeX

The imported `crypt` function is used only to decode records during verification. The fixture-healing utility is retained as source for that import; it is not called to manufacture a battle or save/reload result.

## Follower defaults and feature review — 13 October 2026

The current launcher source (also in `launcher-source`) has a revised Features page, feature/roadmap guides and normal **Following Pokémon** settings. Companion interactions default on when no preference was saved; explicit off choices survive save-slot switches, restart and launch. The launcher supplies the new `UNOVA_COMPANION_INTERACTIONS` variable and the legacy variable for existing released runtimes.

`patches/companion-defaults.patch` contains the corresponding native change relative to the published **1.0.6 source ZIP**, preserving attribution. From its extracted `Unova-Together-Source` folder, apply the patch with `git apply --ignore-space-change /path/to/companion-defaults.patch`, then build with `source/melonDS/README.md`. This makes direct emulator launches default on too; an explicit new/legacy environment override still controls it. It does not alter the interaction or A-button gates.

Compile the production interaction/default-policy checks with `python tools/test_companion_and_soaring.py` after overlaying these tools onto the source workspace. Launcher checks are `test_launcher_ui.py`, `test_launcher_services.py` and `test_launcher_preferences.py`; use Python 3.12 with TOMLKit and Pillow. No live ROM gameplay session is implied by these tests. Existing public release assets are unchanged.

## Soaring regional debug — development follow-up after 1.0.11

`patches/soaring-region-debug.patch` applies to the published 1.0.11 source header; its JSON manifest records baseline and result hashes. Overlay this directory's `tools` onto the source workspace as usual. It adds the profile-scoped **Show Soaring collision data (debug)** setting, ROM collision sampling and scenic flyway connectors for disconnected chunks in the main Unova matrix. Flyways are visual only; they do not create collision or landing points. Run `python tools/test_soaring_scene_worker.py`, the launcher tests, and compile/run `tools/check_soaring_scene.cpp` after applying the native patch. These changes are development work; the public 1.0.11 release assets remain unchanged.

Release 1.0.12 includes these changes in its matching emulator and launcher. Empty matrix cells use decorative ocean, forest islets and visual flyways; authored NPC event positions are excluded from landing candidates; returning to take-off asks for confirmation; and game input remains blocked until the native landing warp reaches its target and settles. Fixed-step flight updates and a cached scene frame reduce flicker during speedup. The collision-data setting remains optional and profile-scoped. The corresponding complete source is in the 1.0.12 source download. The patch above remains a historical delta from the 1.0.11 baseline.
