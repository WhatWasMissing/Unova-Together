# Companions and flight preview

Enable **Companion interactions** and/or **Latias / Latios flight preview** in **Launcher → Settings → Experimental**, then restart the game. Both are off by default. Open **Unova → Pokémon**.

## Your companion

Choose **My companion** to talk to, pet, or play with the first Pokémon in your party. You can also click its following sprite while standing still in the field. Keep followers enabled in **Unova → Settings**.

Its responses reflect its current health and friendship. A tired or fainted Pokémon asks to rest. Eggs cannot be interacted with. Talking, petting, and playing animate the follower without changing friendship, HP, items, or your save. Changing the lead Pokémon clears the previous companion’s reaction.

**Greet teammate’s Pokémon** is also available on this page. It needs a connected presence relay and a nearby teammate; it uses the existing greeting system.

Press **B** to return to the Pokémon tab.

## Soar

Choose **Soar preview** for a pixel-art flight preview above a snapshot of your current surroundings. Use the D-pad to steer and L/R to switch between Latias and Latios. B returns to the Pokémon tab. This is a menu preview, not a recreation of ORAS’s 3D Hoenn or flight through Unova’s actual maps. The preview does not move your character.

If HM02 is in your bag and your game is idle, **Fly destinations** opens the original Pokémon party screen. Select an eligible Pokémon, then **Fly**, to choose from the game’s own destinations. Existing story requirements and native Fly restrictions still apply. The mount selected in the preview does not grant you that Pokémon or bypass travel unlocks.

## Verification

Focused compiled tests cover health/friendship reactions, eggs and invalid records, all 649 species, read-only input, both mounts, and bounded steering. The copied-ROM UI fixture also checks reactions, busy/battle rejection, unchanged party/bag data, menu navigation and visual output. Completed Fly travel remains subject to the existing native Fly playtest limitation.
