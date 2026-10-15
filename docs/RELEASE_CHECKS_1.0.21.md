# Unova Together 1.0.21 release checks

## Mega Serperior

- Built the Windows emulator with the public Mega roster: Serperior only. The title, About dialog, and Windows file version now identify this build as 1.0.21.
- Replayed the exact user-supplied armed slot 4 state from a disposable copy against the supported Redux ROM. Serperior 497 holding Serperiorite 113 transformed to form 1; both active battle copies verified Mega stats `94 / 115 / 121 / 102 / 131` and Sap Sipper (91), with 147/147 HP and saved-party data unchanged. The sprite stayed stable for 20 frames and the fatal-screen detector remained clear.
- Replayed a fresh post-overlay battle through teardown. Mega form, ability, and stats were verified in both copies; the battle ended without a fatal screen, HP stayed unchanged, and saved-party data stayed byte-for-byte unchanged. The fixture injects the battle-end transition after verification; a natural knockout was not part of this check.
- All eight Mega CTests pass, including the Redux cartridge overlay, native call transaction, LAN event transport, and hook signature checks.
- The exact Redux ROM SHA-256 is `353FB0CF82C3E4EDDFC8986EFA8910B00EB1C4D6F106C220ABEF59D69D3A520A`; the armed slot 4 SHA-256 is `52FD130625FDB0BD0AE5702E07D07FA884BC8175AEC5974A8834B883711957F2`. Both were read-only.
- The 96x96 artwork is packed as DS-native 4bpp tiles and palette data. This build uses static front/back sprite presentation.
- A live two-emulator Mega battle remains untested. Update both players before trying co-op.

## Build fingerprint

- `melonDS.exe` SHA-256: `C4432770056847D7D7622B2960B3433F7C2209848CD60A0A87BF25F7F3508D0B`.
- Black 2 Redux Complete v1.4.1 (`IREO`) is the only supported Mega test target; the original ROM and save were not modified or included in the release.
- The user confirmed the supplied Mega Serperior artwork may be used in this free, non-commercial mod. The source file has no reliable creator metadata; it is credited as user-provided fan artwork.

## Launcher and package checks

- The launcher patch-note feed reads `https://raw.githubusercontent.com/WhatWasMissing/Unova-Together/main/patchnotes/index.json`, validates the index, and links each entry to its Markdown file in `patchnotes/`. The feed regression suite passes 3/3; it verifies the index is read separately from GitHub Releases and that release-note fallback still works offline.
- The sprite converter regression suite passes 5/5. It checks the 96x96 canvas and DS 4bpp/palette conversion.
- The release packager completed its ZIP integrity, Qt platform-plugin, build-version, portable-controls, and private-file checks. Neither package includes a ROM or save.
- The release contains `Unova-Together-1.0.21-Windows-x64.zip`, `Unova-Together-1.0.21-Source.zip`, `Unova-Together.exe`, `Repair-Launcher.exe`, and `SHA256SUMS-Unova-Together-1.0.21.txt`.
- The checksum manifest is the source of truth for asset sizes and SHA-256 values; the GitHub release upload is checked against these entries.

A live two-emulator Mega battle remains untested.
