# Development checks — 16 October 2026

These results cover the local development source. They are not a public release or a live emulator playtest.

## Followers

- The trail now keeps HeartGold/SoulSilver's one-tile gap and interpolates between 50 ms route samples. Its walk-cycle phase follows distance traveled along the breadcrumb route, so turns do not restart the gait. The overlay also retains fractional positions for followers instead of snapping them to whole screen pixels.
- The focused follower regression checks the gap, straight-line movement, stopping, corner turns, 60 fps sampling across 50 ms updates, continuous gait and visible subpixel motion. It passed; the full Qt emulator target also rebuilt successfully.
- The implementation is data-level and build-verified. A live field playtest is still needed to confirm the spacing and motion on the user's game setup.

## Regional Soaring

- The worker reads the Black 2 zone-header `fly_from` bit and reciprocal, non-rail warp records, then resolves connected outdoor matrix offsets. The field layout and warp records were checked against the Black 2 decomp.
- The retail Black 2 ROM and the supplied Redux ROM produced the same 13-matrix connected region.
- All 11 Soaring worker tests passed. The cross-matrix fixture checks destination map/tile coordinates, atlas world positions and shifted collision tiles.
- An export from the retail ROM rendered an atlas containing all 13 connected matrices (1,449 geometry faces, 41 textures). The native scene test loaded the exported scene and rendered it; the measured 120-frame test averaged 0.86 ms with a 0.94 ms p95. A native synthetic test also checked format 3, atlas origins and global landing coordinates.
- A second read-only export pass sampled four locations in the Overworld and linked matrices 107, 255 and 414 from both retail Black 2 and Redux. Every scene carried the same 13 matrix offsets. At the take-off point, the exporter produced 22,106 terrain faces, 198 landing sites and 237 collision tiles; at linked matrix 107 it produced 23,156 faces, 204 landing sites and 496 collision tiles. Both ROMs produced matching counts and landing maps.
- The native renderer loaded the real Redux take-off and linked-matrix scenes. The 120-frame render check averaged 4.9 ms (8.2 ms p95) at take-off and 8.8 ms (11.4 ms p95) in the linked scene. This confirms the scene format, scenery and landing data load within the renderer's frame budget; completing a landing through the game's live field transition still needs an in-game test.
- Live flight, cross-map landing and in-game follower spacing still need playtesting.

## Cross-feature regression checks

- The native Mega/follower/menu-sound suite passed all 12 tests. This includes full GIF-frame playback for the 46 packed Mega animation clips and a regression for the Black 2 Fly-style warp call layout.
- The launcher UI suite passed all 30 tests, and the GitHub patch-note feed passed all 4 tests.
- All 11 Soaring geometry/stream tests passed, and the native Soaring check passed take-off, controls, altitude limits, map bounds, landing and rendering.
- Black 2's decomp shows Fly chains `EventMapChangeWarp_CreateGrid` from `s028A_MapChangeFlyWarp`. The Soaring bridge now calls that same overlay-35 Thumb function (`0x0217DB41`) with the decompiled register/stack ABI. The regression and full Qt target compile pass; a live landing is still required to confirm map reload behavior.
- These checks validate the local source and fixtures. The launcher update/download flow, Soaring landings and follower motion still need a real end-to-end test with the published build and emulator.
