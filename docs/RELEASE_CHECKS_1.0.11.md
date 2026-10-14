# Release checks — 1.0.11

## Soaring

- [x] Python Soaring worker regression suite passed, including fallback through smaller radii when a scenery budget is exceeded.
- [x] ROM-backed extraction covered route terrain, a neighboring zone and the edge of the verified outdoor matrix.
- [x] Assertion-enabled native renderer check passed for streamed scenes and neighboring-zone landing.
- [x] Sampled scene at 3,072 units contained 16,076 faces. A 256×192 scene-only renderer microbenchmark measured 7.75 ms p95 versus 7.22 ms at 2,048 units. This does not guarantee full-game performance.
- [ ] Player live test of route-to-town transitions, landing, save/reload and frame pacing remains requested.
- [ ] Separate map matrices are not joined; unverified model backs, props and map transitions remain possible gaps.

## Package

- [x] Runtime and corresponding source archives pass ZIP integrity checks and exclude ROM, firmware, save and RAM-capture extensions.
- [x] Launcher build metadata and emulator version identify as 1.0.11.
- [x] Bundled keyboard/controller settings are preserved in the portable runtime configuration.
- [ ] Two-computer and physical WAN playtests are outside this release's Soaring verification.
