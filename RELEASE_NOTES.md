# Current release

See [Unova Together 1.0.12 release notes](RELEASE_NOTES_1.0.12.md). Earlier version-specific release notes are retained below for history.

# Unova Together 1.0.9 — Client launcher migration

Fixes the remaining case where a client's usual launcher shortcut keeps opening 1.0.5 after updating the game package.

- **Repair-Launcher.exe** migrates the original shared `Pokemon Together.exe` entry point into a small permanent bootstrap. Existing shortcuts keep the same target. The bootstrap reads the active update slot and opens its current shared launcher with the same installation/profile home.
- The original executable is backed up. Migration preserves game files, ROMs, profiles, saves and backups. If Windows locks the old launcher, repair asks you to close its window and retries; it never terminates the game.
- New launchers remember their original entry point and schedule this migration after an update. The standalone installer provisions a permanent entry in its existing data home. Future updates are followed without repairing the shortcut again.
- The repaired entry can follow consecutive newer releases without being replaced on every update. Updated slot executables cannot be mistaken for the old entry, and failed replacement restores the original executable and home mapping.

## Existing clients running launcher 1.0.5

1. Install the game update through **Updates** first. The repair supports an installed 1.0.8 or newer package.
2. Download and run **Repair-Launcher.exe** below. Select the **old Pokemon Together.exe used by your usual shortcut**, not the executable inside `.updates/versions`.
3. If asked, select your original Unova installation folder containing `.updates` or `builds`. Close the old launcher window if repair asks, then use your usual shortcut.

This is a one-time migration. Old 1.0.5 code cannot automatically run a repair it does not contain; installing the game package alone does not replace its external launcher. Fresh installations and future updates from the migrated entry use the new route.

The package includes the companion changes, stable **Settings → Following Pokémon** controls and optional experimental flight shortcut from the previous release. Gameplay is unchanged; native resource/credit labels advance to 1.0.9. Full free-flight Soaring remains unfinished.

Windows runtime, matching GPL source, standalone installer, repair utility and SHA-256 checksums are provided. No ROM, firmware, save or RAM capture is bundled. Original contributions by **mvq1303 / WhatWasMissing**, built on melonDS; dependency notices are preserved.
