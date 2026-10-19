# Next update — draft

- Fixed a crash that could occur when entering a Pokémon Center.
- Improved update checks so incomplete release information does not interrupt the launcher; available release notes remain visible.
- Corrupted save backups now show a clear error without interrupting the launcher or changing the current save.
- Corrupted update metadata no longer prevents the launcher from opening its repair tools.
- Damaged standalone-install metadata now gets a clear error without changing existing files.
- Launcher repair now reports damaged release metadata clearly.
- Old-install cleanup now skips malformed installation records safely instead of aborting.
- Save backups now enforce the same file-count and size limits as restore, preventing the launcher from creating backups it cannot restore.
- Emulator and Multiplayer windows now show the same release version as the packaged game.
