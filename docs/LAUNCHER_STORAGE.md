# Installation storage

Unova Together by mvq1303 / WhatWasMissing. Launcher 1.0.4.

Open **Tools → Clean old installations**. Cleanup also runs at launcher startup. It keeps the active build, one previous build for rollback, and builds used by a running emulator or launcher. It shares the update-installation lock and skips cleanup if running processes cannot be checked reliably.

The standalone home is `%LOCALAPPDATA%/UnovaTogether/Standalone`; portable ZIP installs use their own folder. Obsolete packaged files under `.updates/versions` are removed only when their contents still match an installation record. Legacy builds use their runtime checksum record and identical launcher binaries. ROMs, saves (`.sav`, `.save`, `.dsv`, `.ml*`), firmware, settings, save backups, modified files and unknown custom files are retained. Small old directories may remain. The launcher sentinel is retained so older EXEs can delegate to the current installed version.

Identical immutable executables/libraries are shared with hardlinks where possible; changes and configuration retain separate copies. Installing or repairing writes into a fresh folder, verifies it, and switches the active marker only after success. Interrupted or corrupt downloads do not activate. New receipts identify the complete packaged file set for later cleanup. Older EXEs stop unpacking an unused bundle when a newer build is already active.

Downloads still contain a complete checksum-verified runtime ZIP. This fixes accumulated installations and repeated unpacking; it is not differential downloading. Saves/backups are never used as cleanup targets. User-added or modified files can prevent an old directory from disappearing; preserve those files rather than deleting the directory manually.

Validation: `python tools/test_unova_storage.py`, `python tools/test_unova_updater.py`, `python tools/test_unova_single_exe.py`, and `python tools/test_launcher_ui.py`. Tests use disposable installations and include Windows junction protection and the real cleanup button. Private local cleanup evidence stays outside release assets.
