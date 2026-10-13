# Unova Together 1.0.7 preview checks

This prerelease packages the searchable trainer browser and launcher-gated Take flight shortcut. It is a development preview, not a claim of full free-flight Soaring or multiplayer playtest completion.

## Build and packaging

- Native melonDS target compiled with the configured MSYS2 UCRT64 toolchain, run from the MSYS2 Bash environment so GCC can launch `cc1` and its other compiler helpers.
- Windows launcher built from the matching launcher source with the attributed PyInstaller build script.
- Release packaging checks the Windows and corresponding-source ZIP contents, archive integrity, checksum manifest and absence of ROM, save, firmware and RAM-capture file types.
- The Windows ZIP includes the launcher, runtime libraries, source/docs links, LAN helpers and settings. Existing stable v1.0.6 assets are unchanged.

## New-feature scope

- Practice search uses trainer records and parties parsed from the selected ROM. Party size and level range are shown. Practice has no story rewards. Story co-op remains on the separately curated list.
- Soaring is off by default. When enabled in **Settings → Experimental features**, the game menu opens the native Pokémon party screen. The game's own Fly move, destination list and landing transition remain in charge.
- No live ROM session, save/reload check, two-emulator battle, or physical-computer multiplayer check was run specifically for these new UI changes. The planned free-flight scene, atlas and route discovery are not included.


## Rebuild

Use the corresponding source ZIP and the source build instructions. `maintenance-tools/patches/development-polish.patch` is generated from the published 1.0.6 source baseline; the release source ZIP includes the complete directly buildable source tree used for this prerelease.
