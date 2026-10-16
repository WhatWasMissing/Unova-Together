# Following Pokémon

The first Pokémon in your party follows your footsteps, about one tile behind,
matching HeartGold and SoulSilver's previous-step spacing. Movement
stays smooth between steps and follows your turns instead of cutting across corners.
Change the first party slot to change your follower. Eggs and fainted leads stay
hidden. Following Pokémon default on. Show or hide your own or teammates' followers in **Unova → Settings**.

Followers stop when you stop, follow corners, and reset after a map change or
teleport. They hide during battles and full-screen game menus. They are cosmetic:
they do not block movement, change encounters, edit your party or alter saves.

All 649 species through Generation 5 have directional follower sprites. Generations
1–4 use the loaded Black 2 ROM's overworld artwork. Gen 5 uses credited hg-engine
overworld artwork bundled into the emulator. Party icons are never used as followers.
Standing sprites without natural idle motion receive a subtle bob with anchored feet. Companion interactions can add short reaction motions; see the [interaction guide](COMPANIONS_AND_SOARING.md).
The 1.0.7-dev source/local build has 743 assets with normal/shiny palettes,
supported female appearances and alternate forms. Unsupported forms use base
art. Large sprites keep 64-pixel dimensions with transparent animation headroom.
See [coverage and provenance](FOLLOWER_VARIANTS.md). Published 1.0.6 assets retain
their earlier appearance coverage.

Teammates can see your follower when both use this build and the host runs its
updated presence relay. The relay sends species, form, gender and shiny metadata alongside
existing presence updates; each emulator loads its own follower graphics. Older relays
can still connect but discard this optional follower information.

## Validation

`tools/check_pokemon_follower.cpp` validates the breadcrumb path and decodes all
649 species from both retail Black 2 and Redux Complete 1.4.1. Each species has
12 non-empty, bounded display frames. Development checks also decode all 743
variants with normal/shiny palettes and 32/64-pixel widths. The same tests cover stopping,
corners, map changes, warps, invalidation and lead changes. Relay tests validate
optional metadata and reject invalid species/form values.

The current motion regression now also checks the one-tile gap, smooth positions
between updates, corner turns, walk-cycle steps and trail resets after map
changes or teleports. It passes on the desktop build; a live field playtest is
still needed to judge the spacing on screen.

The 2026-10-16 motion pass additionally checks that the walking pose stays active
at refresh boundaries. Both the focused regression and full Qt emulator build
passed; live in-game spacing still needs visual review.

The 60-fps refresh regression now advances the owner between 50-ms trail samples
and verifies that follower position, facing, movement state, and gait do not jump
when a new trail sample arrives. It also checks that the walk cycle continues to
advance during sustained movement. The focused test passed on 2026-10-16.

HeartGold/SoulSilver's `FollowMon_InitMapObject` creates the follower at the
player's map location, then its movement scripts make the follower retrace the
player's earlier tile steps. The overlay keeps that one-tile gap while
interpolating fractional positions between samples, so the camera-projected
sprites move smoothly instead of snapping from tile to tile.
See the [HeartGold/SoulSilver follower implementation](https://github.com/pret/pokeheartgold/blob/master/src/follow_mon.c)
and [map setup](https://github.com/pret/pokeheartgold/blob/master/src/field_warp_tasks.c#L287).

The native menu fixture separately checks the actual copied-save first party
record, ROM frames, camera projection, battle hiding/recovery and the toggle.
Synthetic path tests are not a multiplayer field playtest; test teammate
appearance with the updated relay before a public release.

`tools/verify_complete_followers.py` checks all 649 species against Black 2,
Redux and Unova Together: four directions, nonempty 32×32 frames, changing
movement poses, and zero party icons. It also compares the supplied HeartGold
dump: 493 North/South texture sets match Black 2; 492 also match its palette
exactly. Fearow has a palette difference; Black 2 has adapted side poses.

Gen 5 art comes from [BluRosie/hg-engine](https://github.com/BluRosie/hg-engine),
pinned at `5f1c91fb93ee6d78cf54105ecf1ce1933e043dad`. Original artist credits and
free-use terms are included in `res/followers/CREDITS.md` and `ASSET_TERMS.md`.
Unova Together's asset conversion and menu implementation are by mvq1303;
this does not claim authorship of the supplied artwork.

The Gen 1–4 sprite ordering was cross-checked against the factual species/sprite
constants in [pret/pokeheartgold](https://github.com/pret/pokeheartgold/tree/master/include/constants).
Gen 1–4 artwork is decoded from the player's ROM. Unova Together implementation by
mvq1303 / WhatWasMissing; existing upstream and GPL notices remain applicable.

The Gen 5 identity audit corrected evolved-species mappings (including Herdier,
Zebstrika, Boldore, Gurdurr, Duosion and Klang) and added native Leavanny,
Scolipede, Krookodile, Gothorita and Shelmet. The completed asset set replaces
all former party-icon fallbacks and standing-only Gen 5 poses. Contact sheets are generated with the
optional output-directory argument to the follower checker.
