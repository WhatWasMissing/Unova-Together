# Unova Together launcher guide

Start `builds/unova-together-0.3.5/Unova-Together/Start Unova Together.cmd`.

## Play profiles

Open Profiles. The first profile keeps your existing ROM and save folder. Select its ROM on Play. Set a profile name and player name, then Save profile. To switch games, select another profile on Profiles.

New profile creates a separate save folder under `play-profiles/<profile>/saves`. It does not copy or move existing saves. To continue an existing game, choose the folder containing its matching `.sav` on Profiles. A blank save folder uses the ROM folder. Each profile remembers its game settings and connection. Removing a profile keeps its saves and backups.

## Co-op setup

Choose Local LAN, Internet UDP, Tailscale backup or Solo. Enter the **presence relay** address, its port (usually 8765) and a shared room name. Save connection, then Check relay. A successful check confirms the presence service—not native wireless, another player's ROM, or battle readiness.

For internet play, Open internet setup wizard starts the existing UDP setup helper. Enter the UDP server/role/credentials there. The launcher does not save authentication keys. Tailscale guide opens the included backup instructions. Both players still host/join the native LAN game inside melonDS's network menu. Launch passes the profile's player/relay fields to the emulator. Solo disables automatic presence connection and trainer co-op for that launch.

Keep both games at normal speed, with C-Gear wireless OFF and matching mod/ROM revisions. Settings keeps game volume and display preferences per profile; the startup update checkbox is shared. Co-op launches keep the emulator running when focus moves away.

## Save backups and restore

Save normally first. Tools → Back up saves creates a dated, checksummed ZIP for the selected profile. Backups include normal `.sav`/`.dsv` files (and numbered instance saves), not savestates or unsaved gameplay. Updates and repairs automatically back up every profile's existing save files before downloading. Backups are kept under `save-backups/<profile>` and are not pruned automatically.

To restore, close **all** melonDS instances, select the backup on Tools and press Restore selected. The current on-disk saves are backed up before restoration. A damaged or mismatched backup is rejected. Open backups folder lets you manage archived ZIPs yourself.

## Launch checks and repair

Tools → Run launch checks checks the executable, ROM compatibility fingerprint and frame-limit/focus settings. Missing executable/ROM blocks launching. C-Gear, live fast-forward, the partner's game version and ROM revision cannot be verified before connecting; the checks say which steps remain in-game.

Verify installed files compares game executables/DLLs with the installation checksum record. It is an integrity check, not an anti-tamper system. For missing or damaged files, Find repair download finds the official published release matching the installed version (latest if no version can be recovered), then Repair game files downloads and checks its GitHub SHA-256 archive. Repair creates a new side-by-side slot; the old runtime, configuration, profiles, saves and current launcher are preserved. Published game files replace local game customizations, including this local profile integration if it has not yet shipped publicly.

## Troubleshooting

Export troubleshooting bundle creates a ZIP containing version/hash information and at most twenty redacted text-log tails. ROMs, saves, RAM dumps, launcher profiles and credentials are excluded. Review the bundle before sharing; automatic text redaction cannot promise to identify every private detail in arbitrary logs.

## Optional cheats

Choose a supported ROM on Play, then open Settings. The reviewed catalog supports Black 2 USA/Europe and Redux Complete v1.4.1 / Unova Together ARM9 fingerprints. Cheats default off and apply on the next launch.

- Max money: press Select in the overworld after enabling and launching.
- Refill repel: press Select in the overworld after enabling and launching.
- 999 Rare Candies: press L+R in the overworld. This REPLACES the first medicine slot; back up your save first.

Disable and relaunch after use. Disabling does not undo saved items/money. Existing user cheat codes are preserved; turning on the cheat engine also enables any existing codes marked enabled in the copied file. XP/story/battle-changing codes are excluded. Code source attribution and CC BY-SA license are included in Settings.

## What was verified

Disposable tests cover profile switching/preferences, launch environment, automatic pre-update backups, checksum-verified restore/recovery copies, relay protocol checks, diagnostic redaction, damaged-file detection and verified same-version repair/corrupt active runtime recovery. Native ROM-backed menu integration confirmed profile fields and Solo mode reach the emulator, and existing menu checks still pass. The standalone installed launcher was smoke-tested. Real internet pairing/partner revision and C-Gear checks remain in-game; this work is not a new full co-op battle playtest.

