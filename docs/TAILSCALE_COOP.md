# Play together across different networks with Tailscale

Tailscale connects the computers in your group as if they were on the same private network. It is a separate service; every player needs their own account and must accept the group invitation.

## Set up Tailscale

1. Install Tailscale on each Windows PC. The official installer is included in the Unova Together ZIP under setup/Tailscale; you can also download it from [Tailscale](https://tailscale.com/docs/install/windows/msi).
2. Sign in and accept the host’s invitation to the group network.
3. Confirm each computer is online in the Tailscale app.
4. On each PC that will host a game, run the setup_tailscale_firewall.ps1 script in Unova Together’s tools folder from an Administrator PowerShell window.

## Connect for a play session

1. Everyone connects to the same Tailscale network and starts the same Unova Together release with matching game versions.
2. Choose one player to host. Find their Tailscale IPv4 address in the Tailscale app; it begins with 100.
3. On the host’s Multiplayer panel, use relay host 127.0.0.1, port 8765, choose a room, and select **Connect**.
4. On the guest’s Multiplayer panel, enter the host’s Tailscale address, port 8765, and the same room. Use a different player name.
5. Confirm everyone appears in the player list. For native co-op battles, the host starts a LAN game and the guest joins using the same Tailscale address.

No router port forwarding is needed. Movement sharing and the game’s native wireless connection are separate, so check both player lists before starting a co-op battle.

## Troubleshooting

- If a PC is missing, make sure it is signed in, connected to the invited network, and approved if the host requires device approval.
- If the connection is refused, check the host address, room name, and firewall rules. Guests should not use the host’s local-only address to connect to another computer.
- If another VPN or firewall blocks the connection, temporarily disconnect it or allow Unova Together through its settings.
- If a battle stops responding, return to the field and create a new session. A disconnected battle may not resume.

The optional Internet UDP relay is a separate connection method. It needs a server provided by your group; see the [UDP server guide](UDP_SERVER_GUIDE.md).
