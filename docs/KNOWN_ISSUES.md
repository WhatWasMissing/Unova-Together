# Unova Together 1.0.12 — known limits

Release 1.0.12 improves Soaring's regional scenery and protects the landing transition from NPC input. Soaring remains experimental and needs live playtesting across maps. The previously reported movement hitching, idle follower disappearance, distorted bobbing and Redux shiny follower colours were confirmed fixed in 1.0.10 gameplay. Broader physical-PC, WAN and every-species testing remains limited. See [release checks](RELEASE_CHECKS_1.0.12.md).

- **Other VPNs can block connections.** NordVPN caused a tester’s presence-relay connection to fail with WinError 10013. Disconnect other VPNs while using Tailscale; check their kill-switch and network-filter settings if access remains blocked. This is not evidence that the game server is offline.
- **Online UDP is experimental.** It has been checked locally, but reliable battle completion between players on different networks has not yet been confirmed. Use Tailscale if it fails.
- **Sometimes players can get stuck reported as "In Battle" or "Unavailable"**. If changing map or going inside does not fix this, save **in game** and restart the emulator through the launcher or portable zip. Do not load a save state.
- **No public server is supplied.** The UDP option needs a server provided by your group. Player sharing also needs a reachable server; joining a UDP room does not configure that automatically.
- **Slow or unstable connections can interrupt battles.** A battle may stall or end unexpectedly. Changing the connection method cannot guarantee a fix.
- **Teammate rendering can flicker.** Camera sample gaps and map transitions can interrupt the displayed sprite. This release does not claim that all camera/rendering issues are fixed.
- **Intermittent menu-dependent disappearance remains unconfirmed.** An earlier report recovered before RAM capture. Player-object replacement and battle-status recovery were fixed and tested, but that exact symptom has not been reproduced.
- **Different starters:** verified rival script families can agree on the host's enemy variant. All 33 named Redux rival records pass native startup checks; not every different-starter story encounter has been played through to save/reload.
- **Launcher updates need GitHub access and disk space.** Downloads install beside the previous build. Save normally before switching. An unavailable check does not prevent offline play. Older update folders are retained for recovery.
- **Wait before retrying a cancelled trade.** Let both players return to Ready before sending another request. Rapid retries can be rejected.
- **An immediate second co-op battle can fail to reconnect.** A repeated local two-core test completed the first battle but lost a partner during the next attempt; both returned to the field and cleared their battle status. If this happens, let recovery finish and recreate the native LAN session before retrying.
- **Native cleanup can time out after completion.** A final local check required guest checkpoint recovery, discarding that guest battle progress. Check both games return normally before saving or starting another encounter.
- **Fast-forward can prevent wireless pairing.** Turn it off before connecting and throughout shared battles.
- **A disconnected battle cannot reliably resume.** Return to the field and create a new LAN session. Recovery may discard that battle's progress.
- **Co-op experience gain is disabled to prevent desynchronisation.** Do not expect shared trainer battles to award experience in co-op.
- **Some trainer encounters still need testing.** Not every special event or Redux fight has been played through. Check each player's story progress and save separately after battles.
- **Single-Pokémon opponents are duplicated for co-op.** When a trainer normally has one Pokémon, a matching copy fills the second enemy position.
- **Some networks block UDP.** The helper may fail even when other internet apps work. Use Tailscale as the fallback.
- **Python is required for the UDP helper.** Python/tkinter and the dependency installer are separate from the bundled emulator. This release is for Windows x64; it is not an Android emulator build.


## Optional features and field tools

Nearby battle scenery remains experimental. Special cinematic scenes keep original backgrounds; not every environment has been playtested. Disable the option if a background looks wrong.

Companion interactions are in Settings → Following Pokémon and enabled by default when no preference has been saved. Saved off choices are preserved. Use R+A or tap the follower; A alone advances game text. Regional Soaring remains experimental and off by default. Outdoor maps join the flight atlas when reciprocal fly-enabled warps define their shared position; standalone maps without a safe link stay separate. Unsupported cells appear as ocean or sky, and landing is limited to verified clear terrain. Flight is local; B returns to the take-off point.

Field HMs retain native story requirements. Fly needs a party member with a move slot without another field action. Full obstacle traversal and every save/reload path have not been separately playtested. Encounter gifts, scripted legendaries and Hidden Grottos are excluded. Relearning offers the current species/form's level-up moves at or below its level.

Direct party Pokémon trades exclude eggs, held Mail and native trade-evolution entries. Use the Union Room for those cases. Both players must save normally after trades and relearning.

- **Practice can complete asymmetrically under latency.** A local simulated 100 ms round trip left one peer completed and the other rolled back after partner loss. The completion handshake still needs a fix. Verify both peers returned normally before saving; do not treat this maintenance release as a WAN reliability fix.

- **Boosted solo XP persistence has a targeted pass.** A published 1.0.2 solo Cheren victory saved 5,951 Servine XP / level 20 and the badge, independently parsed with PKHeX, then reloaded in a fresh emulator process. This interpreter fixture does not establish JIT or full-playthrough behavior. See `XP_COMPENSATION_BATTLE_TEST.md`.

The historical 1.0.2 test used 1.65× XP. Current releases use **1.25×**, validated by production-dispatch checks; a fresh end-to-end battle/save/reload test for that multiplier has not been established. Co-op XP remains disabled. Proposed fixes and additions are listed in the [roadmap](ROADMAP.md).
