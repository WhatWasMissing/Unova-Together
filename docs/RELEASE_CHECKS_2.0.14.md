# Unova Together 2.0.14 release checks

- The Windows x64 emulator target builds in Release configuration.
- The two-endpoint ENet co-op transport regression passes, including the shared Mega battle event.
- LAN traffic now requests a send flush for the background network worker. The emulator thread no longer performs the explicit socket flush for each wireless or co-op packet.
- Package checks verify the selected emulator binary, launcher version, patch-notes feed, source archive, checksums, and exclusion of ROMs and saves.

The transport regression uses two local emulator endpoints. A live test with players on separate computers is still useful to confirm movement feel across different network and Windows scheduling conditions.
