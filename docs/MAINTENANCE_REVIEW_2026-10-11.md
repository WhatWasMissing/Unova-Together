# Post-release maintenance review — 11 October 2026

Unova Together by mvq1303 (GitHub: WhatWasMissing), built on melonDS.

This review used the published 1.0.0 emulator in independent private runtimes. No gameplay patch was installed, release assets were replaced, or user save was edited. The evidence is sealed by `tools/record_maintenance_100.py` in `test-fixtures/release-1.0.0/maintenance.json`.

## Verified

- Independent normal boots reached a shared native battle, cancelled, restored both field checkpoints, then repeated the battle and cancellation. Both peers released owned allocations and could start again.
- The same cancellation/retry passed through the actual encrypted UDP bridges and relay on loopback. This does not establish WAN reliability.
- Terminating the guest after both battles were running made the host restore its field checkpoint, release owned allocations and become available for another battle.
- An actual automatically paired Cheren encounter completed with an agreed victory on both games. Ordinary saving from each captured completed state wrote the badge to both save banks; separate fresh normal boots, without savestates, read the earned badge on both peers. EXP, levels, moves, IVs and EVs remained unchanged in the saved parties. Disposable combat-stat boosts accelerated this test; normal game difficulty was not validated.
- The first save-input run reached the confirmation screen but timed out before writing. Its failed reloads are retained. They are not counted as persistence passes; the separate completed-state saving and subsequent normal boots provide that evidence.
- Native HM party-menu dispatch and the Fly destination map worked with JIT disabled and enabled, without changing party records. This check intentionally did not write a save or fly to a destination.
- Production HM dispatch cases covered 24 record shuffles, six HMs, missing items, eggs, foreign members, isolation from battle/tutor moves and duplicate refusal. Native routine fingerprints matched original Black 2 and Redux.
- Production field-tool readers covered 13,234 learnable moves and 9,048 encounter rows across 540 area/season tables. Encrypted party decoding covered 96 IV/EV cases. Experience setter isolation and the fingerprint/bounds-checked reward guard passed against the current active NPC capture.

## Fixes to the verification tools

`check_release_100_native.py` now uses independently booted LAN processes for cancellation/retry instead of cloning wireless state from a savestate. `verify_lan_coop.py` can terminate the guest during a running battle and assert host recovery. Output names identify encrypted relay, guest loss and injected battle latency.

`verify_npc_story_live.py` can select moves through native touch input, avoiding repeated directional input drifting through the move menu. A save-after run must finish its save-input window to pass; a completed battle alone no longer passes that requirement. Actual persistence still requires `verify_npc_save_reload.py` and a fresh normal boot.

`probe_native_field_hms.py` accepts an explicit matching ROM, so the reviewed state can be reused without a stale fixture ROM copy. None of these changes enable gameplay cheats in a normal build.

## Remaining substantive work

1. **Practice result/cleanup under latency.** Introducing 50 ms one-way latency after both Practice battle scenes were running produced one completed peer and one peer that rolled back after partner loss. Starting with the same latency also failed to reach two running battles within the window. These are failed tests. They do not establish that automatic NPC story battles have the same problem. `NativeCoopRuntime::Finish` clears the challenge after local completion, while the result agreement and host waiting for remote cleanup are guarded by story-specific conditions. This is a plausible teardown race, not a proven fix. A correction needs a two-sided Practice completion barrier and tests for victory, defeat, cancellation, guest loss and asymmetric pacing. PvP outcomes need separate handling because each player's win/loss result differs.
2. **Co-op XP.** Reward suppression is working in this encounter; four reward batches were suppressed on each peer. Restoring XP requires synchronized recipients, levels, resulting stats and move choices, plus rollback and duplicate-award prevention. Removing the guard would reintroduce the known one-sided reward-UI problem. See `XP_DESYNC_INVESTIGATION_2026-10-11.md`.
3. **Physical PCs and WAN.** All new multiplayer checks used two local processes. Router/NAT behavior, real packet loss, jitter and remote disconnect/rejoin remain unverified.
4. **Wider persistence and travel coverage.** The completed trainer award persisted. This pass did not independently save/reload a relearned move, complete Fly travel, or play through every special trainer and story gate.

The mod remains feature complete in scope, with maintenance and these known limitations remaining. The existing full 1.0.0 release has not been silently changed by this review.
