# Reusable implementation guidance

This file records repeatable project-specific practices and findings. Treat current source, tests, `AGENTS.md`, and dated verification notes as the authority for current behavior; re-check them before applying a note to a new version.

## Pokémon Black 2 / White 2 decomp reference

- The project's reference fork is [WhatWasMissing/pokebw2](https://github.com/WhatWasMissing/pokebw2), forked from [fuddlesworth/pokebw2](https://github.com/fuddlesworth/pokebw2). GitHub identifies the upstream as a work-in-progress Pokémon Black 2 and White 2 decompilation under GPL-3.0. At fork creation on 2026-10-21, the fork's `main` matched upstream commit `215b992f5c87bcadc4c5d7a40e78a309b2555f8b`. Check the fork's current commit before relying on a source detail; upstream continues to change.
- Use this as source evidence for vanilla B2W2, not as proof of compatibility with Blaze Black 2 Redux Complete v1.4.1. Record the full commit SHA, file path, and relevant function for each finding. Re-resolve tables, scripts, overlays, and expected instruction bytes in the supported Redux ROM before using a value in a patch.
- The decomp is GPL-3.0. Preserve its license and upstream contributor attribution when distributing or adapting decomp source. Do not copy ROMs, saves, firmware, or proprietary game assets into the mod repository or fork. The decomp build expects a user-owned matching ROM and does not provide one.
- The locally extracted `F:\gen5decomps\black2-92%\pokebw2-main` snapshot described in `docs/BW2_DECOMP_RESEARCH.md` had no Git metadata. Its archive hash can identify those local bytes, but cannot prove its upstream commit or the advertised matching percentage. Prefer the Git-tracked fork for new research.
- Start with `docs/BW2_DECOMP_RESEARCH.md`, `docs/references/gen5/README.md`, and `maintenance-tools/tools/research/bw2_rom_reference_audit.py`. These record source provenance, caveats, and a reproducible read-only comparison. Reference material contributed from Project Pokémon retains its original authorship and uncertainty markers; do not silently promote tentative labels to verified facts.

## ROM, save, and runtime address discipline

Keep these number spaces separate in notes, code, and reviews:

- An NDS named-file path such as `a/0/5/6` is an FNT-resolved file in the ROM, not a byte offset into the `.nds` file.
- A NARC member index is an entry inside that archive. Redux can add, remove, or reorder members; resolve the target table before reusing an index.
- An overlay's RAM load address is where its decompressed code runs, not its ROM file offset. A C structure member offset is relative to an object, not a fixed RAM address.
- A decomp save-structure member offset is not automatically an absolute offset into a retail or Redux save file. BW save references are not B2W2 layouts.

For every binary patch, identify the exact supported ROM bytes, derive the correct overlay or asset from that ROM, and guard the patch with expected bytes or a suitably narrow signature. Fail closed on an unknown revision or mismatch. Keep the original ROM untouched; apply to a separate derived copy or through the launcher's in-memory patch mechanism. Test that patch output is deterministic and repeated application does not corrupt data.

The comparison in `docs/BW2_DECOMP_RESEARCH.md` used a clean Black 2 USA/Europe NDSi-enhanced base with SHA-1 `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb` and a local file named Redux v1.4.1 with SHA-256 `332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a`. These hashes identify the compared bytes only; a filename or header does not authenticate a release. That comparison found, among other differences:

- Field-script archive members changed from 1,289 to 1,290, with 179 common member indices differing.
- Trainer records and parties changed from 814 to 891 members, with 77 additions and extensive changed common entries.
- Move and item archives had changed common members.
- Overlay 167 moved from load address `0x021998C0` / size 268,096 bytes to `0x02199740` / size 268,480 bytes. A same-named overlay is not proof of the same code or address.

Those are findings for the two exact files in that dated comparison, not a universal guarantee about all Redux builds. Re-run the audit when the target ROM or upstream revision changes. Do not use an address from the base ROM or an old release without re-deriving it.

