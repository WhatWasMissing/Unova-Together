# HGSS follower artwork import

The user supplied five HGSS overworld sprite sheets in `F:/walkingspriteshgss`.
This update imports normal artwork without resampling, smoothing, or generating
new poses. Shiny artwork remains a separate selection using the existing shiny
BTX assets; these normal-only sheets never override a shiny Pokémon.

## Acceptance and preservation checks

1. Import every covered species and matching authored gender/form; preserve all
   four directions and both source poses.
2. Preserve the existing artwork for missing variants, including Generation 5.
3. Preserve every existing shiny asset and the frames returned for shiny Pokémon.
4. Exclude sheet backgrounds, borders, labels and gender-marker dots.
5. Compile the production loader and full Windows emulator, check the packaged
   resources, and publish a versioned release with corresponding source.

The runtime base is the verified 2.0.22 corresponding-source archive
(`e0b423733748efe8dbe5297a6c21e66d54908c36071ccb14bf7727621b7a1c50`).
Current main's balanced Mega Stone shop changes are also included. This change
does not alter follower movement, networking, battles, ROMs or saves. Rollback is
the previous release; original assets remain available in the new build.

## Source and mapping

`maintenance-tools/assets/followers/official-hgss/manifest.json` records the five
source hashes, every imported frame's source rectangle and output checksum.
`audit_hgss_walking_sheets.py` matches full RGB555 silhouettes against the pinned
existing source cache; `import_hgss_walking_sheets.py` imports those matches and
57 separately reviewed replacements. The result contains 545 normal variants:
493 base species and 52 gender/form variants. The other 20 existing variants
within Generations 1–4 retain their original assets. All Generation 5 variants
and all 743 original BTX files remain unchanged.

The sheets credit Dragoon / TSR (Generations 1, 2, 4 and miscellaneous) and
redblueyellow, with thanks to PokeTex (Generation 3). Pokémon artwork belongs to
its original owners. Import tooling is an Unova Together contribution by
mvq1303 / WhatWasMissing. Existing hg-engine credits and notices remain intact.

## Verification

Verification results are recorded in the release check document after testing.
Source-level and loader checks do not establish live gameplay behavior.

The import tools require Pillow and NumPy. Run the audit against the existing
pinned hg-engine source cache, then pass its report and the same cache to the
importer. Both tools expose their paths through `--help`; the manifest records
every source sheet hash and cutout coordinate. Copy the entire
`maintenance-tools/assets/followers/official-hgss` directory into
`source/melonDS/res/followers/official-hgss` when rebuilding from the development
patch. The corresponding-source release already includes these resources.

For preservation checks, run `test_hgss_followers.py --source <source-tree>
--snapshot <output.json>` on 2.0.22, then run it on the updated source with
`--baseline <2.0.22-output.json>`. This compiles and executes the real loader and
resource collection. `verify_hgss_import.py --sheets <sheet-folder>` checks the
cutouts and all original BTX hashes directly.
