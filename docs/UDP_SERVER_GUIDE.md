# Host an experimental Unova Together UDP server

This guide is for the person providing a server. If you only want to play, use [the player guide](PLAYER_GUIDE.md). No public Unova Together server is supplied.

The relay lets two players connect their native LAN games across networks without Tailscale. Internet battle reliability is still unverified; keep [Tailscale](TAILSCALE_COOP.md) available as a fallback.

## Set up the relay


Use a Linux server close to the players with a public IPv4, DNS name and permission to open TCP 8766 and UDP 8767. A home server works if those ports are forwarded and the ISP allows inbound connections; CGNAT may require a hosted server. Players make outbound connections and do not need router port forwarding. This implementation always uses the relay; direct peer-to-peer NAT traversal is not implemented.

1. Point an A record such as `relay.your-domain.example` at the server. Replace that example everywhere below with your actual domain.
2. Copy the release's `tools` directory to `/opt/pokeplay/tools` on the server. Install Python and a virtual environment (Ubuntu/Debian example):

   ```sh
   sudo apt update
   sudo apt install python3 python3-venv certbot
   sudo mkdir -p /opt/pokeplay /etc/pokeplay
   sudo python3 -m venv /opt/pokeplay/venv
   sudo /opt/pokeplay/venv/bin/pip install -r /opt/pokeplay/tools/requirements-online-udp.txt
   ```

3. Obtain a trusted TLS certificate. For Certbot standalone, TCP 80 must reach this server during certificate issuance/renewal and no other service may occupy that port:

   ```sh
   sudo certbot certonly --standalone -d relay.your-domain.example
   ```

   An existing valid certificate is also supported. Do not disable certificate verification. The relay needs restarting after renewed certificate files are installed.

4. Generate a private access key. Keep this file outside the release/source folder; share the key only with your testers:

   ```sh
   sudo sh -c 'umask 077; /opt/pokeplay/venv/bin/python -c "import secrets; print(secrets.token_hex(32))" > /etc/pokeplay/access.key'
   ```

5. Allow **TCP 8766**, **UDP 8767**, and TCP 80 for certificate issuance in your server/provider firewall. If UFW is already used, add `sudo ufw allow 8766/tcp` and `sudo ufw allow 8767/udp`. Keep your existing administrative access rules.
6. Start the server in the foreground for the first test:

   ```sh
   sudo /opt/pokeplay/venv/bin/python /opt/pokeplay/tools/online_udp_relay.py \
     --listen 0.0.0.0 --port 8766 --udp-port 8767 \
     --cert /etc/letsencrypt/live/relay.your-domain.example/fullchain.pem \
     --private-key /etc/letsencrypt/live/relay.your-domain.example/privkey.pem \
     --access-key-file /etc/pokeplay/access.key
   ```

   This foreground example uses root to read Certbot files. For continuous operation, use a dedicated service account with read access to protected certificate copies and the access key; do not make private keys world-readable. Run the command as a managed service and restart it after renewal. Stopping the server disconnects every room.

7. Send testers the domain, control port **8766**, access key and a shared room name. UDP port 8767 is announced automatically by the server. Rooms contain 1â€“32 letters, digits, underscores or hyphens. Exactly one host and one guest may join each room. Up to 16 rooms / 32 TLS connections are accepted.


## Set up player sharing

The UDP relay carries game communication only. For movement, item offers and challenge coordination, provide a shared player-sharing server as well. On a trusted host, run:

`sh
/opt/pokeplay/venv/bin/python /opt/pokeplay/tools/presence_server.py --host 0.0.0.0 --port 8765
`

Allow TCP 8765 from your players and give them this server address, port and a common room name. This existing service is not encrypted by the UDP helper; restrict it to your group. Use Tailscale for player sharing if you need private network protection.

## Give players these details

- UDP server hostname, control port (normally 8766), a room name and the access key.
- Which player will host the native LAN game.
- Player-sharing server address, port (normally 8765) and room name.
- The [player guide](PLAYER_GUIDE.md) and [known issues](KNOWN_ISSUES.md).

Do not share the private TLS key. No ROMs or saves need to be uploaded to the relay. Limit access to trusted players; individual accounts and anonymous public matchmaking are not supported. Stopping or restarting the relay disconnects its rooms. Interrupted battles need field recovery and a new session.
