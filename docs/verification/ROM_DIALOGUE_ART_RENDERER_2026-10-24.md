# Actor dialogue-art verification — 2026-10-24

**IMPLEMENTED AND VERIFIED for the exact desktop ROM/runtime combination below.** The portrait, nameplate, frame, and native dialogue text render together in a real actor conversation. The example is a private derived ROM.

## Identities and provenance

- Source branch: MVQ1303/romhack-tools-dialogue-art, based on commit 3cbad2c294e2c597910a9cf980e41305231b5b58.
- Patcher SHA-256: f9d88dbaed851adfef59357a0bf9cac3d9d032aa2e40308ef4992eb9310aabbf.
- C helper SHA-256: daf42ac9363d1c1a49d34d287f526a5ffbdefeb9ed4511bc47f2cf54b49ae116.
- Supported user ROM: Redux Complete v1.4.1, IREO, SHA-256 353fb0cf82c3e4eddfc8986efa8910b00eb1c4d6f106c220abef59d69d3a520a. Original overlay 36 CRC32: A7CF9125.
- Tested emulator: Unova Together 2.0.33 package, melonDS 1.1, executable SHA-256 f8a6b7071f13bd151e714327c7f00a22c94fefe6e763d1b8b09307a88524d9ca.
- Python 3.14.7, Pillow 13.0.0, ndspy 4.2.0, Unicorn 2.1.4; ARM GNU Toolchain 12.3.Rel1 / GCC 12.3.1; Windows AMD64.
- Original generated art SHA-256: bfd9ee9effb22bfded2cafd716aca4371d5d462a5203dc27bf2c4a6051f423c3. Its source/provenance is recorded in maintenance-tools/assets/dialogue-art/ART-CREDITS.md.
- A fresh git ls-remote confirmed the project's [pokebw2 fork](https://github.com/WhatWasMissing/pokebw2/tree/215b992f5c87bcadc4c5d7a40e78a309b2555f8b) main at 215b992f5c87bcadc4c5d7a40e78a309b2555f8b. The local talkmsgwin.c and include/field/field_actor_internal.h matched that commit byte-for-byte. Relevant function bodies also matched in field_msgbg.c (ActorMsgWin_CheckAndCreate, func_ov036_02188884), scrcmd_msg.c (ActorMsgWin_CreateWindow, SetupActorMessageWindow), and lib/nitro/src/os/os_arena.c (OS_GetInitArenaLo). Other local symbol-name changes were not used as compatibility evidence. Final instruction addresses, structures, and tables were rechecked against the exact Redux image.

## Runtime design and corrected defects

The helpers are copied into executable ITCM by the game's own boot autoloader. They begin at 0x01FF93A0, extending the original 0x13A0-byte image at 0x01FF8000. The final 1,012-byte helper is padded to a 1,024-byte extension; ITCM's arena floor becomes 0x01FF97A0. This ROM's TwlSDK copy table has four words per entry: destination, size, BSS address, BSS size. Its table/source tail move forward while the other autoload payloads and entries, original executable bytes, and main BSS bounds are preserved. The patcher guards the whole ROM hash, module parameters, table entries, arena literal, overlay CRC, and patch-site bytes.

The abandoned post-data design was invalid: 0x08000000 is GBA slot space in the emulator, not memory-mapped DS ROM. Earlier boot-only observations did not execute its helper and must not be cited as evidence that it worked. The replacement uses executable RAM and preserves overlay 36 RAM size 0x561A0, BSS 0x10040, and the full 0x10000-byte field heap.

Direct Thumb branches reach ITCM without consuming an argument register. The actor constructor remains stock; binding follows registration at 0x021A8D0E. Dispatch compares Thumb's odd LR, 0x021A8D13. Cleanup preserves the original ARM memset target's even address. The compiled ABI test reproduced the bad dispatch before correction.

