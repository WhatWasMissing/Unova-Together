# Unova Together 1.0.0 release checks

Reviewed on 11 October 2026. Launcher and modified melonDS identify as 1.0.0; upstream melonDS remains credited as 1.1. Validation uses disposable profiles, copied saves and private fixtures.

| Feature group | Checks |
| --- | --- |
| Launcher pages, keyboard/controller navigation and window sizes | Native launcher UI suite; nine pages, focus, settings, profiles, news and update states; screenshot review |
| Profiles, settings, backups, restore, repair and diagnostics | Preference, service, all-settings, updater and bootstrap suites; checksum validation and preservation checks |
| Release updates | Stable release preferred over newer preview; beta-only feed remains compatible; bad downloads/paths/checksums rejected |
| Shared exploration and camera | Current production rendering, interpolation, camera continuity, battle badges and post-battle presence contracts |
| LAN lobbies and pairing | Real ENet three-player lobby fixture; selected partner agreement, readiness/result, radio isolation and disconnect cleanup |
| Item offers | Relay conservation/recovery suite and rebuilt binary native transfer fixture; normal, interrupted and recovered decisions |
| Pokémon trades | Relay suite and rebuilt binary native party/Dex fixture on Black 2 and Redux; normal swap, rejection, interrupted commit and one-time recovery |
| Co-op and PvP controls | Native menu requests/invitations and readiness fixture; story constructor, retained-story return, shutdown and trainer agreement contracts |
| Following Pokémon | All 649 followers decode on original Black 2, Redux and the edited Unova Together ROM; trail, projection and battle visibility checks |
| Companion interactions | Current production facing/A-button input and read-only reaction tests; opt-in, eggs, health/friendship and battle gates |
| IVs/EVs | Encrypted-record decoder across 24 shuffles; native menu agrees with party record and leaves it unchanged |
| Encounter finder and relearning | All 649 learnsets, seasonal ordinary encounter tables on both ROMs; native confirm/cancel, actual replacement and other-slot preservation |
| Field HMs | Six HM dispatch paths, missing items, eggs, 24 shuffles, original story gates, battle/tutor isolation and unchanged Pokémon records |
| Optional scenery | ROM-backed arena export/bounds, resource preservation, surrounding geometry and worker contracts |
| Optional cheats | Production Action Replay executor on captured RAM; activation buttons, intended writes, native bag interpretation and ROM fingerprint gates |
| Native game menu handoff | Rebuilt binary fixture covers Unova entry, Options/Trainer Card return, direct tabs, configured buttons and input release |

The workspace holds the detailed contracts and native fixture reports under `test-fixtures/release-1.0.0`. Matching corresponding source, dependency notices and SHA-256 checksums ship with the release. Packages are checked for version agreement, archived source identity, ZIP integrity, retained keyboard/controller controls and exclusion of ROMs, saves, firmware, recovery journals and diagnostics.

These checks complement existing gameplay evidence and the author's current playtesting. They do not constitute a new end-to-end playthrough of every trainer script, HM obstacle, network, map or special battle. Co-op XP remains disabled, interrupted battles can require checkpoint recovery, and the optional UDP bridge and nearby scenery retain their documented limits. See [known limits](KNOWN_ISSUES.md).

The native menu fixture passes with the matching original Redux ROM and reviewed copied state. Its first attempt combined an older state with the edited ROM and failed menu-entry checks; that mismatched fixture is not counted as a pass. Native item transfers and Pokémon trades pass, including interrupted commit recovery on both original Black 2 and Redux. The legacy two-core cancellation fixture remained waiting for a wireless peer and timed out before a battle started; it does not verify live cancellation in this release. The 13 compiled lifecycle, 342 boss, 54 party-return and 14 PvP payload cases pass. A new complete two-device battle playtest was not performed during this polish pass.

The frozen launcher and standalone EXE pass clean-install smoke checks. The final package checks match 1,033 archived source files to the workspace, verify both executable versions and retained keyboard/controller bindings, and exclude private/game data.

Made by mvq1303 / WhatWasMissing; playtesters maxback221 and randomitem19. Upstream and dependency attribution is preserved.
