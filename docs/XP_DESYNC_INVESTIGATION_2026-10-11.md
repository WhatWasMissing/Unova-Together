# Mid-battle XP investigation — 11 October 2026

Unova Together by mvq1303 (GitHub: WhatWasMissing).

## Findings

Automatic NPC startup sets both `automaticStory=true` and `manualTest=true` in NativeCoopRuntime.cpp. The misleading manualTest name does not mean story battles bypass XP suppression. Both reward-builder and setter hooks remain enabled during AwaitBattle/AwaitStory, excluding PvP and completed battles.

Historical dual-npc-input-review-03 captures recorded active suppression but zero experience setter interceptions. A move-learning prompt was observed in that test. Setter interception alone cannot prevent reward UI: the controller can enqueue the prompt before attempting the guarded save write.

The subsequent reward-builder hook intercepts overlay 29 at 0x021AEE0C, checks the caller 0x021A8E1F and both code fingerprints, and clears exactly six 12-byte reward records. The historical dual-no-exp-04 evidence records three suppressed rewards on each peer, unchanged human EXP/levels/moves, both completed battle results, and unchanged saved party banks.

A level-up or move-learning prompt appearing on only one game is the leading explanation for interrupted shared battle flow. Different levels, resulting stats, and move choices also need synchronization if XP is enabled; extending the peer-loss grace period alone is not a complete solution. This investigation has not reproduced a new level-up stall on the current build and does not establish that every reward path is intercepted.

## Checks performed

- Four captured native experience-setter wrapper cases passed: getters/cleanup preserved, only XP writes skipped.
- Four compiled retained-story return cases passed.
- Reward guard fingerprint/bounds test run against an active overlay capture (dual-npc-input-review-03), rather than a completed field capture where overlay 29 is no longer resident.

## Next implementation boundary

Keep the current no-XP safety behavior until a disposable two-console test verifies an XP-enabled reward path. Test asymmetric levels, one-sided level-up, move learning, multiple fainted enemies, switching and full-party recipients. Any solution must preserve each independent party and native save ownership, synchronize resulting battle stats/moves before the next turn, and handle cancellation without double awards. Post-battle game-owned rewards are a possible direction, not an implemented feature.

