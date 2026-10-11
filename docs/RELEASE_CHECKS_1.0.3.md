# Release 1.0.3 checks

Launcher 1.0.3; unchanged modified melonDS 1.0.2. Original contributions by mvq1303 / WhatWasMissing, built on melonDS.

20 native UI tests, 15 save-service tests and 6 standalone installation tests passed. Real `.save`, `.2.save`, `.sav` and `.dsv` payloads backed up and restored byte for byte through launcher controls, with previous saves and other profiles preserved. Normal boot of restored data preserved level 20, 5,951 XP and the Cheren badge. ROM/source inputs stayed unchanged.

Frozen 1.0.3 launcher and standalone installation passed. ZIP integrity, sanitized configuration, controls preservation, private-file exclusions and 1,056 source-file matches passed. No ROM, firmware or player save is distributed. Emulator SHA-256 remains `7f9ddca58a2b84da36dc078c8f51f3916f0b83e3a2c27fec09a18b3f35268310`.

GitHub uploaded digests are verified after publication. Earlier release assets remain immutable. ROM checks and XP-budget calculations have the limitations documented in LAUNCHER_GEN5_TOOLS.md; no new physical two-PC/WAN or full JIT gameplay verification is claimed.
