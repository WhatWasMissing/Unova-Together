# Solo XP compensation

Unova Together **1.0.5 and 1.0.6** multiply newly awarded solo battle XP by **1.25×** on supported English Black 2 and Redux profiles. No launcher setting is needed. Existing accumulated XP is unchanged. **Co-op XP remains disabled.**

The multiplier runs after native level scaling, XP sharing, traded Pokémon bonuses and Lucky Egg calculations, before reward text/application. Fractional XP rounds down per award. The native 100,000 XP award limit, flags and EV rewards are preserved. Cleared co-op reward records remain zero.

At 1.25×, the replacement XP budget balances approximately **20% of the original earned XP being missed** in co-op. This is a budget calculation, not a playthrough prediction. Encounter choices and level-dependent XP feedback affect actual levels. The launcher's Redux Challenge progression calculator uses the same 1.25× rate.

## Compatibility and validation

The hook checks cartridge identity, instruction mode, RAM layout, caller, reward-builder/return fingerprints, offsets and reward bounds. Unsupported layouts retain native behavior. The dynamic POP-to-PC return boundary is handled by both interpreter and JIT dispatch.

Current 1.25× production-dispatch checks passed against genuine Redux and English Black 2 overlays: rounding, award cap, unchanged flags/EV bytes, zero co-op awards and refusal of invalid contexts. These checks do not establish a new end-to-end JIT or full-playthrough test.

## Historical battle and save/reload evidence

Release **1.0.2 used 1.65×**, before 1.0.5 reduced it to 1.25×. Its documented solo Cheren test awarded the badge, saved 5,951 Servine XP / level 20 and reloaded those records in a fresh emulator. Independent PKHeX parsing checked the save and Pokémon checksums. The fixture used boosted combat stats and the interpreter; it does not establish normal Challenge difficulty.

That historical test verifies the recorded 1.0.2 result. It is **not** a fresh battle/save/reload validation of the current 1.25× release. Failed earlier saving attempts remain documented separately. See [measured battle results](XP_COMPENSATION_BATTLE_TEST.md), [1.0.5 notes](../patchnotes/RELEASE_NOTES_1.0.5.md) and [known limits](KNOWN_ISSUES.md).
