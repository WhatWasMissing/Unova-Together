# Unova Together 1.0.4 — Installation storage cleanup

Full release: launcher 1.0.4 with the unchanged modified melonDS 1.0.2 runtime, based on melonDS 1.1. Download Unova-Together.exe or the Windows ZIP. Existing users can install through launcher Updates.

## Changes

- Added **Clean old installations** to launcher Tools, with recovered-space feedback.
- Automatic startup cleanup keeps the active installation, one rollback build and all running builds. Older verified package files are removed; saves, ROMs, backups, custom files and modified files are preserved.
- Added an installation file receipt so future cleanup can identify packaged files safely. Legacy cleanup uses existing runtime checksum records and matching launcher binaries, retaining unknown files.
- Reuses identical executable/library files through hardlinks when supported. Changed files and writable configuration are separate; unsupported hardlinks leave normal copies intact.
- Older standalone EXEs now use an already newer active installation without unpacking an unused older bundle.
- Records the previous active build for rollback retention. Installation and cleanup share the same lock.

Updates still download a complete checksum-verified release ZIP; this release reduces retained disk usage, not network download size. Small metadata folders and preserved user files may remain for older builds. Older standalone launchers require their launcher sentinel file to delegate to the current installation, so cleanup retains it.

## Verification

Nine storage tests cover retention, save/custom-file preservation, running builds, modified binaries, malformed paths, Windows junctions, process-check failure, hardlink reuse and copy fallback. 21 native UI tests include the working cleanup button; 13 updater and six standalone installer tests pass. Frozen launcher, standalone installation, package integrity, matching source and uploaded digests are checked before/after publication.

The emulator executable is byte-identical to release 1.0.2; existing gameplay limitations remain. No ROMs, saves, firmware or private settings are distributed. Original contributions by **mvq1303 / WhatWasMissing**, with melonDS and dependency attribution preserved. Matching GPL source and SHA-256 checksums are included.
