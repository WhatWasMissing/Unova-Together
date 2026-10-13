# Maintenance tool source snapshots

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
