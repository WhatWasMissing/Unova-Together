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
- Save backups now reject linked folders and outside archives, keeping backup files within the selected launcher profile.
- Cheat settings now stop safely when their profile storage folder points outside launcher-managed storage.
- The advanced emulator-settings editor now reports malformed settings sections clearly instead of crashing.
- If an update cannot write its final activation record, the downloaded version is cleaned up so the update can be retried without affecting the current game.
- Opening the save-backups folder now reports a clear error if the folder cannot be created or opened.
- The problem-report window now shows an error in the launcher if its report folder cannot be opened.
- The Games & saves page now handles inaccessible save or backup folders without interrupting the launcher or keeping a previous profile’s backup selected.
- The launcher verifies prepared player-model ROMs before reuse and prevents a cached variant from being overwritten when it is selected as a new source.
