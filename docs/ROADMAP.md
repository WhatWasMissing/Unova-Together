# Unova Together roadmap

Maintained for **mvq1303 / WhatWasMissing**, built on melonDS. Published release **1.0.6**; current source/local build **1.0.7-dev**, reviewed **13 October 2026**. Implemented capabilities are listed in [Features](FEATURES.md).

Development work now includes the Practice result/cleanup barrier (targeted local latency pass), protocol/ROM readiness, rematch categories, contextual session dialogue, 743 normal/shiny female/form assets, sprite stability, reduced motion and ₽10 Super Repels. See [validation and remaining playtests](DEVELOPMENT_POLISH_2026-10-13.md). The priorities below describe areas to continue validating or expanding; they are not release promises.

## 1. Make shared battles and recovery reliable

- Fix the completion handshake that can finish one peer's practice battle while rolling the other back under latency.
- Make successive battles reconnect cleanly and ensure both players return to the field with matching session status.
- Explain cancellation/recovery in the game and coordinate both peers before either treats an encounter as complete.
- Validate wins, losses, cancellations, player disconnects and normal save/reload on two physical PCs, in both host directions, including Tailscale.

This is the first priority because new battle modes would inherit current completion and recovery problems. Progress and rewards must remain owned by each player's original game script and save.

## 2. Improve connection setup and compatibility checks

- Show one readiness checklist for ROM/build agreement, presence sharing, native wireless, partner availability and C-Gear/normal-speed requirements.
- Make reconnect status and the next action clearer, including what can reconnect in the field and what requires creating a new LAN session.
- Reduce repeated address entry and improve the first-run Host/Join flow.

An invite-code service or hosted relay could simplify internet setup later. That requires actual service infrastructure and maintenance; it is not currently available.

## 3. Give followers more personality and context

- Add responses to the current area, time of day, season, weather and recent battle result where those values can be read reliably.
- Remember recent interaction choices during a session to reduce repeats and support small recurring jokes or routines.
- Add species/type-specific reactions and more grounded motion, with readable symbols and less clipping around scenery.
- Expand shiny, alternate-form and gender sprite coverage when matching, correctly credited assets are available.
- Add options for idle bob strength, reduced motion and reaction frequency.

The ten actions, five friendship bands, subtle nature cues and animated reactions already exist. Development dialogue now has area/calendar/type context and per-Pokémon/action session visit counts. Weather, outcome-specific scenes, permanent memories and friendship/item rewards remain future work. Keep interactions read-only unless persistent effects are separately designed and validated. The launcher moves interactions out of Experimental and defaults them on while preserving explicit choices.

## 4. Make progression and trainer co-op easier to follow

- Show each player's eligibility and story progress before a shared trainer invitation, with a clear reason if the encounter cannot start.
- Improve invitations for ordinary trainers and add a useful rematch browser with tested encounter coverage.
- Explore co-op challenge presets or boss gauntlets after the battle/recovery gate passes.
- Investigate safe, agreed co-op XP accounting. **Co-op XP remains disabled today**; simply enabling native rewards is not a supported fix.

Independent parties and saves should remain the default. Shared story flags would require a separate design.

The development practice browser now searches ROM-backed trainers and shows party size and level span. Experimental local Soaring now links outdoor matrices when reciprocal, fly-enabled warps establish their shared positions. The remaining standalone matrices still need safe links, and broad live flight/landing tests remain future work; see [Soaring design](SOARING_DESIGN.md).

## 5. Polish field tools, presentation and accessibility

- Filter/search encounters and optionally show caught/seen state using verified save data. Extend special encounters only with correct source coverage.
- Validate complete HM routes and move-relearning save/reload, then improve explanations of native restrictions.
- Improve teammate/follower occlusion, camera transitions and visual stability around buildings and map changes.
- Refine battle scenery for seasons/time of day and broaden gameplay checks across environments.
- Improve text scaling, controller focus, small-window layouts and reduced-motion settings.

## Suggested development order

Battle completion/recovery → connection checks → contextual follower interactions → progression/encounter coverage → expanded challenge content and presentation. Keep the [known issues](KNOWN_ISSUES.md), launcher Features tab and release evidence in step with each change.
