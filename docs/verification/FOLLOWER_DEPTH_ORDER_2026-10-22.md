# Follower and co-op avatar depth order — 2026-10-22

Status: **IMPLEMENTED — RUNTIME UNVERIFIED**. Branch: `MVQ1303/follower-depth-order`, based on `e074691aa2366aad181e4f491a32e988d659a6dd` (main, 2.0.25). No publication, release, installation replacement, ROM edit or save edit is part of this task.

## Acceptance and boundaries

1. **PASS — SOURCE/UNIT VERIFIED:** closer scenery masks follower and co-op trainer sprite pixels and shadows, including small depth differences missed previously.
2. **PASS — SOURCE/UNIT VERIFIED:** screen-space occlusion edges remain fixed under fractional avatar translation and rotated cameras. Reaction rotation does not bypass the test.
3. **PASS — SOURCE/UNIT VERIFIED:** idle/walk timing, sprite dimensions, foot anchors, reduced-motion behavior, missing-depth fallback, trainer labels/status badges and navigation markers are preserved in the exercised cases.
4. **PASS — BUILD:** Windows Release emulator with software and OpenGL renderer support compiles and links.
5. **NOT RUN — GAMEPLAY / TWO-CLIENT INTEGRATION:** representative scenery, camera movement and map transitions with live game data. Synthetic QPainter rendering is not native GPU readback or gameplay evidence.

Risk: HIGH (emulator frontend rendering). The change is limited to two existing native-file sections of `maintenance-tools/patches/development-polish.patch` and its digest, plus tests/guidance. No networking, shop, XP, battle, ROM or save-format logic changes. Rollback is removal of this branch's focused delta. User-selected model configuration was not independently inspected; no model switch was performed.

## Trace and cause

