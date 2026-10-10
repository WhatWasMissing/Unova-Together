# Unova Together

Explore Unova together with shared multiplayer exploration, item trading and experimental co-op trainer battles in Pokémon Black 2 and Blaze Black 2 Redux. Built on a modified melonDS emulator. Made by mvq1303.

## Download and play

**Current release: beta 0.3.9.** Update both players to this version and restart the player-sharing relay.

1. [Download the Windows beta](https://github.com/WhatWasMissing/unova-together/releases/tag/v0.3.9). Choose **Unova-Together.exe** under Assets. The portable ZIP is also available.
2. Open **Unova-Together.exe**. For the ZIP, extract the entire folder and run **Start Unova Together.cmd**. Choose your ROM and select **Play**.
3. Load the [edited Blaze Black 2 Redux Rom](https://drive.google.com/file/d/1ZL4StVex1m6dvdEjG89o7kxOJwdJeR9L/view?usp=sharing). Both players need the same game revision.
4. Follow [the player guide](docs/PLAYER_GUIDE.md) to connect.

For different networks, start with [Tailscale setup](docs/TAILSCALE_COOP.md). Its official installer is included. The experimental UDP option requires a server supplied by your group; no default public server is available.

Launcher revision **20261010.2** adds LAN Host/Join, remembered connections, Retry, report review, controller navigation, optional music and a screenshot-based Features page. [Launcher guide](docs/LAUNCHER.md).

## What changed in 0.3.9

Added optional area-based 3D battle scenery, corrected follower identities and fixed the Options shortcut. Enable scenery in launcher Settings; it is generated locally from your ROM. Cheren co-op was tested through completion on both instances at about 59–60 FPS. [Release notes](RELEASE_NOTES_0.3.9.md) · [Scenery guide](docs/AREA_BATTLE_SCENES.md).

## What changed in 0.3.8

Launcher LAN lobbies now support up to 16 connected players, with the host pairing with any one guest. Added traded Pokémon obedience support and fixed stale invitations after cleanup. Larger lobbies use Local LAN or Tailscale; the UDP bridge remains two-player. [Release notes](RELEASE_NOTES_0.3.8.md) · [Lobby guide](docs/LAN_LOBBIES.md).

## What changed in 0.3.7

Corrected live outdoor map tracking, post-battle position recovery and menu map retention. Nearby players no longer rely on cached entry IDs. [Release notes](RELEASE_NOTES_0.3.7.md). All players must update. Live multi-device confirmation is still needed.

## What changed in 0.3.6

Fixed battle-presence recovery when the field returns before its player sprite is resolved, refreshed retained state flags, and corrected misleading “Other map” labels when local position is unavailable. [Release notes](RELEASE_NOTES_0.3.6.md). The latest reported two-player symptom still needs live confirmation.

## What changed in 0.3.5

- Added a launcher with official GitHub update checks and checksum-verified installation. The launcher runs without a separate Python installation.
- Fixed Give item being blocked by an idle co-op observer or the custom trade menu.
- Improved battle-status recovery and tracking after a field rebuild; camera validity no longer keeps a returned player marked in battle.
- Different starter choices can pair at verified rival encounters using the host's matching ROM team.
- Hardened wireless packet, player-list and compressed-ROM input handling.

All 33 populated Redux rival records passed two-player native startup checks. This does not prove every rival story script or save progression. Intermittent teammate disappearance, co-op experience and online limitations remain listed in [known issues](docs/KNOWN_ISSUES.md).

## Features

- **Explore with a teammate:** see each other moving around Unova, find teammates in the Players menu, and teleport to their map.
- **Trade items in-game:** choose items from your bag and send offers to a teammate, with accept/decline controls.
- **Co-op trainer battles:** face supported trainers together, including Gym Leaders and Redux teams. NPC encounters can wait for both players; a Solo/Co-op toggle lets you keep playing independently.
- **Independent saves:** each player keeps their own party and story progress. Back up saves before playing the beta.
- **Custom camera:** adjust the overworld camera's angle and rotation in Multiplayer → Camera.
- **Play across networks:** connect through Tailscale, or try the experimental UDP bridge with a server hosted by your group.
- **In-game multiplayer menus:** access teammates and trading from the game screen; advanced diagnostics stay behind the Debug toggle.
- **Launcher and updates:** select your ROM, launch the game, and get verified updates from this repository without replacing a running build. [How updates work](docs/LAUNCHER.md).

Co-op battles remain experimental: experience gain is disabled, not every trainer event has been verified, and connection problems can interrupt a battle. See [known issues](docs/KNOWN_ISSUES.md).

## Guides

- [Player setup, playing together and recovery](docs/PLAYER_GUIDE.md)
- [Known issues](docs/KNOWN_ISSUES.md)
- [Tailscale setup](docs/TAILSCALE_COOP.md)
- [UDP server hosting](docs/UDP_SERVER_GUIDE.md) — only for the person providing a server

Keep fast-forward off during shared battles and back up your saves. Co-op experience gain is disabled, some trainer events remain unverified, and unstable connections can interrupt battles. Internet UDP battle completion is still unverified.

Authorship and attribution: [mvq1303 / WhatWasMissing](AUTHORSHIP.md). Preserve original and upstream credits; do not misrepresent somebody else's work as your own.
