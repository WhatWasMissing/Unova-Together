# Unova Together 1.0.23 release checks

## Mega Evolution

- Rebuilt the Windows emulator from the updated source.
- All 9 configured CTest Mega checks pass, including battle selection, ability restoration, packet encoding and transport, Redux cartridge overlay, and hook signatures.
- The native lifecycle regression passes its 77 assertions across captured battle stages, including cleanup and a fresh arming state. Its fixture models the game's native form handler; it is not a complete consecutive-battle playthrough.
- Mega Serperior sprite conversion checks pass. On-screen framing and a live second-battle playthrough still need player verification.
- A linked co-op battle between two complete emulator clients remains untested.

## Launcher and package

- Launcher and emulator metadata use version 1.0.23.
- The package includes the standalone launcher, repair tool, portable Windows ZIP, corresponding source ZIP, and SHA-256 manifest.
- Package checks confirm ZIP integrity, required Qt Windows plugin, matching launcher metadata, and exclusion of ROMs and save files.

## Build fingerprint

- `melonDS.exe` SHA-256: `EF64FBF45D1B47864B4E415435C983C029AFF106664EB3F3AA69E3155E9F57CA`.
- Source regression results are documented in `source/melonDS/docs/MEGA_EVOLUTION_IMPLEMENTATION.md`.
