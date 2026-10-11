# Verified Frost editor workflow

Unova Together maintenance by mvq1303 / WhatWasMissing, built on melonDS. Frost's Gen 5 Editor is a separate tool by FrostFalcon. It is downloaded locally rather than bundled into our public release.

## What was implemented and checked

On 11 October 2026 we downloaded the official Frost **5.0.1** archive and verified its GitHub SHA-256 digest:

`56f50a4b0f4d9b7e13df16d3b66fc55e5e243447be705f34b4d76c84dfde0a27`

`tools/setup_gen5_editor.py` installs the pinned archive and verifies all 45 installed files. `tools/run_frost_roundtrip.ps1` calls the shipped editor's parser/exporter through a C# bridge, using its normal ROM initialization. It requires the reviewed executable hash and a fresh output directory. It runs headlessly using Windows PowerShell 5.1; no permanent execution-policy change is made.

The actual Redux 1.4.1 round trip compared **662 files**. Frost repacked **17 NARCs**, but their contained entries stayed byte-identical. ARM9/ARM7 code, decoded overlays and all six growth tables stayed unchanged. All 606 growth values read by Frost matched ndspy's original data. The original ROM's SHA-256 stayed unchanged.

Redux's type-name bank `a/0/0/2`, entry **398**, had 17 labels and lacked **Fairy**. With `-PrepareFairyType`, the runner adds that label only when missing and recompresses only that text entry before export. The resulting private editor-ready copy changed exactly that entry; code, overlays, growth tables and other contained entries were unchanged. A second parse/export confirmed all 18 labels and did not add a duplicate.

This is content-level verification using the actual editor binary. Startup, battles, co-op and save/reload of the exported ROM have **not** been tested. The original player ROM and released 1.0.2 assets are unchanged. The private editor-ready ROM is not distributed.

## Reproduce

From the workspace root, using Python with ndspy installed:

```powershell
python tools/setup_gen5_editor.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/run_frost_roundtrip.ps1 -Rom "path/to/Redux.nds" -OutputDirectory "test-fixtures/frost-check"
python tools/audit_gen5_editor_export.py "path/to/Redux.nds" "test-fixtures/frost-check/Redux-frost-roundtrip.nds" --frost-report "test-fixtures/frost-check/frost.json" --report "test-fixtures/frost-check/audit.json"
```

For an isolated editor-ready copy, use a different fresh output directory and add `-PrepareFairyType`. Its exported filename is `Redux-frost-editor-ready.nds`. The audit intentionally exits **1** for this content change: review `changedFiles` and confirm that the only changed contained entry is `a/0/0/2:398`. A no-op export must exit **0**. Do not classify the expected reviewed label edit as an unchanged export.

`python tools/test_gen5_editor_audit.py` checks that the audit accepts unchanged data and rejects changed ARM code, growth entries and ROM identities.

## How to use this next

Open the private editor-ready copy in `tools/external/gen5/Frost-5.0.1/app/FrostsGen5Editor.exe` to inspect trainer teams, scripts and encounters. Audit every export against its input. Preserve the original growth thresholds alongside the 1.65× battle XP boost. Require gameplay checks before adopting a ROM export as a player build.

Private evidence is retained under `test-fixtures/gen5-editor-20261011`: successful no-op export in `frost-roundtrip-05`, label preparation in `frost-editor-ready`, and the idempotency check in `frost-ready-recheck`. Earlier failed runner attempts are retained and are not counted as editor passes.

Sources: [Frost's release](https://github.com/FrostFalcon/FrostsGen5Editor/releases/tag/5.0.1), [Redux/Fairy compatibility notes](https://github.com/FrostFalcon/FrostsGen5Editor), [ndspy](https://github.com/RoadrunnerWMC/ndspy).

Follow-up helper sources are available in [maintenance-tools](../maintenance-tools/README.md); these are separate from the immutable 1.0.2 release packages.
