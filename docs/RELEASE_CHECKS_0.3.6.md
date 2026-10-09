# Battle presence recovery — 9 October 2026

A confirmed non-battle dispatcher can return to an owned field/map matrix while the player actor is missing or ambiguous. The old presence state required a resolved actor before clearing battle status, leaving the saved pre-battle position advertised. Recovery now accepts three consecutive matching, verified field-map samples with a confirmed non-battle dispatcher. Unknown process states, battle intros and native menus do not qualify.

Retained actor samples now merge the current process flags and are explicitly marked as unowned positions. The player table no longer claims “Other map” when the local position is unresolved.

Verification passed: compiled transition/ownership regressions, supplied before/battle/after/menu RAM captures, post-battle capture recovery, and 12 presence-relay checks. The exact latest two-player incident has not been captured or reproduced yet; the screenshot alone cannot prove which pointer/state was stale.

For a live check, use the corrected executable on both devices, enter and finish a normal battle, then verify both players return to Ready and Same map. Repeat with one player changing maps while the other is fighting. If status remains incorrect, capture RAM snapshots on both devices before moving indoors or restarting.

No saves, ROM data, battle outcomes or story flags are changed by this correction.
