# LAN lobby fix — beta 0.3.8

1. Close the game on every participating device and use the same 0.3.8 build. The LAN protocol changed; older versions cannot join this lobby.
2. Open Co-op in the launcher. The host chooses Host & play. Lobby size defaults to 16; Advanced settings allows 2–16.
3. Each guest chooses Join & play using the host address. Keep fast-forward and C-Gear wireless off.
4. For a story co-op battle, the lobby host and the chosen guest both enable Co-op trainer battles and approach the same trainer. Other guests should stay outside that encounter or use Solo trainer battles.
5. Battles contain two human players. The host can partner with a later-joining guest without removing earlier guests. Guest-to-guest story battles are not part of this change.

Local LAN and Tailscale support the larger lobby. The Internet UDP bridge remains a two-player path.

Tested: real three-player ENet discovery, pairing with the second guest, switching partners, readiness/results/cleanup, mismatched-result rejection, spectator isolation and disconnects. Three muted emulator processes joined through the launcher. Native co-op combat ran around 59–60 FPS with the first guest idle. Automatic NPC victory/badge progression in a three-player lobby was not verified.
