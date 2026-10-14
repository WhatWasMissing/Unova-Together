# Mega Evolution test

Unova Together 1.0.15 adds a first experimental Mega Evolution profile for the English Pokémon Black 2 Redux v1.4.1 ROM (`IREO`). It is a custom Mega Serperior form, not an official form or a feature of the original game. Other ROMs are not supported by this overlay.

To test it, use a Serperior holding Serperiorite (reserved item slot 113). If you need a stone, open the emulator's Multiplayer panel while standing idle in the overworld with C-Gear wireless off, select **Debug**, choose **Serperiorite**, then select **Grant Mega Stone (debug)**. Save normally in the game if you want to keep the item.

In battle, open **Fight** and press **L + R together** while Serperior is available at the move-selection screen. Mega Serperior keeps Grass/Dragon typing and Contrary, with base stats `80 / 100 / 115 / 133 / 102 / 105` in the Redux record's order. Each trainer can Mega Evolve once per battle. The transformation is held in battle data; it does not change the saved party record and ends with the battle.

The local native transformation, form data, sprite conversion, ROM overlay, battle cleanup and paired LAN message path have focused Debug and Release regressions. The ENet regression exercises two LAN peers, and deterministic paired-call tests cover the sender and receiver handlers. A live two-emulator battle has not yet verified co-op animation, failed-peer recovery or natural battle teardown. Test solo first, then try co-op and report whether both clients show the same form and return to base Serperior after battle.

No ROM, save, firmware or RAM capture is included. Keep independent saves and save normally before testing. Mega Serperior's custom artwork was supplied for this project; its creator and public reuse terms have not been confirmed.
