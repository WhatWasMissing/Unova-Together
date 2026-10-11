# Unova Together 1.0.1 — Maintenance release

Launcher 1.0.1 and modified melonDS 1.0.1, based on melonDS 1.1. This full release packages the post-1.0.0 maintenance review, improved verification tools and current known limitations. Gameplay behavior is unchanged from 1.0.0.

Download **Unova-Together.exe**, or extract **Unova-Together-1.0.1-Windows-x64.zip** and run **Start Unova Together.cmd**. Existing players can use launcher Updates. Update both players; existing saves and ROMs need no conversion.

## Maintenance changes

- Cancellation/retry verification now independently boots both radios instead of cloning savestate wireless state.
- Added a guest-process-loss recovery check and clearer relay/latency evidence names.
- Added native touch-based NPC move selection and a strict save-input completion check.
- HM verification accepts an explicit matching ROM; checks passed with JIT enabled and disabled.
- Included the maintenance review and reproducible verification sources.

## Verification and limits

Local independent-process cancellation/retry passed, including the encrypted UDP relay. Guest loss restored the host checkpoint and released battle allocations. A shared Cheren victory awarded the badge on both games, and separate fresh normal boots verified both saved awards. Saved EXP, levels, moves, IVs and EVs were preserved. This NPC test used disposable boosted combat stats; it does not validate normal difficulty.

Co-op XP remains disabled. A simulated 100 ms round trip in Practice exposed asymmetric completion: one peer finished and the other rolled back. That issue is documented and remains unfixed. Physical two-PC/WAN reliability, complete Fly travel and independent save/reload of relearned moves are not newly verified. See **docs/MAINTENANCE_REVIEW_2026-10-11.md** and **docs/KNOWN_ISSUES.md**.

The complete Windows runtime, matching GPL source and SHA-256 checksums are included. No ROMs, firmware, user saves or private settings are distributed. Unova Together's original contributions are by **mvq1303 / WhatWasMissing**; melonDS and dependency notices are preserved.
