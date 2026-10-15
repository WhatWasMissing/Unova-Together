# Unova Together 1.0.17 — Mega Serperior battle test

This release makes the experimental, battle-only Mega Serperior available for
the supported English Pokémon Black 2 Redux v1.4.1 ROM (`IREO`). This is a
custom form for this mod, not an official form or a feature of the original
game. Other ROMs are not supported by the Mega overlay.

Use a Serperior holding Serperiorite (reserved item slot 113). In battle, open
**Fight** and press **L + R together** at move selection. The change is
temporary: the tested ChangeForm handler updated both active battle copies,
while the saved party record remained unchanged. Each trainer may Mega Evolve
once per battle. If you need the stone, use the Multiplayer panel's **Debug**
tab while idle in the overworld with C-Gear wireless off, then save normally.

The fresh-state regression replay confirmed form 0→1, Contrary (ability 126),
and battle stats changing from `[78, 109, 95, 109, 129]` to
`[103, 131, 128, 120, 151]`. Max HP remained 147 and the saved party record
was unchanged. The client and server battle copies can be sampled at different
points in a turn, so ordinary damage may have reached only one copy at that
instant. The regression also exercised battle-end cleanup; it does not claim
a natural knockout or win was played through.

Install **Unova Together 1.0.17** and give all co-op players the same build.
Save normally before trying the feature. A live two-emulator Mega battle and
its animation or failed-peer recovery still need playtesting. See the
[Mega Evolution guide](docs/MEGA_EVOLUTION.md) and
[release checks](docs/RELEASE_CHECKS_1.0.17.md).

The supplied custom Mega Serperior sprite is included. Its original artist and
public reuse terms remain unconfirmed. No ROMs, saves, firmware, or RAM
captures are included. The other draft Mega forms remain disabled in the
public game and are under local development.
