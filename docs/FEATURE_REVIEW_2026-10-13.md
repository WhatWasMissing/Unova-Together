# Feature and follower-settings review — 13 October 2026

Authorized project maintenance for **mvq1303 / WhatWasMissing**, built on melonDS; implemented with OpenAI Codex assistance. Original and upstream attribution/licensing are retained.

## Changes

- Audited launcher Features against current native menus and release 1.0.6. Added all ten companion actions, friendship/nature replies, emotes/motions, R+A/touch controls, solo XP, field tools, scenery and current save/maintenance tools. Added links to the feature guide, known issues and roadmap.
- Moved companion interactions from Experimental into **Following Pokémon**, defaulting on when unset. Preserved explicit per-slot off/on choices. The game already defaults followers themselves on.
- Added `UNOVA_COMPANION_INTERACTIONS`; retained the legacy switch for released runtime compatibility. The native post-release build also defaults on when launched directly without either override. Input, battle and menu gating are unchanged.
- Corrected outdated profile/menu instructions, the removed flight-preview link and the calculator's old 1.65× description. Separated historical 1.0.2 battle/save evidence from current 1.25× dispatch checks.
- Added a proposed roadmap headed by battle recovery and connection reliability. Proposed contextual dialogue, sprite variants and other additions are not claimed as shipped.
- A real guide-refresh check exposed a size-limit failure on GitHub's full commit response. Guide pinning now reads the bounded branch-reference response instead, preserving the same commit-pinned downloads and offline fallback.

## Verification

- `python tools/test_launcher_ui.py`: **28 tests passed**, including default-on behavior, explicit off persistence through slot changes/restart/launch, both runtime switches, and page/navigation checks. Rechecked after the final UI change.
- `python tools/test_launcher_services.py`: **15 tests passed**, including explicit boolean preferences and atomic guide refresh/offline fallback.
- `python tools/test_launcher_preferences.py`: **7 tests passed**.
- `python -m unittest discover -s tools -p test_game_routes.py`: **2 tests passed**.
- Production C++ interaction/default-policy checks passed: 5,000 reaction combinations, all 649 species, new/legacy override precedence and read-only data.
- Production follower/input-gate checks passed, including ordinary A-button forwarding and deliberate R+A activation.
- Full Windows x64 emulator build and PyInstaller launcher build passed. The rebuilt frozen launcher's isolated startup self-test reported the mod library, Following Pokémon settings and enabled interactions.
- Viewed normal/minimum-size Features captures, the bottom guide buttons and the Following Pokémon settings card. Reviewed relative Markdown links resolve.
- The 26-line native patch applies to exact published 1.0.6 source, including its Windows line endings, and reproduces the compiled source changes.
- A live GitHub refresh passed with all ten official guides cached in the installed offline guide store after correcting branch-reference lookup.

These are automated/source/build and UI checks. No new live ROM interaction session, real two-PC battle test or save/reload gameplay result is claimed.

## Distribution scope

Launcher **1.0.6 / revision 2026101302** and the corresponding native post-release build were installed locally with the preceding files backed up. Current launcher sources, tests and the native patch are included on `main`. Public **v1.0.6** download assets remain unchanged and still contain the preceding launcher/default. A subsequent packaged release is needed to deliver this settings change to download users.
