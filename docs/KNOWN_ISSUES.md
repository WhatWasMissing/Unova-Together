# Unova Together beta 0.3.1 — known issues

- **Online UDP is experimental.** It has been checked locally, but reliable battle completion between players on different networks has not yet been confirmed. Use Tailscale if it fails.
- **No public server is supplied.** The UDP option needs a server provided by your group. Player sharing also needs a reachable server; joining a UDP room does not configure that automatically.
- **Slow or unstable connections can interrupt battles.** A battle may stall or end unexpectedly. Changing the connection method cannot guarantee a fix.
- **Fast-forward can prevent wireless pairing.** Turn it off before connecting and throughout shared battles.
- **A disconnected battle cannot reliably resume.** Return to the field and create a new LAN session. Recovery may discard that battle's progress.
- **Co-op experience gain is disabled to prevent desynchronisation.** Do not expect shared trainer battles to award experience in this beta.
- **Some trainer encounters still need testing.** Not every special event or Redux fight has been played through. Check each player's story progress and save separately after battles.
- **Single-Pokémon opponents are duplicated for co-op.** When a trainer normally has one Pokémon, a matching copy fills the second enemy position.
- **Some networks block UDP.** The helper may fail even when other internet apps work. Use Tailscale as the fallback.
- **Python is required for the UDP helper.** Python/tkinter and the dependency installer are separate from the bundled emulator. This release is for Windows x64; it is not an Android emulator build.

Version 0.3.1 improves the instructions and release presentation. It does not change gameplay or fix the issues listed above. See [the player guide](PLAYER_GUIDE.md) for recovery and reporting steps.