The TalkMsgWin bitmap slot is window offset 0x0C. The stock accessor's 0x24 already includes the system's 0x18 prefix. The earlier double addition freed the old bitmap without replacing its slot. The corrected hook installs a 30×4 text window, preserves the native printer and choices, supplies light text with transparent page/cursor clears, and uses a separate BG for the art. It removes BG2's alpha target bit during custom dialogue and restores that bit on cleanup. Identity mismatch or bitmap allocation failure retains the original text window.

The WinFrame archive retains its original 12 members byte-for-byte and appends the base art pair, each speaker's art pair, and a text palette; this example has 17 members. Generic bottom-system art is disabled by default. The retained field-system-art experiment is **NOT RUN** and outside this verified actor path.

## Checks

| Check | Result | Evidence level |
|---|---|---|
| Focused patcher and compiled CPU suite | PASS, 15 tests | SOURCE/UNIT VERIFIED |
| ITCM data/metadata preservation; reject bad metadata/payload | PASS | Synthetic ARM9 byte fixture |
| ARM/Thumb mode, arguments, stack, callee-saved register | PASS | Real compiled helper with stub game callees |
| Exact identity/mismatch, bitmap slot, allocation failure, blend restoration | PASS | Real compiled C with stub game callees |
| Original resource, heap, BSS and exact-ROM build checks | PASS | INTEGRATION VERIFIED |
| Independent rebuild | PASS, byte-identical outputs | INTEGRATION VERIFIED |
| Refuse existing output; preserve its hash | PASS | INTEGRATION VERIFIED |
| Portrait, nameplate, frame, readable two-line text | PASS | GAMEPLAY VERIFIED |
| Page advance, Yes/No choice, B to decline, A to close | PASS | GAMEPLAY VERIFIED |
| Reopen custom dialogue | PASS | GAMEPLAY VERIFIED |
| Unconfigured NPC on same exact-profile build | PASS, native white window | GAMEPLAY VERIFIED |
| Exit to Lentimas Town after both dialogue styles | PASS, no residual art/freeze | GAMEPLAY VERIFIED |
| Original ROM/save hashes unchanged during these runs | PASS | INTEGRATION VERIFIED |
| DSi mode, hardware, two-client co-op, every window style/NPC | NOT RUN | Outside this desktop scenario |

Reproduce the source tests using the dependencies in maintenance-tools/tools/rom/requirements.txt and the ARM GNU toolchain:

    python -m unittest maintenance-tools.tools.rom.test_dialogue_art_patch maintenance-tools.tools.rom.test_dialogue_art_hook_cpu -v

CPU tests execute production C in Unicorn with explicit stubs for game allocation/rendering entry points. They establish the hook ABI and state behavior, not the full engine or graphics. Missing dependencies/toolchain fail visibly. The separate live runs establish actual rendering.

## Live scenario and final artifact

The example binds zone 460, actor UID 6, with the name Emma and original generated portrait. This intentionally demonstrates the skin on the nurse; her scripts and dialogue are unchanged. The exact ROM's zone header selects event member 606, whose UID 6 has model 78 and script 2100. A session-local checkpoint confirmed live ScriptActorWork selected actor 6. UID 3 belongs to another worker; the earlier example targeting it correctly fell back to stock.

Two independent local builds produced identical output. From a copied Lentimas save, the player entered the Pokémon Center and spoke with the nurse. The box showed “Hello, and welcome to the Pokémon Center.”, advanced through the explanation and rest prompt, displayed native Yes/No choices, and closed after declining. Reopening displayed the custom box again. An unconfigured nearby NPC displayed “A cool mind feels no heat!” in a stock window, then the player exited to town.

All sessions used private volume zero with DSi volume synchronization off. After the first muted check, SDL's dummy audio driver also prevented physical audio output. The wrapper requests a hidden process window. Native MCP buttons, waits, screenshots, and one checkpoint operated the game without desktop input simulation. All sessions stopped with exportedSave null. The original source ROM and save remained unchanged during testing; no save export was made.

The derived ROM and copied save remain private and are not public release assets. ROMs, saves, and gameplay captures are excluded from source commits. Reusable source, tests, original generated art, and documentation remain.
