# Unova Together 2.0.26 release checks

## Acceptance and scope

1. Merge reviewed follower/co-op depth, stale-relay recovery, Features presentation and Tailscale setup changes; preserve the current main README edit.
2. Verify combined launcher behavior, legacy relay restart and native rendering unit coverage. Preserve game hooks, XP policy, original ROMs and saves.
3. Build version-matched emulator, launcher and repair entry; package corresponding source, notices and player-facing notes without private game/test data.
4. Publish the reviewed main commit and verify release asset names, sizes, SHA-256 digests and latest discovery.

Risk: HIGH (emulator and release). Base main: `37af897048fdf4f06d2017a2b36a54270c4d2d5a`. Rollback is the preceding 2.0.25 release. The unfinished CPU performance experiment and renderer configuration probes are excluded. Old divergent 1.0.x branches are superseded and excluded; all other historical branches are already ancestors of main.

Live two-client Teleport and scenery/camera verification: **NOT RUN**. Follow `docs/verification/FOLLOWER_DEPTH_ORDER_2026-10-22.md` and the stale-relay section of `docs/DEVELOPER_TESTING.md`. Automated evidence must not be read as gameplay verification.

## Results

- **PASS — SOURCE/UNIT VERIFIED:** 125 canonical launcher, service, appearance, preference, version and patch-note tests; 81 maintenance relay/service/UI tests; 22 updater/release tests, with one optional skip. Three native-patch metadata tests and eight real-renderer groups passed. The existing legacy presence-rendering fixture failure is documented in the follower verification record and predates this change.
- **PASS — BUILD:** Release emulator rebuilt with GCC 16.2.0, CMake 4.4.2, Ninja 1.13.2 and Qt 6.11.2; Python 3.12.8 / PyInstaller 6.22.3 built launcher, bootstrap and standalone. Emulator, launcher and repair entry report 2.0.26. Emulator SHA-256: `f03acbe0d3ad39d0dec0ff8ba37ca8f8c344d65c0afaa7a6a8c13dad83908e6b`.
- **PASS — SOURCE MATCH:** All 2,387 native files in the corresponding-source input match the build tree byte-for-byte. Base is the recorded official 2.0.24 source archive, with the two follower-depth files and two version files changed. The complete development patch reverse-check passed against this source. Diagnostic CPU/benchmark instrumentation is absent from the built source and release archive.
- **PASS — LAUNCHER RUNTIME:** Packaged launcher self-test created the window, checked disabled Play without a ROM, update availability, credits, settings and cleanup entry. Two UI tests covered responsive pages and feature layout; an isolated Features capture was visually inspected after animation loading. UI parity passed for 43 files. No live game was launched by these launcher checks.
- **PASS — RELAY INTEGRATION:** The Windows lifecycle test replaced a real legacy Python listener in a disposable install and verified the current version/capability handshake. This is process integration, not paired Teleport gameplay.
- **PASS — PACKAGE:** Runtime/source ZIP integrity, portable controls, patch-note index, build identities, Qt platform plugin, corresponding source and privacy exclusions passed. Packaged app, metadata, news and relay helper match the reviewed tree. New renderer test sources are included.
- **NOT RUN — GAMEPLAY:** Two-client Teleport, cross-network Tailscale, live follower/co-op scenery occlusion and fast camera motion. Classic OpenGL readback and compute-backend depth limitations remain as documented.

An initial release build stopped on a nonnumeric launcher revision; it was rebuilt with numeric revision `2026102201`. An initially stale bundled news feed was updated and regression checks rerun. Only the final artifacts below are intended for publication. Prior failed staging outputs remain local, unshipped.


## Final assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Repair-Launcher.exe` | 12,217,924 | `9bbc4e0bf31518f802d0d0fff7bff43ce4fe17b290b09e10c621c993c5febf02` |
| `SHA256SUMS-Unova-Together-2.0.26.txt` | 378 | `9c58dda840301d1822ca27eff5896b5b82d39aaed78acbae325483c23ea379cb` |
| `Unova-Together-2.0.26-Source.zip` | 33,012,193 | `354cae06778c891441792f67547b19b7a1c7d6a7d00a314a5477a0e6036f8c38` |
| `Unova-Together-2.0.26-Windows-x64.zip` | 207,417,068 | `1e22da44199d2759f99edc19015b84bb76d0027d4e28d34f7cb0df70067cf8b3` |
| `Unova-Together.exe` | 247,985,189 | `de58eb5e91e0f0c3a0eeae237cd765c8fc75565915388c6d2b6df8cc9b7dc3da` |
