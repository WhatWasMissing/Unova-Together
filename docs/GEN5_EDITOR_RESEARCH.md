# Gen 5 editor investigation — 11 October 2026

Recommendation: use Frost's Gen 5 Editor for inspecting ROM content, ndspy for reproducible checks, and PKHeX for inspecting disposable save copies. Pokeweb Serverless is a useful second opinion for maps and generated balance documentation. These tools complement the emulator mod; ROM edits do not automatically fix multiplayer synchronization.

| Tool | Useful work for Unova Together | Limits and verification |
| --- | --- | --- |
| [Frost's Gen 5 Editor](https://github.com/FrostFalcon/FrostsGen5Editor) | Inspect trainer teams, encounters, Pokémon data, scripts, text, overworld objects and six EXP curves. Latest release checked: [5.0.1](https://github.com/FrostFalcon/FrostsGen5Editor/releases/tag/5.0.1). | Maintainer documents full B2W2 support and Redux compatibility, subject to Fairy type setup. We have inspected source, not tested a Redux export round trip. Windows .NET Framework 4.8 application. |
| [Pokeweb Serverless](https://github.com/hzla/Pokeweb-Serverless) | Gen 5 browser editor; map/collision inspection, trainer and encounter data, Fairy type chart, NARC comparisons and Dynamic Calc/Dex documentation generation. | Current successor to the deprecated original Pokeweb. Run locally with its documented npm/Vite workflow. Redux export compatibility still needs validation. |
| [PKHeX](https://github.com/kwsch/PKHeX) | Inspect party Pokémon and XP in actual Gen 5 saves; help verify save/reload after real battles. | Save editor, not ROM editor. Interpret levels against Redux's actual growth tables. Edited saves are test fixtures, not evidence that native rewards persisted. |
| [BW Tool](https://github.com/suloku/BW_tool) | Inspect specialized Gen 5 save systems, including trainer/badge data, Memory Link, medals and Join Avenue. | More specialized than PKHeX; unnecessary for changing battle XP. |
| [ndspy](https://github.com/RoadrunnerWMC/ndspy) | Extract NARCs and overlays, compare ROM data, automate regression checks and reproduce known edits. Already used by our local checks. | A Python library rather than a visual editor. Best paired with a GUI editor. |
| [Pokémon DS Map Studio](https://github.com/Trifindo/Pokemon-DS-Map-Studio) | Create new Gen 4/5 map assets if the project later expands into new areas. | Its README explicitly says it cannot import or modify original game maps. Lower priority for this feature-complete mod. |

## Frost and the 1.65× XP boost

The [EXP curve form](https://github.com/FrostFalcon/FrostsGen5Editor/blob/main/Forms/ExpCurveEditor.cs) edits the XP needed between levels and writes cumulative thresholds through [XPCurveNARC](https://github.com/FrostFalcon/FrostsGen5Editor/blob/main/Data/NARCTypes/XPCurveNARC.cs). It does not multiply the reward earned from a battle. Changing those thresholds alongside our 1.65× reward hook would compound progression changes. Keep the existing thresholds for the current release; use the editor to cross-check our extracted six curves.

Our ROM analysis already matched all six Redux growth tables in `a/0/1/7`. That is local data verification, separate from Frost's compatibility claims. The completed Cheren battle comparison verified XP in RAM, but normal save/reload remains unverified. Save inspection tools can help close that gap after a successful in-game save.

## Redux precautions and a concrete workflow

Frost's README says Redux's Fairy implementation requires the type list in BW2 text file **398** to contain **Fairy** (BW1 uses 199). Inspect a disposable ROM copy first; do not blindly append a duplicate entry. Before accepting any editor output, compare extracted files and confirm that only intended content changed.

1. Hash and preserve the original ROM and save; create isolated working copies.
2. Inspect content in Frost. Export only from the copy, and compare NARCs/overlays with ndspy.
3. First test an unchanged export round trip, including startup, normal battle, co-op and save/reload. Our emulator hooks depend on specific code fingerprints; another editor's code patches can cause a hook to decline to apply.
4. For a real content change, keep a machine-readable change list and regenerate Challenge trainer/XP documentation from the edited ROM.
5. Verify the result through gameplay and actual saved data. Never manufacture reward or badge changes to count a battle test as passed.

The best next use is inspection and stronger test evidence, rather than adding more gameplay features. No editor was installed, no ROM was uploaded to a web editor, and no ROM/save was modified during this investigation.

## Common tool-name traps

[Current PokEditor v3](https://github.com/turtleisaac/PokEditor) and [DSPRE](https://github.com/DS-Pokemon-Rom-Editor/DSPRE) focus on Gen 4. The historical [PokEditor v1](https://github.com/turtleisaac/PokEditor-v1) had Gen 5 support, but is a legacy project. They are not the first choice for our Black 2 Redux workflow.

Research is based on project documentation and source as checked on 11 October 2026. Compatibility beyond the existing ndspy checks has not been established through editor round-trip testing.
