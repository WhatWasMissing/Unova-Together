# Black / White PK5 structure

User-supplied reference, added 2026-10-20. Original reference: [Project Pokémon](https://projectpokemon.org/home/docs/gen-5/bw-save-structure-r60/), credited in the existing reference index to **evandixon**. Original research and wording remain credited to their contributors; this is not original Unova Together research. No additional license is asserted for this contributed reference.

This historical reference includes inherited Generation 4 material: Platinum-only form statements, Pal Park locations, and some save-location statements are not a verified Black 2 / White 2 or Redux specification. Consult the game-specific save layout and decomp before applying offsets. The listed character-image filenames are references; those images were not supplied.

Attachment SHA-256: `488a93607887c1b5e2b606e1ec5915ed08f67422b3efe013fe7bb6b0c78b0dda`. The supplied text below is preserved apart from surrounding blank lines and line-ending normalization.

## Supplied reference

```text
Pokémon in the games Pokémon Black and White are stored in a 136 byte or 220 byte structures. All unencrypted values are stored in little-endian format. The game encrypts the data when it is stored in the save file. Party Pokémon have additional values to hold current battle stats and conditions. The information below describes the Pokémon data format.
Checksum / Block Shuffling / Encryption

Same as before, see Pokemon NDS Structure.
Unencrypted bytes
Offset 	Contents
0x00-0x03 	Personality value (Also known as the PID)
0x04-0x05 	Unused
0x06-0x07 	Checksum
Encrypted bytes
Block A
Offset 	Contents
0x08-0x09 	National Pokédex ID
0x0A-0x0B 	Held Item
0x0C-0x0D 	OT ID
0x0E-0x0F 	OT Secret ID
0x10-0x13 	Experience points
0x14 	Friendship (Steps to Hatch if an egg)
0x15 	Ability
0x16 	Markings
0x17 	Original Language
0x18 	HP Effort Value
0x19 	Attack Effort Value
0x1A 	Defense Effort Value
0x1B 	Speed Effort Value
0x1C 	SP Attack Effort Value
0x1D 	SP Defense Effort Value
0x1E 	Cool Contest Value
0x1F 	Beauty Contest Value
0x20 	Cute Contest Value
0x21 	Smart Contest Value
0x22 	Tough Contest Value
0x23 	Sheen Contest Value
0x24-0x25 	Sinnoh Ribbon Set 1
0x26-0x27 	Unova Ribbon Set
Block B
Offset 	Contents
0x28-0x29 	Move 1 ID
0x2A-0x2B 	Move 2 ID
0x2C-0x2D 	Move 3 ID
0x2E-0x2F 	Move 4 ID
0x30 	Move 1 Current PP
0x31 	Move 2 Current PP
0x32 	Move 3 Current PP
0x33 	Move 4 Current PP
0x34-0x37 	Move PP Ups
0x38-0x3B 	Bits 0-29 - Individual Values

HP ( [0-31] << 0 )
Attack ( [0-31] << 5 )
Defense ( [0-31] << 10 )
Speed ( [0-31] << 15 )
SP Attack ( [0-31] << 20 )
SP Defense ( [0-31] << 25 )
Bit 30 - IsEgg Flag
Bit 31 - IsNicknamed Flag
0x3C-0x3D 	Hoenn Ribbon Set 1
0x3E-0x3F 	Hoenn Ribbon Set 2
0x40 	Bit 0 - Fateful Encounter Flag
Bit 1 - Female
Bit 2 - Genderless
Bit 3-7 - Alternate Forms
0x41 	Nature
0x42 	0x1 - HasDreamWorldAbility flag,
0x2 - N's pokemon flag
0x43 	Unused
0x44-0x47 	Unknown
Block C
Offset 	Contents
0x48-0x5D 	Nickname
0x5E 	Unknown
0x5F 	Origin game
0x60-0x61 	Sinnoh Ribbon Set 3
0x62-0x63 	Sinnoh Ribbon Set 4
0x64-0x67 	Unused
Block D
Offset 	Contents
0x68-0x77 	OT Name
0x78-0x7A 	Date Egg Received
0x7B-0x7D 	Date Met
0x7E-0x7F 	Egg Location (Diamond/Pearl)
0x80-0x81 	Met At Location (Diamond/Pearl)
0x82 	Pokérus
0x83 	Poké Ball
0x84 	Bit 0-6 - Met At Level
Bit 7 - Female OT Gender
0x85 	Encounter Type
0x86 	Unused
0x87 	Unused
Battle Stats

The battle stats are encrypted in the same manner, however the seed is not the checksum, it is the PID, and the bytes are not shuffled.
Encrypted Bytes
Offset 	Contents
0x88 	Bits 0-2 - Asleep (0-7 rounds)
Bit 3 - Poisoned
Bit 4 - Burned
Bit 5 - Frozen
Bit 6 - Paralyzed
Bit 7 - Toxic
0x89 	Unknown - Flags - Max Value 0xF0
0x8A-0x8B 	Unknown
0x8C 	Level
0x8D 	Capsule Index (Seals)
0x8E-0x8F 	Current HP
0x90-0x91 	Max HP
0x92-0x93 	Attack
0x94-0x95 	Defense
0x96-0x97 	Speed
0x98-0x99 	Special Attack
0x9A-0x9B 	Special Defense
0x9C-0xD3 	Mail message- fill-in-the-blank choices + OT name
0xD4-0xDB 	Unused
Original Language
Value 	Language
0x1 	日本語 (Japan)
0x2 	English (US/UK/AU)
0x3 	Français (France/Québec)
0x4 	Italiano (Italy)
0x5 	Deutsch (Germany)
0x7 	Español (Spain/Latin Americas)
0x8 	한국어 (South Korea)
Markings
Bit 	Marking
0x01 	Circle
0x02 	Triangle
0x04 	Square
0x08 	Heart
0x10 	Star
0x20 	Diamond
Alternate Forms

Alternate forms are stored at offset 0x40 of the Pokemon structure. Each form follows the pattern of index << 3 where index starts at zero for the main form.
Unown's Forms
Bit 	Form 	Bit 	Form 	Bit 	Form 	Bit 	Form
0x00 	A 	0x38 	H 	0x70 	O 	0xA8 	V
0x08 	B 	0x40 	I 	0x78 	P 	0xB0 	W
0x10 	C 	0x48 	J 	0x80 	Q 	0xB8 	X
0x18 	D 	0x50 	K 	0x88 	R 	0xC0 	Y
0x20 	E 	0x58 	L 	0x90 	S 	0xC8 	Z
0x28 	F 	0x60 	M 	0x98 	T 	0xD0 	 !
0x30 	G 	0x68 	N 	0xA0 	U 	0xD8 	 ?
Deoxy's Forms
Bit 	Form
0x00 	Normal
0x08 	Attack
0x10 	Defense
0x18 	Speed
Burmy's & Wormadam's Forms
Bit 	Form
0x00 	Plant
0x08 	Sandy
0x10 	Trash
Shellos' & Gastrodon's Forms
Bit 	Form
0x00 	West
0x08 	East
Rotom's Forms

Rotom's alternate forms will only be displayed in Pokemon Platinum. Rotom may be traded between Diamond, Pearl, and Platinum without losing the alternate form.
Bit 	Form
0x00 	Normal
0x08 	Heat
0x10 	Wash
0x18 	Frost
0x20 	Fan
0x28 	Cut
Giratina's Forms

Giratina's Origin form will only be displayed in Pokemon Platinum.
Bit 	Form
0x00 	Altered
0x08 	Origin
Shaymin's Forms

Shaymin's Sky form will only be displayed in Pokemon Platinum.
Bit 	Form
0x00 	Land
0x08 	Sky
Arceus' Forms
Bit 	Form 	Bit 	Form 	Bit 	Form
0x00 	Normal 	0x30 	Insect 	0x60 	Zap
0x08 	Fist 	0x38 	Spooky 	0x68 	Mind
0x10 	Sky 	0x40 	Iron 	0x70 	Icicle
0x18 	Toxic 	0x48 	Flame 	0x78 	Draco
0x20 	Earth 	0x50 	Splash 	0x80 	Dread
0x28 	Stone 	0x58 	Meadow 	0x4C 	Curse
Nickname and OT Name

Since generation 5, the nickname and OT name are encoded with Unicode instead of a game-specific character map. However, there are some exceptions, which are listed below. Note that unlike generation 4, the last two bytes of are always 0xFFFF, even if there already was a terminator before. Exceptions to this rule are the Roaming Pokémon, Starters, and various gifts and in game trades, in which the OT name does not have the escape sequence.

There are no normally occurring trash bytes for generation 5 Pokémon, but the Poké Transfer will keep existing trash bytes (except the last two) even if the Pokémon evolves in generation 5. In the advent of a different language Pokémon evolving in another language game, characters not overwritten are left as trash bytes.
Characters that can be replaced in Unicode

In the game, those are half-width versions of existing Unicode characters used in non-japanese versions with long name support.
Original character 	Unicode index 	Replace with 	Unicode index
⑽ 	0x247d 	☂ 	0x2602
⑻ 	0x247b 	☁ 	0x2601
⑺ 	0x247a 	☀ 	0x2600
⑹ 	0x2479 	♪ 	0x266a
⑸ 	0x2478 	◇ 	0x25c7
⑷ 	0x2477 	△ 	0x25b3
⑶ 	0x2476 	□ 	0x25a1
⑵ 	0x2475 	○ 	0x25cb
⑴ 	0x2474 	◎ 	0x25ce
⑳ 	0x2473 	★ 	0x2605
⑲ 	0x2472 	♦ 	0x2666
⑱ 	0x2471 	♥ 	0x2665
⑰ 	0x2470 	♣ 	0x2663
⑯ 	0x246f 	♠ 	0x2660
⑮ 	0x246e 	♀ 	0x2640
⑭ 	0x246d 	♂ 	0x2642
⑬ 	0x246c 	… 	0x2026
⑨ 	0x2468 	÷ 	0xf7
⑧ 	0x2467 	× 	0xd7
Pokémon exclusive characters

Some game-exclusive characters do not exist in Unicode and should be replaced with bitmaps.
Original character 	Unicode index 	Pokémon exclusive
$ 	0x24 	Gen5 unicode 36.png
⇒ 	0x21d2 	Gen5 unicode 8658.png
⇔ 	0x21d4 	Gen5 unicode 8660.png
∀ 	0x2200 	Gen5 unicode 8704.png
∃ 	0x2203 	Gen5 unicode 8707.png
∧ 	0x2227 	Gen5 unicode 8743.png
∨ 	0x2228 	Gen5 unicode 8744.png
① 	0x2460 	Gen5 unicode 9312.png
② 	0x2461 	Gen5 unicode 8744.png
③ 	0x2462 	Gen5 unicode 9314.png
④ 	0x2463 	Gen5 unicode 8658.png
⑤ 	0x2464 	Gen5 unicode 8660.png
⑥ 	0x2465 	Gen5 unicode 8704.png
⑦ 	0x2466 	Gen5 unicode 8707.png
⑩ 	0x2469 	Gen5 unicode 9321.png
⑪ 	0x246a 	Gen5 unicode 9322.png
⑫ 	0x246b 	Gen5 unicode 9323.png
⑾ 	0x247e 	Gen5 unicode 9312.png
⑿ 	0x247f 	Gen5 unicode 9343.png
⒀ 	0x2480 	Gen5 unicode 9344.png
⒁ 	0x2481 	Gen5 unicode 9345.png
⒂ 	0x2482 	Gen5 unicode 9346.png
⒃ 	0x2483 	Gen5 unicode 9347.png
⒄ 	0x2484 	Gen5 unicode 9348.png
⒅ 	0x2485 	Gen5 unicode 9349.png
⒆ 	0x2486 	Gen5 unicode 9350.png
⒇ 	0x2487 	Gen5 unicode 9351.png
￢ 	0xffe2 	Gen5 unicode 9314.png
Encounter Types

Encounter types are not used in Black and White. Pokeshifted Pokemon keep their Encounter Type hex.
Value 	Country
0x0 	Pal Park, Egg, Hatched, Special Event
0x2 	Tall Grass
0x4 	Dialga/Palkia In-Game Event
0x5 	Cave, Hall of Origin
0x7 	Surfing, Fishing
0x9 	Building
0xA 	Great Marsh (Safari Zone)
0xC 	Starter, Fossil, Gift (Eevee)
Ribbons

Diamond, Pearl, and Platinum store the ribbon information as bitfields in 1-byte words. Given below are the bytewise representation of the ribbon bitfields.
Sinnoh Ribbon Set 1
Bit 	Ribbon
0x24 & 0x01 	Sinnoh Champ Ribbon
0x24 & 0x02 	Ability Ribbon
0x24 & 0x04 	Great Ability Ribbon
0x24 & 0x08 	Double Ability Ribbon
0x24 & 0x10 	Multi Ability Ribbon
0x24 & 0x20 	Pair Ability Ribbon
0x24 & 0x40 	World Ability Ribbon
0x24 & 0x80 	Alert Ribbon
0x25 & 0x01 	Shock Ribbon
0x25 & 0x02 	Downcast Ribbon
0x25 & 0x04 	Careless Ribbon
0x25 & 0x08 	Relax Ribbon
0x25 & 0x10 	Snooze Ribbon
0x25 & 0x20 	Smile Ribbon
0x25 & 0x40 	Gorgeous Ribbon
0x25 & 0x80 	Royal Ribbon
Unova Ribbon Set
Bit 	Ribbon
0x26 & 0x01 	Gorgeous Royal Ribbon
0x26 & 0x02 	Footprint Ribbon
0x26 & 0x04 	Record Ribbon
0x26 & 0x08 	Event Ribbon
0x26 & 0x10 	Legend Ribbon
0x26 & 0x20 	World Champion Ribbon
0x26 & 0x40 	Birthday Ribbon
0x26 & 0x80 	Special Ribbon
0x27 & 0x01 	Souvenir Ribbon
0x27 & 0x02 	Wishing Ribbon
0x27 & 0x04 	Classic Ribbon
0x27 & 0x08 	Premier Ribbon
Sinnoh Ribbon Set 3
Bit 	Ribbon
0x60 & 0x01 	Cool Ribbon
0x60 & 0x02 	Cool Ribbon Great
0x60 & 0x04 	Cool Ribbon Ultra
0x60 & 0x08 	Cool Ribbon Master
0x60 & 0x10 	Beauty Ribbon
0x60 & 0x20 	Beauty Ribbon Great
0x60 & 0x40 	Beauty Ribbon Ultra
0x60 & 0x80 	Beauty Ribbon Master
0x61 & 0x01 	Cute Ribbon
0x61 & 0x02 	Cute Ribbon Great
0x61 & 0x04 	Cute Ribbon Ultra
0x61 & 0x08 	Cute Ribbon Master
0x61 & 0x10 	Smart Ribbon
0x61 & 0x20 	Smart Ribbon Great
0x61 & 0x40 	Smart Ribbon Ultra
0x61 & 0x80 	Smart Ribbon Master
Sinnoh Ribbon Set 4
Bit 	Ribbon
0x62 & 0x01 	Tough Ribbon
0x62 & 0x02 	Tough Ribbon Great
0x62 & 0x04 	Tough Ribbon Ultra
0x62 & 0x08 	Tough Ribbon Master
Hoenn Ribbon Set 1
Bit 	Ribbon
0x3C & 0x01 	Cool Ribbon
0x3C & 0x02 	Cool Ribbon Super
0x3C & 0x04 	Cool Ribbon Hyper
0x3C & 0x08 	Cool Ribbon Master
0x3C & 0x10 	Beauty Ribbon
0x3C & 0x20 	Beauty Ribbon Super
0x3C & 0x40 	Beauty Ribbon Hyper
0x3C & 0x80 	Beauty Ribbon Master
0x3D & 0x01 	Cute Ribbon
0x3D & 0x02 	Cute Ribbon Super
0x3D & 0x04 	Cute Ribbon Hyper
0x3D & 0x08 	Cute Ribbon Master
0x3D & 0x10 	Smart Ribbon
0x3D & 0x20 	Smart Ribbon Super
0x3D & 0x40 	Smart Ribbon Hyper
0x3D & 0x80 	Smart Ribbon Master
Hoenn Ribbon Set 2
Bit 	Ribbon
0x3E & 0x01 	Tough Ribbon
0x3E & 0x02 	Tough Ribbon Super
0x3E & 0x04 	Tough Ribbon Hyper
0x3E & 0x08 	Tough Ribbon Master
0x3E & 0x10 	Champion Ribbon
0x3E & 0x20 	Winning Ribbon
0x3E & 0x40 	Victory Ribbon
0x3E & 0x80 	Artist Ribbon
0x3F & 0x01 	Effort Ribbon
0x3F & 0x02 	Battle Champion Ribbon
0x3F & 0x04 	Regional Champion Ribbon
0x3F & 0x08 	National Champion Ribbon
0x3F & 0x10 	Country Ribbon
0x3F & 0x20 	National Ribbon
0x3F & 0x40 	Earth Ribbon
0x3F & 0x80 	World Ribbon
Save File Location

The party Pokémon are stored in the save file beginning at offset 0x18e08.

In the first small save block, the first Daycare Pokémon is located at 0x0141C, and the second is located at 0x01508. In the second small block, the first Daycare Pokémon is located at 0x4141C, and the second is located at 0x41508.

In the first small save block, the Pal Park Pokémon are stored beginning at 0x0BA28. In the second small save block, the Pal Park Pokémon are stored beginning at 0x4BA28.

Each party and Daycare Pokémon is 220 bytes in size.

The PC storage Pokémon are stored in the save file from Box 1 to Box 24. The offset starts at 0x24400. Each Pokémon stored in the PC is 136 bytes in size.
```
