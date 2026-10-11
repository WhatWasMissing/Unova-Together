# Release 1.0.4 checks

Launcher 1.0.4; unchanged modified melonDS 1.0.2. Attribution remains mvq1303 / WhatWasMissing and melonDS contributors.

Nine storage tests, 21 native UI tests (including Clean old installations), 13 updater tests and six standalone installer tests passed. Windows junctions, malformed paths, changed/unknown files, private saves, running builds, process-check failures, rollback retention, hardlinks and copy fallback were covered. Older bootstrap tests prove a newer active installation prevents unused old extraction.

On the local installation, cleanup removed 4,021 obsolete program files from 20 builds, reclaiming 5,439,716,876 bytes plus 251,917,587 bytes through binary sharing. The active and previous build were kept, and 461 protected files had identical hashes afterward. Private path/file inventories are not distributed.

Frozen standalone installation passed and the packaged cleanup button is present. Windows ZIP/source integrity, sanitized configuration, preserved controls and 1,058 matching source files passed. The emulator digest remains unchanged from 1.0.2. Publication verification checks full/latest flags and uploaded asset sizes/digests. Previous release assets are preserved.

Full release ZIP downloads remain; this release prevents retained installation growth and redundant older-bundle extraction. Unknown legacy files and bootstrap sentinels may leave small old folders. No new gameplay or two-PC/WAN claims are made.
