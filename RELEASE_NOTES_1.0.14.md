# Unova Together 1.0.14 — Smoother LAN hosting

This full release addresses the intermittent movement hitch reported while hosting a LAN game.

- The LAN socket worker now services a small bounded batch of ENet events on each poll instead of draining a large burst while holding the shared network lock. This shortens lock contention with the emulator's wireless send path.
- Launcher and emulator version labels now both report **1.0.14**. Existing ROMs, saves and settings are kept when updating.

The change targets host-side hitches that can happen without an FPS drop. It has passed the native build and release packaging checks; please test a hosted session with this release to confirm the improvement on your machine. Clients should use the same release and restart their game after updating.

No ROMs, saves, firmware or RAM captures are included. Made by **mvq1303 / WhatWasMissing**, built on melonDS. Upstream and dependency notices are retained.
