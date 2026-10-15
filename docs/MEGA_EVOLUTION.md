# Mega Evolution test guide

Unova Together 1.0.24 adds twelve experimental Mega forms for the supported English Pokémon Black 2 Redux Complete v1.4.1 profile. Give a Pokémon its matching stone, then press **L + R together** while choosing a move in battle. The Mega form is temporary and returns to normal after the battle.

To grant a stone for testing, open the emulator's **Multiplayer** panel while idle in the overworld with C-Gear wireless off. Select **Debug**, choose the matching stone, and select **Grant Mega Stone (debug)**. Save normally before testing.

| Pokémon | Stone | Mega ability/effect | Mega BST |
|---|---|---|---:|
| Serperior | Serperiorite | Adaptability | 635 |
| Arcanine* | Arcaninite | Intimidate, Flash Fire, or Justified (keeps the Pokémon's existing ability slot) | 655 |
| Aggron | Aggronite | Filter | 610 |
| Altaria | Altarianite | Pixilate effect (Normal moves become Fairy-type; the DS ability slot uses Natural Cure for compatibility) | 620 |
| Banette | Banettite | Prankster | 575 |
| Gallade | Galladite | Inner Focus | 618 |
| Heracross | Heracronite | Skill Link | 600 |
| Latios | Latiosite | Levitate | 700 |
| Manectric | Manectite | Intimidate | 575 |
| Sableye | Sablenite | Magic Bounce | 550 |
| Salamence | Salamencite | Aerilate effect (Normal moves become Flying-type; the DS ability slot uses Moxie for compatibility) | 700 |
| Scizor | Scizorite | Technician | 600 |

*Arcanine and Serperior are custom forms for this project; the other Mega designs follow their official Mega concepts. BST is the sum of the six stats in the Mega profile. Redux-specific base stats are retained when the published Mega stat changes are applied.

The Serperior battle flow, form restoration, party-menu behavior, sprite assets, and roster setup have automated checks. The other forms still need live battle tests, including their in-battle abilities and sprites. Linked two-player Mega battles also need live playtesting. Do not treat an automated pass as proof that every form works in a live game.

The custom art is user-provided fan artwork for a free, non-commercial mod. No ROM, save, firmware, or RAM capture is included. The source package includes the modified source code and upstream license notices.