## Field maps, NPCs, and scripts

- In the decomp's example layout, zone event records are represented by `res/field/events/<zone>.json` and packed into `a/1/2/6`; scripts are under `res/field/scripts/` and packed into `a/0/5/6`; text uses `a/0/0/3`. `res/field/events/order.json` controls archive ordering. Treat these paths as a map of the decomp, then verify the target ROM's archive and zone tables.
- An NPC placement combines object/model, movement, event flag, script ID, facing, parameters, and grid/rail coordinates. A working script does not prove the actor resource or map placement is correct. Inspect the target map's existing actors, collision, warps, and event flags before adding one.
- Prefer existing field-script commands for an ordinary dialogue/reward event. A plugin command may add overlay loading and dispatch requirements; use one only when stock commands cannot express the behavior.
- Use saved event flags for one-time rewards. Temporary flags are for state intended to reset. Do not copy the base game's numeric flag, script, map, or NPC IDs directly into Redux.
- Keep map/event edits reviewable as one change: event record, text-bank entry, script, actor resource if needed, archive ordering, persistent flag, and patcher test.

## Trainer data, battle flow, and Mega Evolution

- Trainer records, trainer parties, field scripts, trainer AI, and battle runtime are separate systems. In the reference decomp, trainer data and parties use `a/0/9/1` and `a/0/9/2`; trainer AI is a separate archive at `a/1/6/9`. Resolve each from the target Redux file rather than carrying over base trainer indices or teams.
- A trainer holding a Mega Stone does not prove its AI or battle engine can Mega Evolve. Trace the battle decision path, held-item handling, form-change request, client/server ownership, and end-of-battle restore. Verify trainer AI separately from party data.
- The reference decomp has no native Mega Evolution implementation. Its normal `CheckEvolution` path checks ordinary evolution records; it is not a Mega hook. Unova Together's Mega behavior is added through emulator-side hooks. Treat patch hook addresses as version-specific and verify both the matching ROM and expected instruction bytes.
- For a Mega change, cover selection and form change in singles and doubles, co-op ownership, a switched-in active Pokémon, fainting, level-up/reward processing, disconnects where relevant, and restoration after battle. Test the player's Mega path and trainer AI separately. Source-level tests do not establish a working live battle.
- When changing battle forms or abilities, review stat recalculation, ability changes, move selection, item checks, form restoration, party/save serialization boundaries, and any code path that runs after level-up. A successful transform alone is not enough evidence.

## Items and shop data

- A new or reused item ID needs a complete audit: item name and description, pocket/category, icon and alignment, held effect, battle/field use, price, shop stock, gift/trade behavior, and any special flags inherited from the original slot. Replacing the label or icon alone can leave the item behaving like Mail or another original item.
- The verified Mart research in `docs/verification/MEGA_STONE_SHOP_DISTRIBUTION_2026-10-20.md` found the native shop arrays sized to 45 entries and standard shop archive members addressed as `fileId + 6` in the cited upstream source commit `068abb42f92f8da5e34d07be85bc8adde8a68840`. Re-check the latest fork and Redux data before relying on those details.
- The tested distribution policy gives each of 20 standard Mart inventories three distinct Mega Stones, covering all 49 supported stones with 11 repeated across shops; the other 54 lists are left alone. It preserves ordinary item order and the native 45-row limit. The policy and byte-level fixture verify generated stock, not live merchant navigation or purchases.
- Do not work around the 45-row limit by installing an unverified heap-backed shop overlay. The documented implementation retained the native limit after a custom overlay was associated with merchant crashes. Prefer a bounded data distribution that preserves ordinary stock.
- Validate shop changes at three levels: policy/unit tests, exact-ROM data extraction and integrity checks, then live shop browsing and purchases in-game. Passing the first two does not prove the merchant UI is safe.

## Multiplayer state, relay, and co-op rewards

