# 1.0.13 launcher release checks

- Launcher preferences and UI regression suites pass, including an update staged while this installation's emulator is open.
- The UI test confirms Play remains disabled during the open game and returns to enabled after the process exits.
- Process matching covers legacy and versioned runtimes under the same home, and ignores an emulator installed elsewhere.
- The local Soaring scenery writer imports successfully after correcting its package initializer.
- The full runtime and source archives pass ZIP integrity, checksum, private-file exclusion and launcher-version metadata checks.
- Release tests use disposable temporary directories that clean themselves up.
