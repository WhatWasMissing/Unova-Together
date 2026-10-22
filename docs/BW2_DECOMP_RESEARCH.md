# BW2 decompilation research for Unova Together

Research snapshot: 2026-10-20. This is a source and ROM-structure investigation, not a game build, patch, or gameplay test. It records what was observed and where to verify it; it does not promote a base-game address or save offset to a Redux address.

## Source identity and limits

The extracted reference inspected locally is `F:\gen5decomps\black2-92%\pokebw2-main`. It has no `.git` metadata. Its README SHA-256 is `a5aff06d844ab8affbe41b22601443afac6b5513e4dc2e060e4aa99bfd4aa646`, the archive SHA-256 is `4c26bf799bc7e3f724af0dc819dbbadfad0cf8d0518c736fa4d46144b2bb25a9`, and the snapshot contains 1,220 C source files. The local `b2_us.sha1` identifies the clean Black 2 base as `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb`, which matches the hash published by the upstream project. These checks identify the local bytes and the baseline ROM; they do **not** identify the snapshot's exact upstream commit or establish a “92% complete” match result.

The upstream project describes itself as a work-in-progress Black 2 / White 2 decompilation that targets byte-for-byte rebuilds of USA/Europe NDSi-enhanced ROMs and points to ByteMatch for progress. The local tree lacks the provenance needed to tie this particular extraction to a commit or CI result. See the [upstream repository](https://github.com/fuddlesworth/pokebw2), its `README.md`, and the existing [local-decomp inventory](references/gen5/LOCAL_DECOMP.md). The decomp is GPL-3.0; this document contains findings and paths, not copied decomp source. The supplied reference archive keeps its original author attributions in [its index](references/gen5/README.md).

No decomp build was run: the extracted folder has no ROM input/build output, its own guidance requires a matching build to verify changes, and this task does not change that source tree. The `ndspy` parser was already available in Python 3.12 and read the two local ROMs. Its NARC and decompressed ARM9-overlay APIs worked. Its `loadArm9()` main-binary path previously failed on the DSi-enhanced image's copy-table data, so the audit deliberately does not use or infer ARM9 main-binary addresses.

## Event scripts, flags, maps, and actors

The documented field-script flow is a good template for small story events:

1. A zone's event record is stored in `a/1/2/6` and represented by `res/field/events/<zone>.json`. The JSON distinguishes background events, NPCs, warps, triggers, and init-script tables. `tools/data/event_data.py` describes the record encodings, converts event NARC records to JSON, and packs them again (`event_data.py:1-11, 20-27, 80-130, 135-149, 205+`). The archive member order is separately recorded in `res/field/events/order.json`; it must agree with generated zone names.
2. Event JSON NPC entries identify an object/model, movement/type, event flag, script ID, facing, parameters, and grid or rail position. The sample baseline `res/field/events/route_7.json` contains 17 NPCs, 27 background events, 3 warps, 2 triggers, and one init script (script ID 4). Treat that as a source-tree example only: Redux's zone archive differs, so re-read the target ROM before reusing a numeric ID or coordinate.
3. The script itself is in `res/field/scripts/<zone>.s`, assembled into `a/0/5/6`; text lives in `a/0/0/3` and is named from script text banks. The VM consumes a 16-bit command ID followed by command arguments. The field-script guide explains variable operands and stack comparisons (`docs/scripts.md:3-5, 63-109`; implementation `include/system/vm.h:9-52`, `src/system/vm.c:49-86`).
4. Use an existing field command when possible. IDs at or above 1000 are plugin commands supplied by overlays; Overlay 12 maps plugin IDs to zones and loads/unloads those overlays (`docs/scripts.md:83-103`, `src/ov012/script_plugin.c:26-95`). A new plugin command therefore adds an overlay lifecycle and dispatch concern; a normal NPC interaction should not need one unless stock commands are insufficient.
5. Use saved event flags for persistent one-time rewards and temporary flags only for state that may reset. `EVENT_WORK_0x4000` starts saved work variables; `EVENT_FLAG_TEMP_0` is `0x4000` (`generated/vars.txt:2`, `generated/flags.txt:3065`). In `EventWork`, 431 16-bit work values occupy `0x35E` bytes, saved flags occupy the next 383 bytes, the hidden-item byte is at source-layout offset `0x4DD`, and the structure size is `0x4DE` (`include/save/event_work.h:7-31`). `event_work.c:23-75` confirms saved and temporary flags use different storage. These are source-structure facts, not an invitation to edit Redux saves by those offsets.

An NPC model or sprite is a separate data path. `res/field/actors/<object-code>/` supplies the model table `a/0/4/7` and graphics `a/0/4/8`; `field_actor_data.py` documents sprite strips (32- or 64-pixel square frames with a palette) and Nitro models (`field_actor_data.py:1-44`; `include/field/field_actor.h:16-92`). Map matrices, models, textures, and zone headers are likewise separate archives (`docs/data.md:62-89, 910+`). This separation helps isolate a broken NPC interaction from a missing object resource or incorrect map/zone registration.

## Trainer battles and AI

Trainer definitions are data, not event-script byte blobs. The decomp maps `res/trainers/data/<trainer>.json` to trainer records in `a/0/9/1` and party records in `a/0/9/2`; the packer uses generated trainer ordering and packs both archives (`docs/data.md:72, 602-610`; `tools/data/trainer_data.py:32, 52, 153+`). Field scripts call a trainer constant and branch on the outcome. The Mistralton Gym source calls `TRAINER_LEADER_SKYLA_2` or `TRAINER_LEADER_SKYLA`, checks `TrainerBattleIsVictory`, then closes the battle event (`res/field/scripts/mistralton_city_gym.s:92-105`). The battle event creates `BtlSetup`, resolves trainer data, adjusts challenge-key levels, and enters the battle callback (`src/ov012/event_battle.c:214-256`; declaration in `include/field/event_battle.h:12-21`). Trainer completion flags are event flags computed as `trainerId + 0x5F0`, not file or RAM offsets (`src/ov012/trainer_script.c:44-62`).

Trainer AI is a separate 14-script archive at `a/1/6/9`; AI flag bits select the scripts (`docs/scripts.md:6-10, 45-53`; macros and handlers in `res/trainers/ai/`, `include/asm/tr_ai.inc`, and `src/ov170/tr_ai.c`). A Mega-capable opposing trainer would need explicit battle-runtime support in addition to trainer data and AI policy. Merely assigning a stone/item or changing the party does not establish that the original Gen 5 battle engine can transform it.

## Battle-area zone selection

The pinned decomp reference at `WhatWasMissing/pokebw2` commit `215b992f5c87bcadc4c5d7a40e78a309b2555f8b` shows the battle's source zone explicitly. In `src/ov036/field_encount.c`, `SaveBtlFieldStatus` gets `Field_GetPlayerStateZoneID(field)`, uses that zone for `GetZoneBattleBGID`, and stores it as `status->zoneId` (lines 265-272). `include/field/field_event.h` defines `BtlFieldStatus.zoneId`; `src/system/btl_setup.c` copies the status into the battle environment in `BtlSetup_LoadGameData` (around line 240). This makes the loaded field zone the right key for an area's battle backdrop.

The runtime tracker also reports `map`, which can identify the current outdoor matrix cell, separately from `fieldZone`, the loaded zone. On the local supported Redux output ROM (game code `IREO`, SHA-256 `353fb0cf82c3e4eddfc8986efa8910b00eb1c4d6f106c220abef59d69d3a520a`), `a/0/1/2` contains 617 zone headers and `a/0/1/3` contains 409 area records. The Route 7/Mistralton example resolves loaded field zone 107 and matrix cell 337 to area 38 in both cases. The mod reads these mappings from the selected ROM; the decomp supplies the meaning of the battle field, not Redux table values.

Nearby cropped map geometry still needs the matrix-cell coordinates. It is therefore used only when the matrix zone and loaded battle zone resolve to the same area; otherwise the runtime chooses the fallback arena for the loaded battle zone's area. This check does not change the decomp or game logic.

## Memory structures and address spaces

Do not mix these different kinds of numbers:

| Kind | Confirmed source/example | What it means |
| --- | --- | --- |
| NDS named-file path | `a/0/5/6`, `a/1/6/9`, `a/0/9/1` | An FNT-resolved ROM file path, not a byte offset in the `.nds` file. |
| NARC member index | `route_7.json` archive member / array index | An entry within the named archive. Redux can add or change entries; resolve by the target's names and table. |
| ARM9 overlay load address | Overlay 167 loads at `0x021998C0` in clean Black 2 and `0x02199740` in the local Redux file | A decompressed overlay's RAM load address, not its ROM byte offset or a universal code address. |
| Save-structure member offset | `EventWork` offsets above | A C structure's layout within the decomp's save block, not a validated absolute save-file offset for Redux. |
| Runtime object member offset | `BattleMon` fields below | A field offset within an object, not the object's fixed RAM address. |

`GameData` is a runtime aggregate with pointers to `SaveControl`, player states, event data, party, `EventWork`, and other subsystems (`src/system/game_data.c:87-125, 407-409`). The VM stores its `pc`, stack, work, environment, and callback state on an allocated object (`include/system/vm.h:35-52`, `src/system/vm.c:18-29`). Neither structure supplies a fixed address that a patch can safely assume.

The local `BattleMon` definition gives a 0x1F8-byte battle object and separates the persistent party source from current battle state (`include/battle/btl_pokeparam.h:108-173`). Under that source layout, `BattleMonCore.baseAbility` is at `0x16`; `BattleMon.ability` is at `0x13C` and `BattleMon.form` at `0x141`. The field layout is used directly when the battle object is initialized and read (`src/ov167/btl_pokeparam.c:40, 70-80, 1354-1374`). These are **object-member offsets derived from this C layout**. They are not ROM addresses and do not prove that the same offsets or object layout survive in Redux's compiled overlay. The supplied BW PK5 note is a useful reminder that boxed/party records are encrypted and distinct from live battle objects; the B2W2 save guide separately documents a historic block map. Neither is a safe Redux write specification. In particular, the archived strength-boulder checksum value `0x201E2` is flagged by its source as anomalous, and the BW badge-date note includes `0x407004`, outside a 512 KiB save. Keep these warnings visible (`references/gen5/B2W2_SAVE_STRUCTURE.md:113-116`, `references/gen5/BW_SAVE_STRUCTURE.md:86-93`).

## Clean Black 2 versus the local Redux v1.4.1 file

The baseline file SHA-1 is `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb`, matching the upstream decomp's expected Black 2 USA/Europe NDSi-enhanced base. The local file named `Pokemon Black 2 Redux Complete (v1.4.1).nds` has SHA-1 `3a51c56e46280edc9bac1c30d0d1ab899b760076` and SHA-256 `332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a`. Both headers identify `POKEMON B2`, game code `IREO`, unit code 2, ROM version 0. The filename and header alone do not authenticate a Redux release; the digest identifies the exact local bytes compared.

Read-only NARC and decompressed-overlay comparison (`maintenance-tools/tools/research/bw2_rom_reference_audit.py`) observed:

| Resource | Clean base → Redux | Practical implication |
| --- | --- | --- |
| Field scripts `a/0/5/6` | 1,289 → 1,290 members; 179 common member indices differ | Do not reuse source script indices blindly. Resolve the Redux script and zone tables first. |
| Trainer AI `a/1/6/9` | 14 → 14; NARC SHA-256 identical (`eb4caa69e2a4d0464bd38cda8b5ce6403aeb8a626e5736b0c4e578c573a668af`) | The trainer AI archive itself matches byte-for-byte in these two local ROMs. This does not prove that all battle code or trainer data match. |
| Trainer records `a/0/9/1` | 814 → 891; 534 common member indices differ; 77 added | Redux trainer roster/records differ substantially. |
| Trainer parties `a/0/9/2` | 814 → 891; 648 common member indices differ; 77 added | Vanilla party IDs/contents cannot be treated as Redux teams. |
| Zone headers `a/0/1/2` | One NARC member in each; member differs | Re-read zone/map metadata from the supported target before placing events. |
| Moves `a/0/2/1` / items `a/0/2/4` | 207 / 232 common members differ | Verify IDs and effects against the exact Redux build before item or battle edits. |
| Overworld graphics `a/0/4/8` | Same 975 members; indices 13, 108, 174, and 903 differ | Most actor graphics are shared in this comparison, but changed entries still need target-side inspection. |
| Overlay 012 | RAM `0x021503C0`, size 123,520; decompressed hash identical | Its overlay bytes matched in these two images. |
| Overlay 036 | RAM `0x0217F600`, size 352,672; hash differs | Same load address does not mean same code. |
| Overlay 167 | `0x021998C0`, 268,096 bytes → `0x02199740`, 268,480 bytes | Redux shifts this overlay's load address down `0x180` and adds 384 bytes. Re-derive and signature-check any battle hook. |
| Overlay 170 | RAM `0x0217F600`, size 10,432; decompressed hash identical | The trainer-AI overlay matched in this comparison; validate any other patch target separately. |

The named archives and overlay APIs were read through `ndspy`; no ROM was rewritten or extracted. The summary is reproducible with:

```powershell
python maintenance-tools/tools/research/bw2_rom_reference_audit.py <clean-black2.nds> <redux-v1.4.1.nds>
```

This checks only the selected NARCs and overlays. It does not prove gameplay behavior, test a patch, inspect the White 2 counterpart, or read/write a save.

## Mega Evolution integration point

A targeted source search found no explicit Mega Evolution, Mega Stone, or Mega Form symbols in `src/`, `include/`, field scripts, or trainer AI scripts. Gen 5's `CheckEvolution` at `src/ov167/btl_server_flow.c:7484-7494` asks whether the species has one of seven normal evolution records; it is not a Mega hook. Thus the decomp gives useful battle structures and call flow, but does not expose a native Gen 5 Mega feature that can simply be enabled.

The current Unova Together development patch contains emulator-side Mega hooks, including `FightSelect` `0x021B3C01`, `MoveInput` `0x021CF111`, `ChangeFormHandler` `0x021AE261`, and `ClientChangeForm` `0x021B89CD`, plus the member offsets `0x16` and `0x13C` (`maintenance-tools/patches/development-polish.patch:2998-3005`). Its item-preview hook uses `0x0204C040` and returns at `0x0219E57F`, guarded by the main-RAM mask and call-site checks (`development-polish.patch:1375-1384`). These are evidence of the mod's current emulator approach, not generic vanilla offsets; this research did not run or gameplay-test those hooks. Overlay 167's observed Redux delta above is exactly why a code address must be tied to the matching ROM and guarded against expected instruction bytes.

## Uploaded reference documents incorporated

The attributed archive under [`docs/references/gen5/`](references/gen5/README.md) was read alongside the decomp:

- `B2W2_FILE_SYSTEM.md`: historical archive-path catalogue; decomp `docs/data.md` confirms several important paths, while the supplied catalogue's tentative labels remain tentative.
- `B2W2_SAVE_STRUCTURE.md`: useful block/checksum overview, explicitly unverified for Redux; its known checksum anomaly is not a write instruction.
- `BW_PK5_STRUCTURE.md`: explains encrypted Gen 5 Pokémon data and the distinction between boxed and party records; cross-check against `include/pml/poke_party.h` before any record parser change.
- `BW_SAVE_STRUCTURE.md`: Black/White-specific and includes inherited Gen 4 or out-of-range notes; not a B2W2/Redux layout specification.
- `STANDARD_PID_CREATION.md`: historical disassembly comments and absolute addresses are not revision-pinned; verify each claim against target code before use.
- `LOCAL_DECOMP.md` and `README.md`: record the snapshot's local identity, provenance limits, authorship, and license.

These documents are research material, not instructions to edit a ROM or save. Original credits remain with Bond697, evandixon, and other contributors as detailed in the archive index and linked Project Pokémon pages.

## Practical next steps grounded in this evidence

1. For a new story NPC, start from the target ROM's event JSON and zone table, add its actor resource only if an existing `OBJ_CODE_*` cannot be reused, and use stock field-script commands plus a saved flag for one-time behavior. Keep any reward flag, text-bank entry, event script, and NPC placement together in the review.
2. For a trainer rematch, resolve a Redux trainer constant/record/party and its flag from the target rather than assuming the base index; use the existing field-battle script pattern. Verify trainer AI separately from the party's held item.
3. For Mega work, trace the exact Redux battle overlay and both client/server form-change paths before changing code. Validate item ID/data, move selection, form/ability/stat recalculation, end-of-battle restore, doubles/co-op ownership, and level-up/reward flow. The base game's `CheckEvolution` and the uploaded save tables are not substitutes for that trace.
4. Keep ROM baselines identified by hashes, and record archive-member and overlay deltas with the included read-only audit tool before each new hook or patch update. Only promote an observed base-source structure or address to a Redux patch after target-specific validation.

## Verification record

- **PASS — source inventory:** local README/archive hashes, missing Git metadata, 1,220 `src/*.c` files, and expected clean Black 2 SHA were checked read-only.
- **PASS — ROM identity and selected resources:** the included audit tool completed against the clean base and local file named Redux v1.4.1; results are listed above. Tool environment: Windows PowerShell, Python 3.12, preinstalled `ndspy` 4.2.0.
- **NOT RUN — decomp build / matching:** no matching-toolchain build was necessary or attempted; exact extraction commit is unknown.
- **NOT RUN — gameplay/runtime:** no emulator session or event/battle hook was changed or tested.
- **NOT RUN — save compatibility:** no save file was opened or modified.
