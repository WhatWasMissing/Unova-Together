# Unova Together 2.0.23 release checks

This release updates normal follower artwork from the supplied HGSS sheets and
distributes all 49 Mega Stones across standard Pokémon Center Mart inventories.

## Verified checks

- **Artwork:** 545 normal variants cover all 493 Generation 1–4 base species and
  52 gender/form variants. All 4,360 cutouts reproduce opaque source pixels
  exactly, without scaling, smoothing or intermediate alpha. Sheet boundaries,
  borders and marker dots were excluded. The 57 differing replacement groups
  were reviewed in a nearest-neighbor contact sheet.
- **Preservation:** SHA-256 checks confirm all 743 original BTX assets are
  unchanged. Executing the production loader/resource collection against the
  previous 2.0.22 source and the updated source produced identical rendered-frame
  hashes for all 743 shiny appearances and all 198 uncovered normal variants.
  Every imported normal variant decodes to 12 valid directional frames. The
  loader's gender fallback was also exercised for all 649 base species.
- **Full roster:** The production roster test decodes all 649 base species as
  walking followers with no party-icon fallback. Its old assertions requiring
  every pair of artwork poses to differ and every normal/shiny silhouette to
  match were updated: native artwork can repeat poses, and separate shiny art
  is an explicit user requirement. The new differential hash test verifies
  preservation instead of requiring altered artwork. These tests do not verify
  movement timing in a running game.
- **Shops:** The compiled balanced-stock contract passed roster coverage,
  native capacity, idempotency and malformed-input checks. Both the original
  full-size Redux ROM and the launcher's trimmed copy passed stock checks;
  their SHA-256 hashes were identical before and after the read-only tests.
  Shop-overlay regression tests passed **7/7**.
- **Launcher:** Patch-note, versioning and release-validation tests passed
  **21/21**. Canonical and maintenance launcher UI trees match **49 files**.
  The bundled news feed includes the new notes and preserves previous notes.
- **Build:** A clean Windows Release build succeeded with CMake 4.4.2, Ninja,
  GCC 16.2.0 and Qt 6.11.2. The launcher and bootstrap were built with Python
  3.12.8 / PyInstaller 6.22.3. Emulator FileVersion and ProductVersion are
  **2.0.23**; emulator SHA-256 is
  `dc7af63b5f5bb15e42cb3c6abdb3427ff9a7fc511a7f30a3418723222f0d5e36`.

## Source provenance and limits

The emulator source base is the official 2.0.22 corresponding-source archive,
SHA-256 `e0b423733748efe8dbe5297a6c21e66d54908c36071ccb14bf7727621b7a1c50`.
Comparing its existing files with the build tree found exactly five changed
files: `res/followers.qrc`, `res/melon.rc.in`, `ProjectCredits.h`,
`TrainerSprites.cpp` and `Gen5ShopPolicy.h`. New normal PNG resources and their
provenance/credits were added. The compiled shop policy matches current main's
distributed patch. No battle, network, follower movement, save or field-engine
code was changed.

**NOT RUN:** Live gameplay and two-client gameplay were not performed for this
release. Resource decoding, rendered-frame hashes, pixel checks, ROM-data checks
and compilation are distinct from in-game visual or timing verification.

Reproduction instructions and sheet hashes are in
[HGSS follower import](HGSS_FOLLOWER_IMPORT.md). Temporary build fixtures and
inspection captures are removed after checks; reusable test source is retained.

## Packaged assets

ZIP integrity, emulator/launcher versions, keyboard settings, platform plugin,
corresponding source and exclusion of ROMs/saves/private files passed packaging
validation. An independent byte comparison matched every emulator source file
and the new test tools against the final source ZIP. Player art credits and the
frozen news feed match current source.

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12,217,771 | `12e112f147a399d97a87f4b154fd501a9ae15969666c53fe9ee1e807cb142096` |
| `SHA256SUMS-Unova-Together-2.0.23.txt` | 378 | `e72a2d742eb9ba0ba4cb6f2e887d663a5e5813a47e8df5cb794e4173de1e1294` |
| `Unova-Together-2.0.23-Source.zip` | 33,112,373 | `311f271b5ebe1f97bee92f28fb01a15e73eeafd169802637e88c30d0490c5f37` |
| `Unova-Together-2.0.23-Windows-x64.zip` | 207,577,581 | `f62478ce0caa45596bc10ff1572dfde395a965d3a84984277d7ea6b45fc296e0` |
| `Unova-Together.exe` | 248,139,914 | `202f4af776dbd89230880e9558af95fa217093251f2f0ef4bba9e1c1c3f04f80` |
