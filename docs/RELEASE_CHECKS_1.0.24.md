# Unova Together 1.0.24 release checks

## Mega Evolution build

- Rebuilt the Windows emulator from the current source with the 1.0.24 Windows version resource.
- Emulator SHA-256: `D5C03C50BD745AEA6A0116A6C7CE9EAD389679F747220A68DB884A5ACC9EE3AE`.
- All 9 configured Mega CTest checks pass. They cover the 12-form release roster and sprite assets, native move selection, party/ability restoration, co-op packet and LAN transport, Redux cartridge overlay, and hook signatures.
- Automated checks do not replace live playtesting. The 11 forms beyond Mega Serperior and linked two-player Mega battles still need in-game verification.

## Launcher and package

- The launcher, emulator, and runtime manifest identify as 1.0.24.
- Release packaging verifies the Windows Qt platform plugin, ZIP integrity, matching executable and runtime version, source inclusion, and that ROMs, saves, RAM dumps, and firmware are absent.
- The Windows ZIP and SHA-256 manifest are the assets used by the existing launcher's update flow.

## Public launcher download verification

- The production updater downloaded the public GitHub runtime ZIP, verified its checksum, and installed it into an isolated test home.
- Version selection, archived patch notes, the Windows Qt plugin, settings preservation, and a save sentinel all passed. No downloaded executable was run.
- Result: `{"downloadBytes": 172295278, "emulatorSha256": "d5c03c50bd745aea6a0116a6c7ce9ead389679f747220a68db884a5acc9ee3ae", "newsSource": "patchnotes", "patchNotes": 34, "saveSentinelPreserved": true, "settingsPreserved": true, "version": "1.0.24", "windowsQtPluginPresent": true}`
- The generated download and extracted test installation were removed after recording these results.

