# Unova Together 1.0.22 release checks

## Mega Serperior battle-menu fix

- Rebuilt the Windows emulator from the current source with the guarded Black 2 Redux fallback for missing Mega-form party icons and palettes. The Windows file and product versions both report 1.0.22.
- All eight configured Mega regression tests passed, including the native battle flow, co-op event transport, Redux cartridge overlay, and ROM hook-signature checks.
- The fallback changes only party-menu icon and palette lookups. It leaves the battle form and Mega sprite selection intact.
- The exact Black 2 Redux v1.4.1 in-game Pokémon-menu path still needs a live playtest. A live two-emulator Mega battle also remains untested.

## Launcher update test

- The release uses launcher and emulator version 1.0.22 so an existing 1.0.21 launcher can discover this release.
- The launcher was built as version 1.0.22 with the matching repair launcher and version metadata.
- The release includes the full Windows x64 ZIP, standalone EXE, repair launcher, matching source ZIP, and SHA-256 manifest.
- Verify the downloaded files against `SHA256SUMS-Unova-Together-1.0.22.txt`. The archive is checked for ZIP integrity, required Qt platform plugin, matching launcher version, and excluded ROMs/saves.

## Build fingerprint

- `melonDS.exe` SHA-256: `91B1F61FD05299CCE7F86ED10C28B6FD8B8F50DA012BA8F3B27BB9C104BD927D`.
- The exact Black 2 Redux v1.4.1 cartridge hook-signature test passed. The ROM was read-only and is not included.
