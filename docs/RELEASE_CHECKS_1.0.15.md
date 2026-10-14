# 1.0.15 release checks

- Rebuilt the Windows x64 native emulator from the matching source with both emulator metadata labels set to 1.0.15.
- Built the standalone launcher and permanent repair/bootstrap executable with version 1.0.15; their embedded build identity, runtime metadata and release filenames agree.
- All seven Mega Evolution CTest regressions pass in Debug and Release, including the exact Redux ROM overlay, supplied move-selection capture, native form call, battle cleanup and paired co-op message path. The optional two-instance ENet loopback transport test passed five consecutive runs.
- Launcher version, migration, service, preference and UI suites pass: 29 tests total.
- Runtime and corresponding-source ZIPs pass archive integrity, matching-version, portable-control and private/game-data exclusion checks. The release packaging script verifies executable bytes, launcher metadata, documentation and source tests.
- Four downloadable binaries/archives are covered by the SHA256 manifest; the release package checker verified all manifest entries against the built files.
- Live two-emulator Mega Evolution, co-op animation, failed-peer recovery and natural battle-end restoration were not verified. See [the Mega Evolution test guide](MEGA_EVOLUTION.md).
- Mega Serperior artwork was supplied for the project, but the original artist and public reuse terms have not been confirmed.
