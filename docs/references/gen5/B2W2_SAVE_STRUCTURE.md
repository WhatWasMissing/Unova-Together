# Black 2 / White 2 save layout notes

User-supplied reference, added 2026-10-20. Original reference: [B2W2 Save Structure](https://projectpokemon.org/home/docs/gen-5/b2w2-save-structure-r72/), credited to **evandixon** and the original research contributors. The pasted notes are attributed research, not original Unova Together work.

This is a historical reference. Offsets and labels have not been validated against Blaze Black 2 Redux Complete v1.4.1. Start and end offsets are inclusive. “Mirror” is the checksum mirror location; it is not a second copy of the entire block.

## Main save blocks

| Start | End | Checksum | Mirror | Description |
| --- | --- | --- | --- | --- |
| `00000` | `003DF` | `003E2` | `25F00` | Box Names |
| `00400` | `013EF` | `013F2` | `25F02` | Box 1 |
| `01400` | `023EF` | `023F2` | `25F04` | Box 2 |
| `02400` | `033EF` | `033F2` | `25F06` | Box 3 |
| `03400` | `043EF` | `043F2` | `25F08` | Box 4 |
| `04400` | `053EF` | `053F2` | `25F0A` | Box 5 |
| `05400` | `063EF` | `063F2` | `25F0C` | Box 6 |
| `06400` | `073EF` | `073F2` | `25F0E` | Box 7 |
| `07400` | `083EF` | `083F2` | `25F10` | Box 8 |
| `08400` | `093EF` | `093F2` | `25F12` | Box 9 |
| `09400` | `0A3EF` | `0A3F2` | `25F14` | Box 10 |
| `0A400` | `0B3EF` | `0B3F2` | `25F16` | Box 11 |
| `0B400` | `0C3EF` | `0C3F2` | `25F18` | Box 12 |
| `0C400` | `0D3EF` | `0D3F2` | `25F1A` | Box 13 |
| `0D400` | `0E3EF` | `0E3F2` | `25F1C` | Box 14 |
| `0E400` | `0F3EF` | `0F3F2` | `25F1E` | Box 15 |
| `0F400` | `103EF` | `103F2` | `25F20` | Box 16 |
| `10400` | `113EF` | `113F2` | `25F22` | Box 17 |
| `11400` | `123EF` | `123F2` | `25F24` | Box 18 |
| `12400` | `133EF` | `133F2` | `25F26` | Box 19 |
| `13400` | `143EF` | `143F2` | `25F28` | Box 20 |
| `14400` | `153EF` | `153F2` | `25F2A` | Box 21 |
| `15400` | `163EF` | `163F2` | `25F2C` | Box 22 |
| `16400` | `173EF` | `173F2` | `25F2E` | Box 23 |
| `17400` | `183EF` | `183F2` | `25F30` | Box 24 |
| `18400` | `18DEB` | `18DEE` | `25F32` | Inventory |
| `18E00` | `19333` | `19336` | `25F34` | Party Pokémon |
| `19400` | `194AF` | `194B2` | `25F36` | Trainer Data |
| `19500` | `195A7` | `195AA` | `25F38` | Trainer Position |
| `19600` | `1A937` | `1A93A` | `25F3A` | Unity Tower and survey data |
| `1AA00` | `1B1C3` | `1B1C6` | `25F3C` | Pal Pad Player Data (30d) |
| `1B200` | `1BF53` | `1BF56` | `25F3E` | Pal Pad Friend Data |
| `1C000` | `1C093` | `1C096` | `25F40` | C-Gear |
| `1C100` | `1C757` | `1C75A` | `25F42` | Card Signature Block & ???? |
| `1C800` | `1D293` | `1D296` | `25F44` | Mystery Gift |
| `1D300` | `1D4AB` | `1D4AE` | `25F46` | Dream World Stuff (Catalog) |
| `1D500` | `1D8EB` | `1D8EE` | `25F48` | Chatter |
| `1D900` | `1D95B` | `1D95E` | `25F4A` | Adventure data; original note links to [B2W2 General ROM Info](http://projectpokemon.org/forums/showthread.php?24589-B2W2-General-ROM-Info&p=167300&viewfull=1#post167300) |
| `1DA00` | `1DBDF` | `1DBE2` | `25F4C` | Trainer Card Records |
| `1DC00` | `1DCA7` | `1DCAA` | `25F4E` | (blank in source) |
| `1DD00` | `1E15F` | `1E162` | `25F50` | (40d) |
| `1E200` | `1F5FF` | `1F602` | `25F52` | (blank in source) |
| `1F700` | `1F9A3` | `1F9A6` | `25F54` | Downloaded Musical flags and references |
| `1FA00` | `1FADF` | `1FAE2` | `25F56` | Fused Reshiram/Zekrom Storage |
| `1FB00` | `1FE4B` | `1FE4E` | `25F58` | (blank in source) |
| `1FF00` | `203DF` | `203E2` | `25F5A` | Const Data Block and Event Flag Block (0x35E is the split) |
| `20400` | `204F7` | `204FA` | `25F5C` | (blank in source) |
| `20500` | `207FB` | `207FE` | `25F5E` | Tournament Block |
| `20800` | `20893` | `20896` | `25F60` | (blank in source) |
| `20900` | `20C5B` | `20C5E` | `25F62` | Battle Box Block |
| `20D00` | `20ED3` | `20ED6` | `25F64` | Daycare Block (50d) |
| `20F00` | `210DF` | `201E2` | `25F66` | Strength Boulder Status Block |
| `21100` | `211EF` | `211F2` | `25F68` | Badge Flags, Money, Trainer Sayings |
| `21200` | `213B3` | `213B6` | `25F6A` | Entralink (Level & Powers etc) |
| `21400` | `218DB` | `218DE` | `25F6C` | Pokédex |
| `21900` | `21933` | `21936` | `25F6E` | Swarm and other overworld info (2C swarm; 2D Repel steps; 2E Repel type) |
| `21A00` | `21A3B` | `21A3E` | `25F70` | (blank in source) |
| `21B00` | `21CAB` | `21CAE` | `25F72` | (blank in source) |
| `21D00` | `2288F` | `22892` | `25F74` | (blank in source) |
| `22900` | `229AB` | `229AE` | `25F76` | Online Records |
| `22A00` | `2324F` | `23252` | `25F78` | Area NPC data - encrypted (60d) |
| `23300` | `23583` | `23586` | `25F7A` | (blank in source) |
| `23600` | `2360F` | `23612` | `25F7C` | (blank in source) |
| `23700` | `237A7` | `237AA` | `25F7E` | (blank in source) |
| `23800` | `2396B` | `2396E` | `25F80` | (blank in source) |
| `23A00` | `23A7F` | `23A82` | `25F82` | (blank in source) |
| `23B00` | `23BFB` | `23BFE` | `25F84` | Hollow/Rival Block |
| `23C00` | `252A7` | `252AA` | `25F86` | Join Avenue Block |
| `25300` | `25797` | `2579A` | `25F88` | Medal data |
| `25800` | `2585F` | `25862` | `25F8A` | Key-related data |
| `25900` | `259FB` | `259FE` | `25F8C` | (70d) |
| `25A00` | `25DE3` | `25DE6` | `25F8E` | (blank in source) |
| `25E00` | `25EEF` | `25EF2` | `25F90` | (blank in source) |
| `25F00` | `25F93` | `25FA2` | — | Checksum Block (73d) |

## Download / extra content

| Start | End | Checksum | Mirror | Description |
| --- | --- | --- | --- | --- |
| `4C000` | `4D913` | `~` | `~` | Battle Video (Native) |
| `4DA00` | `4F313` | `~` | `~` | Battle Video (1st Download) |
| `4F400` | `50D13` | `~` | `~` | Battle Video (2nd Download) |
| `50E00` | `52713` | `~` | `~` | Battle Video (3rd Download) |
| `52800` | `54DFF` | `54E02` | `54F00` | C-Gear Background |
| `55800` | `6D3FF` | `6D342` | `6D500` | Musical Download (narc download) |
| `6D800` | `73A03` | `73A06` | `73B00` | Pokédex Skin |
| `74000` | `7555B` | `7555E` | `75600` | Hall of Fame (Main); extra checksum at `75612` |
| `75800` | `76D5B` | `76D5E` | `76E00` | Hall of Fame (Backup); extra checksum at `76E12` |
| `77000` | `77511` | `77512` | — | Unknown |
| `7A000` | `7B213` | `7B216` | `7B300` | PWT Download 1; extra checksum at `7B312` |
| `7B400` | `7C613` | `7C616` | `7C700` | PWT Download 2; extra checksum at `7C712` |
| `7C800` | `7DA13` | `7DA16` | `7DB00` | PWT Download 3; extra checksum at `7DB12` |
| `7E000` | `7EA1F` | — | — | Memory Link Data (2 blocks of 0x400 length, extra data afterwards) |
| `7F000` | — | — | — | CRGF - GameFreak CRC table - Nintendo 3DS Link data |

## Nintendo 3DS Link data

| Start | End | Checksum | Mirror | Description |
| --- | --- | --- | --- | --- |
| `7F010` | `7F013` | `~` | `~` | Unknown; note suggests value may prevent receiving a Pokémon again |
| `7F014` | `7F093` | `7F094` | `~` | Nintendo 3DS Link data slots? 4 bytes each; can be item/Pokémon |

## Source anomalies to verify

The supplied Strength Boulder checksum is `201E2`, which falls outside the listed block and does not follow the neighboring checksum sequence. It is retained verbatim and is likely a typo; do not use it for save writes until checked against a known-good implementation. The musical download checksum/mirror values also look unusual relative to the region bounds and remain as supplied. Several descriptions and checksums are explicitly uncertain in the source.
