# Development polish — 13 October 2026

Unova Together by **mvq1303 / WhatWasMissing**, built on melonDS. AI-assisted maintenance by OpenAI Codex at the author's request. This is the **1.0.7-dev source/local build** and the matching **1.0.7 GitHub prerelease**, following the stable 1.0.6 release. New-build packaging and limits are in [1.0.7 preview checks](RELEASE_CHECKS_1.0.7.md).

## Changes

- Followers have **743 directional assets**: all 649 base species, supported alternate forms and authored female variants, each with normal/shiny palettes. Unsupported forms use base art. Large 64-pixel art retains its dimensions; walking frames have headroom. A bounded sprite cache, short camera-gap retention and consistent local trainer silhouettes reduce disappearing limbs and transient flicker.
- Gen 5 nature, gender and shininess come from the decrypted Pokémon record. Nature no longer incorrectly comes from PID modulo 25.
- Companion dialogue adds verified area names, DS calendar/time, loaded-ROM Pokémon types and a neutral recent-battle context. Each Pokémon/action has a session visit counter. This remains cosmetic: no friendship, items, HP or save writes. Weather and win/loss-specific dialogue are not implemented. Reduced follower motion keeps sprites and reaction symbols visible while suppressing decorative movement.
- Practice uses a two-sided result barrier before the native parent tears down wireless communication, followed by guest cleanup acknowledgement. PvP is excluded from equal-result agreement because opponents have different outcomes. Retries reset result/readiness/cleanup state. Stale cancellation nonces are scoped to their sending peer.
- Co-op protocol 2 separates incompatible battle clients. Presence includes validated protocol, mod revision and ROM fingerprints; player-battle controls explain incompatible or missing information. Normal exploration remains available. Updated clients need an updated presence relay. Native trainer agreement also checks protocol/ROM.
- Launcher Co-op has a combined readiness card for the selected build/profile, presence test result and explicit in-game checks. It cannot verify a partner's game state before connecting. Practice browsing filters All, Gym leaders, Rivals, League and Other trainers; teams/levels still come from the loaded ROM.
- **Super Repels cost ₽10**, the lowest positive native price: item records store prices in units of ten. Active ordinary money-shop catalogs stock them. A cartridge read overlay preserves files and other item fields; no instruction hook forces a price. Special currency/exchange shops are outside this policy.

## Validation

- Full native CMake build and PyInstaller launcher build.
- Production renderer checks: stable gait occlusion, large companions, reduced motion, partial screen edges, camera expiry/map transitions and battle badges.
- Production sprite loader: all 649 base species and all 743 authored variants decoded against original Black 2 and Redux, including shiny palettes.
- 96 encrypted-record permutations/flag cases verify IVs/EVs, independently stored nature, gender/form and shininess without writes. Input gates retain ordinary A-button text advancement.
- 5,000 nature/action/friendship/variation cases, plus contextual dialogue coverage; 16 presence relay tests; launcher checks.
- Real ENet three-player lobby tests cover pairing a second guest, ready/result/cleanup agreement, radio isolation, repeated pairings, differing outcomes and partner loss.
- Generated ARM payload: 17 field-return cases include holding unagreed Practice results, releasing agreed results and preserving PvP behavior.
- Independent normal boots completed a Cheren Practice battle with **50 ms one-way delay added after both scenes were running**. Both games agreed on victory, returned to the field, released allocations and could start again. This used a disposable combat fixture; it does not prove normal difficulty, persistent rewards, physical two-PC or WAN behavior.
- Both original Black 2 and Redux: 32 active money-shop catalogs contain Super Repels; respectively 27 and 28 additions. Other stock and item data are unchanged. Executing each ROM's actual native item-price routine returns **10**. Live shop checkout/save persistence has not been separately tested.

Initial 120/160-second battle runs reached active scenes but timed out before completion. Their evidence is retained and is not counted as a pass. A concurrent cancellation runner exited during guest boot; it is not a recovery pass. Expanded physical-PC, defeat, repeated-battle and real shop playtests remain required before a public release.

A subsequent isolated normal-boot cancellation/retry run passed on the final native build: both games ran the first battle, restored their checkpoints, paired and ran a second battle, then restored again with released allocations and field readiness. The failed concurrent boot is retained separately.

The final guest-loss run also passed: after both scenes ran, the test terminated the disposable guest. The host restored its checkpoint, released owned allocations and became field-ready. This proves recovery rather than resuming the interrupted battle.

## Reproduce the source

Use the published **Unova-Together-1.0.6-Source.zip**, verified by `maintenance-tools/patches/development-polish.json`. From its extracted `Unova-Together-Source` directory, apply `maintenance-tools/patches/development-polish.patch` with `git apply --ignore-space-change`. This patch includes the earlier companion-default change; do not also apply `companion-defaults.patch`.

Copy `maintenance-tools/assets/followers/variants` into `source/melonDS/res/followers/variants`, then overlay `maintenance-tools/tools` onto the workspace's `tools` folder. Build using the included melonDS build instructions. The generated ARM header is supplied; regenerating it needs the documented private supported capture and ARM toolchain. ROMs, saves and RAM captures are not published.

To rebuild the variant assets from public sources, copy `maintenance-tools/references/follower-completion-20261010` to the workspace's `research/follower-completion-20261010`, then run `build_follower_variants.py`. The pinned tree/species constants are public metadata; no ROM or RAM fixture is used by this asset builder.

Run `test_follower_polish.py`, `test_super_repel_shops.py`, `test_party_stats.py`, `test_companion_and_soaring.py`, `test_overworld_companion.py` and the launcher/presence tests. Native battle runners need isolated private fixtures. See [variant provenance](FOLLOWER_VARIANTS.md).
