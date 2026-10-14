# Unova Together 1.0.11 — Wider Soaring view

This full launcher-detectable release packages the next Soaring test step. The flight scene now streams a wider view of the verified Black 2 outdoor matrix, with fog fading distant terrain and a fallback that reduces scene radius in dense areas to stay within the scenery budget.

Enable **Settings → Experimental features → Soaring flight**, then use **Unova → Pokémon → Take flight**. Soaring remains off by default and local to the player. It does not use the Town Map or claim to connect every separate map matrix. Use the visited-spot landing option where available; verified clear ground and return-to-take-off remain the safe landing paths. Unsupported or missing scenery is covered by the cloud sea.

The release includes matching game and launcher version **1.0.11**, the Windows x64 runtime, standalone launcher, repair utility, corresponding GPL source and SHA-256 checksums. Install from launcher **Updates** or download the complete package. Both players should update to the same version. Existing ROMs and saves do not need conversion.

## Validation

The scene worker regression tests cover the wider radius and budget fallback. ROM-backed checks cover route terrain, a neighboring zone and matrix-edge sky. The assertion-enabled native renderer check passed streamed-scene and neighboring-zone landing cases. The sampled 3,072-unit scene rendered 16,076 faces; the 256×192 renderer microbenchmark measured 7.75 ms p95, compared with 7.22 ms for the 2,048-unit sample. These are focused checks, not full-game frame-time guarantees. Please test the expanded flight view, landing and performance in your own game.

The whole region is not yet a connected atlas: separate matrices have no verified shared coordinates, and some model backs or unsupported props may be missing. Soaring stays experimental. No ROMs, firmware, saves or private captures are included.

Made by **mvq1303 / WhatWasMissing**, built on melonDS. Upstream and dependency notices are retained.
