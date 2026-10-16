# Development checks — 16 October 2026

These results cover the local development source. They are not a public release or a live emulator playtest.

## Followers

- The trail now keeps HeartGold/SoulSilver's one-tile gap and interpolates between 50 ms route samples. Its walk-cycle phase follows distance traveled along the breadcrumb route, so turns do not restart the gait. The overlay also retains fractional positions for followers instead of snapping them to whole screen pixels.
- The focused follower regression checks the gap, straight-line movement, stopping, corner turns, 60 fps sampling across 50 ms updates, continuous gait and visible subpixel motion. It passed; the full Qt emulator target also rebuilt successfully.
- A visual regression showed animation poses sliding vertically inside the sprite box. The renderer now anchors each pose by its own feet and adds a route-timed whole-sprite lift while walking. Pixel-output checks confirm the feet stay planted across frame changes and the sprite itself rises during its gait; the focused test and Qt build pass.
- The implementation is data-level and build-verified. A live field playtest is still needed to confirm the spacing and motion on the user's game setup.

## Regional Soaring

- The worker reads Black 2 Redux terrain and collision data. Matrix dimensions and Fly-style landing behavior were checked against `F:\gen5decomps\pokebw2-main`.
- The 30×30 regional atlas covers all 69 outdoor matrix IDs. Its 440 authored cells and 327 sea-fill cells form one connected footprint with no enclosed holes or empty cells beside mapped terrain. All 69 possible take-off roots resolve to the same world placements. The decomp confirms all 68 original outdoor matrix dimensions; Redux adds matrix 416.
- All 33 Soaring Python tests passed (28 worker and 5 geometry). The audit decoded 427 unique chunks: 361 WB, 45 GC and 21 NG. NG chunks render as scenery but do not supply landing ground.
- The native real-ROM sweep loaded and rendered the outdoor roots, exercised flight movement, selected clear ground and simulated landing. With streaming enabled, it reloaded nearby scenery and confirmed flight position and motion stayed intact for every root. Sixty-eight maps have safe ground; Marine Tube (matrix 273) correctly keeps the return-to-take-off option.
- All roots stayed below the 33.3 ms p95 frame budget. One initial 120-frame run reported a 47.68 ms maximum on matrix 337; an immediate focused rerun measured a 10.58 ms maximum there, so the spike did not repeat.
- Three decorative flyways bridge groups that lack a reciprocal warp path. Twenty-eight supplemental placements anchor areas without a unique spatial warp; some story variants sit beside related areas at approximate positions.
- Native Black City map-ID 0 tracking and the decomp-matched Fly warp ABI regressions passed. These checks do not replace a live emulator test of flight, landing and returning to the field.

## Cross-feature regression checks

- The native Mega/follower/menu-sound suite passed all 12 tests. This includes full GIF-frame playback for the 46 packed Mega animation clips and a regression for the Black 2 Fly-style warp call layout.
- The launcher UI suite passed all 30 tests, and the GitHub patch-note feed passed all 4 tests.
- All 33 Soaring worker/geometry tests passed; the real-ROM native sweep and mid-flight scenery reload checks covered all 69 roots.
- Black 2's decomp shows Fly chains `EventMapChangeWarp_CreateGrid` from `s028A_MapChangeFlyWarp`. The Soaring bridge now calls that same overlay-35 Thumb function (`0x0217DB41`) with the decompiled register/stack ABI. The regression and full Qt target compile pass; a live landing is still required to confirm map reload behavior.
- These checks validate the local source and fixtures. A live in-game Soaring flight/landing/return and follower-motion playtest remain outstanding.

