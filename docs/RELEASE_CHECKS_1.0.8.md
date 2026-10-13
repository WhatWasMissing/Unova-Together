# Unova Together 1.0.8 checks

This maintenance release changes launcher update handoff and version reporting. The native resource/credit labels are updated; gameplay remains at the 1.0.7 implementation.

## Validation

Regression checks cover updating a frozen shared hub, preserving the profile/save home and command-line arguments, cold startup forwarding, equal-version loop prevention, older/legacy/malformed candidate rejection, failed-launch fallback, and version reporting from the running build. Windows resource generation is checked with a version different from the source default.

The existing launcher UI/routing, update installation and standalone installer suites are run alongside these regressions. Frozen launcher and standalone smoke checks use disposable homes without loading a game. Build/package checks verify embedded and external launcher metadata, Windows file/product versions, runtime versions, matching source, archive integrity and uploaded SHA-256 digests.

Existing shared launchers older than 1.0.8 require a one-time restart into the new executable because their already-compiled update handler restarts itself. See the release notes. The local shared-launcher entry point is repaired without terminating a running game.

No new gameplay, ROM playthrough or two-PC multiplayer check is claimed for this maintenance release. The existing trainer browser and experimental flight shortcut retain the documented 1.0.7 limitations.
