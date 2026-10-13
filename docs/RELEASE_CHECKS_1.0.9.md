# Unova Together 1.0.9 checks

Client migration replaces the original shared-launcher entry with a permanent bootstrap. Native changes are version/credit labels only; gameplay matches 1.0.8.

## Checks

- Regression suites cover migration, versioning, launcher UI, verified updater installation and standalone setup.
- Migration checks replace the exact old shortcut target, retain its executable backup and persistent home, preserve saved-data/profile fixtures, reject unrelated or active-slot executables, restore the old file on replacement failure, and retain a locked executable until retry.
- The same entry follows two successive release slots without another repair. Updated launcher startup does not overwrite the record of the original entry.
- Frozen checks repair a disposable legacy entry and run that exact executable path to open the active packaged launcher. A second frozen launcher build checks that the unchanged entry follows a newer slot and reports the new launcher version.
- Build/package verification includes runtime libraries, executable versions, embedded launcher metadata, the repair utility, corresponding source, archive integrity, absence of game/private data and uploaded SHA-256 digests.

Old 1.0.5 clients need the repair utility once after downloading an updated game package. This is explicitly tested as a migration rather than claimed to be remotely executed by already-compiled old updater code. Physical remote-client machines and gameplay are not newly playtested for this launcher-only maintenance change.
