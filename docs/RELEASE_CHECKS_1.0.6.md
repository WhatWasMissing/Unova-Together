# Release checks 1.0.6

- `python tools/test_companion_and_soaring.py` passed. This compiles the production interaction header and checks 5,000 combinations (25 nature values × five friendship bands × ten actions × four variations), all 649 species, four distinct replies per action and band, visual cue and motion values, running reactions, HP/fainted cases, and read-only input data.
- `python tools/test_overworld_companion.py` passed. It compiles the production follower-facing eligibility and A-button gate, including NPC dialogue forwarding, the deliberate R+A chord, held/released input, expiry, D-pad, menus and battle/field gates.
- `cmake --build melonDS-source-1.1/build --target melonDS --parallel 4` passed for the Windows x64 Release build.
- The release package is checked for ZIP integrity, matching executable bytes, valid portable controls, inclusion of the companion guide and release notes, and exclusion of ROMs, firmware, saves and diagnostic captures.
- The published-format single-file launcher passed an isolated startup self-test after extracting its own embedded runtime. It opened the shared mod library, listed Black 2 and Pokémon X, exposed the companion setting, and reported success with no ROM configured.

Interaction checks use synthetic party values and production code; no live ROM field session or two-computer gameplay playtest was run. They do not modify a user's save.