- Movement, battle ownership, item exchange, and Teleport depend on state shared across the game hook, multiplayer protocol, relay, and peer. Trace the complete path from local game state through message serialization to the other client; a UI button or successful send is not proof the peer applied the action.
- Test with two clients at the same game/mod version. Include host and join, map transitions, reconnects, and a solo session to catch regressions outside multiplayer. If movement stutters only while connected, compare position updates and input sampling even when the displayed FPS stays stable.
- Relay version/capability is part of the feature contract. On an update, identify and replace or stop the stale relay process, restart the host relay, and verify the running executable path and version before testing Teleport. Closing and reopening the launcher alone does not prove an old external relay stopped.
- The game's local-relay startup helper must validate the exact `buildVersion` and required `fieldZonePresence` welcome capability before reusing a protocol-v1 listener; protocol compatibility alone can silently reuse a stale relay and disable Teleport. Prefer launching the packaged launcher with `--presence-relay <port>` so process ownership remains identifiable. When migrating older relays, stop a Python process only if Windows confirms its interpreter plus the exact installed `tools/presence_server.py` and host/port arguments, or the exact `tools/unova_launcher.py --presence-relay <port>` command; fail closed for external listeners. Cover both launcher checks and the game's startup helper, including same-build relays missing the capability, unknown/older builds, remote/unowned listeners, and restart cleanup. See `docs/DEVELOPER_TESTING.md` for the current verification record.
- Co-op experience and level-up handling are documented as experimental in `docs/XP_COMPENSATION.md` and `docs/KNOWN_ISSUES.md`. Suppression is the default in the current documented behavior. Comparison tests must use the same toggle on both players and check experience, levels, move-learning prompts, fainted participants, and disconnect/rejoin cases. Never infer synchronized rewards from solo tests or a policy fixture.
- Keep each player's save ownership clear. Test trades and item gifts for valid/invalid inputs and interrupted connections, and verify no item/Pokémon is duplicated or lost after save/reload.

## Followers, sprites, and rendering

- Preserve pixel-art edges when processing sprites: use nearest-neighbor transforms, retain transparency, avoid smoothing, and keep shiny forms as separate assets so shiny Pokémon remain shiny.
- Normalize each sprite using its feet/ground contact as the anchor, not the visual center of its full canvas. Compare all directions and frames against the player-sized field grid; mismatched canvas padding can look like vertical warping even when the actor coordinates are stable.
- Treat movement animation, world position, and map depth as separate concerns. A follower should advance on tile/facing state and animation timing, while draw priority follows the game's map/object layering. Test in front of and behind tall objects, fences, bridges, grass, stairs, and map transitions.
- Diagnose apparent bobbing/warping with frame-by-frame captures and actor coordinates. Separate an actual Y-coordinate change from animation-frame changes and occlusion/priority errors before changing timing or offsets.
- For field-scene occlusion, match the renderer's native depth conversion before comparing values. B2W2's `FieldG3D_InitCallback` selects Z-buffering; melonDS quantizes Z in `0x200` steps and applies a `0x3FFF` bias. An idealized OpenGL projection or a large normalized tolerance can leave objects in front of an avatar unmasked. W-buffering uses a different representation; do not generalize this field-only calculation to it.
- Set the scenery clip in screen coordinates before translating or rotating avatar art, and include its ground shadow. Keep status labels and navigation markers separate. Apply the same rule to companions and co-op trainer sprites without changing movement/gait timing or the foot anchor. Scan only the actor's transformed bounds. See [the depth-order verification](docs/verification/FOLLOWER_DEPTH_ORDER_2026-10-22.md) and `maintenance-tools/tools/test_follower_depth.py --source-root <matching-source>` for real-renderer tests, source prerequisites, and remaining live checks.
- Prefer official game sprites when licensing and source provenance allow; record source game, extraction method, frame layout, and attribution. Keep a clearly identified fallback for species/forms absent from the official set.

## Area-reactive battle scenery

