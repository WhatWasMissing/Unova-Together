# 1.0.20 release checks

## Mega Serperior battle crash fix

- Rebuilt the Windows emulator with the public roster enabled: Mega Serperior only.
- Replayed the user's exact Mega-armed slot 4 state against the supported Redux ROM in both JIT and interpreter modes.
- Both battle copies reached Mega form with stats `94 / 115 / 121 / 102 / 131`, Contrary, and 147/147 HP. The saved party was unchanged and battle teardown completed without a crash screen.
- The public-config Mega regression suite passes 7/7, including the full Redux ROM overlay test.
- A two-emulator live Mega battle remains a playtest item.

## Patch notes feed

- The launcher reads `patchnotes/index.json` from GitHub's `main` branch, independently of the GitHub Release list.
- Feed tests check that the newest note appears first and each version links to a file in `patchnotes/`.
- All 31 notes are retained in the folder; older GitHub Release entries are not required for displaying them.

## Art distribution

The Mega Serperior image was supplied by the user, but its creator and public reuse terms are still being checked. Do not publish a package containing that artwork until this is cleared.


## Local package fingerprints

These hashes identify the locally verified candidate artifacts. They have not been uploaded.

- Runtime emulator: `builds/release-runtime-1.0.20/melonDS.exe` — SHA-256 `79f6e57ddfce8a86ea1b6c5d09e854256d7002bcdf20add280ef6b6b04e5aa35`
- Windows x64 runtime ZIP: `downloads/releases/release-1.0.20/Unova-Together-1.0.20-Windows-x64.zip` — SHA-256 `0e76095368f0d2691ddaf16061ce48587b35e086a096ae0960731028f2e4b225`
- Source ZIP: `downloads/releases/release-1.0.20/Unova-Together-1.0.20-Source.zip` — SHA-256 `ff60cd6126a48286d64591f8f4fc7cbd168e9d317c0108db82beb21101054470`
- Standalone launcher: `downloads/releases/release-1.0.20/Unova-Together.exe` — SHA-256 `0f9c8657f4b09c8fff88f38e467c6fca5edf6f2a7f97be0a9c08ad5748398358`
- Repair launcher: `downloads/releases/release-1.0.20/Repair-Launcher.exe` — SHA-256 `e2f2d2699aa6657ffcc3459269698364f769d80b5ceeb45bb65e8de751b628b3`
- The Windows runtime archive contains `patchnotes/index.json`; the source archive contains `Gen5MegaSpriteAssets.h`. Both packages therefore remain local until public artwork reuse is confirmed.
