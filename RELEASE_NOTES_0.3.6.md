# Unova Together beta 0.3.6

Save normally and close the game, then open **Updates → Check for updates** in the launcher. Install beta **0.3.6** and reopen the launcher. Update both players before testing. New players can download **Unova-Together.exe** below; the portable ZIP is also available.

## Fixed

- Battle presence can now clear after three confirmed field-map samples even while the player sprite is unresolved. Previously that recovery gap could keep the battle flag and pre-battle location visible to teammates.
- Retained position samples use current game state rather than leftover battle/menu flags.
- The player list shows **Unavailable** instead of **Other map** when your local position cannot be resolved.

This release also includes launcher 20261009.9: startup/manual GitHub guide refresh with offline copies, LAN Host/Join, remembered connections, Retry, report review, keyboard/controller navigation and the gameplay Features page.

## Testing

Compiled battle transition and missing-actor regressions pass. Existing before/battle/after/menu RAM captures classify correctly; the post-battle capture clears its battle flag. All 12 presence-relay tests pass. The latest reported two-player incident has not been reproduced from a fresh snapshot, so this fixes a verified recovery gap rather than claiming every stale-state issue is resolved.

After updating, finish a normal battle on each device and check that both return to **Ready** and **Same map**. Repeat with one player changing maps while the other is fighting. If status stays wrong, save RAM snapshots from both games before moving indoors or restarting.

Co-op EXP remains disabled. Internet UDP battle completion, some trainer events, native cleanup and reconnects still have beta limitations; read **Setup → Known issues**. Keep C-Gear wireless and fast-forward off for co-op.

Made by **mvq1303 / WhatWasMissing**, built on melonDS. Matching GPL source and checksums are included. No ROMs, saves or firmware are included.
