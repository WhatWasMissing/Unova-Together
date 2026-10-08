# Unova Together beta 0.3.3 — known issues

- **Online UDP is experimental.** It has been checked locally, but reliable battle completion between players on different networks has not yet been confirmed. Use Tailscale if it fails.
- **No public server is supplied.** The UDP option needs a server provided by your group. Player sharing also needs a reachable server; joining a UDP room does not configure that automatically.
- **Slow or unstable connections can interrupt battles.** A battle may stall or end unexpectedly. Changing the connection method cannot guarantee a fix.
- **Teammate rendering can flicker.** Camera sample gaps and map transitions can interrupt the displayed sprite. This release does not claim that all camera/rendering issues are fixed.
- **Wait before retrying a cancelled trade.** Let both players return to Ready before sending another request. Rapid retries can be rejected.
- **Fast-forward can prevent wireless pairing.** Turn it off before connecting and throughout shared battles.
- **A disconnected battle cannot reliably resume.** Return to the field and create a new LAN session. Recovery may discard that battle's progress.
- **Co-op experience gain is disabled to prevent desynchronisation.** Do not expect shared trainer battles to award experience in this beta.
- **Some trainer encounters still need testing.** Not every special event or Redux fight has been played through. Check each player's story progress and save separately after battles.
- **Single-Pokémon opponents are duplicated for co-op.** When a trainer normally has one Pokémon, a matching copy fills the second enemy position.
- **Some networks block UDP.** The helper may fail even when other internet apps work. Use Tailscale as the fallback.
- **Python is required for the UDP helper.** Python/tkinter and the dependency installer are separate from the bundled emulator. This release is for Windows x64; it is not an Android emulator build.

Version 0.3.3 improves movement animation, menu presence and battle AI setup, and adds a C-Gear wireless warning. A crash involving late window/input events was fixed. The reported first-ever ROM-load crash could not be reproduced, so please report it if it recurs. Networking and experience limitations above remain.
