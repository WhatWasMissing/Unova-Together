# Play together across different networks

Use this guide when the players are in different homes or on separate internet connections. Tailscale creates a private network between the computers so Unova Together can reach the host without router port forwarding. The launcher asks each player to scroll through this guide and confirm they have reviewed it before starting a Tailscale session. If you do not want to use Tailscale, see [other ways to connect](#if-you-do-not-want-to-use-tailscale).

## Before you start

- Everyone needs the same Unova Together release and the same supported Blaze Black 2 Redux game revision.
- Choose one player to host. Each player should use a distinct in-game name and the same room name.
- Turn off fast-forward before connecting and keep C-Gear wireless off until the games are ready.
- Install Tailscale only from its [official Windows instructions](https://tailscale.com/docs/install/windows). Each person signs in with their own account; do not share one account.

## Set up the private network

1. Choose a player to manage the Tailscale network. They can invite everyone into one tailnet or share the host PC with each guest. Each person signs in with their own account and accepts the invitation or share. See Tailscale’s guides to [invite users](https://tailscale.com/kb/1064/invite-team-members) and [share a device](https://tailscale.com/kb/1084/sharing).
2. On every PC, open the Tailscale tray app and confirm it says **Connected**. If everyone joined one tailnet, the host should see the guests’ devices online. If the host shared their PC, each guest should see that shared host device.
3. On every PC that will play, open PowerShell as Administrator in the extracted Unova Together folder and run the included firewall helper:

   ```powershell
   .\tools\setup_tailscale_firewall.ps1
   ```

   It adds inbound rules for the game’s native wireless traffic (UDP 7064) and the player-sharing relay (TCP 8765), limited to Tailscale’s address range. The helper is included in the complete Windows ZIP; it configures Tailscale only and does not change router settings.
4. Find the host PC’s Tailscale IPv4 address in the Tailscale app or admin console. It normally begins with `100.`. Use this address only for the guest’s host-address field.

## Host and join

On the host PC, open Unova Together’s launcher and choose **Co-op**. Set **Connection method** to **Tailscale backup**, choose **Host**, set the room name, and save the connection. Keep the host address as `127.0.0.1`. Use **Test connection** to start or check the local player-sharing relay, then choose **Host & play**.

On each guest PC, choose **Tailscale backup** and **Join**. Enter the host’s Tailscale address, use port `8765` and the same room name, and enter a different player name. Save the connection, use **Test connection**, then choose **Join & play**. The host keeps the relay running while the group plays.

Once the games load, open **System → Multiplayer** on each PC and wait for the players to appear. The player-sharing list and the game’s native wireless list are separate. Confirm both are ready before starting a co-op battle. For a supported battle, the host starts it and invites one guest in the game’s **Unova → Co-op** menu.

## If you do not want to use Tailscale

- **Same home network:** Choose **Local LAN** in the launcher when everyone is connected to the same Wi-Fi or wired network.
- **ZeroTier:** ZeroTier can create a virtual LAN across the internet. The network owner creates a private network, each player joins it, and the owner authorizes each PC. Use the host’s ZeroTier address. Unova Together does not configure or officially test ZeroTier; the included firewall script allows Tailscale addresses only, so the host must add equivalent Windows Firewall rules limited to the private ZeroTier network for TCP 8765 and UDP 7064. See ZeroTier’s [network setup guide](https://docs.zerotier.com/start/).
- **Group-hosted UDP relay:** Someone in your group can host the optional relay on a Linux server with a public address, Python, and a TLS certificate. This is experimental and requires the server host to configure it. The UDP relay alone does not provide movement sharing, trades, or invitations; those also need a reachable player-sharing service. See the [UDP server guide](UDP_SERVER_GUIDE.md).

## Troubleshooting

- **A friend is missing from Tailscale:** Confirm their PC is online, the invitation or machine share was accepted, and the device is approved in the admin console.
- **The player-sharing test cannot connect:** Check the host’s `100.x.x.x` address, port `8765`, room name, and that the host relay is running. Confirm the firewall script was run as Administrator on the host.
- **Players appear in the sharing list but cannot start a co-op battle:** Confirm the games use the same release and Redux revision, C-Gear wireless and fast-forward are off, and the firewall helper was run as Administrator on each PC so UDP 7064 is allowed from Tailscale.
- **A different VPN or firewall is active:** It may change routes or block traffic. Test with one private network active and allow only the required game traffic from your trusted group.
- **A battle disconnects:** Return to the field and create a new session. A disconnected battle may not resume.

For same-network setup, see [LAN lobbies](LAN_LOBBIES.md). For general connection help, see the [player guide](PLAYER_GUIDE.md) and [known limits](KNOWN_ISSUES.md).
