# Release checks — 1.0.31

## Verified locally

- All 12 configured native CTest checks passed. This includes the Black 2 Redux cartridge regression, Mega hook signatures, all 46 full-frame animated Mega clips, the follower trail and the Fly-style warp call layout.
- The Windows Qt emulator target rebuilt successfully with the updated field-landing bridge.
- The follower check covers the 1.25-tile trail spacing, 60-fps interpolation between 50-ms samples, stopping, corners, gait continuity and subpixel movement. HeartGold/SoulSilver's decomp creates its native follower as a map object that follows the player's route; this overlay uses a small render-spacing cushion for its separately scaled sprite.
- The Fly-style call was checked against Black 2's decomp: `s028A_MapChangeFlyWarp` chains `EventMapChangeWarp_CreateGrid` with a `VecFx32`, direction and warp flag.

## Needs an in-game check

Soaring flight and landing still need a live test on a Black 2 Redux save. Enable **Settings → Experimental features → Soaring flight**, open **Unova → Pokémon → Take flight**, then land on clear ground. Check the destination map, tile and field visuals. Also test Mega Salamence's full animation from both battle positions. The automated animation check confirms every converted frame is available; it does not prove how the animation looks in a live battle.

## Public launcher download verification

- The production updater downloaded the public GitHub runtime ZIP, verified its checksum, and installed it into an isolated test home.
- Version selection, archived patch notes, the Windows Qt plugin, settings preservation, and a save sentinel all passed. No downloaded executable was run.
- Result: `{"downloadBytes": 175399477, "emulatorSha256": "b33192f067472898ad75a2be0651e7d7a452a16a3517f96d25d08a3f2bef5a92", "newsSource": "patchnotes", "patchNotes": 42, "saveSentinelPreserved": true, "settingsPreserved": true, "version": "1.0.31", "windowsQtPluginPresent": true}`
- The generated download and extracted test installation were removed after recording these results.
