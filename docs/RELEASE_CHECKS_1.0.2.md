# Release 1.0.2 checks

Unova Together by mvq1303 / WhatWasMissing, built on melonDS.

The solo XP production dispatch passed rounding, award-cap, unchanged EV/flag, co-op-zero and unsupported-context checks against genuine English Black 2 and Redux overlays. Genuine solo Cheren battle results are in XP_COMPENSATION_BATTLE_TEST.md. The original comparison did not establish save/reload; a subsequent published 1.0.2 battle now passes native saving, independent PKHeX checksum/data validation and a fresh normal boot with matching XP, level, moves and badge. End-to-end JIT XP is not established by these interpreter battle tests.

Rebuild both versioned executables, rerun feature contracts and XP checks, smoke-test the frozen launcher and standalone EXE, verify sanitized runtime/source archives and matching source, and compare uploaded SHA-256 asset digests. Detailed private reports are retained under test-fixtures/release-1.0.2; private game data is excluded from release assets.
