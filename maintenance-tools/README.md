# Maintenance tool source snapshots

Unova Together maintenance by mvq1303 / WhatWasMissing, built on melonDS. These helper sources are covered by the repository GPL license. Preserve upstream attribution. Frost and PKHeX are separate tools downloaded from their official projects; their binaries and source are not vendored here.

These are follow-up helpers developed after the immutable 1.0.2 release assets. Copy this `tools` directory over the corresponding-source workspace `tools` directory to use the updated helpers. ROMs, saves and private fixtures are deliberately excluded. The native battle/reload runners require the private fixture layout documented in the matching source and are not general-purpose player utilities.

See `docs/GEN5_EDITOR_WORKFLOW.md`, `docs/GEN5_SAVE_INSPECTION.md` and `docs/XP_COMPENSATION_BATTLE_TEST.md` in the repository. Python requires ndspy for ROM inspection and Unicorn for the read-only badge getter. The save inspector requires .NET 10 and the official PKHeX.Core build at the documented commit. Download/install provenance is retained locally.

Frost: https://github.com/FrostFalcon/FrostsGen5Editor
PKHeX: https://github.com/kwsch/PKHeX

The imported `crypt` function is used only to decode records during verification. The fixture-healing utility is retained as source for that import; it is not called to manufacture a battle or save/reload result.
