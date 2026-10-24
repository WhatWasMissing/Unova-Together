# ROM-hacking dialogue workflow

This workflow wraps two data packers from the versioned [`WhatWasMissing/pokebw2` decomp](https://github.com/WhatWasMissing/pokebw2/tree/215b992f5c87bcadc4c5d7a40e78a309b2555f8b). The wrapper runs them locally; it does not include the decomp, a ROM, or game assets in this repository.

## Reviewed tools

The first six entries are from the pinned decomp commit `215b992f5c87bcadc4c5d7a40e78a309b2555f8b`, whose root license is GPL-3.0. The final two are this project’s GPL-3.0-or-later maintenance tools. Paths in the last two rows are relative to this repository. The read-only ROM audit depends on the separately installed `ndspy` package; its upstream project is GPL-3.0 and it is not vendored here.

| Tool | License | What it does | Safety review |
| --- | --- | --- | --- |
| `tools/data/event_data.py` | GPL-3.0 | Packs field-event JSON into the zone-entities NARC. | Directly writes its requested output; selected for the wrapper. |
| `tools/text/text_data.py` | GPL-3.0 | Packs script/system text banks into a NARC. | Directly writes its requested output; selected for the wrapper. |
| `tools/data/species_data.py` | GPL-3.0 | Packs species, stats, evolutions, and learnset data. | Wide data surface with generated-constant dependencies; not adapted for this dialogue task. |
| `tools/data/trainer_data.py` | GPL-3.0 | Packs trainer records and party data. | Directly changes game data; not needed for dialogue authoring. |
| `tools/data/narc.py` | GPL-3.0 | Reads and writes Nitro archives used by the other packers. | Low-level archive helper; callers control input and output paths. |
| `tools/build/romdiff.py` | GPL-3.0 | Compares built and extracted files. | Read-only validation tool; not an authoring command. |
| `maintenance-tools/tools/research/bw2_rom_reference_audit.py` | GPL-3.0-or-later | Compares selected ROM NARCs, overlays, and hashes. | Read-only; requires the separately installed `ndspy` package. |
| `launcher-source/tools/build_bps_patch.py` | GPL-3.0-or-later | Builds a BPS patch from two ROMs. | Reads both ROMs and writes the requested patch directly; no dry-run or overwrite guard. Not used here. |

`romhack_workflow.py inventory` returns this inventory in JSON. The adapted commands invoke the upstream packer source by path; they do not copy or fork its code. They verify the repository URL and exact commit, reject edits/untracked files under its `tools/` directory, reject symlinks in the selected input tree, stage the archive before writing, and return JSON including the output SHA-256. **Dry-run is the default.** Use `--write` to publish a new archive to a local output path. If that output already exists, add `--backup`; the old file is preserved as `.bak` and checked before the staged archive replaces it. The output parent must already exist, and output may not be inside the decomp or input tree.

```powershell
python maintenance-tools/tools/romhack_workflow.py inventory
python maintenance-tools/tools/romhack_workflow.py pack-events "F:\gen5decomps\black2-92%\pokebw2-current\res\field\events" "$env:TEMP\events.narc"
python maintenance-tools/tools/romhack_workflow.py pack-script-text "F:\gen5decomps\black2-92%\pokebw2-current\res\text\script" "$env:TEMP\script-text.narc"
```

Those commands only validate and pack in dry-run mode. To write an archive, repeat with `--write`. Inputs are editable decomp data, not a ROM. The generated NARCs still need to be integrated through the matching decomp build or a separately validated patch process; this tool does not modify or build a ROM.

## Dialogue data and preview

`maintenance-tools/dialogue-demo/field_researcher.json` is a small interactive demonstration. Each node names a speaker, expression, text, and either a next node or a choice list. A choice can test a boolean event flag, which maps to a condition the field-script VM can represent. The preview lets a tester toggle that flag. The renderer uses text content APIs and validates every target before rendering.

```powershell
python maintenance-tools/tools/dialogue_preview.py validate maintenance-tools/dialogue-demo/field_researcher.json
python maintenance-tools/tools/dialogue_preview.py render maintenance-tools/dialogue-demo/field_researcher.json $env:TEMP\field-researcher-preview.html
```

The decomp’s field layout is 256×192 pixels (32×24 8-pixel tiles). Its talk-window bar is 32×4 tiles. `CalcMsgWindowDimensions` measures the text with the game font and adds a 2-pixel margin. The preview therefore keeps dialogue to two lines and at most 28 display cells per line (8 pixels per cell, conservatively leaving room inside the 256-pixel bar). This is an authoring guard, not a claim that the game has a fixed 28-character limit; confirm any longer message with the exact game font and window layout.

No portrait art is bundled. With no image, the demo uses a small expression-aware silhouette. To preview artwork, set an expression’s `portrait` to a relative path inside an assets folder and include `credit`, `license`, and an HTTPS `sourceUrl`; pass that folder with `--assets`. The preview embeds those files into the output HTML. The tool validates the metadata fields and path containment, but it cannot establish that the stated license is true; verify rights and preserve required attribution before using or distributing an image. It accepts PNG, JPEG, WebP, and GIF images up to 4 MiB each.

## Engine boundary

At the pinned source revision, field dialogue has ordinary text windows and event scripts but no general portrait/expression command. The HTML dialogue demo is a preview. The exact-build actor renderer below is a separate in-game implementation. No Sovereign of the Skies code, dialogue, or art was copied.

## In-game actor dialogue art

The exact-build renderer in `maintenance-tools/tools/rom/` now displays the generated portrait, nameplate, and framed panel in an actual actor conversation. The native text printer, page advance, cursor, Yes/No menu, and close behavior remain in use. The supported input is the user-provided Redux `IREO` ROM with SHA-256 `353fb0cf82c3e4eddfc8986efa8910b00eb1c4d6f106c220abef59d69d3a520a`. This fingerprint is mandatory; the patcher refuses other builds and existing output paths. It writes a separate ROM.

Use Python 3.11 or later, the dependencies in `maintenance-tools/tools/rom/requirements.txt`, and an ARM GNU toolchain providing `arm-none-eabi-gcc`, `objcopy`, and `nm`. The tool also checks `C:\SysGCC\arm-eabi\bin` when those programs are absent from PATH. Dependencies can be installed in a private virtual environment.

```powershell
python maintenance-tools/tools/rom/dialogue_art_patch.py `
  --base-rom "<your supported source ROM>" `
  --speaker-profiles maintenance-tools/assets/dialogue-art/speaker-profiles.example.json `
  --output-rom "<new private output ROM>"
```

The example deliberately assigns the Emma demo skin to the central Lentimas Town Pokémon Center nurse: zone 460, actor UID 6. It does not alter the nurse's scripts or text. The actor placement at UID 3 is a different worker; the running nurse script and the exact ROM's event member 606 identify UID 6. Unconfigured speakers retain their stock dialogue windows.

Each manifest profile has `name`, `zone_id`, `actor_uid`, and `art`. Names support 1–8 Latin letters, spaces, or hyphens and are drawn in uppercase pixel lettering. Artwork must resolve inside `maintenance-tools/assets/dialogue-art/`. Up to 64 exact speaker profiles are supported. Wildcard IDs require the explicit test-only `--allow-wildcard-speaker-profiles` flag. The default without a manifest adds no speaker art.

The patch extends the existing ITCM autoload image, reserves its new space by updating the ITCM arena floor, and branches directly to RAM helpers. Overlay 36, its BSS, and its full 64 KiB field heap keep their original sizes and addresses. `0x08000000` is the GBA slot address space, not mapped DS ROM: the abandoned post-data implementation was invalid despite booting successfully. The TwlSDK autoload table in this exact ROM has four words per entry; ndspy's generic three-word section parser must not be used to rewrite it.

The standard path changes only configured actor conversations. Signs and ordinary system messages retain their stock rendering. `--field-system-art` retains the older fixed narrator-art experiment as an explicit diagnostic option; it is **NOT RUN** in the final verification and is not part of the verified actor workflow. Diagnostic actor lifecycle modes are for no-profile fault isolation, not normal play.

To run an isolated, silent test with the installed runner:

```powershell
python maintenance-tools/tools/rom/run_muted_dialogue_test.py `
  --runner "<installation>/tools/emulator_agent.py" `
  --emulator "<installation>/builds/current/melonDS.exe" `
  --rom "<derived ROM>" --save "<source save to copy>"
```

This writes a fresh private configuration with volume zero and uses SDL's dummy audio driver. Its returned `session.json` can be passed to the configured Unova MCP controls. Stop that session with `control_emulator` and no save-export path. Keep frame waits below the request timeout; 480 frames worked in the tested runtime, while one 1,400-frame request timed out even though the same session remained alive.

Run focused checks with:

```powershell
python -m unittest maintenance-tools.tools.rom.test_dialogue_art_patch maintenance-tools.tools.rom.test_dialogue_art_hook_cpu -v
```

The CPU tests compile and execute the real helper code in Unicorn, with game functions replaced by explicit stubs. They verify the hook ABI, state updates, and fallback paths; the separate live scenarios in [the renderer verification record](verification/ROM_DIALOGUE_ART_RENDERER_2026-10-24.md) establish actual game rendering. The private patched ROM and save are not distributable release assets.
