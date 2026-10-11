---
version: alpha
name: "Unova Together launcher"
description: "A Gen 5-inspired Windows starting point for a shared adventure."
colors:
  background: "#e8e8e8"
  surface: "#ffffff"
  nav: "#202020"
  hero: "#303030"
  primary: "#9b2536"
  primaryHover: "#741b29"
  text: "#202020"
  muted: "#555555"
  border: "#9b9b9b"
  navText: "#dedede"
  accent: "#f4f4f4"
  selection: "#dcdcdc"
  warning: "#8b5417"
  warningSurface: "#fff0d8"
  danger: "#a33434"
  disabled: "#dce5e5"
  disabledText: "#61777d"
  focus: "#9b2536"
typography:
  display:
    fontFamily: "Consolas"
  body:
    fontFamily: "Segoe UI"
  utility:
    fontFamily: "Consolas"
rounded:
  DEFAULT: "0px"
spacing:
  sidebar: "198px"
  padding: "26px"
  heroHeight: "238px"
components:
  button:
    rounded: "{rounded.DEFAULT}"
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
  card:
    rounded: "{rounded.DEFAULT}"
    backgroundColor: "{colors.background}"
    textColor: "{colors.text}"
---

# Unova Together Launcher Design System

Launcher 2026101105: Games & saves names the profile surface in player language. Play shows the active save slot and a Manage saves action. Slot names persist automatically; a new slot reuses the current ROM with a separate managed folder. Backup and restore share this surface, with readable UTC timestamps and explicit empty states. Custom folder paths, player names and slot removal use Advanced save options. Technical ROM, save and XP inspection stays on Tools. Existing profiles retain their files and settings.

## Overview

### Creative North Star

A desktop companion to Black 2's C-Gear: charcoal machinery, teal communication rings, pale rectangular panels, and restrained pixel-art gameplay. A real two-player gameplay capture is the signature, rather than invented promotional art.

### Product context and register

Windows players choose their own matching ROM, read official release notes, install verified updates, and open connection guides. This is an English product surface for the existing international beta audience; Japanese-market forms and locales are out of scope. Play carries brand expression; News, Updates and Setup favor readable utility. No sign-in, public server, live player count or network availability is implied.

Runtime token ownership uses Model B: theme.json is canonical. Components load the JSON directly; this document mirrors exact values. Project tests check color/font/layout drift. No independent page palettes are allowed.

## Colors

Pale background separates the content from charcoal navigation. Teal is reserved for primary actions, heading accents and keyboard focus. Selected navigation uses a pale teal background and dark text. Warnings have text as well as amber color. Remote error messages remain readable without a transient toast.

## Typography

Bahnschrift is the Windows display face for page headings, branding and the Play headline. Segoe UI is the body/control face. Consolas displays the installed version in the footer. Native Tk falls back to installed fonts if a family is missing. Short uppercase utility labels contrast with sentence-case action labels; body text stays plain English.

## Layout

The default window is 1040 by 760, minimum 860 by 660. A 198px sidebar stays stable while page content changes. Play, Updates and Setup each own a visible native scrollbar. News owns separate bounded release-list and article scrollbars. A persistent footer keeps feedback across navigation. Below a 675px content width, Play hides decorative artwork so the ROM field and actions remain available. No web/mobile view is promised.

## Elevation & Depth

Tonal surfaces and one-pixel borders convey hierarchy. No drop shadows, blur, glass layers, animated wallpaper or synthetic depth.

## Shapes

Square native controls and panels echo the Gen 5 menu vocabulary. The C-Gear-inspired ring insignia is the one circular exception. Native Windows file picker and cancellation confirmation retain platform geometry and keyboard semantics.

## Components

Shared button(), label(), card(), emblem() and ScrollPage owners live in components.py. Primary buttons have white text on teal; neutral actions have dark text on white. Focus uses a two-pixel teal outline, and disabled actions reject invocation. Sidebar selection is persistent and distinct from focus. Status text uses one persistent footer plus workflow-local details.

Play owns a labeled native ROM entry and Browse action. Updates owns version comparison, check/install/cancel controls and a stable progress bar. News renders bounded plain release text, never remote HTML; only constructed official release URLs open externally. Setup links to included guides or the same official repository.

No ambient motion is used. Download progress is the only moving visual. These choices work without a reduced-motion toggle. The gameplay artwork comes from media/announcement-20261008/06-walking.png, cropped to the top DS screen with nearest-neighbor sampling. Nintendo/game artwork ownership is not claimed. Attribution remains visible on all pages.

## Do's and Don'ts

- Do show real version, download and saved-news state.
- Do keep Play usable after a failed GitHub check.
- Don't fabricate developer announcements, players online or connection status.
- Don't alter game saves or replace the user's running emulator during a UI update.


## Settings and optional cheats

Settings owns native checkboxes and a keyboard-operable volume slider. Choices save automatically; emulator settings apply at the next launch. TOMLKit preserves unrelated controls/comments and a one-time original config backup. The exact runtime must be closed before writing settings. No user ROM or save file is edited by the launcher.

