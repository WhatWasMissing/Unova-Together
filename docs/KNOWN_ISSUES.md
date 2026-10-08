# Unova Together beta 0.3.5 — known issues

- **Online UDP is experimental.** It has been checked locally, but reliable battle completion between players on different networks has not yet been confirmed. Use Tailscale if it fails.
- **No public server is supplied.** The UDP option needs a server provided by your group. Player sharing also needs a reachable server; joining a UDP room does not configure that automatically.
- **Slow or unstable connections can interrupt battles.** A battle may stall or end unexpectedly. Changing the connection method cannot guarantee a fix.
- **Teammate rendering can flicker.** Camera sample gaps and map transitions can interrupt the displayed sprite. This release does not claim that all camera/rendering issues are fixed.
- **Intermittent menu-dependent disappearance remains unconfirmed.** A beta report recovered before RAM capture. Player-object replacement and battle-status recovery were fixed and tested, but that exact symptom has not been reproduced.
- **Different starters:** verified rival script families can agree on the host's enemy variant. All 33 named Redux rival records pass native startup checks; not every different-starter story encounter has been played through to save/reload.
- **Launcher updates need GitHub access and disk space.** Downloads install beside the previous build. Save normally before switching. An unavailable check does not prevent offline play. Older update folders are retained for recovery.
- **Wait before retrying a cancelled trade.** Let both players return to Ready before sending another request. Rapid retries can be rejected.
- **An immediate second co-op battle can fail to reconnect.** A repeated local two-core test completed the first battle but lost a partner during the next attempt; both returned to the field and cleared their battle status. If this happens, let recovery finish and recreate the native LAN session before retrying.
- **Native cleanup can time out after completion.** A final local check required guest checkpoint recovery, discarding that guest battle progress. Check both games return normally before saving or starting another encounter.
- **Fast-forward can prevent wireless pairing.** Turn it off before connecting and throughout shared battles.
- **A disconnected battle cannot reliably resume.** Return to the field and create a new LAN session. Recovery may discard that battle's progress.
- **Co-op experience gain is disabled to prevent desynchronisation.** Do not expect shared trainer battles to award experience in this beta.
- **Some trainer encounters still need testing.** Not every special event or Redux fight has been played through. Check each player's story progress and save separately after battles.
- **Single-Pokémon opponents are duplicated for co-op.** When a trainer normally has one Pokémon, a matching copy fills the second enemy position.
- **Some networks block UDP.** The helper may fail even when other internet apps work. Use Tailscale as the fallback.
- **Python is required for the UDP helper.** Python/tkinter and the dependency installer are separate from the bundled emulator. This release is for Windows x64; it is not an Android emulator build.

Version 0.3.4 improves movement animation, menu presence and battle AI setup, and adds a C-Gear wireless warning. A crash involving late window/input events was fixed. The reported first-ever ROM-load crash could not be reproduced, so please report it if it recurs. Networking and experience limitations above remain.

Version 0.3.4 also retains the private position anchor through unresolved menu transitions, publishing it only after validated menu ownership.
