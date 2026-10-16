# Play Unova Together with friends

Unova Together adds shared exploration, trading, co-op trainer battles, and Mega Evolution to supported Pokémon Black 2 and Blaze Black 2 Redux games.

## What each player needs

- A Windows x64 PC and the latest Unova Together launcher or portable ZIP.
- Your own compatible game file and save. Both players need the same game version and Redux revision.
- A network connection method. Players on the same home network can use LAN; players on different networks can use [Tailscale](TAILSCALE_COOP.md).

Unova Together does not include Pokémon ROMs, save files, or firmware. Change your controls under **Config → Input** if you want to adjust the defaults.

## Start playing

1. Download the launcher or the complete Windows ZIP from the [latest release](https://github.com/WhatWasMissing/Unova-Together/releases/latest).
2. Extract the ZIP into a folder if you chose the portable version. Keep its folders together.
3. Open the launcher, select your own supported game file, and choose **Play**.
4. Start from your normal in-game save. Open **System → Multiplayer** to set your player name and connection.
5. Turn fast-forward off before connecting and keep it off during shared battles.

Each player uses their own save. Save from the game as usual, and avoid loading emulator save states while connected.

## Choose a connection

| Where you are playing | Connection |
| --- | --- |
| Same home network | Use the launcher’s local co-op options. |
| Different networks | Follow the [Tailscale guide](TAILSCALE_COOP.md). |
| Different networks with a server supplied by your group | Use the optional [UDP connection guide](UDP_SERVER_GUIDE.md). |

There is no public Unova Together server. Everyone should use the same release and game revision and enter the same room name.

## In-game co-op

Open the game’s pause menu and choose **Unova**. **Players** is for teammate information and trades, **Pokémon** has party tools, **Co-op** contains battle options, and **Settings** controls presentation and followers. Use L/R or touch the tabs to move between pages.

Trades require both players to confirm. Keep both games open until the trade finishes, then save in each game. Co-op trainer battles are supported for selected encounters; each player keeps their own story progress and save.

## If a connection stops

If a teammate disappears or a battle stops responding, let both games return to the field. If needed, close the connection and create a new LAN session. A disconnected battle may not resume, so save normally before starting another encounter.

If you cannot connect, check that both players use the same release and game revision, turn off fast-forward, and confirm the host address and room name. A VPN or firewall can block connections. For different networks, [Tailscale](TAILSCALE_COOP.md) is the recommended option.

## More help

See the [launcher guide](LAUNCHER.md), [co-op tools](COOP_TOOLS.md), [Mega Evolution](MEGA_EVOLUTION.md), and [known limits](KNOWN_ISSUES.md). The launcher’s **Updates** page installs game updates while keeping save files in place.