Cheats are off by default, scoped to the selected ROM path, and gated by reviewed ARM9 fingerprints. A debounce detects ROM changes without frame-by-frame hashing. Max money and repel use Select; Rare Candies use L+R and explicitly warn about replacing the first medicine slot. Individual .mch flags are written to a separate managed directory with existing user codes preserved. All off restores the original cheat engine enable switch. Catalog attribution and CC BY-SA license are included. XP/story/battle behavior codes are excluded. Captured-RAM executor tests establish intended byte writes; they do not prove an entire multiplayer playtest.

Verification: test_launcher_preferences.py (preservation, opt-in/out, running guard, unsupported ROM, malformed data); test_launcher_cheat_engine.py (production executor, isolated RAM, native inventory getter); test_launcher_ui.py (native Settings states and persistence).


## Profiles, connections and maintenance

Profiles owns a native readonly selector and explicit Save profile. ROM selection on Play is part of the selected profile. New profiles receive a separate save directory; existing saves are never moved. Selecting a profile restores its game preferences and network fields. Removing a profile preserves saves/backups. Launch commits edited fields.

Co-op owns local/internet/Tailscale/solo selection, presence address, port and room. Save connection validates fields. Check relay is a bounded worker probe that verifies the presence protocol, not native wireless or a partner's game state. Internet setup opens the existing secure UDP wizard; credentials remain outside launcher profiles. Process-scoped emulator overrides carry player name and connection fields. Solo disables automatic presence and trainer co-op; native LAN host/join stays in-game.

Tools owns dated save backups, profile-scoped checksum-verified restore (all melonDS instances must be closed), launch checks, installed game-file verification, verified same-version repair, and diagnostic ZIP export. Updates and repairs back up each profile before downloading. Repairs use a fresh installation slot, preserve configuration/current launcher and keep the old runtime intact. Installation checksum records cover exe/DLL files. Diagnostics exports bounded redacted text logs and version/hash information, never ROMs, saves, RAM dumps or profile credentials; users are asked to review before sharing. Live C-Gear/partner revision state is explicitly unverified pre-launch.

Additional verification: test_launcher_services.py, profile/connection/restore native UI cases, production native-menu fixture reports for process-scoped launcher overrides. Shared readonly Comboboxes and native Text controls follow the Form owner; page ScrollPage remains the only page scroll owner.

## Full emulator settings and relay handoff

SettingsEditor is the canonical searchable configuration editor: native Treeview, labeled search/value fields, native vertical/horizontal scrollbars, staged edits and explicit Save settings. The full TOML view supports settings beyond the generated catalog; Config.cpp owns the 176 catalog defaults. Existing values/comments remain intact, invalid types/structure are rejected, a config backup is written and the exact game build must be closed before saving. Profile volume/filter/focus/save-folder fields synchronize after a save. Pokémon save-owned Options remain in the game.

Saving Co-op connection settings writes a bounded atomic runtime-local request, independent of relay reachability. Updated native Multiplayer panels consume it once per revision and defer while a battle or item/Pokémon transaction is active. Live endpoint changes reconnect presence only; no native battle session is rewritten. Refused connections explain which address lacks a listening presence server and distinguish it from the UDP/native wireless endpoint.

## Co-op player flow (Launcher 20261009.3)

The Co-op page is a three-step sequence: connection method, player sharing, then in-game native host/join. Contextual guides follow Local LAN, Tailscale or experimental UDP. Host/Join controls set a local address or invite the player to enter their friend’s address. Test connection retains actual protocol verification and localhost-only server startup. Room name and host address remain visible; sharing port and explicit server start/stop are collapsed under Advanced settings. Returning to a page resets its scroll position so headings are visible.

Launcher 20261009.4 copy policy: page titles use navigation names; no repeated eyebrow headings. Subtitles contain only actionable context. Detailed connection, repair and emulator explanations live in guides. Keep precise error recovery and irreversible cheat/save warnings visible.

Play page copy: show the project name and gameplay screenshot, followed by the ROM picker and Play button. No promotional slogan or duplicate feature-card row. Keep a brief beta backup reminder. Launcher 20261009.5.


Gen 5 visual revision: monochrome framed menu panels, dark navigation, berry-red action emphasis, a Poké Ball navigation cursor, and actual Gen 5 sprite artwork. No promotional slogans, gradients, glass effects or oversized feature cards. Body text remains readable native Segoe UI. Optional recorded game BGM defaults off and stops before game launch or launcher exit. Artwork credits live in assets/ART-CREDITS.md.

Launcher 20261009.7: Features is a scrollable native page with actual gameplay screenshots and short capability/limitation descriptions. Co-op owns Host & play / Join & play. Native launch requests use a random per-process identity and atomic status reports; old or unrelated status files are ignored. Buttons are disabled while a launched game is running. Hosting sets localhost player sharing and joining retains the chosen host. Native LAN and presence setup remain distinct.

Launcher 20261009.8: per-profile LAN role and previous join host survive host/join switching and restart. Retry uses the last role, refuses to restart a running game and asks the player to save/close first. Native status distinguishes starting, host waiting, joining, connected, teammate disconnected, stale status and game closed. Reports are prepared locally, redacted, and shown for review with a manual GitHub issues link; nothing is uploaded. Keyboard focus uses Tab, Enter and Ctrl+Tab; focused XInput controller navigation uses D-pad/stick, A, B and shoulder buttons. Background emulator input is not intercepted.
