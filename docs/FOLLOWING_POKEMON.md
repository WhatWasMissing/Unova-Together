# Following Pokémon

The first Pokémon in your party follows your footsteps, roughly one tile behind.
Change the first party slot to change your follower. Eggs and fainted leads stay
hidden. Following Pokémon can be switched off in Multiplayer → Players.

Followers stop when you stop, follow corners, and reset after a map change or
teleport. They hide during battles and full-screen game menus. They are cosmetic:
they do not block movement, change encounters, edit your party or alter saves.

All 649 species through Generation 5 have directional follower sprites. Generations
1–4 use the loaded Black 2 ROM's overworld artwork. Gen 5 uses credited hg-engine
overworld artwork bundled into the emulator. Party icons are never used as followers.
Repeated standing poses on floating or legless sprites receive a small movement bob.
Shiny colours and every alternate-form
or gender-specific appearance are not implemented. Selected native form variants
(Unown, Deoxys, Burmy/Wormadam, Shellos/Gastrodon, Giratina, Shaymin, Rotom and
Basculin) use their available overworld variants.

Teammates can see your follower when both use this build and the host runs its
updated presence relay. The relay sends only species and form numbers alongside
existing presence updates; each emulator loads its own follower graphics. Older relays
can still connect but discard this optional follower information.

## Validation

`tools/check_pokemon_follower.cpp` validates the breadcrumb path and decodes all
649 species from both retail Black 2 and Redux Complete 1.4.1. Each species has
12 non-empty, bounded 32×32 display frames. The same tests cover stopping,
corners, map changes, warps, invalidation and lead changes. Relay tests validate
optional metadata and reject invalid species/form values.

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
