# Unova Together 1.0.18 — Mega Serperior test

This launcher update keeps Mega Serperior as the only playable Mega Evolution
in the public build. It supports the English Pokémon Black 2 Redux v1.4.1 ROM
(`IREO`) only. Mega Serperior is a custom form for this mod, not an official
form or a feature of the original game.

Give Serperior the Serperiorite reserved item (item slot 113). In battle, open
**Fight** and press **L + R together** at move selection. Mega Evolution uses
the native ChangeForm command, applies to both battle copies, and restores the
saved party record when the battle ends. Each trainer may Mega Evolve once per
battle. If you need the stone, use **Multiplayer → Debug → Serperiorite → Grant
Mega Stone** while idle in the overworld with C-Gear wireless off, then save
normally.

The matching-overlay 1.0.17 battle replay verified form 0→1, Contrary (126),
both battle copies, unchanged max HP and an unchanged saved party record. The
1.0.18 Release checks pass 8/8, and the exact Redux ROM cold-boots with a visible
advancing frame and reads the relocated Mega archive. The one available newer
checkpoint was captured with a local-draft executable, so it is not a valid
cross-build battle replay; the runtime rejected it safely and preserved the
saved party. Please start a fresh battle after updating and test Serperior
there. The replay uses an injected battle-end transition, not a natural
knockout or victory.

Install **Unova Together 1.0.18** and give all co-op players the same build.
Save normally before testing. A live two-emulator Mega battle and failed-peer
recovery still need playtesting. Other Mega profiles remain disabled in the
public executable; local drafts are experimental and not part of this playable
build. The custom Mega Serperior art was supplied for the project, but
its original artist and public reuse terms remain unconfirmed. No ROM, save,
firmware or RAM capture is included.

See the [Mega Evolution guide](docs/MEGA_EVOLUTION.md) and
[release checks](docs/RELEASE_CHECKS_1.0.18.md).
