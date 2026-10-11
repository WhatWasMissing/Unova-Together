# Unova Together beta 0.4.0

## New experimental options

Open **Launcher → Settings → Experimental**, enable the features you want, and restart the game. Both are off by default.

- **Companion interactions:** talk to, pet, and play with your lead Pokémon. Responses reflect its health and friendship. Click its following sprite or open **Unova → Pokémon → My companion**. Interactions do not change HP, friendship or your save.
- **Latias / Latios flight preview:** steer a pixel-art preview over your current surroundings. D-pad steers, L/R switches mount, and B returns. With HM02, the Fly button opens the original party screen; select a Pokémon and choose Fly to use the game’s own destinations.

The pause-menu entry is now **Unova**. Players, Pokémon, Co-op and Settings are sibling tabs; settings are no longer presented as part of Players.

## Setup

Download **Unova-Together.exe**, or extract the complete portable ZIP. Update all players, restart the game, and follow the included player guide. No new ROM or save is required. Tailscale remains the fallback for different networks; the UDP bridge requires your own server.

## Known limits

The flight option is a menu preview, not free flight through a 3D Unova region. Native Fly retains its normal story restrictions, and completed Fly travel still needs gameplay testing. Companion interactions require a resolved idle field, and eggs cannot interact. In co-op, XP remains disabled to avoid desync. Keep fast-forward off during native wireless battles.

## Checks

The native ROM-backed menu fixture verifies opt-in gating, Talk/Pet/Play, battle safeguards, unchanged party/bag data, steering and mount switching, the native party shortcut, Options and existing menus. Compiled helper tests cover health/friendship responses, all 649 species and bounded steering. These checks do not establish full ORAS-style flight or completed Fly travel.

Made by mvq1303 / WhatWasMissing. Playtesters: maxback221 and randomitem19. Built on melonDS; corresponding GPL source is included.
