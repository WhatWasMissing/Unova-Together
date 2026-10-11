# Solo XP battle check — 2026-10-11

Completed genuine solo Cheren battles from disposable copies of the same private
save, booted normally without savestates or fabricated results. The fixture has
boosted combat stats to make testing practical; initial species, level, XP and
story progression were identical. Ordinary DS button/touch inputs selected moves.
Automatic NPC co-op was disabled.

| Build | Initial Servine XP | Final Servine XP | XP gained | Final level | Cheren badge |
|---|---:|---:|---:|---:|---|
| Published 1.0.1, normal XP | 5,144 | 5,642 | 498 | 20 | Awarded |
| Local 1.65× solo XP build | 5,144 | 5,951 | 807 | 20 | Awarded |

The measured total increase was **62.05%**. The nominal multiplier applies to
each native award, after level scaling. The boosted Pokémon reached level 20
earlier; Gen V scales subsequent awards using the recipient's current level.
Together with per-award rounding, this explains why the entire battle's measured
XP total need not be exactly 65% higher. Production-dispatch multiplier and
rounding checks independently passed against both supported ROMs.

Actual party XP was decoded from validated, checksum-checked native RAM records
after returning to the field. Badge ownership was read with the ROM-backed
getter. The reserve Elekid stayed at zero XP in both runs. Source save SHA-256
remained `3bc7b6457b884e6c246a17f38a4fd5bdc9f231c3df3782790e7838c96207b871`.

Evidence:

- `test-fixtures/coop-launcher/xp-baseline-solo-battle-02/summary.json`
- `test-fixtures/coop-launcher/xp-165-solo-battle-03/summary.json`
- Each folder retains before/after RAM captures, input scripts, logs and frames.

**The original comparison did not verify save/reload.** Its automated post-battle save inputs did not
write the results to disk: both valid party save banks retained the original
5,144 XP and no badge. This is recorded as `normalSaveVerified: false`, separate
from `battleCompleted: true`. Failed/timed-out earlier attempts are retained and
are not counted as completed battle or save validations. This test used the
interpreter; an end-to-end JIT battle is not established by this result.

Local XP build SHA-256:
`4913724318054b9805cde22e371598fe0fb81c9ffb5a6928de92e4bf5abb8604`.

Unboosted 1.0.1 SHA-256:
`2beff45f7fcbf22fa47e6aa709312db8204d18f4057d4108e8aa0e5c69220b8f`.

## Successful 1.0.2 save/reload follow-up — 11 October 2026

The published 1.0.2 emulator completed another genuine solo Cheren battle from
the same disposable starting save. Servine again gained **807 XP**, reaching
**5,951 XP / level 20**. The reserve Elekid stayed at zero XP. The game awarded
the Cheren badge. This fixture used boosted combat stats, the interpreter and a
240 FPS target; it does not establish normal Challenge difficulty or JIT behavior.
Ordinary input selected Wrap when Leaf Tornado ran out of PP.

The native save UI then wrote the result to disk. Both checksum-validated party
save banks contained the real result and badge. The independent **PKHeX.Core
26.8.26.0** parser confirmed valid save-block and Pokémon checksums, the same XP,
level, moves and badge. It did not modify or export the save. A deliberately
corrupted private save was independently rejected with exit status 1.

A **fresh emulator process**, booted normally from a copy of that actual `.sav`
without a savestate, reloaded Servine at 5,951 XP / level 20 and the Cheren badge.
Party identity and moves matched the disk evidence. **Normal save/reload is now
verified for this 1.0.2 solo battle.** The source starting save remained unchanged.

The first follow-up attempt reached "Saving..." but its fixed cutoff stopped the
emulator before completion. It remains a failed attempt. The runner now waits
for validated disk data and lets the complete save transaction settle, advances
post-victory dialogue and turns/walks away before opening Save. Supervised battle
input corrections may still be needed at learning prompts or exhausted PP.

Evidence:

- `test-fixtures/coop-launcher/xp-102-save-reload-02/summary.json`
- `test-fixtures/release-1.0.2/pkhex-saved-victory.json`
- `test-fixtures/coop-launcher/xp-102-normal-reload-01/summary.json`
- Failed attempt: `test-fixtures/coop-launcher/xp-102-save-reload-01/summary.json`

Published emulator SHA-256:
`7f9ddca58a2b84da36dc078c8f51f3916f0b83e3a2c27fec09a18b3f35268310`.

Saved victory SHA-256:
`52aeb1961ebd44531449114c2d04d8f2e2d8354484942498c240619edd798343`.

PKHeX source commit: `66ef5983a5d349efa2dd615f2926a1b1ee97306e`.
See `GEN5_SAVE_INSPECTION.md` for the read-only tool workflow. This closes the
specific solo XP persistence gap; co-op persistence, JIT battles and a complete
playthrough remain separate verification tasks.
