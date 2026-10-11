# Unova Together 1.0.2 — Solo XP compensation

Launcher 1.0.2 and modified melonDS 1.0.2, based on melonDS 1.1. This full release adds **1.65× solo battle XP** to help compensate for XP suppressed in co-op.

Download **Unova-Together.exe**, or extract **Unova-Together-1.0.2-Windows-x64.zip** and run **Start Unova Together.cmd**. Existing players can use launcher Updates. Update both players; existing ROMs and saves need no conversion.

## Changes

- Newly earned solo battle XP is multiplied by 1.65 after the game calculates level scaling, XP sharing, traded bonuses and Lucky Egg bonuses.
- Fractional XP rounds down per Pokémon; the native 100,000 XP per-award limit remains in force.
- Existing accumulated XP, reward flags and EV rewards are unchanged. Co-op XP remains suppressed: zero rewards stay zero.
- Verified ROM identities, native instruction fingerprints and reward bounds protect unsupported contexts.
- Added reproducible production-dispatch tests, a disposable solo battle runner and the selected Redux Challenge XP-budget calculation.

## Verification and limits

Genuine solo Cheren victories on disposable saves awarded the badge and applied actual party XP: Servine gained **807 XP** with the boost versus **498 XP** normally. The measured total was 62.05% higher; the earlier level-up affects later Generation V rewards, and per-award rounding applies. The reserve Pokémon received no XP. The fixture used boosted combat stats and the interpreter; this does not validate normal difficulty or an end-to-end JIT battle.

**Normal save/reload of the boosted result remains unverified.** Automated post-battle save inputs did not write either result to disk; this is recorded as a failed verification step, separate from the completed battles. No save/reload pass is claimed. See **docs/XP_COMPENSATION_BATTLE_TEST.md**.

The previously documented Practice completion issue under simulated latency remains unfixed. Physical two-PC/WAN reliability, full Fly travel and relearned-move save/reload are not newly verified. See **docs/KNOWN_ISSUES.md** and the maintenance review.

The complete Windows runtime, matching GPL source and SHA-256 checksums are included. No ROMs, firmware, user saves or private settings are distributed. Unova Together's original contributions are by **mvq1303 / WhatWasMissing**; melonDS and dependency attribution is preserved.

## Subsequent save/reload verification — 11 October 2026

After publication, the same 1.0.2 emulator completed another genuine solo Cheren battle, saved Servine at **5,951 XP / level 20** and the badge through the game UI, and reloaded the same result in a fresh process without a savestate. PKHeX independently verified the written data and checksums. This closes the targeted solo XP persistence gap described above; JIT and full-playthrough behavior remain unverified. See [the follow-up evidence](https://github.com/WhatWasMissing/Unova-Together/blob/main/docs/XP_COMPENSATION_BATTLE_TEST.md). Release binaries, corresponding source archives and checksums are unchanged.
