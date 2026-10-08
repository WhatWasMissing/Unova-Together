# Beta 0.3.5 validation

The Windows emulator and bundled launcher were built and checked on Windows. This is a beta validation record, not a guarantee that every game event, network or upstream emulator subsystem is bug-free.

- 1,000 repeated battle-to-field status transitions pass, including unresolved gaps and invalid camera projections. Camera drawing no longer controls whether the battle badge clears.
- Actual two-core battle completion restores native field ownership and clears the presence battle flag on both returned RAM snapshots.
- The repeated-battle fixture exposed a second-attempt partner-disconnect failure. Both recovered/completed into an owned field and their battle flags cleared. Immediate second-battle completion is not claimed.
- All 33 populated named Redux rival records passed native two-core opening and ROM team/AI audits. Seven earlier harness failures passed after correcting single-Pokémon count expectations and waiting for the actual battle scene. Original failure reports were preserved.
- 63 real ENet starter-pair agreements and mismatch/cancel/retry/session-restart cases pass. Verified rival script families use the host's ROM-owned starter variant; full different-starter NPC story/save progression is not proven.
- Item transfers and staged/restarted recovery conserve item counts. Native menu tests verify custom trade readiness and stock-menu blocking.
- Relay tests pass: 12 presence, 36 item trading, 40 Pokémon trading, 10 encrypted UDP and 9 wireless helper tests.
- Launcher tests verify official release selection, checksum/size checks, archive containment, cancellation, failure rollback, configuration preservation and safe active-version paths. Its bundled Windows executable creates the UI without a separately installed Python runtime.
- The code review identified four network/ROM input issues, which were patched. Production event-handler tests reject malicious player lists; 514,304 wireless cropping cases preserve memory guard bytes; production Zstandard tests verify exact sizes, unknown-size frames, truncation and buffer growth. DS/GBA minimum-header guards compile; a dynamic tiny-ROM parser playthrough is not claimed.

The review covered important mod, networking, ROM-loading and save/event ownership boundaries. It was not an exhaustive line-by-line clearance of every CPU/JIT/GPU/DSP implementation or vendored dependency. The intermittent menu-dependent disappearance recovered before RAM capture and remains unconfirmed. Internet UDP battle completion remains unverified.

A final fresh-battle test hit a guest communication-cleanup timeout after completion. Recovery discarded the guest battle progress. Both returned RAM snapshots had owned field state and cleared battle flags; reliable cleanup is not claimed.
