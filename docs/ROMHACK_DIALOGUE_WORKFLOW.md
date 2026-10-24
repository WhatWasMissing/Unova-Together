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

At the pinned source revision, the field dialogue code provides ordinary text windows, menus, and event-script conditions; it does not expose a general field portrait/expression command. The demo is an interactive local preview, **not an in-game ROM implementation**. The decomp contains specialized scene/portrait rendering elsewhere, but that does not make those systems reusable from an ordinary field NPC. A future in-game version needs a compatible renderer and a validated integration into the decomp build/Redux patch flow. No Sovereign of the Skies code, dialogue, or art was copied.
