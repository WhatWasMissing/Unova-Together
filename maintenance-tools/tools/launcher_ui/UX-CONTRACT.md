# Launcher behavior

The user request, docs/LAUNCHER.md and unova_updater.py define the existing update policy. The UI redesign preserves official repository pinning, checksum checks, contained side-by-side installs, atomic activation, independent saves and settings preservation. No emulator/network logic changes are part of this design.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Form | ROM, profile, connection and settings controls; SettingsEditor | Launcher.launch / preferences.py / settings_editor.py | native Windows file picker, typed TOML values | test_launcher_ui.py / test_launcher_all_settings.py |
| Table Selection | SettingsEditor native Treeview | settings_editor.py | single configuration leaf | test_launcher_ui.py |
| Scrollbar | ScrollPage and native ttk.Scrollbar | DESIGN.md / components.py | page, release list, article | test_launcher_ui.py |
| Toast | Persistent status footer and workflow detail | Launcher._poll | success, error, progress | test_launcher_ui.py |

The Toast row identifies feedback ownership; the desktop app deliberately uses persistent native text rather than floating notifications. No CRUD, tables, date controls or authored comboboxes apply.

## Navigation and operations

Eight compact native sidebar buttons switch Play, Profiles, Co-op, News, Updates, Settings, Tools and Setup. Navigation remains usable while checking/downloading and retains page scroll state. Tab and Shift+Tab traverse native controls; Space invokes buttons; arrow keys select releases. The read-only article supports selection/copy and keyboard scrolling. Native dialogs restore focus when dismissed.

GitHub check fetches releases once for both news and update comparison. Checks and installs run in a worker; all Tk updates occur on the main thread. Duplicate check/install requests are rejected. A tracked running game disables update installation and duplicate Play, while news remains refreshable. Closing the launcher never terminates the game.

News is release news, not a separately administered announcement service. Published semantic-version releases are bounded, sanitized plain text; drafts are excluded and link destinations are constructed from the pinned repository. Last successful news is cached atomically per installation, with bundled release notes as an offline fallback. A failed refresh explicitly says saved notes are shown. Missing news offers Refresh news.

Updates distinguishes unrequested, checking, available, current, downloading, verifying/preparing, installed, cancelled and error states. Cancel download leaves the original active build intact. Validation errors remain on Updates as well as in the footer. Save/ROM paths and emulator control settings follow the existing backend policy. Beta limitations must not be described as solved unless validated independently.


## Settings and optional cheats

Settings owns native checkboxes and a keyboard-operable volume slider. Choices save automatically; emulator settings apply at the next launch. TOMLKit preserves unrelated controls/comments and a one-time original config backup. The exact runtime must be closed before writing settings. No user ROM or save file is edited by the launcher.

Cheats are off by default, scoped to the selected ROM path, and gated by reviewed ARM9 fingerprints. A debounce detects ROM changes without frame-by-frame hashing. Max money and repel use Select; Rare Candies use L+R and explicitly warn about replacing the first medicine slot. Individual .mch flags are written to a separate managed directory with existing user codes preserved. All off restores the original cheat engine enable switch. Catalog attribution and CC BY-SA license are included. XP/story/battle behavior codes are excluded. Captured-RAM executor tests establish intended byte writes; they do not prove an entire multiplayer playtest.

Verification: test_launcher_preferences.py (preservation, opt-in/out, running guard, unsupported ROM, malformed data); test_launcher_cheat_engine.py (production executor, isolated RAM, native inventory getter); test_launcher_ui.py (native Settings states and persistence).


## Profiles, connections and maintenance

Profiles owns a native readonly selector and explicit Save profile. ROM selection on Play is part of the selected profile. New profiles receive a separate save directory; existing saves are never moved. Selecting a profile restores its game preferences and network fields. Removing a profile preserves saves/backups. Launch commits edited fields.

Co-op owns local/internet/Tailscale/solo selection, presence address, port and room. Save connection validates fields. Check relay is a bounded worker probe that verifies the presence protocol, not native wireless or a partner's game state. Internet setup opens the existing secure UDP wizard; credentials remain outside launcher profiles. Process-scoped emulator overrides carry player name and connection fields. Solo disables automatic presence and trainer co-op; native LAN host/join stays in-game.

Tools owns dated save backups, profile-scoped checksum-verified restore (all melonDS instances must be closed), launch checks, installed game-file verification, verified same-version repair, and diagnostic ZIP export. Updates and repairs back up each profile before downloading. Repairs use a fresh installation slot, preserve configuration/current launcher and keep the old runtime intact. Installation checksum records cover exe/DLL files. Diagnostics exports bounded redacted text logs and version/hash information, never ROMs, saves, RAM dumps or profile credentials; users are asked to review before sharing. Live C-Gear/partner revision state is explicitly unverified pre-launch.

