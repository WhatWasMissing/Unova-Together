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

**Save/reload is not verified.** The automated post-battle save inputs did not
write the results to disk: both valid party save banks retained the original
5,144 XP and no badge. This is recorded as `normalSaveVerified: false`, separate
from `battleCompleted: true`. Failed/timed-out earlier attempts are retained and
are not counted as completed battle or save validations. This test used the
interpreter; an end-to-end JIT battle is not established by this result.

Local XP build SHA-256:
`4913724318054b9805cde22e371598fe0fb81c9ffb5a6928de92e4bf5abb8604`.

Unboosted 1.0.1 SHA-256:
`2beff45f7fcbf22fa47e6aa709312db8204d18f4057d4108e8aa0e5c69220b8f`.
