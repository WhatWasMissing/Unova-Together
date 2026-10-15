# 1.0.19 release checks

## Qt startup repair

- Root cause: the 1.0.18 runtime archive had the Qt 6 core/gui libraries but
  no app-local `builds/current/platforms/qwindows.dll`; startup depended on
  whether another Qt plugin happened to be discoverable on the machine.
- Windows Qt deployment now adds the platform plugin to the runtime stage.
- Release packaging fails early if `platforms/qwindows.dll` is absent, is not
  a valid-sized Windows PE file, or differs from the copy in the archive.
- The clean-runtime smoke test launches the Release emulator with every Qt
  plugin environment variable cleared and confirms the process loaded the
  staged app-local `platforms/qwindows.dll`. Its visible window title and
  Windows product version both report 1.0.19.
- Runtime ZIP and standalone download both contain the matching platform
  plugin. Source archive, versions, checksum manifest and private-file
  exclusions pass their package checks.

## Mega feature scope

- No battle behavior changed from 1.0.18; Mega Serperior remains the only
  playable Mega profile in the public release.
- Other local profiles are not enabled or shipped by this startup hotfix.
- A live two-emulator Mega battle remains a player test item.
