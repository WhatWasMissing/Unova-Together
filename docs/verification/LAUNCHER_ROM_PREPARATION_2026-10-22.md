# Launcher ROM preparation responsiveness — 2026-10-22

The Cynthia Route 7 ROM check ran inside `Launcher.launch()` on Tk's event thread. It hashes the selected ROM and cached event copy and may apply a BPS patch; an optional player-model variant adds more file work. During that work, the launcher could not process input or redraw, leaving Play unusable and the status fixed on “Preparing Cynthia”. Even a valid cached event copy required synchronous hashing.

Launch preparation now uses the launcher's background worker and message queue. Status updates are delivered to the UI thread, and the game starts only after the prepared ROM path returns. Preparation errors clear the busy state and make Play available again. ROM patching behavior is unchanged.

**SOURCE/UNIT VERIFIED:** `py -3.12 -m unittest test_launcher_ui -v` passed 47 tests, including a blocked-preparation responsiveness test and a preparation-failure recovery test. `py -3.12 -m unittest test_cynthia_event test_player_models test_launcher_preferences test_launcher_tree_parity test_patchnotes_feed test_release_validation -v` passed 38 tests after merging current `main`. The UI tests use a controlled worker and placeholder ROM; they do not launch melonDS or verify a real ROM patch.

**BUILD:** The Windows emulator, launcher and bootstrap were rebuilt with version 2.0.28. The corresponding-source archive was based on the published 2.0.27 source download (SHA-256 `9f252681d0bf0100883b1a48efa83071126f0074720a7b9efc8d6bee48e95b96`). Before updating version metadata, all 2,388 native source files matched that archive. The release package passed the repository package builder's archive, controls, source inclusion and private-file exclusion checks.

**NOT RUN:** A visible launch of the packaged launcher with a real game file and live Route 7 patch preparation. The test suite verifies the window stays responsive under a deliberately blocked preparation worker and recovers after a simulated error; it does not prove in-game behavior.
