# Play together across different networks

Each Windows release includes the official Tailscale x64 installer in
`setup/Tailscale`. Skip installation if Tailscale is already installed.
Use matching Unova Together builds and exactly the same ROM version on both PCs.
Each player supplies their own ROM and save. Tailscale connects the computers;
Unova Together still needs both its presence connection and its native LAN connection.

## One-time setup for each tester

1. Extract the entire Unova Together ZIP into a folder you will keep using.
2. Run the `.msi` installer in `setup/Tailscale`. Allow the Windows
   administrator prompt. Windows 10 or later on an x64 PC is required.
3. Open Tailscale from the system tray and choose **Log in**.
4. The organiser invites testers into their Tailscale network (tailnet).
   Accept using your own account, then connect your PC to that invited network.
   Accepting an invitation alone does not connect a PC. If you have several
   networks, select the organiser's network.
5. The organiser checks the Tailscale admin device list: both PCs must appear
   online. Approve new devices if approval is enabled.
6. On each PC that will host, run this in PowerShell **as Administrator**,
   replacing the folder with your extracted Unova Together folder:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Games\Unova Together\tools\setup_tailscale_firewall.ps1"
   ```

   This allows UDP 7064 and TCP 8765 only from Tailscale IPv4 addresses.
   Repeat after moving the emulator to a different folder.

## Every play session

1. Both players connect Tailscale. Choose one PC as the host.
2. On the host, copy its Tailscale IPv4 address from the tray menu/device list
   (a `100.x.x.x` address). Send that address to the guest.
3. Both start `Start Emulator.cmd`, load their matching ROMs and enter play.
4. On the host's Multiplayer panel, set **Relay host** to `127.0.0.1`,
   **Port** to `8765`, choose a room and press **Connect**. This starts or
   checks the host's local presence relay.
5. On the guest, use the host's **Tailscale address**, port `8765` and the
   exact same room. Choose distinct player names. Press **Connect**.
6. Confirm both players appear in the list. Stand on the same map and check
   movement and item trading.
7. For native wireless/co-op tests, the host selects **System → Host LAN game**,
   with two players. The guest selects **Join LAN game** and enters the host's
   Tailscale address directly. Broadcast discovery does not cross networks.
8. Confirm the native LAN player list shows both players before initiating
   an interaction. Use copied saves for experimental shared battles.

No router port forwarding or exit node is needed. Do not run `Online Co-op.cmd`
alongside this direct setup. Keep Tailscale connected. Movement and native
wireless use separate connections: working movement alone does not confirm
that the native LAN game is joined.

## Troubleshooting

- **WinError 10013 / access forbidden:** Another VPN or its network filter may block the connection. NordVPN caused this in a beta test. Disconnect other VPNs and check their kill-switch settings, then retry with Tailscale connected. If it persists, check security software and firewall application rules.

- **PC missing/offline:** Log in on that PC, select the invited network and
  check device approval. An accepted user invite is not a connected device.
- **Connection refused:** The host must connect its local relay first.
  Check the host address, port and firewall. The guest must not use
  `127.0.0.1` to connect to another PC.
- **Native game missing:** Join by address directly, then check the host's
  emulator firewall rule. Do not rely on discovery.
- **Slow battles:** Latency or a relayed Tailscale path can affect native
  wireless. Shared battles remain experimental; bundling Tailscale does not
  establish that battle startup/completion or performance issues are fixed.

Optional checks on the guest, replacing HOST_IP with the host's address:

```powershell
tailscale status
tailscale ping HOST_IP
Test-NetConnection HOST_IP -Port 8765
```

The TCP check works after the presence relay starts; it does not test native
UDP wireless. Check the LAN player list for that connection.

Official instructions: [Windows installation](https://tailscale.com/docs/install/windows/msi)
and [connecting devices](https://tailscale.com/docs/how-to/connect-to-devices).
The unmodified installer is checksum verified and signed by Tailscale Inc.
No accounts, invitations, authentication keys or personal addresses are bundled.
Tailscale is a separate product with its own [terms](https://tailscale.com/terms).
