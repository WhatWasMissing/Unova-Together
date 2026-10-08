# Play Unova Together with a friend

Unova Together adds shared exploration, item trading and experimental co-op trainer battles to Pokémon Black 2 and Blaze Black 2 Redux. Made by mvq1303.

## What each player needs

- A Windows x64 PC and the complete Unova Together 0.3.1 ZIP, extracted into a folder.
- Their own ROM and save. Both players must use exactly the same game version, including the same Redux revision.
- A backup of their save before playing this beta.
- A connection method below. Tailscale is included; the experimental UDP option also needs Python.

ROMs, saves and DS firmware are not included. Preset keyboard/controller bindings are included; check Config → Input before playing.

## Start the game

1. Extract the whole ZIP. Keep its folders together.
2. Open **Start Emulator.cmd**.
3. Load your ROM and start from your normal saved game.
4. Turn **fast-forward off** before connecting. Keep it off during shared battles.
5. Open **System → Multiplayer**. Choose a player name different from your friend's.

Each player keeps their own save. Avoid loading savestates while connected.

## Choose how to connect

| Where you are playing | Use this |
| --- | --- |
| On the same home network | The local setup below |
| On different networks | [Tailscale setup](TAILSCALE_COOP.md), recommended for this beta |
| On different networks, with a UDP server address supplied | The experimental UDP setup below |

There is no default public Unova Together server. If nobody has supplied a UDP server, use Tailscale. Do not run the UDP helper and a Tailscale native LAN connection for the same session.

## Same home network

Choose one player as the **host**.

1. Host: in Multiplayer, set **Relay host** to `127.0.0.1`, **Port** to `8765`, choose a room name and press **Connect**. This starts/checks the local player-sharing service.
2. Host: give your friend your PC's local IPv4 address, such as `192.168.1.20`. Use your actual address, not the example. On Windows, run `ipconfig` and find IPv4 under your active Wi-Fi/Ethernet adapter.
3. Guest: in Multiplayer, enter the host's address, port `8765` and the same room, then press **Connect**.
4. Check that both players appear in the list and can see each other's movement on the same map.
5. Host: choose **System → Host LAN game** and select two players.
6. Guest: choose **Join LAN game** and enter the host's local address.
7. Check that the LAN game lists both players as ready. If Windows asks about firewall access, allow the emulator/Python on your trusted private network. The host needs TCP 8765 and UDP 7064 accessible from the guest.

Unova Together uses two connections: the Multiplayer connection shares players/items; the LAN game connects the games for wireless battles. Working sprites alone do not mean battles are connected.

## Different networks with Tailscale

Follow [TAILSCALE_COOP.md](TAILSCALE_COOP.md). The official installer is in **setup/Tailscale**; skip installation if you already have it.

Both PCs must be online in the same Tailscale network. For the guest's Multiplayer connection and Join LAN game, use the host's Tailscale address. Keep Tailscale connected throughout play. You do not need **Online Co-op.cmd** for this route.

## Experimental UDP connection

This option is still being tested across the internet. Have the session host provide:

- UDP relay server address, control port, room name and access key.
- Player-sharing server address, port and room name. This is a separate setting.
- Which player will host the game.

If you are setting up the relay yourself, use the separate [server guide](UDP_SERVER_GUIDE.md). Ordinary players can skip that guide.

1. On both PCs, install Python 3 with tkinter and pip. Python 3.12 x64 is the tested version.
2. Run **Install UDP Dependencies.cmd** once. It needs internet access. Wait for it to report successful installation.
3. Game host: choose **System → Host LAN game**, with two players.
4. Both: open **Online Co-op.cmd**. Enter the supplied server address, control port (normally `8766`), room and access key.
5. Choose **host** on the game host and **guest** on the other PC, then press **Connect**. Keep both helper windows open.
6. Wait for **UDP reachable** and **Partner connected**. If connection fails, check the supplied details or use Tailscale.
7. Guest: choose **Join LAN game** and enter **`127.0.0.1:17064`**. This address is correct for the UDP helper; do not enter the remote server address here.
8. Confirm that both players appear ready in the LAN game.
9. In each Multiplayer panel, enter the supplied player-sharing server address, port (normally `8765`) and room. Press **Connect** and check that both players appear.

`127.0.0.1` normally means your own PC. Use it for the UDP guest's **Join LAN game** step above; it will not connect your Multiplayer panel to a server on somebody else's PC.

## Play together

1. Enter the same area and check that both players can see each other move.
2. Use the in-game **Trade** menu to send items. Stay idle in the overworld with C-Gear wireless off while making an offer. The other player accepts it; save both games after the transfer finishes.
3. For trainer battles, choose **Co-op** under Multiplayer → Players or in-game Players → Game. Both players should talk to the same trainer and wait for pairing to finish.
4. To fight alone, choose **Solo** before the encounter. You can stay connected to your friend.
5. For a first battle test, use **Practice** from the boss challenge controls. Practice does not award story progress.
6. After a story battle, check that each game returns to normal play and save each game separately. Check your own badge/story progress before continuing.

Co-op battles are experimental. Read [known issues](KNOWN_ISSUES.md), including experience gain and special trainer encounters.

## If a connection or battle gets stuck

1. Wait briefly for your friend; a slow connection can delay a turn.
2. If it does not recover, use **Return to field** in Multiplayer → Debug if available. Recovery can discard the interrupted battle's progress.
3. Leave the LAN game on both PCs. For UDP, press **Stop** in both helpers before reconnecting.
4. Create a new host LAN game, reconnect the helpers if using UDP, then have the guest rejoin.
5. Reconnect the Multiplayer player-sharing connection if needed. Check movement before starting another battle.
6. If UDP keeps failing, close the helpers and switch to the Tailscale guide.

An interrupted battle cannot be resumed reliably by reconnecting. Avoid saving a broken battle state over your backup.

## Reporting a problem

Include your Unova Together version, game/Redux version, which PC hosted, connection method, what you were doing and whether one or both players were affected. Mention any low FPS or error message. Capture both players' Debug screens if possible. If RAM snapshots are requested, share them privately; they can contain personal save information.
