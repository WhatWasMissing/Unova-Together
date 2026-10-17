# Unova Together 2.0.15 release checks

- The Windows x64 emulator target builds in Release configuration.
- All 21 emulator regression tests pass, including Mega Evolution battle lifecycle coverage.
- Double-battle checks cover both active positions, action ordering, and cleared battle-view pointers.
- Co-op checks cover independent local and partner Mega uses, either action order, and stable party-slot selection.
- The two-endpoint ENet transport test passes with the shared Mega battle event.
- Package checks verify the emulator binary, launcher version, patch-notes feed, source archive, checksums, and exclusion of ROMs and saves.