Made by mvq1303 / WhatWasMissing. This enhanced launcher is installed locally; GitHub releases have not been changed by this task.


## Relay addresses and full emulator settings

Save connection on Co-op applies the address to the updated Multiplayer tab even if Check relay fails. Idle games consume the change within about a second; active battles/trades defer it. Older running builds need to be restarted with this updated build. WinError 10061 means no presence server accepted the connection at that address/port, not that saving the address failed.

To host sharing, choose Host presence relay here. The compiled launcher hosts it without a separate Python installation. Use Check relay to confirm it started. Guests enter the host PC’s LAN/Tailscale address and matching relay port/room. Allow Windows Firewall access if prompted. Stop hosted relay stops only the process started by this launcher. Closing the launcher leaves its hosted relay running so the game stays connected. Hosting presence does not configure native LAN, UDP wireless or port forwarding. Internet UDP helper prerequisites still apply.

Settings → All emulator settings opens a searchable 176-setting catalog and Full configuration tab. Edit controls/hotkeys, display, audio, firmware, networking and paths. Values use TOML syntax (true/false, numbers, quoted strings or arrays). Apply value stages the row; Save settings validates and saves, with a before-edit backup. Close the game before saving. Changes apply next launch. Profile volume/filter/focus and save-folder fields sync with saved config. Profile-managed optional cheats may override cheat-engine paths/switches at launch; manage them on Settings. Pokémon’s save-owned text speed, battle style and sound settings remain in its in-game Options menu.

## Launcher revision 20261009.2

Use the updated single-file app in builds/single-exe/Unova Together.exe. The footer identifies Launcher 20261009.2. The bootstrap repairs older cached launcher revisions even when both are Beta 0.3.5; existing controls/configuration, saves and backups are preserved.

Check relay verifies the actual presence protocol. If localhost has no server, the launcher starts its bundled presence relay and checks it. Guests still enter the host computer address; a remote server cannot be started by this button. Native LAN/UDP pairing is configured separately in-game. Settings → All emulator settings opens the complete searchable configuration editor.

## Launcher LAN and feature overview

Co-op → Host & play starts the chosen ROM and a two-player native LAN host. Join & play uses Host address to join it. Player sharing is checked first, and local hosting starts the embedded presence server if required. Launch the host before the guest. For different networks, connect both PCs through Tailscale first; the UDP option still needs its separate experimental setup. These controls start a new emulator process; close the launched game before retrying or changing LAN roles.

Features contains gameplay screenshots for walking, item gifts, co-op battles, Pokémon trades and the camera, plus short notes on travel, connection methods, player battle controls, profiles/backups and settings/updates. Known issues is linked from the page. Screenshot descriptions do not imply that all trainer events or cross-network battle completion have been verified.

## Reconnect, reports and navigation

Co-op remembers your role and the last host address for each profile. Retry uses that role; save normally and close a running game before retrying. A disconnected teammate is reported distinctly from a new lobby waiting for its first guest.

Tools → Report a problem prepares a redacted ZIP, then opens a review window. Open the report folder to inspect it, and use Open GitHub issues to submit it yourself. Nothing is uploaded automatically. Reports contain version/checksum information and bounded text logs, not ROMs, saves, RAM dumps or profile credentials.

Keyboard: Tab / Shift+Tab moves focus, Enter selects a focused button, Ctrl+Tab / Ctrl+Shift+Tab changes launcher pages. XInput controllers (Xbox-compatible): D-pad or left stick moves focus, A selects, B returns/closes an owned editor, LB/RB changes pages. Left/right changes a focused dropdown or volume slider. Type addresses with the keyboard. Launcher controller input only runs while its window/editor has foreground focus.

## Updated guides

The launcher checks the official GitHub guides at startup. Use **Setup > Refresh guides** to check again. Updated guides are downloaded independently of the game and kept for offline use. Failed downloads preserve the previous complete set. Opening a guide uses the downloaded copy when available; bundled guides remain the fallback.

