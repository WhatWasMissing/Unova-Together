# Unova Together beta 0.3.13 — Direct menus and Options fix

- Switch directly between **Players**, **Pokémon**, **Co-op** and **Settings** using the bottom tabs or **L/R**. **B** or **Close** leaves any main page.
- Follower controls, the original **Game options** and **Trainer card** are on Settings. Ready/Busy and trainer battle mode are together on Co-op.
- Fixed the Options shortcut selecting the wrong native menu entry. An unavailable target now cancels safely instead of opening an unrelated screen.
- Removed the spectate controls.
- Checkpoint recovery now synchronizes wireless transport membership with the restored radio power state so retries do not retain stale membership.
- **maxback221** and **randomitem19** are credited as playtesters in the emulator and in a dedicated launcher strip that stays visible when resizing.

Use **Updates** in the launcher, or download **Unova-Together.exe** below. Save normally and close the emulator before replacing its build. No new ROM or save is required. Keep every player on the same version.

Native ROM-backed tests passed for direct navigation, B/Close, item-menu exit, Options, Trainer card, intentionally selecting the wrong native tile, and invalid-target cancellation. Launcher credits were checked at three window sizes. A two-process LAN test entered battle, cancelled back to the field, entered a second battle without restarting, and cancelled cleanly on both games. A powered-checkpoint test verified that transport membership is restored. Existing relay tests and retained story-result checks passed. This update does not add new battle or internet functionality; existing [beta limitations](https://github.com/WhatWasMissing/Unova-Together/blob/main/docs/KNOWN_ISSUES.md) still apply.

Made by **mvq1303 / WhatWasMissing**, built on melonDS. Thank you to playtesters **maxback221** and **randomitem19**. Matching GPL source and SHA-256 checksums are included. No ROMs, saves or firmware are bundled.