- Use the game's loaded field zone as the battle-area key. In the pinned B2W2 decomp, battle setup captures `Field_GetPlayerStateZoneID` into `BtlFieldStatus.zoneId`; the overworld `map` sample can instead identify an outdoor matrix cell. Resolve both IDs through the selected ROM's zone table and use nearby field geometry only if both resolve to the same area. Otherwise retain the area's fallback arena.
- Keep the selected background latched while the tracker reports a battle; update it from a verified field sample after returning. Keep area lookup lightweight and scene generation asynchronous, outside the emulation frame.
- Maintain a protected open center for battlers. Reject prop polygons that intersect the protected square, including long faces whose vertices all lie outside it; checking vertices alone is insufficient. Verify crossing, boundary-touching, and wholly exterior cases.
- Preserve the original background when zone/area metadata or generated nearby geometry fails validation. Test area lookup against the exact supported ROM and the pinned decomp reference; source tests do not prove the camera framing in a live battle.

## Launcher UI

- Group navigation labels by the task players are trying to complete, and make the current page unmistakable through both selection styling and accessible text/state.
- Give frequently used settings a clear home and provide direct shortcuts only when they preserve the same underlying setting and persistence behavior.
- Test the smallest supported window size as well as the normal layout. Let content reflow or scroll; do not solve space pressure by shrinking text until it is hard to read.
- Show progress and a useful status message during background work, and keep controls responsive where the operation permits it.
- Preserve existing routes, settings keys, update/repair flows, and error handling while improving presentation.
- The canonical launcher is under `launcher-source/tools/launcher_ui/`; compare any corresponding `maintenance-tools/tools/launcher_ui/` files and keep them aligned when both are shipped or tested.
- Verify with relevant launcher tests, the UI parity check, and a real launch/visual inspection when available. Report screenshot or live-runtime checks that could not be completed.
- Confirm distribution rights for each artwork contribution before packaging it; a sprite-hosting repository's code license does not cover Pokémon images. When requested, fan-made Generation 5-style Pokémon sprites are appropriate launcher art only if the artist or project explicitly permits reuse; credit both the animator and any base-sprite artists, pin the source revision, and record the terms in `assets/ART-CREDITS.md`. Do not infer art permissions from source-code licenses, and do not bundle game captures or ROM-extracted character art in launcher pages.

## Launcher News and patch notes

- The launcher fetches `patchnotes/index.json` from the repository's `main` branch, and its “Read on GitHub” links also target `main`. Notes added only to a release branch or a GitHub release description will not appear in the News page. When releasing from a non-main branch, publish the note file and matching index entry to `main` as part of the release workflow; keep `patchnotes/README.md` in sync.
- Keep the patch-note index, Markdown files, and bundled `launcher-source/tools/launcher_ui/assets/news.json` consistent in the release source. Verify the launcher's real `launcher_feed()` fetch against the public `main` endpoint; local index tests alone cannot detect that the default branch is behind. GitHub's raw endpoint may serve a cached index for up to five minutes, so confirm the live feed after that cache expires.
- On the default branch, the newest published note may be newer than that branch's embedded `VERSION.txt`. Tests should require the current version's note to be present and the feed to be correctly ordered without assuming the checkout version is always the newest published note.

## Verification, packaging, and handoff

Report the evidence level precisely:

1. A unit/source test proves only the code paths and inputs it exercises.
2. A byte-level fixture proves the tested transformations against its supplied data; it does not execute the game.
3. A successful build proves compilation/linking for that configuration; it does not prove in-game behavior.
4. Package checks prove the inspected archive contents, metadata, and checksums; they do not prove a clean install or update path unless one was run.
5. A live single-player test and a two-client co-op test are separate checks. Record unavailable checks as not run, with reproducible steps.

For releases, use the explicitly configured repository, version, verified remote commit, player-facing notes, title, and every prepared asset with `maintenance-tools/tools/publish_release.py`. Verify the GitHub release is discoverable as latest and compare every asset's name, size, and SHA-256 digest to the prepared local artifacts. Scan packages for ROMs, saves, firmware, credentials, and unintended generated files. Keep release notes about player-visible changes; put implementation/provenance detail in verification docs.

