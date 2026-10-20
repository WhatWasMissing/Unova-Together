# Launcher UI overhaul checks

The UI changes were made on `codex/launcher-ui-overhaul`, based on repository commit `63c91404a8f113ce4df409f82b95030559a38c94` (Unova Together 2.0.23). They are limited to the native launcher UI and its existing UI tests.

On Windows 10 with Python 3.12.8 and PyInstaller 6.22.3:

- `python test_launcher_ui.py`: **PASS**, 38 tests. The suite rendered the actual Tk window and checked navigation, settings shortcuts, selection, and layout at 1040×760, 860×660, and 800×620.
- `python -m unittest discover -s . -p 'test_launcher*.py'`: **PASS**, 113 tests.
- `python -m unittest test_game_routes test_unova_storage test_release_validation test_updater_settings_copy`: **PASS**, 21 tests.
- `python build_unova_launcher.py --output-dir ..\builds\launcher-ui-overhaul-check --work-dir ..\test-fixtures\launcher-ui-overhaul-build --revision ui-overhaul`: **PASS**, standalone launcher built with ProductVersion 2.0.23. SHA-256: `5e39a73665b41b46038a03066c11f1dd81ce9735d14fa6f41e38eaaa3e7c63c2`.

The UI tests used temporary placeholder game files and never launched the emulator. Play, Co-op, updates, and settings semantics were not changed; live gameplay testing was not needed for this launcher-only change. Screenshots and build outputs are local test artifacts and are excluded from the source commit.
