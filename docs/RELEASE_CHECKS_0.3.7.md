# Beta 0.3.7 release checks

- Current native build compiles.
- Both supplied field captures resolve to zone 446 at adjacent tiles; the complete 783-cell decoded grid matches the loaded ROM zone plane.
- Seeded stale battle status clears on three confirmed field samples.
- Recorded before/battle/after/menu captures classify correctly.
- Stock menu retention survives a deliberately stale matrix entry ID.
- Damaged matrix dimensions fail closed.
- Player motion, status markers, depth/camera and rendering regression checks pass.
- All 12 presence relay tests pass.
- Native menu fixture passes, including stock screen overlay suppression.
- Bundled executable/portable ZIP contain the matching native binary and exclude ROMs, saves and diagnostics.

Limits: capture replay and emulator fixtures are not a fresh multi-device playthrough. No claim of eliminating all desyncs or fixing co-op EXP is made.
