# Unova Together 2.0.20 release checks

This update fixes stale presence relays that stayed alive after a launcher update or restart and were then accepted as current.

- **PASS — LAUNCHER TESTS:** Presence service tests passed **30/30**. Relay welcome-version test passed **1/1**. Patch-note feed passed **5/5**, release package checks **2/2**, and launcher versioning **14/14**. The mirrored launcher UI trees match across **49 files**.
- **PASS — WINDOWS RELAY LIFECYCLE:** An isolated installation started the 2.0.19 relay, detected it as stale, stopped it only after verifying its listener and managed executable path, and started the 2.0.20 relay. The current build identity and Teleport field-zone capability were confirmed from its live welcome message. The temporary fixture was removed.
- **PASS — PACKAGE:** The Windows and source archives passed ZIP integrity checks. The Windows archive contains the 2.0.20 launcher, relay replacement helper and user-facing patch notes. The source archive carries the matching emulator source from 2.0.19 and the updated 2.0.20 launcher helpers. Release scans found no ROM, save, RAM-dump, key or firmware files.
- **SOURCE PROVENANCE:** The unchanged emulator source came from the official [2.0.19 source release](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v2.0.19); GitHub's reported asset digest matches the local source ZIP (`4e39b8ae044cb86e5ea48dac933b106a60d75a683d9ede2b457f62dbe03056cc`). The staged emulator SHA-256 is `9df2832875076ad17e9843960ea6ae3db1149d292dd166ef84e7e2553f016ea2`; its embedded Mega shop-patch fingerprint matches `Gen5ShopOverlayPatch.h` from that source archive (SHA-256 `ccfeecf007a83a52c7415454489636698f1eff4b2f13705d1a3672daffc0da97`). Launcher build environment: Windows 10 build 19045, Python 3.12.8, PyInstaller 6.22.3.
- **NOT RUN — GAMEPLAY:** Teleport and multiplayer were not tested in a live game session. The packaged emulator is unchanged from 2.0.19; this release updates the launcher and relay protocol checks.
- **PASS — GITHUB RELEASE:** [v2.0.20](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v2.0.20) is published, non-draft, and the latest release. GitHub reports commit `8f5514dd4be81867666726854f59ec0b21dc445b`. All five reported asset names, byte sizes, and SHA-256 digests match this table and the local checksum manifest.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `Repair-Launcher.exe` | 12,216,717 | `22318cf6a45b475f6eb9c1545746f686fcdab7a0138c17a6ace01924ddcc49fb` |
| `SHA256SUMS-Unova-Together-2.0.20.txt` | 378 | `d8b398779ff5b647b6e6fab4da107357a078edf94f7bd25ab036bf3ce1b61880` |
| `Unova-Together-2.0.20-Source.zip` | 31,815,942 | `6733323db3aa0e5121c2ea43c17ba10b800491257938eef8d68ad16ecd07224b` |
| `Unova-Together-2.0.20-Windows-x64.zip` | 206,536,233 | `51cba60cf58081bc6fff18b95b8e57046e69cb23e848d3792a33fde533249b49` |
| `Unova-Together.exe` | 246,063,785 | `9503ea6d1f0c7d40446f563de26d7a26eb97101410eb45f3769ac774f5250de7` |
