# Mega Evolution test

Unova Together 1.0.20 includes Mega Serperior for the English Pokémon Black 2 Redux Complete v1.4.1 ROM (`IREO`). It is a custom form for this mod. No other Mega forms are enabled in this build.

Give Serperior Serperiorite (reserved item slot 113). If you need the stone, open the emulator's Multiplayer panel while standing idle in the overworld with C-Gear wireless off, select **Debug**, choose **Serperiorite**, then select **Grant Mega Stone (debug)**. Save normally if you want to keep the item.

In battle, open **Fight** and press **L + R together** at the move-selection screen. Mega Serperior keeps Grass/Dragon typing and Contrary. The change lasts through battle and does not alter the saved party record.

The crash reported after choosing a move has been fixed. The user's Mega-armed battle state passes in both JIT and interpreter replay; the active battle copies agree, expected stats and HP are checked, and battle teardown completes. The public Mega regression suite passes, including the ROM-overlay test. A live two-player Mega battle still needs a test.

No ROM, save, firmware or RAM capture is included. Use an independent backup and save normally before trying a new feature. The supplied custom Serperior sprite remains local until its public reuse terms are confirmed.
