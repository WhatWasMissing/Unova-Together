# Companion interactions

In the updated launcher source/local build, **Companion interactions** is under **Settings → Following Pokémon** and is on by default. A previously saved off choice remains off. Changes apply on the next game launch. Following Pokémon already default on; show or hide them in **Unova → Settings**. Walk at least one tile so your lead Pokémon appears behind you.

The published v1.0.6 downloads contain the earlier launcher: enable **Companion interactions** in **Settings → Experimental**, then restart the game. The new default and settings location will be included when the updated launcher is packaged in a subsequent release.

Stop and face the follower, then hold **R** and press **A** to open its interaction menu. You can also click or tap its sprite. A by itself always goes to the game, so you can advance an NPC text box while facing your follower.

Choose **Talk**, **Pet**, **Play**, **Praise**, **Tell a story**, **Ask about today**, **Sit together**, **Show a trick**, **Tell a joke** or **Sing together**. Use the D-pad and A, or tap an option. In a reply, A or B returns to the actions; X closes the menu. Each action has four rotating lines across five friendship bands. The lead Pokémon's nickname, health, nature and current friendship shape its response. Nature appears through small changes in tone and behavior instead of being named.

The 1.0.7-dev build adds area, DS time/season, loaded-ROM Pokémon types and neutral recent-battle context. Visit counts are separate for each Pokémon/action for the current session; they do not create permanent memories in the save. Weather and battle-result-specific dialogue remain future work. Gen 5 nature is now read from its independently stored record field.

Reactions appear over the follower as a question or exclamation mark, heart, star, musical note or ellipsis. Depending on the action, friendship and personality, the Pokémon may peek, sway, hop, spin or run a short loop around you.

Development Settings offers **Reduced follower motion**, preserving sprites and symbols while disabling decorative bobbing, leaning and reaction movement. See [development evidence](DEVELOPMENT_POLISH_2026-10-13.md).

Interactions are read-only: they do not change HP, friendship, items or save data. They are unavailable during battles, movement, co-op preparation and native menus. Idle follower sprites bob subtly while their feet stay anchored.

Normal native Fly remains available. The old soaring preview is no longer included; the historical filename is retained for existing guide links.
