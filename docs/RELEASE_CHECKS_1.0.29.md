# Release checks — 1.0.29

- Mega sprite stream regression: all 46 supplied animation clips map to a supported form and traverse their complete frame sequence. Mega Salamence has 67 front frames and 67 back frames.
- Clean Windows Qt Release build: all 205 build steps passed, including the native Mega frame uploader; the executable version resource reports 1.0.29.
- Follower spacing/smoothing regression: passed in CTest with a one-tile HeartGold-style trail, route corners, 60-fps interpolation, facing and walk-cycle continuity.
- Soaring checks: 11 Python geometry/stream tests and the native scene-control/rendering check passed. They cover take-off, steering, speed and altitude, streamed neighbor-zone landing, and continued flight beyond the first scene window.
- Launcher checks: 6 tests passed for navigation/confirm/cancel cues, saved volume, keyboard navigation, small-window layout and patch-note discovery from `patchnotes/index.json`.
- Mega/follower regression suite: all 8 CTest cases passed, including the 46-clip full-frame animation stream.
- Package verification: Windows ZIP, matching source ZIP, standalone launcher, repair launcher, Qt Windows platform plugin, release notes and SHA-256 sidecar.
- Mega Salamence playback has not been visually checked in the user's emulator. The release asks the player to confirm that it animates and stays centered in battle.
- ROMs, saves, firmware, RAM dumps and temporary test captures are excluded.
