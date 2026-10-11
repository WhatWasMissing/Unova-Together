# Solo XP compensation

Unova Together now multiplies newly awarded solo battle XP by **1.65×** on the
supported English Black 2 and Redux profiles. This is a native emulator change;
the launcher needs no additional setting. Existing accumulated XP is untouched.

The multiplier runs after native level scaling, XP sharing, traded Pokémon
bonuses and Lucky Egg calculations, before reward text and XP application.
Fractional XP rounds down for each Pokémon. The native 100,000 XP award limit
remains in force. Flags and EV rewards are preserved. Co-op still suppresses
XP: its cleared reward records remain zero after multiplication.

The hook verifies the cartridge identity, instruction mode, RAM layout, caller,
reward builder, epilogue, output offset and reward bounds. Unknown layouts are
left alone. The builder returns using a dynamic POP to PC, which terminates the
JIT block; the same return boundary is handled by the interpreter and JIT.

At 1.65×, the replacement budget balances approximately **39.39% XP lost** to
co-op. This is a budget calculation, not a prediction of an actual playthrough.
See the selected-multiplier table in
`research/xp-balance-20261011/REPORT.md` for Redux Challenge examples.

Validation: compiled production-dispatch checks against genuine private Redux
and English Black 2 overlays cover multiplier rounding, the award cap, unchanged
flags/EV bytes, zeroed co-op rewards, and refusal of foreign or invalid contexts.
Existing compiled story return and shutdown tests also pass. These checks do
initially did not constitute an end-to-end solo battle and save/reload XP test.

A subsequent genuine solo Cheren battle completed on both the normal and boosted
builds: 498 XP normally, 807 XP with the multiplier, with the badge awarded and
actual party XP verified in RAM. See `docs/XP_COMPENSATION_BATTLE_TEST.md`.
Save/reload remains unverified because the automated save input did not write the
post-battle result to disk. The battle evidence used the interpreter.

The native menu smoke attempts using `Redux.ml1` and `courtyard-check.ml1`
produced no report and were stopped; they are not counted as passed. Logs are
retained under `test-fixtures/coop-launcher/xp-165-native-menu*`.

This change is included in the 1.0.2 release candidate. Previous 1.0.1
release assets are unchanged.
The previous local emulator is backed up at
`builds/backups/xp-165-20261011/melonDS.exe`.
