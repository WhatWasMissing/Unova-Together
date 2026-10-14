# Release checks — 1.0.12

## Soaring and landing

- [x] Python scene-worker tests cover collision categories, NPC event decoding, landing clearance, regional fills, matrix streaming, deterministic flyways and scene-budget fallback.
- [x] Assertion-enabled native renderer check covers flight controls, altitude limits, map bounds, landing phases, generated region faces, collision visualization and frame rendering.
- [x] Native emulator built from the matching source tree.
- [ ] Live ROM testing of repeated landings beside NPCs, dialogue input after landing, speedup and transitions between supported zones remains needed.
- [ ] Separate map matrices still lack verified shared coordinates; generated ocean, forest and flyways are visual only.

## Launcher and package

- [x] Launcher tests cover navigation, settings, update services and saved preferences.
- [x] Emulator and launcher metadata both identify as 1.0.12.
- [x] Windows runtime and corresponding GPL source archives pass ZIP integrity checks and exclude ROMs, saves, firmware, RAM captures, build folders and diagnostics.
- [x] Standalone launcher, repair utility and checksum manifest are generated for the full release.
- [ ] Physical two-computer and WAN playtests remain outside these local regression checks.
