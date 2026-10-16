# Release checks — 1.0.31

## Verified locally

- All 12 configured native CTest checks passed. This includes the Black 2 Redux cartridge regression, Mega hook signatures, all 46 full-frame animated Mega clips, the follower trail and the Fly-style warp call layout.
- The Windows Qt emulator target rebuilt successfully with the updated field-landing bridge.
- The follower check covers the one-tile trail distance, 60-fps interpolation between 50-ms samples, stopping, corners, gait continuity and subpixel movement.
- The Fly-style call was checked against Black 2's decomp: `s028A_MapChangeFlyWarp` chains `EventMapChangeWarp_CreateGrid` with a `VecFx32`, direction and warp flag.

## Needs an in-game check

Soaring flight and landing still need a live test on a Black 2 Redux save. Enable **Settings → Experimental features → Soaring flight**, open **Unova → Pokémon → Take flight**, then land on clear ground. Check the destination map, tile and field visuals. Also test Mega Salamence's full animation from both battle positions. The automated animation check confirms every converted frame is available; it does not prove how the animation looks in a live battle.
