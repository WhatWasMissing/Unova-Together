# Unova Together 2.0.36 verification

This release fixes the native battle-scenery handoff for ordinary wild and trainer battles. The launcher and its feature settings do not change. The scenery behavior is documented with source and test details in [the battle-context verification](verification/AREA_BATTLE_SCENERY_CONTEXT_2026-10-24.md).

## Build and source provenance

- Native source baseline: official Unova Together 2.0.34 source asset, SHA-256 `de592d351d8e2ea24f8b79769bf4d7ebdb6445e1ebc23183c95c0421902ac0bb`. The 2.0.35 release reused the same emulator binary and source.
- Native toolchain: Windows 10 build 19045, CMake 4.4.1, Ninja 1.13.2, MSYS2 UCRT64 GCC/G++ 16.2.0, Qt 6.11.2.
- Configuration: Release, Qt6, OpenGL enabled, LTO disabled. The complete 210-step `melonDS` build passed; the version-resource update rebuilt and linked the final 2.0.36 binary successfully.
- Final `melonDS.exe`: 11,937,792 bytes, FileVersion/ProductVersion 2.0.36, SHA-256 `bb89b52b0eb15883b57461665e59fe86c0eb351da3c14c25690b58e3cd353640`.

## Checks

- PASS: focused C++ context check, C++17 with `-Wall -Wextra -Werror`; ten verified, retained, invalid, unknown, and unloaded-catalog cases.
- PASS: source-patch suite, 5/5; applied the distributed patch to the exact 2.0.34 source archive and matched the output hashes.
- PASS: release fingerprint unit checks, 2/2.
- PASS: patch-note feed checks, 5/5; launcher UI parity, 43 files.
- PASS: full native emulator build and final version metadata.
- NOT RUN: live wild/trainer gameplay. MCP status found no isolated session; no emulator was launched or controlled, and no installed runtime, ROM, save, or profile was changed.

## Dialogue-art test clarification

Custom dialogue art remains an explicit ROM patch for the sample Lentimas Pokémon Center nurse (zone 460, actor UID 6). The normal launcher does not patch the main profile ROM. If that ROM is selected, stock dialogue is expected. To see the custom box, use the steps in [Dialogue art testing](DIALOGUE_ART_TESTING.md) to build a separate `Dialogue Art Demo.nds`, then run it with a copied save in the muted isolated runner. The source ROM and live save must remain untouched. The prior exact-build renderer gameplay evidence is recorded in [the dialogue renderer report](verification/ROM_DIALOGUE_ART_RENDERER_2026-10-24.md); it does not imply that the unpatched profile displays custom dialogue art.
