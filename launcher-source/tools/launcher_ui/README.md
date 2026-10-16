# Unova Together launcher UI

Made by mvq1303 / WhatWasMissing. This native Windows UI adds Mod library with separate Unova and Pokémon X routes; Unova has Play, Games & saves, Co-op, Features, News, Updates, Settings, Tools and Setup to the existing verified GitHub updater. News is the official published release notes, cached for offline use. It is not a separately hosted announcement system.

Run `python tools/unova_launcher.py --home <complete-install-folder>` from the collection root. Build with `python tools/build_unova_launcher.py` after installing PyInstaller and TOMLKit. The standalone output is in `builds/mod-hub/current/Pokemon Together`; keep its `_internal` directory and notices alongside the executable. End users do not need Python for the launcher.

Run `python tools/test_unova_updater.py` and `python tools/test_launcher_ui.py` for backend and native page checks. The UI test uses Pillow only for optional screenshots, disposable placeholders and mocked launch requests; it never starts a game. `--output <new-folder>` records screen captures. It checks keyboard/page navigation, small-window action bounds, refresh/offline/empty news, duplicate-launch blocking, guide routing, cancel recovery, and actual side-by-side update activation.

theme.json is the runtime token owner. DESIGN.md and UX-CONTRACT.md document the visual and interaction rules. Frozen application assets are static PNG/ICO/JSON; runtime Pillow is not required. The gameplay capture shows the existing mod; Nintendo artwork remains third-party material.

Launcher navigation, confirmation and cancel sounds are short original cues. Toggle them in Settings → Menu sounds; the setting is saved with the launcher and does not change game audio.

Settings/code preservation: `python tools/test_launcher_preferences.py`. Captured-RAM/native-parser validation: `python tools/test_launcher_cheat_engine.py --output <fresh-output-folder>`. Bundled code catalog is separately attributed CC BY-SA 4.0; see assets/CHEATS-SOURCES.md.

Maintenance checks: `python tools/test_launcher_services.py` uses disposable saves and mocked release downloads. Backups are kept under save-backups; repair slots remain alongside old runtimes.


## Relay addresses and full emulator settings

Save connection on Co-op applies the address to the updated Multiplayer tab even if Check relay fails. Idle games consume the change within about a second; active battles/trades defer it. Older running builds need to be restarted with this updated build. WinError 10061 means no presence server accepted the connection at that address/port, not that saving the address failed.

To host sharing, choose Host presence relay here. The compiled launcher hosts it without a separate Python installation. Use Check relay to confirm it started. Guests enter the host PC’s LAN/Tailscale address and matching relay port/room. Allow Windows Firewall access if prompted. Stop hosted relay stops only the process started by this launcher. Closing the launcher leaves its hosted relay running so the game stays connected. Hosting presence does not configure native LAN, UDP wireless or port forwarding. Internet UDP helper prerequisites still apply.

Settings → All emulator settings opens a searchable 176-setting catalog and Full configuration tab. Edit controls/hotkeys, display, audio, firmware, networking and paths. Values use TOML syntax (true/false, numbers, quoted strings or arrays). Apply value stages the row; Save settings validates and saves, with a before-edit backup. Close the game before saving. Changes apply next launch. Profile volume/filter/focus and save-folder fields sync with saved config. Profile-managed optional cheats may override cheat-engine paths/switches at launch; manage them on Settings. Pokémon’s save-owned text speed, battle style and sound settings remain in its in-game Options menu.

## Current feature/settings review

Launcher 1.0.6, build revision 2026101302, updates Features for release 1.0.6 and links FEATURES.md / ROADMAP.md through the offline guide service. Companion interactions are under Following Pokémon and default on when unset. Existing explicit off preferences are preserved. R+A or tapping opens them; A alone reaches the game. The launcher supplies both UNOVA_COMPANION_INTERACTIONS and the legacy UNOVA_EXPERIMENTAL_COMPANION so released runtimes respect the choice. Nearby battle scenery remains experimental and off by default. Public v1.0.6 assets retain the preceding launcher until a new package is released.
