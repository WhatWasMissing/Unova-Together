# Black / White save layout notes

User-supplied reference, added 2026-10-20. Original reference: [BW Save Structure](https://projectpokemon.org/home/docs/gen-5/bw-save-structure-r73/), credited to **evandixon** and the original research contributors. The pasted notes are attributed research, not original Unova Together work.

This is the original Black/White table. It is a different layout from Black 2/White 2. Offsets and labels have not been validated against Blaze Black 2 Redux Complete v1.4.1. Start/end offsets are inclusive. “Mirror” identifies the checksum copy listed in the source.

The source describes a primary save beginning at `0x0` and a backup beginning at `0x24000`.

## Main save blocks

| Start | End | Size | Checksum | Mirror | Description |
| --- | --- | --- | --- | --- | --- |
| `00000` | `003DF` | `3E0` | `003E2` | `23F00` | Box Names |
| `00400` | `013EF` | `FF0` | `013F2` | `23F02` | Box 1 |
| `01400` | `023EF` | `FF0` | `023F2` | `23F04` | Box 2 |
| `02400` | `033EF` | `FF0` | `033F2` | `23F06` | Box 3 |
| `03400` | `043EF` | `FF0` | `043F2` | `23F08` | Box 4 |
| `04400` | `053EF` | `FF0` | `053F2` | `23F0A` | Box 5 |
| `05400` | `063EF` | `FF0` | `063F2` | `23F0C` | Box 6 |
| `06400` | `073EF` | `FF0` | `073F2` | `23F0E` | Box 7 |
| `07400` | `083EF` | `FF0` | `083F2` | `23F10` | Box 8 |
| `08400` | `093EF` | `FF0` | `093F2` | `23F12` | Box 9 |
| `09400` | `0A3EF` | `FF0` | `0A3F2` | `23F14` | Box 10 |
| `0A400` | `0B3EF` | `FF0` | `0B3F2` | `23F16` | Box 11 |
| `0B400` | `0C3EF` | `FF0` | `0C3F2` | `23F18` | Box 12 |
| `0C400` | `0D3EF` | `FF0` | `0D3F2` | `23F1A` | Box 13 |
| `0D400` | `0E3EF` | `FF0` | `0E3F2` | `23F1C` | Box 14 |
| `0E400` | `0F3EF` | `FF0` | `0F3F2` | `23F1E` | Box 15 |
| `0F400` | `103EF` | `FF0` | `103F2` | `23F20` | Box 16 |
| `10400` | `113EF` | `FF0` | `113F2` | `23F22` | Box 17 |
| `11400` | `123EF` | `FF0` | `123F2` | `23F24` | Box 18 |
| `12400` | `133EF` | `FF0` | `133F2` | `23F26` | Box 19 |
| `13400` | `143EF` | `FF0` | `143F2` | `23F28` | Box 20 |
| `14400` | `153EF` | `FF0` | `153F2` | `23F2A` | Box 21 |
| `15400` | `163EF` | `FF0` | `163F2` | `23F2C` | Box 22 |
| `16400` | `173EF` | `FF0` | `173F2` | `23F2E` | Box 23 |
| `17400` | `183EF` | `FF0` | `183F2` | `23F30` | Box 24 |
| `18400` | `18DBF` | `9C0` | `18DC2` | `23F32` | Inventory |
| `18E00` | `19333` | `534` | `19336` | `23F34` | Party Pokémon |
| `19400` | `19467` | `68` | `19469` | `23F36` | Trainer Data |
| `19500` | `1959B` | `9C` | `1959E` | `23F38` | ??? |
| `19600` | `1A937` | `1338` | `1A93A` | `23F3A` | ??? |
| `1AA00` | `1B1C3` | `7C4` | `1B1C6` | `23F3C` | ??? |
| `1B200` | `1BF53` | `D54` | `1BF56` | `23F3E` | ??? |
| `1C000` | `1C02B` | `2C` | `1C02E` | `23F40` | ??? |
| `1C100` | `1C757` | `658` | `1C75A` | `23F42` | ??? Gym badge data |
| `1C800` | `1D293` | `A94` | `1D296` | `23F44` | ??? |
| `1D300` | `1D4AB` | `1AC` | `1D4AE` | `23F46` | ??? |
| `1D500` | `1D8EB` | `3EC` | `1D8EE` | `23F48` | ??? |
| `1D900` | `1D95B` | `5C` | `1D95E` | `23F4A` | ??? |
| `1DA00` | `1DBDF` | `1E0` | `1DBE2` | `23F4C` | ??? |
| `1DC00` | `1DCA7` | `A8` | `1DCAA` | `23F4E` | ??? |
| `1DD00` | `1E15F` | `460` | `1E162` | `23F50` | ??? |
| `1E200` | `1F5FF` | `1400` | `1F602` | `23F52` | ??? |
| `1F700` | `1F9A3` | `2A4` | `1F9A6` | `23F54` | ??? |
| `1FA00` | `1FCDB` | `2DC` | `1FCDE` | `23F56` | ??? |
| `1FD00` | `2004B` | `34C` | `2004E` | `23F58` | ??? |
| `20100` | `204EB` | `3EC` | `204EE` | `23F5A` | ??? |
| `20500` | `205F7` | `F8` | `205FA` | `23F5C` | ??? |
| `20600` | `208FB` | `2FC` | `208FE` | `23F5E` | ??? |
| `20900` | `20993` | `94` | `20996` | `23F60` | ??? |
| `20A00` | `20D5B` | `35C` | `20D5E` | `23F62` | ??? |
| `20E00` | `20FCB` | `1CC` | `20FCE` | `23F64` | ??? |
| `21000` | `21167` | `168` | `2116A` | `23F66` | ??? |
| `21200` | `212EB` | `EC` | `212EE` | `23F68` | ??? |
| `21300` | `214AF` | `1B0` | `214B2` | `23F6A` | ??? |
| `21500` | `2151B` | `1C` | `2151E` | `23F6C` | ??? |
| `21600` | `21AD3` | `4D4` | `21AD6` | `23F6E` | ??? |
| `21B00` | `21B33` | `34` | `21B36` | `23F70` | ??? |
| `21C00` | `21C3B` | `3C` | `21C3E` | `23F72` | ??? |
| `21D00` | `21EAB` | `1AC` | `21EAE` | `23F74` | ??? |
| `21F00` | `22A8F` | `B90` | `22A92` | `23F76` | ??? |
| `22B00` | `22B9B` | `9C` | `22B9E` | `23F78` | ??? |
| `22C00` | `2344F` | `850` | `23452` | `23F7A` | Entralink Forest Pokémon data |
| `23500` | `23527` | `28` | `2352A` | `23F7C` | ??? |
| `23600` | `23883` | `284` | `23886` | `23F7E` | ??? |
| `23900` | `2390F` | `10` | `23912` | `23F80` | ??? |
| `23A00` | `23A5B` | `5C` | `23A5E` | `23F82` | ??? |
| `23B00` | `23C6B` | `16C` | `23C6E` | `23F84` | ??? |
| `23D00` | `23D3F` | `40` | `23D42` | `23F86` | ??? |
| `23E00` | `23EFB` | `FC` | `23EFE` | `23F88` | ??? |
| `23F00` | `23F8B` | `8C` | `23F9A` | — | Checksum Block |

The supplied note says section sizes can vary based on stored data, which had been observed at least for trainer data. This remains a historical note, not a confirmed property of the Redux save.

## Gym badge obtained date

The supplied note says badge dates are stored at `0x1C704` and `0x407004`: byte 1 is years after 2000, byte 2 is month, byte 3 is day, and byte 4 is zero (its meaning was unknown to the author).

`0x407004` lies outside a 512 KiB save and is retained here exactly as supplied, not as a safe write location. The fourth byte and both offsets need confirmation against the relevant game build before use.
