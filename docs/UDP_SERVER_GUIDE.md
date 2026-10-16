# Optional UDP server for co-op

Unova Together does not provide a public server. Your group can use Tailscale instead, or someone in your group can host the optional UDP relay described here. Players can follow the [Player guide](PLAYER_GUIDE.md).

The relay lets two players connect their native LAN games across different networks. It requires a Linux server with a public address, Python 3, and a valid TLS certificate. Open TCP port 8766 and UDP port 8767 on the server firewall. Players do not need router port forwarding.

## What the server host does

1. Download the matching Unova Together release and copy its tools folder to the server.
2. Install Python 3 and the dependencies listed in the release.
3. Set up a trusted TLS certificate for the server’s public name.
4. Generate a private access key. Keep it separate from the game download and share it only with your group.
5. Allow the relay ports through the server firewall and start the relay using the certificate and access-key files.

Run the relay as a managed service so it can restart after a server reboot. Keep private keys readable only by the service. Restart the relay after renewing its certificate. Stopping it disconnects active rooms.

## Share connection details

Give players the server name, port 8766, access key, and a shared room name. Each room is for one host and one guest.

The UDP relay carries game communication. For movement, trades, and co-op invitations, your group also needs a reachable player-sharing service or Tailscale. Keep any sharing server private to your group.

For player setup and connection tips, see [Playing with friends](PLAYER_GUIDE.md) and [Known limits](KNOWN_ISSUES.md).
