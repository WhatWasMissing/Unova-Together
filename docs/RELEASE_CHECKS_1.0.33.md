# Release checks — 1.0.33

## Verified locally

- The Windows Qt emulator target rebuilt successfully from the current source.
- The focused follower regression and full emulator build passed after correcting the walking pose baseline and route-timed lift.
- Native Mega/follower/menu checks passed, including full timed playback checks for all 46 packed Mega animation clips.
- The 49-form Mega roster, matching stone data, item icons, names, and PC Mart entries passed the source regression checks.
- The Soaring worker/geometry suite passed all 33 tests. Native map, flight, streaming, and simulated landing checks covered all 69 outdoor roots; Marine Tube correctly offers return to take-off instead of a landing.
- The launcher patch-note index was regenerated from the versioned notes, retaining the previous notes for launcher discovery.

## Still needs an in-game check

Soaring is unfinished. Automated checks do not prove that its routes and landing transitions behave correctly during live play. Some positions are approximate and Marine Tube has no safe landing. Save normally before testing it.

Follower spacing and motion, the full Mega roster, and linked co-op Mega battles also need continued playtesting on real saves and across more than one emulator.

## Test commands

The latest focused results are recorded in [development checks](DEVELOPMENT_CHECKS_2026-10-16.md). The ROM, decomp, saves, RAM dumps, captures, and generated test outputs are not included in this release.

