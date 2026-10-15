# 1.0.18 release checks

## Serperior-only build

- Release desktop application built with `UNOVA_MEGA_LOCAL_DRAFTS=OFF` and
  Windows product version 1.0.18.
- The public-roster regression confirms the sole enabled profile is Mega
  Serperior: species 497, item 113 and form 1.
- Launcher versioning (12 tests), launcher migration (12), updater (13), and
  standalone-packaging unit tests (6) pass.
- Launcher versioning (12 tests), launcher migration (12), updater (13), and
  standalone-packaging unit tests (6) pass.
- Release CTest suite: 8/8 passed, including Mega profile/assets, native
  selection and call transaction, paired co-op packet, LAN transport, ROM
  overlay, and the Redux cartridge gate.
- The exact English Redux ROM (`IREO`, SHA256
  `353FB0CF82C3E4EDDFC8986EFA8910B00EB1C4D6F106C220ABEF59D69D3A520A`)
  cold-boots on the Release application. The check observed a rendered,
  advancing frame, relocated archive reads, and Mega enabled.
- The matching-overlay 1.0.17 battle replay verified Mega Serperior's native
  form change and saved-party preservation. A fresh native replay was not
  possible for the current build: the only available state came from a local
  draft executable. Loading it under the Serperior-only build correctly failed
  closed and preserved the party record. A fresh 1.0.18 in-game battle replay
  remains a user playtest item.
- A separate two-emulator in-game Mega battle, natural battle-end test, and
  failed-peer recovery remain unverified.

## Package checks

- Launcher and emulator version labels both report 1.0.18.
- Windows x64 runtime ZIP, corresponding-source ZIP, standalone EXE,
  Repair-Launcher EXE, and SHA256 manifest pass the release packager's archive,
  version, checksum, and private-file exclusion checks.
- No ROM, save, firmware, RAM capture, or generated test fixture is included.
- Other local Mega forms remain disabled in the public executable.

## Release asset manifest

- Emulator Release executable SHA256: `C034B855DC30E13AA236E51775ABECE403EBBB57C0284C89A2510FE9CF6226ED`.
- The Windows x64 release archive contains that executable and the matching
  1.0.18 launcher; its generated launcher files are independently labelled
  1.0.18.

- The release contains `Unova-Together-1.0.18-Windows-x64.zip`,
  `Unova-Together-1.0.18-Source.zip`, `Unova-Together.exe`,
  `Repair-Launcher.exe`, and `SHA256SUMS-Unova-Together-1.0.18.txt`.
- The attached SHA256 manifest is authoritative for download checksums. The
  package builder verifies archive integrity, matching version labels,
  checksum generation, and exclusion of private game files and test fixtures.
