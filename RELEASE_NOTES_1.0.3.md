# Unova Together 1.0.3 — Simpler saves and Gen 5 tools

A full release with launcher 1.0.3 and the previously verified modified melonDS 1.0.2 runtime, based on melonDS 1.1. Emulator gameplay is unchanged, including 1.65× solo XP compensation.

Download **Unova-Together.exe**, or extract **Unova-Together-1.0.3-Windows-x64.zip** and run **Start Unova Together.cmd**. Existing players can install through launcher Updates. Existing profile settings, ROMs, saves and backups are retained.

## Changes

- **Games & saves** replaces the profile wording. Play shows the active slot and a Manage saves button.
- Slot names save automatically. New slots reuse the selected ROM with separate save folders. Advanced folder settings and slot removal are tucked away.
- **Back up now** and **Restore backup** share one page. Backups have readable dates and reasons; current files are backed up before restore.
- Added `.save` and numbered instance `.save` support alongside `.sav` and `.dsv`. Contents are preserved without conversion; melonDS normally uses `.sav`.
- Added read-only English Black 2 ROM/XP-hook checks, a checksum-verified party save comparison and a Redux Challenge XP-budget calculator using the existing 1.65× multiplier.

## Verification and limits

20 native UI tests, 15 launcher-service tests and 6 installer tests passed. Real Redux save copies were backed up and restored through launcher controls under all four tested filenames (`.save`, `.2.save`, `.sav`, `.dsv`), byte for byte. The replaced saves were preserved and another ROM's save was untouched. A restored `.save` payload, copied to melonDS's normal `.sav` filename, passed normal boot without a save state: Servine retained level 20 and 5,951 XP, and the Cheren badge remained present. Frozen launcher and standalone installer smoke tests passed, including the packaged ROM, save and progression tools.

ROM checks cover English Black 2 identity and the XP hook, not every multiplayer feature or edited asset. The calculator requires the reviewed Redux Complete 1.4.1 ROM and reports XP-budget equivalents, not playthrough predictions. Save comparison checks party blocks and Pokémon records, not every save block; differing banks are shown without guessing which is latest.

Previously documented multiplayer edge cases and physical two-PC/WAN limitations remain. The emulator executable is byte-identical to release 1.0.2. See docs/KNOWN_ISSUES.md and docs/LAUNCHER_GEN5_TOOLS.md.

Complete Windows runtime, matching GPL source and SHA-256 checksums are included. No ROMs, firmware, saves or private settings are distributed. Original contributions by **mvq1303 / WhatWasMissing**; melonDS and dependency attribution is preserved.
