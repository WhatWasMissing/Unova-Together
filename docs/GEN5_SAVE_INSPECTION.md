# Independent Gen 5 save inspection

PKHeX's official source was downloaded from [kwsch/PKHeX](https://github.com/kwsch/PKHeX) at commit `66ef5983a5d349efa2dd615f2926a1b1ee97306e`. The existing .NET 10 SDK/runtime was sufficient. Both the core library and Windows editor built successfully, with zero warnings and errors. The upstream source and GPL license are retained under `tools/external/gen5/PKHeX-source`.

Our `tools/pkhex_save_inspector` console helper uses that library to read Black 2 / White 2 save data. It reports party identity, accumulated XP, stored level, HP, moves, party checksums, save-block checksums and badge ownership. It never calls save/export or mutates the source file. Output must use a separate JSON path.

```powershell
dotnet build tools/external/gen5/PKHeX-source/PKHeX.Core/PKHeX.Core.csproj -c Release
dotnet build tools/pkhex_save_inspector/Inspector.csproj -c Release
dotnet tools/pkhex_save_inspector/bin/Release/net10.0/Inspector.dll "path/to/Redux.sav" "test-fixtures/save-inspection.json"
```

Exit status 0 requires valid save-block and Pokémon checksums and an unchanged input. A deliberately corrupted private party block was correctly rejected with status 1; both checksum failures were reported. The authentic starting fixture independently parsed as Black 2 with valid checksums, Servine level 19 / 5,144 XP, Elekid level 1 / zero XP and no Cheren badge.

The built interactive editor is at `tools/external/gen5/PKHeX-source/PKHeX.WinForms/bin/Release/net10.0-windows/win-x64/PKHeX.exe`. Its interface has not been manually tested in this workflow. Keep Redux balance interpretation separate from stock-game legality assumptions; no automatic legality corrections are used here.

`tools/verify_gen5_saved_reload.py` starts a fresh emulator process from a disposable copy of a real saved game, without loading a savestate. It compares the field party and native badge getter with the inspector's disk evidence. A successful parser check alone is not a successful gameplay reload.

The battle runner was improved to advance post-victory dialogue, face/walk away before opening Save, and wait for validated written data rather than stopping at a fixed delay. Battle input may still require supervised correction at move-learning prompts or when a move runs out of PP. These are test-harness changes; no emulator or ROM reward code was changed.

Private installation provenance: `tools/external/gen5/pkhex-install.json`. Private parser evidence and corruption test: `test-fixtures/release-1.0.2/pkhex-*.json` and `pkhex-negative`. Save/reload gameplay evidence is reported separately in the battle test document.

Follow-up helper sources are available in [maintenance-tools](../maintenance-tools/README.md); these are separate from the immutable 1.0.2 release packages.
