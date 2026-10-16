# Release checks — 1.0.32

## Verified locally

- The Windows Qt emulator target linked successfully after melonDS was closed.
- All 35 Soaring geometry and worker unit tests passed.
- Native checks passed for map ID 0 and the Fly-style landing call.
- The end-to-end renderer sweep loaded all 69 outdoor maps, simulated flight and landing, and passed on every map. Sixty-eight have safe landing sites; Marine Tube correctly offers return to take-off.
- The 30×30 regional atlas joins all mapped areas with no enclosed holes or unfilled cells beside mapped terrain. The Black 2 decomp confirmed dimensions for all 68 original outdoor matrices; Redux adds matrix 416.
- Public updater, patch-note discovery, settings preservation and save preservation passed on release 1.0.31. The 1.0.32 package will be checked after upload.

## Needs an in-game check

Soaring still needs a live flight, landing and return-to-field check on a Black 2 Redux save. Enable **Settings → Experimental features → Soaring flight**, choose **Unova → Pokémon → Take flight**, then try several routes and towns. Check that clear landings return to the correct map and location. Save before testing this experimental feature.

## Test commands

```powershell
py -3 -m unittest test_soaring_geometry test_soaring_scene_worker
py -3 test_field_zone_native.py
py -3 -u test_soaring_real_scene_matrix_set.py
py -3 -u audit_soaring_chunk_coverage.py --rom <Black 2 Redux ROM> --decomp <Black 2 decomp>
```

The ROM, decomp, saves, RAM dumps, captures and generated test outputs are not included in the release.

## Public launcher download verification

- The production updater downloaded the public GitHub runtime ZIP, verified its checksum, and installed it into an isolated test home.
- Version selection, archived patch notes, the Windows Qt plugin, settings preservation, and a save sentinel all passed. No downloaded executable was run.
- Result: `{"downloadBytes": 173862690, "emulatorSha256": "f1ce80a0b010b5f0c26a973d9e8b927117fd7bfd6373e5834d9d21e927f7ad7e", "newsSource": "patchnotes", "patchNotes": 43, "saveSentinelPreserved": true, "settingsPreserved": true, "version": "1.0.32", "windowsQtPluginPresent": true}`
- The generated download and extracted test installation were removed after recording these results.
