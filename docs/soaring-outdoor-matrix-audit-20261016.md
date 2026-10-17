# Soaring map guide

The optional Soaring preview connects 69 outdoor areas. Some locations and routes are approximate, and landing is available only on clear ground. Marine Tube has no safe landing spot; use the return-to-take-off option there.

See [Soaring flight preview](SOARING_FLIGHT.md) before using this unfinished feature.

## Decomp-backed coverage check (17 October 2026)

The map was checked against the player's Blaze Black 2 Redux v1.4.1 ROM and the local Pokémon Black 2 / Black 2 and White 2 decompilation sources. The Soaring builder reads outdoor matrices, zone headers, reciprocal warp coordinates, field chunks, terrain models, and collision-derived landing candidates from the ROM. Map matrices are placed from reciprocal outdoor warps where possible; supplemental placements are used for separated exteriors that have no unique reciprocal route. The Redux-only matrix 416 is anchored beside Route 19.

The audit found 149 outdoor zones, 70 matrix IDs representing 69 unique outdoor matrices, and 427 unique outdoor chunks. It decoded terrain for 406 chunks and scenery-only models for 21 chunks, producing 176,846 faces. All 69 outdoor matrices resolved consistently from every outdoor root. The resulting 30-by-30 atlas contains 440 map cells and 327 sea-fill cells; all land and connecting fill is one component, with no enclosed gaps or unfilled cells touching the map. The public decomp has 416 matrix members: 68 outdoor matrices matched it directly, while matrix 416 is Redux-specific. The audit and decomp cross-check passed.

The worker regression suite passed 29 tests and the geometry suite passed 5 tests. A full renderer sweep then loaded and rendered all 69 outdoor matrices. Both background-flight ROM requests (225 and 357) reached their ready state. The 95th-percentile frame time peaked at 14.59 ms on matrix 2; the slowest observed frame was 48.45 ms on matrix 314. These are renderer measurements, not proof that the routes look correct at normal gameplay speed. Marine Tube (map 273) remains the only matrix without a safe landing. Renderer-only fill cells do not create landing destinations: the worker emits landing markers only from source-area landing candidates. The flight menu offers landing only when a clear-ground candidate is nearby and keeps the B return-to-take-off option available.

The clean release regression build passed all 21 checks, covering Mega Evolution rules and data, item compatibility and icons, gym teams, menu and evolution sounds, followers, co-op state, the EV reset data edits, the native Fly-warp call, and the Redux cartridge integration.

These checks establish data coverage, warp-frame consistency, terrain decoding, and the fill/landing separation. They do not prove that every flight path and landing looks correct in a live emulator. Supplemental map positions and the available safe landing sites still need broader visual and gameplay testing, so Soaring remains an experimental preview.
