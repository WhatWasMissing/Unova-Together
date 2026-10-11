# Redux 1.4.1 XP compensation calculation

Read-only analysis of the local Redux Complete ROM. The examples use Challenge mode and the Medium Slow growth curve, which the ROM assigns to all three Unova starters. All six exact growth tables matched ROM file a/0/1/7. Challenge targets use the documented displayed caps, including difficulty level shifts; raw trainer records are retained in the CSV.

**These are XP-budget equivalents, not predicted playthrough levels.** The baseline is a Pokémon starting at level 5 and earning exactly enough XP to reach each boss ace. The multiplier applies to newly earned XP; starting XP is unchanged. Generation V award feedback and encounter choices are not simulated.

| Checkpoint | Baseline | 1.5×, no XP lost | 2×, no XP lost | 2×, 50% XP lost | 2×, 75% XP lost |
|---|---:|---:|---:|---:|---:|
| Cheren | 14 | 15 | 16 | 14 | 11 |
| Roxie | 21 | 23 | 25 | 21 | 17 |
| Burgh | 29 | 32 | 35 | 29 | 23 |
| Elesa | 38 | 42 | 46 | 38 | 30 |
| Clay | 45 | 50 | 55 | 45 | 36 |
| Skyla | 55 | 62 | 68 | 55 | 44 |
| Drayden | 64 | 72 | 79 | 64 | 51 |
| Marlon | 68 | 77 | 84 | 68 | 54 |
| Ghetsis | 72 | 81 | 89 | 72 | 57 |
| Elite Four | 78 | 88 | 97 | 78 | 62 |
| Iris | 79 | 89 | 98 | 79 | 63 |

## Selected 1.65× multiplier

Replaces approximately 39.39% missing XP by budget: 1 - 1/1.65. At 25% lost it supplies 123.75% of baseline earned XP; at 50% lost it supplies 82.5%. Native awards round down per Pokémon and preserve the 100,000 XP award limit. The cumulative model below does not simulate per-award rounding or the cap.

| Checkpoint | Baseline | 1.65×, no XP lost | 1.65×, 25% XP lost | 1.65×, 50% XP lost |
|---|---:|---:|---:|---:|
| Cheren | 14 | 16 | 14 | 13 |
| Roxie | 21 | 24 | 22 | 19 |
| Burgh | 29 | 33 | 30 | 27 |
| Elesa | 38 | 44 | 40 | 35 |
| Clay | 45 | 52 | 48 | 42 |
| Skyla | 55 | 64 | 58 | 51 |
| Drayden | 64 | 74 | 68 | 60 |
| Marlon | 68 | 79 | 72 | 64 |
| Ghetsis | 72 | 84 | 77 | 67 |
| Elite Four | 78 | 91 | 83 | 73 |
| Iris | 79 | 92 | 84 | 74 |

Challenge caps used: 14, 21, 29, 38, 45, 55, 64, 68, 72, 78 and 79. The online guide lists Normal Drayden at 60; the local ROM record 159 contains a level-61 ace. Normal sensitivity rows use 61.

For exact XP-budget replacement, required multiplier = 1 / (1 - fraction of baseline XP lost).

| XP lost to co-op | Required solo multiplier |
|---:|---:|
| 10.0% | 1.11× |
| 20.0% | 1.25× |
| 25.0% | 1.33× |
| 33.3% | 1.50× |
| 50.0% | 2.00× |
| 60.0% | 2.50× |
| 75.0% | 4.00× |
| 80.0% | 5.00× |
| 90.0% | 10.00× |

A 2× multiplier with 25% of XP lost delivers 150% of the baseline earned XP budget. With 50% lost it delivers 100%; with 75% lost, only 50%.

A blanket multiplier cannot exactly compensate every playstyle. If only a few bosses are played together, 2× risks substantial overleveling. If most XP-producing trainer battles are shared, 2× may leave a large deficit. A finite compensation credit earned from co-op victories and spent on subsequent solo XP would track the actual missing rewards more closely.

Sources: local read-only ROM trainer and personal records; [PKHeX exact growth tables](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/PKM/Util/Experience.cs); [Redux 1.4.1 trainer guide](https://smilingzero.github.io/BlazeBlack2ReduxWiki/genTrainerChange/).

All six growth groups, Normal and Challenge trainer records, and multiplier/loss sensitivity combinations are in level-curves.csv.