For each fix likely to recur, add a concise verification record under `docs/` with exact source/ROM revision, tool and test versions, pass/not-run boundaries, and repro commands. Keep reusable test source in `maintenance-tools/tools/` or the relevant test tree; delete only verified disposable outputs after checks. Do not clean up user ROMs, saves, active installations, or release artifacts.
## Black 2 / White 2 player field models

Use the game's **field actor** sprites for selectable walking characters. Battle trainer portraits and front/back battle art are separate assets and do not contain the field walk cycles needed by the player model map; do not treat a battle sprite sheet as a drop-in walking model.

- Read candidate actors from the user's selected supported ROM, using `a/0/4/7` for actor configuration and `a/0/4/8` for graphics. Require the expected billboard actor kind, a moving animation set, and matching `BTX0` texture plus `BMD0` model resources. For the reviewed B2W2 tables, human controllers 2 and 3 have walk cycles; controller 4 is a static single-face set and must be excluded. Keep human NPCs and Pokémon as explicit categories, and exclude props or incomplete actors.
- Use the upstream B2W2 `generated/obj_codes.txt` only as pinned name metadata. Map sparse object codes through the decomp's `GetIndexOfObjID` ranges and verify the code stored at every actor-table row before trusting those names. The catalog names here were derived from `fuddlesworth/pokebw2` commit `215b992f5c87bcadc4c5d7a40e78a309b2555f8b` (GPL-3.0) and checked against all 1,008 actor IDs in the supported Redux ROM; this is not proof that other Redux revisions use the same mapping.
- Document intentional custom object-code reuse. Unova Together's Cynthia event patch assigns her field art to the code used for Durant, so that code must display as Cynthia after the event patch is applied.
- Do not bundle ROM-extracted models, textures, trainer portraits, or Pokémon artwork. Read them from the player-provided ROM and keep using the launcher-owned, hash-checked output copy for the mapping change.
- A launcher preview can decode the selected actor's native I4 `BTX0` faces and apply the pinned billboard animation steps; index 0 is transparent, and `flipS` mirrors the face horizontally. Keep decoding on a worker thread and create Tk images on the UI thread. This is a 2D native-frame preview, not a full 3D scene or proof of every in-game pose.
- Track every picker-owned Tk `after` token and cancel it before destroying the picker. The main launcher must invoke the picker's close/cancel path before interpreter-wide timer cleanup; test closing the main window while the preview dialog is open to avoid deleting callback commands twice.
- Store appearance favorites and named presets in the existing game-profile preferences. Validate types, deduplicate IDs/names, and impose small count/name limits before saving; a preset may refer to a model unavailable in another game ROM and must not be applied silently there.
- Only the normal walking actor is changed by the existing ROM map patch. Do not reuse that model in bike/surf or other player forms without matching movement assets and animation evidence. Battle trainer portraits are separate assets. Co-op model sharing requires the native peer-renderer and protocol path; a launcher-only preference or presence-server field is not enough.
- Run `python -m unittest test_player_models -v` from `launcher-source/tools`, `python check_launcher_tree_parity.py` there, and the launcher UI tests. These prove catalog filtering, labels, profile validation, preview frame decoding, and ROM-table edits at source level; they do not replace a live in-game walk-cycle check for each actor family.

The reviewed ROM currently exposes 227 moving human actors, 619 Pokémon field models, and the patched Cynthia actor (847 entries total); its 245-name human label table also contains 18 static actors which the selectable catalog excludes. The pinned animation references are from `fuddlesworth/pokebw2` commit `215b992f5c87bcadc4c5d7a40e78a309b2555f8b`; the local extracted copies of `fldmmdl_drawdata.c`, `fldmmdl_movedata.c`, and `blact.h` were byte-for-byte checked against that commit. This reference describes upstream B2W2 behavior, not compatibility with other Redux revisions.
