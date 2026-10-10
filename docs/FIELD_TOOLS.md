# Encounter finder and move relearning

Open **Players → Tools → Pokémon** for both tools. They work offline and use the loaded
English Black 2 ROM, including compatible Redux changes.

## Encounter finder

Choose a season with the season button. Browse with the page arrows and select
a Pokémon to see its encounter method. Percentages are the chance of that
species/form within that method, not the chance of encountering it per step.
Grass, dark grass, rustling grass, surfing, rippling water, fishing and fishing
spots are included. These are ordinary ROM encounter tables: gifts, scripted
legendary encounters, Hidden Grottos and special encounter systems are excluded.
An invalid level range in the ROM displays **Lv?** instead of inventing a level.
Caught/seen tracking is not included in this version.

## Relearn moves

Choose a party Pokémon, choose a move, choose its replacement slot, then confirm
**Learn move**. Relearning is free. Cancel is selected by default.
Only the current species/form's level-up moves at or below its current level are
offered. Already-known moves and eggs are excluded. This does not teach arbitrary
TM, tutor, egg or previous-evolution moves.

The new move receives its ROM-defined base PP with no PP Ups. The other moves,
identity, IVs, EVs and remaining party members are preserved. Save normally after
relearning. No `.sav` file is edited directly. Battles, pending item/Pokémon
trades, unsupported profiles and changed party records block the write.

## Field HMs

This build lets a non-egg party Pokémon perform field HMs without
learning them. Keep the HM in your bag. Cut, Surf, Strength, Waterfall and Dive
use the game's normal obstacle interaction; Fly is offered by the original
Pokémon party menu. The original event checks, destinations and animations
remain in charge. Battle moves, PP, Pokémon records and saves are not rewritten.

This supports the reviewed English Black 2 field routines, including Redux
Complete v1.4.1. Unknown routines fail back to their original behavior. Flash,
Dig, Teleport and other non-HM field moves are unchanged.

Fly is added through a move slot which the native field-action filter would
otherwise omit. If that Pokémon already knows Fly, its normal Fly entry is
used. If all four moves already have native field actions, use another party
Pokémon; this version does not replace an existing field action.

## Beta limitations

Native Fly destination selection and focused HM checks passed. Full obstacle traversal, completed Fly travel and save/reload after relearning still need gameplay testing. Back up your save.
