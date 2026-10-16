# Release checks — 1.0.35

- The Mega level-up check verifies that every Mega form can use its regular level-up moves.
- The Black 2 Redux overlay check passes with the original learnset archive layout.
- All 13 configured tests pass, including the in-game menu sound cues; the Windows x64 emulator builds successfully.
- The provided RAM dump confirms the Mega form and level changed together. A RAM dump cannot replay the original CPU execution, so the final level-up scenario still needs live in-game confirmation.

To test in game, use a Mega Pokémon close to leveling up, Mega Evolve it during battle, then earn enough experience to cross the level threshold. Confirm the game stays open, the Pokémon gains a level, and its regular level-up moves are offered. Open an added menu and check the movement, confirm, and back sounds; the setting is under Settings.
