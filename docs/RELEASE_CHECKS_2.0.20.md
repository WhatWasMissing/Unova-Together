# Unova Together 2.0.20 release checks

This update fixes stale presence relays that stayed alive after a launcher update or restart and were then accepted as current.

- **PASS — LAUNCHER TESTS:** Presence service tests passed **30/30**. Relay welcome-version test passed **1/1**. Patch-note feed passed **5/5**, release package checks **2/2**, and launcher versioning **14/14**. The mirrored launcher UI trees match across **49 files**.
- **PASS — WINDOWS RELAY LIFECYCLE:** An isolated installation started the 2.0.19 relay, detected it as stale, stopped it only after verifying its listener and managed executable path, and started the 2.0.20 relay. The current build identity and Teleport field-zone capability were confirmed from its live welcome message. The temporary fixture was removed.
- **PASS — PACKAGE:** The Windows and source archives passed ZIP integrity checks. The Windows archive contains the 2.0.20 launcher, relay replacement helper and user-facing patch notes. The source archive carries the matching emulator source from 2.0.19 and the updated 2.0.20 launcher helpers. Release scans found no ROM, save, RAM-dump, key or firmware files.
- **NOT RUN — GAMEPLAY:** Teleport and multiplayer were not tested in a live game session. The packaged emulator is unchanged from 2.0.19; this release updates the launcher and relay protocol checks.
- **PASS — GITHUB RELEASE:** Verify that `v2.0.20` is the latest release and compare every asset's reported byte size and SHA-256 digest with this table after upload.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `Repair-Launcher.exe` | 12,216,717 | `22318cf6a45b475f6eb9c1545746f686fcdab7a0138c17a6ace01924ddcc49fb` |
| `SHA256SUMS-Unova-Together-2.0.20.txt` | 378 | `d8b398779ff5b647b6e6fab4da107357a078edf94f7bd25ab036bf3ce1b61880` |
| `Unova-Together-2.0.20-Source.zip` | 31,815,942 | `6733323db3aa0e5121c2ea43c17ba10b800491257938eef8d68ad16ecd07224b` |
| `Unova-Together-2.0.20-Windows-x64.zip` | 206,536,233 | `51cba60cf58081bc6fff18b95b8e57046e69cb23e848d3792a33fde533249b49` |
| `Unova-Together.exe` | 246,063,785 | `9503ea6d1f0c7d40446f563de26d7a26eb97101410eb45f3769ac774f5250de7` |