The pinned reference is [WhatWasMissing/pokebw2 at 215b992f5c87bcadc4c5d7a40e78a309b2555f8b](https://github.com/WhatWasMissing/pokebw2/tree/215b992f5c87bcadc4c5d7a40e78a309b2555f8b). `src/ov036/fieldmap.c::FieldG3D_InitCallback` selects manual polygon sorting and `GX_BUFFERMODE_Z`. `include/gfl/blact.h` defines camera-facing billboard types and bottom-center anchoring; `src/gfl/billboard.c::BlActScene_Draw` transforms textured 3D quads into the camera-facing plane. These are vanilla source findings, not Redux memory-address evidence. No decomp source or ROM assets were copied into this branch.

In the emulator, `GPU3D.cpp::SubmitPolygon` converts homogeneous Z to native depth using integer truncation, the `0x3FFF` bias and `0x200` quantization. Software depth export divides by `2^24`; the OpenGL renderer uses the same polygon depth in its vertex shader. `EmuThread.cpp` publishes scene depth and camera data to the display-buffer-specific `PresenceSurface`; `Screen.cpp` composites the frontend overlay over the completed framebuffer.

The previous `PresenceOverlay.cpp::projectWorldDepth` used idealized `(Z/W+1)/2`, and `PresenceOcclusion.h` allowed a `0.0015` gap (about 49 native Z steps). At the synthetic field camera distance of 150 units, nearer scenery differing by `0.0005` was incorrectly ignored. The old clip was companion-only, installed after the shadow, rounded after fractional translation, and disabled for spin reactions. The fixed path uses native quantization and one native Z step of tolerance, rejects invalid depths, and clips the transformed body/shadow bounds in screen coordinates. Labels, emotes and markers retain their UI visibility. The same rendering path now covers remote trainer art.

The 2D background-priority mask and player-silhouette fallback remain in place. This change does not add GPU waits, alter frame scheduling, or change follower coordinates/animation frames. The existing asynchronous OpenGL readback can use an older depth frame; correctness during fast camera movement still needs a live check. W-buffered scenes are outside this field-Z calculation's scope. The separate OpenGL **compute** backend has no `GetPresenceDepthBuffer` override and still lacks 3D avatar occlusion; this branch's depth fix covers the default software backend and classic OpenGL backend. Adding compute depth export is not claimed as implemented.

## Source and test provenance

The local source input was `Unova-Together-2.0.24-Source.zip`, SHA-256 `9aaa56d6069458096c4cd889a974109368667d9bb943e6cd2220a97a3d4df3a3`, matching the archive digest recorded in main's `docs/RELEASE_CHECKS_2.0.25.md`. All 2,387 archived source files matched the existing 2.0.25 extraction except `ProjectCredits.h` and `res/melon.rc.in` version metadata. The test extraction used those existing 2.0.25 metadata files. The two renderer files were unchanged between that authenticated input and the documented 2.0.25 source.

Final tested production files (SHA-256, LF for changed files):

| File | SHA-256 |
| --- | --- |
| `src/PresenceOcclusion.h` | `99927c7a9409033137ca518bf606ffe032ea03d6bac7b9083a59b0f32dbdec28` |
| `src/frontend/qt_sdl/PresenceOverlay.cpp` | `2a9f43a9c731921fba4f5230061895db784caaac8d6f71dd0a015d6c1acc5f96` |
| `src/frontend/qt_sdl/PresenceOverlay.h` (unchanged) | `4769dd8cfc49cb8794382301b9957da1cafd5a1d829404cf7b140737d3fe61ea` |

`check_follower_depth.cpp` compiles the actual production `PresenceOverlay.cpp`, `PresenceOverlay.h` and `PresenceOcclusion.h`; only camera, sprite and scene-depth inputs are synthetic. Eight groups pass, including 40 fractional-position/camera/elevation/follower-or-trainer combinations with a pitched camera. The unchanged pre-fix source fails six of those eight groups, including the remote-trainer case. Assertions cannot disappear under `NDEBUG`: the new harness uses explicit diagnostic failures and nonzero exit status.

The updated source-patch sections were reversed to recover their original baseline, reapplied, and compared with the compiled source after CRLF/LF normalization. The complete patch passed reverse-application checking against the test source with only its two already-different version metadata files excluded. Only the two intended production-file sections changed; the patch digest was refreshed.

## Reproduction and outcomes

Windows; Python 3.12.8; GCC 16.2.0; Qt 6.11.2; CMake 4.4.2; Ninja 1.13.2. Required source: an emulator tree with this branch's development patch applied to the baseline identified by `development-polish.json`. The tree is supplied explicitly; the harness does not download or authenticate source automatically.

```powershell
py -3.12 -B maintenance-tools/tools/test_follower_depth.py --source-root <matching-source> --compiler C:/msys64/ucrt64/bin/g++.exe --pkg-config C:/msys64/ucrt64/bin/pkg-config.exe
```

- **PASS:** eight new groups; production native `tools/test_pokemon_follower.cpp` executable (trail, frame normalization, projection/occlusion, subpixel motion); existing `check_camera_continuity.cpp` and `check_battle_badge.cpp`. All C++ checks used `-std=c++17 -O2 -UNDEBUG`, compiled with production `PresenceOverlay.cpp` and Qt6Gui, with `QT_QPA_PLATFORM=offscreen`.
- **FAIL — pre-existing legacy fixture:** `maintenance-tools/tools/check_presence_rendering.cpp` stops at line 40, expecting stride frame 22 where the unchanged production phase formula returns 21. The same failure occurs against pre-fix source. This legacy fixture was left unchanged; no production animation code was changed to satisfy it.
- **PASS — BUILD:** `cmake -S <matching-source> -B <disposable-build> -G Ninja -DCMAKE_BUILD_TYPE=Release -DENABLE_LTO_RELEASE=OFF -DENABLE_LTO=OFF -DUSE_QT6=ON -DQt6_DIR=C:/msys64/ucrt64/lib/cmake/Qt6`, then `cmake --build <disposable-build> --target melonDS -j 4`, with UCRT64 and MSYS `usr/bin` on PATH. Result: 11,893,248-byte test executable, SHA-256 `a77b762c1a0999b2db3add4a09c217b5643f9cd59498d01d08831e743db15c4c`. Existing Teakra CMake deprecation/policy warnings were emitted. No release package was built.

**BLOCKED — cleanup:** automatic approval review rejected recursive deletion of the disposable `.follower-depth-work` directory as “blocked by policy,” without a more specific reason. Its resolved path was verified inside this workspace, its disposable marker was checked, and it contained zero reparse points. The extracted source, compiled checks, preview capture and test build remain there, untracked and excluded from the commit. The harness's own temporary compile directories were removed automatically. Reusable test sources and this evidence remain tracked.

## Live checks still required

Using a rebuilt emulator and user-owned supported Redux ROM/save copies:

1. In solo mode, pass the follower behind and in front of Route 7 fences, Celestial Tower gravestones, roofs, tall grass, stairs and bridges. Compare the player's occlusion at the same ground position. Check large/small followers, shiny forms, all facings and reduced motion.
2. Walk, run, turn and stop while panning/rotating the camera; verify no clipping-edge shimmer, foot jumps, scaling/vertical warping or new hitches. Exercise hop/spin reactions and field/menu/battle transitions.
3. Repeat with two same-build clients, observing the other player and both followers, including different elevations, map changes and reconnect. Names/status markers should remain legible while bodies pass behind objects.
4. Repeat with software 3D and OpenGL 3D (native and increased internal resolution). Unit tests do not exercise hardware readback timing, framebuffer orientation or native object placement.
