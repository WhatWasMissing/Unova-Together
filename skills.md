# Reusable implementation guidance

## Launcher UI work

Use these practices when changing launcher navigation, settings, status pages, or responsive layouts:

- Keep navigation labels grouped by the task players are trying to complete, and make the current page unmistakable through both selection styling and accessible text/state.
- Give frequently used settings a clear home and provide direct shortcuts only when they preserve the same underlying setting and persistence behavior.
- Test the smallest supported window size as well as the normal layout. Let content reflow or scroll; do not solve space pressure by shrinking text until it is hard to read.
- Show progress and a useful status message during background work, and keep controls responsive where the operation permits it.
- Preserve existing routes, settings keys, update/repair flows, and error handling while improving presentation.
- The canonical launcher is under `launcher-source/tools/launcher_ui/`; compare any corresponding `maintenance-tools/tools/launcher_ui/` files and keep them aligned when both are shipped or tested.
- Verify with the relevant launcher UI tests, the UI parity check, and a real launch/visual inspection when available. Report screenshot or live-runtime checks that could not be completed.

This guidance captures the launcher navigation and responsive-layout choices applied for 2.0.24. Recheck current source and tests before reusing it; it does not establish behavior outside the launcher UI.
