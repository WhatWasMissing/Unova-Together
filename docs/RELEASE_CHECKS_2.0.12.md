# Unova Together 2.0.12 release checks

- Confirmed the previous 2.0.11 package bundled the 1.0.1 emulator, which does not contain Soaring support.
- Selected the 1.0.31 emulator build; verified its executable contains both the `UNOVA_EXPERIMENTAL_SOARING` setting and the in-game flight menu label.
- Added a packaging check that refuses emulator binaries without those Soaring markers.
- Ran the package gate against the previous 1.0.1 executable (rejected) and the 1.0.31 executable (accepted).
- Verified the launcher passes the Soaring setting into melonDS and starts the Soaring scenery worker when the setting is enabled.

Soaring is still an experimental preview; this package check verifies the feature is present, not that every map or landing point is complete.
