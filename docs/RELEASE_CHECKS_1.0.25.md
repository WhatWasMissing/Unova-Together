# Unova Together 1.0.25 release checks

## Mega Evolution and shop items

- Added seven forms to the previously supported 12: Ampharos, Venusaur, Charizard Y, Gengar, Alakazam, Mawile, and Garchomp.
- All 19 matching stones are added once to each of the 20 standard Pokémon Center Marts and cost ₽50,000.
- Exact Black 2 Redux cartridge overlay checks verify the stock, price, and archive member ranges against the supported game profile.
- All configured Mega regression tests pass, including the cartridge overlay and mart stock tests.
- The emulator builds successfully from source. Automated tests do not replace live playtesting of the expanded roster or linked two-player battles.

## Launcher update package

- The Windows runtime ZIP is the asset used by the existing launcher's verified update flow.
- Release packaging checks ZIP integrity, launcher/runtime version metadata, the Windows Qt platform plugin, source inclusion, and exclusion of ROMs, saves, RAM dumps, and firmware.
- SHA-256 checksums are included with the release assets.

## Public launcher download verification

- The production updater downloaded the public GitHub runtime ZIP, verified its checksum, and installed it into an isolated test home.
- Version selection, archived patch notes, the Windows Qt plugin, settings preservation, and a save sentinel all passed. No downloaded executable was run.
- Result: `{"downloadBytes": 172325557, "emulatorSha256": "60f9833b94ce74bf243a8aa6fde4da61ec5a87cdd308247f4909d91b863f1b27", "newsSource": "patchnotes", "patchNotes": 35, "saveSentinelPreserved": true, "settingsPreserved": true, "version": "1.0.25", "windowsQtPluginPresent": true}`
- The generated download and extracted test installation were removed after recording these results.

