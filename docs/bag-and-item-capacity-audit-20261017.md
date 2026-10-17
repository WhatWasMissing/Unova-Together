# Bag and item capacity investigation

## Findings from the Black 2 / Black 2 and White 2 decompilation

The decompilation defines the bag as a fixed save block, not as ROM-backed storage. In `include/save/bag.h`, its pockets have 310 general-item slots, 83 key-item slots, 109 TM/HM slots, 48 medicine slots, and 64 berry slots. Each slot is four bytes. The saved `BagSave` is 0x9EC bytes, including a 21-word free-space bitset. `src/system/save_table.c` places this block in the game's fixed 0x26000-byte save area, and `src/gfl/savedata.c` computes subsequent block offsets from each block's size. Increasing a pocket array therefore changes the save layout; unused cartridge ROM bytes alone do not provide more persistent bag storage and a naive struct-size change would misread existing saves.

The separate item-ID ceiling is 638 (`ITEM_LAST = 638` in `data/constants/items.txt`). The Redux ROM confirms 639 item records in `a/0/2/4`, covering IDs 0 through 638. The existing Mega patch uses unused item records within that range. The free-space flags can represent IDs 0 through 671 because there are 672 bits, but the decomp's item-pocket lookup, item-menu arrays, `ITEM_LAST` checks, item metadata, and icon mapping are currently sized for 639 records. The extra bits are not, by themselves, usable item definitions.

## Safe expansion paths

There are two different limits to address:

- Increasing how many held items fit in a pocket requires a save-format migration and coordinated changes to bag allocation, copy, sort, free-space, and menu code. It must keep old saves readable and remain within the fixed save area.
- Adding new item IDs can potentially use the remaining free-space bits through ID 671, but only after extending the item records, item-pocket lookup, item-name and description messages, icon lookup table, menus, shop bounds, and every `ITEM_LAST` validation that consumes those IDs. The current runtime overlay does not yet do that work.

The 32 IDs above the current limit are a potential item-ID extension, not 32 extra bag slots. The bag already has 614 saved slots (310 general, 83 key, 109 TM/HM, 48 medicine, 64 berries); adding item IDs does not make a pocket hold more objects. The free-space bitmap has 672 bits because it is rounded to 21 32-bit words, while `DUMMY_ITEMS` and `UNHOLDABLE_ITEMS` in `src/system/pml_item.c` are each 20 words. Both those tables and `sItemPockets[ITEM_LAST + 1]` in `src/system/myitem_savedata.c` must be extended together before IDs 639–671 are safe to query.

Item IDs are indexed by more than the bag. `PML_ItemReadDataFile` bounds-checks against `ITEM_LAST` before reading `ARCID_ITEMINFO`; `GetItemGraphicsDatID` indexes `ITEM_GRAPHICS_CHARS_AND_PALETTES`; name and description helpers use the item ID as the message index. A real ID extension therefore needs 33 item-data members, matching icon mappings and icon archive files, 33 name/description message entries, pocket/sort classifications, and every executable-side `ITEM_LAST` check updated. Appending archive members alone would still turn the new IDs into `ITEM_NONE` in many game paths.

## Evidence checked

- `include/save/bag.h`: pocket capacities, save layout, and free-space bitset.
- `src/system/myitem_savedata.c`: pocket selection, item insertion, item lookup, and free-space bit indexing.
- `src/system/pml_item.c`: item records, icons, and names reject IDs above `ITEM_LAST`.
- `src/system/save_table.c` and `src/gfl/savedata.c`: fixed save area and dynamically computed save-block offsets.
- `data/constants/items.txt`: `ITEM_LAST = 638`.
- Read-only inspection of the Redux v1.4.1 ROM: `a/0/2/4` has 639 item records.

## Implementation decision

No pocket capacity or item-ID limit was changed in this pass. Growing pocket arrays changes `BagSave` from its known 0x9EC-byte save-block layout and shifts subsequent save blocks; unused ROM padding is not safe persistent storage. IDs 639–671 are plausible to add without changing that layout, but they require coordinated code, metadata, icon, and message changes. Changing only the archive or constants would make existing bag paths index beyond fixed tables. The current Mega Stones use existing item records, so the 33-bit gap is not needed for the supported roster. Keep an ID extension as a separate, fully tested decomp change rather than shipping a partially expanded item format.

- `include/pml/item.h` and `src/system/pml_item.c`: item-data, icon, and item-message lookups are bounded by `ITEM_LAST`.
- `src/system/pml_item.c`: `DUMMY_ITEMS` and `UNHOLDABLE_ITEMS` each have 20 32-bit words (640 addressable bits).
- `src/system/myitem_savedata.c`: `sItemPockets` has `ITEM_LAST + 1` entries and item loops use the same ceiling.

## Mega Stone shop fix verification (17 October 2026)

The rebuilt native Mega Evolution regression passed against the original Blaze Black 2 Redux Complete v1.4.1 ROM. It verified that all 46 Mega Stones appear across the 74 shop lists, every list remains at or below the native 45-entry limit, every one of the 20 Pokémon Center marts has Mega Stone stock, and the existing shop entries remain intact. The game-data regression also checked unique stone entries and valid item names, icons, and prices. The intended behavior is a shared selection across the mart network; individual marts carry a subset because the game's native shop list is fixed at 45 entries.

The release emulator passed an offscreen startup check with Mega Evolution enabled: it rendered a visible frame, read the relocated archive, and exited successfully. The Windows and source archives passed ZIP integrity and private-game-file checks. Launcher bundle tests (6), updater tests (13), and the production wireless-input bounds check passed. The shop data was verified from the ROM; a live in-game shopping walkthrough was not performed for this release.
