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