Additional verification: test_launcher_services.py, profile/connection/restore native UI cases, production native-menu fixture reports for process-scoped launcher overrides. Shared readonly Comboboxes and native Text controls follow the Form owner; page ScrollPage remains the only page scroll owner.

Full emulator settings use labeled native search/value fields, keyboard-selectable Treeview and a full TOML editor with both scrollbars. Edits are staged; Save settings validates before any file write, refuses a running exact runtime and preserves a before-edit backup. Simple profile preferences and save folder synchronize after saving. Explicit Close does not save staged edits. Raw config search supports every existing setting; catalog defaults cover options before the first game launch. Gameplay save options remain game-owned.

Save connection persists even when Check relay fails. The native panel consumes runtime-local revisioned requests within one second when idle; battle/trade requests wait. Endpoint changes reconnect presence, not native LAN. Checking a server never claims to configure that server or prove native pairing. Windows connection refusal uses an address-specific explanation and leaves the saved fields available to edit.

Co-op uses Choose how to connect → Share your adventure → Meet in-game. Test connection is the player-facing name for the existing bounded presence check. Advanced settings owns sharing port and explicit server start/stop; it starts collapsed. Connection-guide routing follows the chosen mode. Page changes reset scrolling to avoid clipped headings. Hosting sharing remains distinct from native battle pairing.

Launcher music is opt-in, stored separately from game audio preferences, and available from the persistent footer. Recorded WAV playback runs asynchronously, loops at low amplitude, and stops before game launch and launcher destruction. UI fixtures suppress actual sound; native winsound calls are mocked in the focused playback test. Shared framed panels and Poké Ball selection cursor use theme tokens.

Native launcher handoff starts only a new primary emulator process. No user save writes or ROM edits are introduced. Names use native 31-byte bounds; LAN role is process-scoped. Status polling is once per second, bounded to 8 KB and matched by request identity. An ended session is reported as disconnected; in-flight presence failures leave editable fields and do not launch a game.

Recovery never kills or reloads the game. Controller polling is gated on foreground launcher/owned editor windows; held input on return is ignored until a new press. Disconnected/absent controllers have no effect. Report previews are bounded; full contents remain in the local ZIP for review. Reporting includes launcher home logs after updates, but no ROMs, saves, RAM dumps or profile credentials.

Launcher 20261009.9: startup and manual guide refresh fetch a bounded text-only set from a pinned official GitHub commit. Cache activation occurs only after all guides validate. Offline failures retain the last complete cache. No game, profile or save files are modified.


Launcher 20261009.10: LAN hosts default to 16 slots; per-profile Lobby size is 2–16. Launch requests include the selected capacity. Native challenge/readiness/result traffic is scoped to one partner.


## Pokemon Together game routing (20261012)

The launcher name is Pokemon Together; original Unova Together/mvq1303 and upstream
credits stay intact. Existing runtime theme.json remains the token owner. The new
Mod library uses shared native cards/buttons. Black 2/Redux retains the DS ROM,
profiles, settings and update workflow.
Pokemon X shows a separate prepared-research-folder, launch-mode and guest IPv4
form. It opens only the corresponding fixed 3DS script; no DS settings or save
migration are applied. The two routes persist independently in the existing
launcher configuration. Missing setup and invalid addresses produce persistent
footer feedback. Research launch runs asynchronously and disables duplicate launch.

The 3DS adapter is a research integration, not support for arbitrary 3DS games or
a ROM/save distribution. Its original checkpoints and privately dumped ROM stay
in the selected preparation folder. DS release updates retain their current
repository/layout and do not silently update the 3DS emulator. The menu uses native
Windows popup behavior and keyboard focus. Verify both game selections, profile
preservation, bad setup recovery, and existing page/navigation tests.

## Unified hub navigation (20261013)

Startup always lands on Mod library and launches no emulator. No automatic Unova
update checks or guide downloads run until Unova is opened. Mod library is available
from every workspace; returning clears the active workspace without changing either
mod's saved configuration. Entering a mod shows its first page and focuses its nav
button. Hidden pages cannot be navigated to via keyboard cycling or direct show_page.
Mod switching waits while a launcher operation is busy. Controller Back returns to
the mod's first page, then to Mod library. Native Tab/Space/Enter controls remain.

Unova and Pokemon X retain distinct runtime, connection and save ownership. X guide
actions open only the fixed local guide filenames in the chosen X folder. Invalid
setup produces a persistent correction hint and leaves the library reachable.
Unova updater activation refreshes its runtime root; a frozen hub restarts itself
with the same persistent home rather than delegating to an older mod launcher.
