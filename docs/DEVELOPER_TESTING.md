# Developer testing

Run the launcher mirror check before packaging or changing launcher UI code:

```powershell
python launcher-source/tools/check_launcher_tree_parity.py
python -m unittest discover -s launcher-source/tools -p "test_launcher_tree_parity.py"
```

The `launcher-source/tools/launcher_ui/` tree is canonical. The matching tree in `maintenance-tools/tools/launcher_ui/` must have the same files and bytes; the check reports missing, extra, or changed files.

The packaging validation regression check runs both packagers under Python optimization and confirms that release guards still reject failed checks:

```powershell
python -m unittest discover -s launcher-source/tools -p "test_release_validation.py"
```

The companion interaction harness compiles a production header from a separately obtained melonDS source tree. A clean public checkout does not contain that external source. Pass the source root and an immutable source identity explicitly. The runner records the supplied identity and header hash, but it does not authenticate the source origin, so it always labels this evidence `UNVERIFIED SOURCE`.

```powershell
python maintenance-tools/tools/test_companion_interactions.py `
  --source-root "PATH_TO_EXTRACTED_MELONDS_SOURCE" `
  --source-id "UPSTREAM_URL@FULL_COMMIT_OR_RELEASE" `
  --expected-header-sha256 "EXPECTED_64_CHARACTER_HEADER_HASH" `
  --cxx "PATH_TO_GXX" `
  --qt-root "PATH_TO_QT6_INSTALLATION"
```

The source root must contain `src/frontend/qt_sdl/FollowerInteraction.h`. The Qt root must contain `include/qt6/QtCore` and `lib`; `--expected-header-sha256` is optional when no authoritative expected hash is available. The runner prints source identity, header hash, compiler path and version, OS, Qt path and compiler flags before compiling. Its C++ checks remain active regardless of `NDEBUG`.

## Recorded local verification

On 2026-10-18, the companion harness compiled and ran on Windows 10 build 19045 with MSYS2 GCC 16.2.0 and Qt 6.11.2. It passed 5,000 nature/action/friendship/variation combinations and checks covering all 649 species, read-only Pokémon data, interaction cues, and running reactions.

The tested source root was `../../melonDS-source-1.1` relative to this repository. Its Git remote is `https://github.com/melonDS-emu/melonDS.git` at base commit `b86390e4428bf38ce4c1ce0e9ca446d6d25955e8`, but the working tree contains extensive local changes and the tested `src/frontend/qt_sdl/FollowerInteraction.h` is untracked. That header's SHA-256 was `0400efaa06c29306341878b169013f1bb0389d0f3c1c9825518bc74ac4e37449`. Mark this evidence `UNVERIFIED SOURCE`: it covers those local bytes only and does not verify the released emulator or in-game behavior. The temporary C++ source and executable were removed automatically after the run.

## Feature audit verification

On 2026-10-18, a source and launcher audit corrected four issues: the root `VERSION.txt` lagged the published 2.0.16 release, the Mega Evolution guide still identified itself as 2.0.9, the maintenance launcher bundle lacked current updater/cleanup/relay components, and the emulator input patch used a signed integer for an unsigned button mask. The maintenance launcher now packages the shared relay modules it imports. A regression check keeps the root, canonical launcher, and maintenance launcher versions aligned, and the source harness checks the Mega chord's mask type.

The following checks passed from the Unova Together repository on branch `codex/audit-feature-fixes`:

```powershell
py -3.12 -m unittest discover -s launcher-source/tools -p 'test_*.py'
py -3.12 -m unittest discover -s maintenance-tools/tools -p 'test_*.py'
py -3.12 launcher-source/tools/check_launcher_tree_parity.py
```

The canonical launcher suite passed **117 tests**. The maintenance launcher suite passed **139 tests**, including its updater, cleanup, relay, and GUI/service checks. The launcher mirror check passed. The maintenance suite's emulator-facing companion and presence harnesses were pointed at the sibling melonDS checkout described below; those results are not evidence for a clean upstream source tree.

The additional native CMake regression suite passed **18/18 tests** with CMake 4.4.1, Ninja 1.13.2, GCC 16.2.0, and Qt 6.11.2. A reproducible local run is:

```powershell
$build = Join-Path $env:TEMP ('unova-native-audit-' + [guid]::NewGuid().ToString('N'))
cmake -S ..\..\melonDS-source-1.1\tools -B $build -G Ninja
cmake --build $build
ctest --test-dir $build --output-on-failure
$tempRoot = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\'
$resolvedBuild = [IO.Path]::GetFullPath($build)
if (-not $resolvedBuild.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $resolvedBuild) -notmatch '^unova-native-audit-[0-9a-f]{32}$' -or
    ((Get-Item -LiteralPath $resolvedBuild).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw "Refusing to remove unexpected test output: $resolvedBuild"
}
Remove-Item -LiteralPath $resolvedBuild -Recurse -Force
```

Use a fresh temporary build path and remove it after recording the result. The suite covers source-level Mega Evolution assets/rules and battle lifecycle, stone placement, co-op packet handling, follower trail and interaction behavior, input chords, field-warp ABI, and selected item, trainer, and stat helpers. Optional tests that need a Redux ROM, RAM capture, menu ROM, or ENet library were not enabled. The suite does not load a ROM or prove game behavior.

Emulator-facing checks were run against `../../melonDS-source-1.1`, whose Git remote is `https://github.com/melonDS-emu/melonDS.git` and base commit is `b86390e4428bf38ce4c1ce0e9ca446d6d25955e8`. That checkout has extensive local modifications and untracked files. The audited `src/frontend/qt_sdl/EmuInstanceInput.cpp` bytes had SHA-256 `C66ABA6A41BFFC585E0BC1332C2BEEE209BF03795EC07D92F61945CC23E1811B`; the tested `MultiplayerPanel.cpp` and `EmuThread.cpp` hashes were `8FE0E9D3AC5F50423499EB934AF552D6C5D1DEF7871EF7D4B015C0375BE804F1` and `B62A8D194D7E045B1285BDFCEDBBF0B0D003A9BEA53DEF48E24A1AC55330EA51`. Mark all evidence from this checkout `UNVERIFIED SOURCE`; it identifies the bytes tested, not an authenticated release.

The 2026-10-18 feature audit did not run the emulator, load a save, apply a ROM patch, host or join a second player, or verify any feature in-game. Its runtime and two-client checks were **NOT RUN**. The later save-continue regression run is recorded below. Shop scrolling, Mega Evolution in single/double/co-op battles, Cynthia's event and rematch, teleport, follower depth/animation, and movement hitching still need player-runtime checks against the released emulator and supported Redux game. No personal ROM, save, or active installation was used or changed.

### Save-continue stall regression

On 2026-10-19, the packaged Unova Together 2.0.16 emulator (SHA-256 `c36251230b88c61a2078defc5cd761e0629fac41453249a861918f7774d6a21c`) reproduced a black-screen stall after selecting Continue, with melonDS still responsive and the field-map observer unable to resolve a map. It reproduced on three save copies and on both the base and Cynthia-patched Unova Together ROMs. A no-save boot reached the New Game intro, and restoring a slot-1 state rendered Route 7. The 2.0.16 source archive used for the fix is SHA-256 `6d29cbbcc05376f4e53027e27d8acaf97ccbf52a6904128113ccc84f5f7aad76`.

An A/B run isolated the failure to Mega Evolution's replacement of ARM9 overlay 36, the field engine and shop UI overlay. Disabling the Mega cartridge overlay let the same save load; disabling only Mega artwork did not. Keeping the Mega ROM asset and item patches while restoring the original overlay also loaded successfully. The original replacement carried a separately rebuilt field engine, changing 12,652 runs (215,751 encoded bytes) outside the shop-specific need.

The source patch now preserves the Redux overlay except for the shop UI routine span at virtual addresses `0x021ABB70`–`0x021ADC6A` and the 448 appended helper bytes used by the expanded shop. The range boundaries are checked against the overlay-36 symbols `s0149_CallFriendlyShopBuy` and `GetMoveTutorShopSortimentBits` in the [pinned Black 2 decomp symbol map](https://github.com/fuddlesworth/pokebw2/blob/81eea95ee66e9ab41dedf5ead08ff1d3222cbef5/config/b2_us/arm9/overlays/ov036/symbols.txt); the map is a range reference, while runtime compatibility was checked against the supported Redux ROM. The resulting delta is 233 runs, 7,180 changed bytes and 8,345 encoded bytes. The patch packager now marks lines from files without a final newline, preventing adjacent changes from fusing or failing to apply. Regression tests verify the byte range and patch parseability.

**SOURCE/UNIT VERIFIED:** Five focused tests pass. The Mega asset and supported-cartridge checks also pass against the full-size Redux ROM copy, including Mega Stone stock checks. **GAMEPLAY VERIFIED:** A clean CMake Release rebuild from the 2.0.16 corresponding-source archive, using the narrowed `Gen5ShopOverlayPatch.h` from the tracked development patch (SHA-256 `6b2fa0372f02273199a4a06be7beda814390ee189d6fdf0bcbe5dd7ff36ade59`, target CRC `D48275B7`, 233 delta runs), produced `melonDS.exe` SHA-256 `324d47d16526650e9f297bf7096f487fe75ee849414e22867c939190d3b20f08` (10,801,664 bytes). With the MSYS2 UCRT64 runtime available, scripted Continue input reached the Route 7 field (map 337, tile 113,237) after 4,080 frames; the emulator reported input unblocked and rendered both screens. The test ROM copy has SHA-256 `332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a`. The test save copy was SHA-256 `54a3058d8e8b93942c193266a073a965dcd5ebfa2ca89080076729be2e8c0933` before and after. The test used scripted DS button masks rather than physical keyboard input or the launcher, and it does not prove every save or the shop menu's visual layout. The retained-config launch probe did not reach gameplay because TOML serialization failed; see the release validation section below for the 2.0.17 package and 2.0.16 baseline comparison.

### Release source completeness

The 2.0.17 packager referenced 26 command/helper/test sources that were missing from this checkout's maintenance-tools tree. I restored these files from `../../downloads/releases/release-2.0.16/Unova-Together-2.0.16-Source.zip`. The local archive is 31,981,359 bytes; its SHA-256, `6d29cbbcc05376f4e53027e27d8acaf97ccbf52a6904128113ccc84f5f7aad76`, matches the asset digest reported by the published `v2.0.16` GitHub release. Twenty-five restored files are byte-identical to the archive; I removed one extra trailing blank line from `check_rival_agreement.cpp` to keep the diff clean. Restoring these files keeps the release tooling reproducible and retains the co-op utilities in the player package.

### Save-load release validation

**SOURCE/UNIT VERIFIED:** The release package was built from the corrected emulator executable, the regenerated Cynthia BPS files, and matching version 2.0.17 launcher/source. The packager verified both ZIP archives, portable controls, launcher metadata, indexed patch notes, the standalone executable's embedded source, and excluded ROM/save/firmware file types. The launcher UI mirror check passed for 48 files. Five Mega shop overlay tests, three Cynthia event tests, and one optimized release-validation test passed. The launcher suite passed 117 tests; the maintenance suite passed 146 tests with two skipped. The Tailscale bundled installer matched its manifest SHA-256.

**GAMEPLAY VERIFIED:** The clean CMake Release build and scripted Continue test described above reached Route 7 using a disposable ROM and save. **NOT RUN:** A gameplay check from the extracted release package. The direct launch harness exited before gameplay with a TOML serialization error for both the staged 2.0.17 package and a disposable 2.0.16 baseline. Because the same failure occurs on the baseline, this does not establish a new 2.0.17 regression; it does mean the extracted-package gameplay path remains unverified. The package validator parsed the generated portable configuration and confirmed its controls, but that check does not substitute for a successful launch.

### Cynthia Route 7 script branch correction

The event generator had several reversed `CMP_STACK` branches. In the actual VM, `VMJumpIf CMP_STACK` jumps when the popped value is not `1`; the event had treated it as a true branch. This reversed the post-Skyla gate, one-time reward check, party scan, species-to-stone match, and rematch flags. The generator now emits the correct comparison polarity, and validates the compiled script's decoded branch targets and outcomes for all 46 species, an empty/nonempty party, a full Bag, and both rematch results.

**SOURCE/UNIT VERIFIED:** `python launcher-source/tools/test_cynthia_event.py` passed 3 tests. `test_cynthia_route7_rematch.py` passed on generated copies from both supported source ROMs and validated the compiled event logic, trainer roster, levels, Garchompite, and map actors. Before the fix, the validator rejected the existing patched ROM at the first-time gift check. Python 3.14.7, `ndspy==4.2.0`, `Pillow==13.0.0`, and Arm GNU Toolchain 12.3.Rel1 were used. Build dependencies are listed in `launcher-source/tools/requirements-cynthia-route7.txt`. The local BW2 decomp extraction has no Git metadata, so compiler/tooling evidence from that tree is **UNVERIFIED SOURCE**. Its `s001F_VMJumpIf` function body and `field_script.h` comparison constants were compared against official upstream commit `81eea95ee66e9ab41dedf5ead08ff1d3222cbef5`; both matched.

The regenerated Redux patch targets ROM SHA-256 `c34498dc807a83e3d5a5c85a341464c24f56a1ed515db6cfc7ef4e2a71dc3df7`; the matching Unova Together patch targets `234079a05e5360b81b5fbe41d39815bec65193b986ac2d877e23a86d76377220`. A fresh disposable output made from the Redux test ROM copy also matched `c34498dc807a83e3d5a5c85a341464c24f56a1ed515db6cfc7ef4e2a71dc3df7`. The launcher copied each source ROM to its private patch cache, verified the target hash, reused the cached output on a second call, and left the source ROM unchanged.

**GAMEPLAY VERIFIED:** The 2.0.16 filtered-overlay emulator build (SHA-256 `c3de037c3526c80b83a830b32b4e8cb9d0337151eeed7c9a5f207759b53cc3fb`) loaded the exact slot-1 test save with the corrected Cynthia patch. Scripted DS input reached Route 7 (map 337, tile 107,237); melonDS reported input unblocked and rendered the field. The source save was unchanged. This confirms the Continue path for this test save; Cynthia's dialogue, stone award, and rematch battle were not exercised in the emulator. The test used a disposable ROM and save copy, not the launcher or physical keyboard.

### Frost Generation 5 editor parser/export check

On 2026-10-19, the isolated FrostFalcon/FrostsGen5Editor 5.0.1 release was used with `maintenance-tools/tools/run_frost_roundtrip.ps1` against a disposable Cynthia-patched Redux ROM copy (SHA-256 `c34498dc807a83e3d5a5c85a341464c24f56a1ed515db6cfc7ef4e2a71dc3df7`). The editor executable SHA-256 was `30601dceb0ca0a414a690b955bb082c3725352a4ed3c707e536bd3ada5626111`; the setup script pins the official release archive from [FrostFalcon/FrostsGen5Editor 5.0.1](https://github.com/FrostFalcon/FrostsGen5Editor/releases/download/5.0.1/FrostsGen5Editor.zip) and verifies its SHA-256 before extraction. **PASS:** Frost identified the image as Pokémon Black 2, parsed the ROM resources, and exported a ROM image; the source hash was unchanged. The generated output remains in a local, untracked disposable-test directory because the filesystem policy blocked its cleanup. **NOT RUN:** opening the map editor, validating NPC placement, or launching the export in an emulator. This round-trip proves parser/exporter operation for the identified local fixture only; it does not establish the fixture's upstream provenance or gameplay compatibility.

### Mega Evolution focused regression suite

On 2026-10-19, the focused native tests were built from the published 2.0.16 source archive (SHA-256 `6d29cbbcc05376f4e53027e27d8acaf97ccbf52a6904128113ccc84f5f7aad76`) in `temp-npc-catalog-probe/verified-release-source/Unova-Together-Source/source/melonDS/tools`. The tested Redux ROM fixture was `temp-npc-catalog-probe/runtime-repro/app/FullSizeRoute7Test214.nds` (SHA-256 `332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a`). This is evidence about that source archive and test fixture, not a fresh build of the current `main` source.

The isolated Windows build used MSYS2 UCRT64 GCC 16.2.0, CMake, and ENet 1.3.18 from `C:\msys64\ucrt64`. The process-local `PATH` needed the UCRT64 `bin` directory so `cc1plus.exe` could load its runtime DLLs; no system-wide environment or dependency installation was changed. After configuring the optional ENet tests against `C:/msys64/ucrt64/include` and `C:/msys64/ucrt64/lib/libenet.dll.a`, the targeted build and test were:

```powershell
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
cmake -S 'temp-npc-catalog-probe/verified-release-source/Unova-Together-Source/source/melonDS/tools' `
  -B 'temp-npc-catalog-probe/build-mega-tests-v216-filtered' `
  -DUNOVA_ENET_INCLUDE_DIR:PATH='C:/msys64/ucrt64/include' `
  -DUNOVA_ENET_LIBRARY:FILEPATH='C:/msys64/ucrt64/lib/libenet.dll.a'
cmake --build 'temp-npc-catalog-probe/build-mega-tests-v216-filtered' --target coop_mega_lan
ctest --test-dir 'temp-npc-catalog-probe/build-mega-tests-v216-filtered' --output-on-failure -R 'mega_|gym_leaders'
```

**PASS:** 14/14 selected tests passed: `native_mega_evolution_sound_asset`, `mega_rules_and_assets`, `mega_native_selection`, `mega_party_ability_restore`, `mega_stone_preview_centering`, `mega_native_call_transaction`, `mega_coop_packet`, `mega_release_roster`, `mega_full_gif_sprite_stream`, `mega_item_mail_and_pocket_compatibility`, `gym_leaders_6_to_8_mega_teams`, `mega_coop_lan_transport`, `mega_redux_cartridge`, and `mega_ate_hook_signatures`. The ENet test used a synthetic RAM/CPU fixture to exercise a host and guest loopback, message validation, remote form application, and session teardown. The tests also cover simulated double-battle selection and configured Cynthia/Gym Mega teams. These checks do **not** prove actual emulator clients, trainer AI activation in a live battle, high-latency behavior, or gameplay in the released executable.

**ROM ARTIFACT CHECK:** On the same supported-ROM fixture, ARM9 overlay 142 has RAM base `0x021998C0`; bytes at `0x0219E4DC` match the expected selected-item preview function signature `F0 B5 85 B0 0E 1C 6B 21`. The 47 imported Mega Stone icon arrays have opaque pixel bounds and nonzero-pixel centroids centered on the 32×32 canvas. This supports the conclusion that the selected-item preview offset is caused by the renderer actor's native coordinates, not transparent padding in the icon files. It does not verify the Bag, mart, or battle screen visually; those still need an in-game check.

### Mega cartridge and sprite follow-up — 2026-10-19

Using the existing Release test build from the 2.0.16 source archive (SHA-256 `6d29cbbcc05376f4e53027e27d8acaf97ccbf52a6904128113ccc84f5f7aad76`), the battle-selection, native-call, gym-team, ENet co-op, and Mega Stone preview-layout executables all passed. Assertions were enabled in that build. The supported Redux ROM fixture (`332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a`) also passed the full Mega cartridge-overlay check, Gym Leader overlay check, and ARM9 hook-signature check; its SHA-256 was identical before and after these read-only checks. The cartridge test confirmed Mega Stone stock in every Poké Mart and both BP counters.

The ROM-side sprite test reports animated artwork on 84 of 92 front/back sides. Static fallbacks are Sceptile front and back, Mawile front and back, Aggron front and back, Altaria front, and Glalie back. The emulator preview hook remains guarded by the verified Redux actor-creation call and only changes matching Mega Stone preview coordinates. These source and ROM checks do not verify the Bag or mart visually, a live trainer Mega action, or an actual two-client battle; those gameplay checks remain **NOT RUN**.

### Maintenance test discovery and external fixtures

On 2026-10-19, maintenance test discovery was hardened so native checks are registered with `unittest` and ROM/RAM-dependent checks no longer read private fixtures while Python imports the test modules. The decompression and wireless-crop boundary test compiles the extracted production routines in a temporary directory. Its external melonDS source tree and C++ compiler must be supplied when not on the default local paths:

```powershell
$env:UNOVA_MELONDS_SOURCE_ROOT = "PATH_TO_EXTRACTED_MELONDS_SOURCE"
$env:UNOVA_CXX = "PATH_TO_GXX"
py -3.12 -m unittest discover -s maintenance-tools/tools -p 'test_release_input_bounds.py' -v
```

The optional co-op story harness uses `UNOVA_COOP_STORY_CAPTURE`, `UNOVA_COOP_CONTEXT`, and `UNOVA_MELONDS_SOURCE_ROOT`. The rival-payload test takes a user-supplied Redux v1.4.1 ROM path in `UNOVA_TEST_REDUX_ROM`; its shared native setup helper uses `UNOVA_COOP_CONTEXT` and `UNOVA_MELONDS_SOURCE_ROOT`. The launcher cheat-engine harness additionally needs `inspect_inventory.py`, a captured RAM fixture (`UNOVA_TEST_LAUNCHER_RAMDUMP`), three ROM profile fixtures (`UNOVA_TEST_ROM_ORIGINAL`, `UNOVA_TEST_ROM_REDUX`, and `UNOVA_TEST_ROM_UNOVA`), and the same melonDS source/compiler. These ROM and memory files are not distributed or committed. A configured but missing fixture fails clearly; an unconfigured, unavailable optional fixture is reported as skipped.

The complete launcher suite passed **117 tests** on rerun; the launcher UI module passed **32 tests**. The maintenance suite passed **150 tests with five skips**. The skips cover unavailable private ROM/RAM assets or optional runtime dependencies; they are not passes for those runtime scenarios. The native boundary check passed against the local `maintenance-tools/melonDS-source-1.1` tree using MSYS2 UCRT64 GCC 16.2.0, `-std=c++20 -O2 -Wall -Wextra -Werror`, and its installed zstd library. The exact source files tested had SHA-256 `9F4F73A0AC31DCA236F1C6A38F20093C38BE6E68922B056C41ED054C5BB99EA3` (`src/frontend/qt_sdl/EmuInstance.cpp`) and `1305DFE963C48F276B68F2484999F191124466A1E34247A0BDB91398ACE16006` (`src/Wifi.cpp`). The local source tree has no authenticated revision in this checkout, so this result is **UNVERIFIED SOURCE** and proves only the exact local bytes exercised by the extracted-routine test, not the published emulator or gameplay.

### Updater and installation path hardening

On 2026-10-19, disposable regression tests reproduced writes through junctions at `.updates` and `.updates/versions` before the old updater rejected the active slot. Follow-up tests found the same issue in the single-executable bootstrap. The path checks also missed NTFS hard links: an empty hard-linked install lock or metadata `.pending` file could be written through to its other directory entry. These cases affected update installation, storage cleanup locks/atomic records, standalone first-run setup, and launcher repair locks.

The shared storage helper now rejects reparse points and multiply-linked managed metadata files. The updater and standalone installer validate their update directories, slot, lock, and activation markers before writes and again before activation. The standalone bootstrap now uses the shared installation lock; launcher repair validates its lock path as well. The files mirrored between `launcher-source/tools` and `maintenance-tools/tools` remain byte-identical.

**PASS:** Before the correction, the new updater, storage, and standalone-junction tests failed because the unsafe operations were allowed or rejected only after writes. After the fix, `python -B -m unittest -v test_unova_updater test_unova_storage test_unova_single_exe test_launcher_migration` passed **47 tests**. Coverage includes junctions, hard-linked locks and pending records, checksum/cancellation paths, standalone updates, migration and cleanup preservation. `git diff --check` passed. All filesystem fixtures were temporary; no user installation, ROM, save, or release asset was touched.

The first full-discovery attempt used Python 3.14, where `tomlkit` and Pillow were absent, so six modules failed during import before their tests ran. On 2026-10-19, the full maintenance suite was rerun with the installed Python 3.12 environment, which includes those dependencies:

```powershell
py -3.12 -B -m unittest discover -v
```

**PASS:** 166 tests ran; all passed, with six optional ROM/RAM or external-runtime checks skipped. This includes the updater, storage, standalone installer, migration, launcher services, GUI, and Legendary Researcher static checks. The skips do not count as runtime/gameplay verification.

### Launcher atomic staging-write safety

A disposable regression test found that save restore used a predictable staging filename and opened it in truncating mode. The same write-through affected the Cynthia patch and player-model ROM-copy caches and the updater's integrity manifest. A pre-existing hard link at a staging path could therefore overwrite the other linked file. The shared launcher atomic-write helper now creates a UUID-named staging file with exclusive creation before replacing its destination. Save restore, launcher settings, news and guide caches, diagnostic ZIP exports, Cynthia patch copies, and player-model copies use this path. Integrity manifests now go through the storage helper that rejects linked staging and destination files. The standalone Cynthia ROM builder also reserves a unique staging path; tests verify it preserves a stale pending symlink and rejects a hard-linked staging collision. Existing predictable pending files are left untouched. Hard-link regressions cover these paths; before the corrections, the save, event-copy, player-model, and integrity-manifest tests reproduced linked-file overwrites.

**PASS:** The canonical launcher suite passed **127 tests**. The full maintenance suite passed **167 tests**, with six optional ROM/RAM or external-runtime checks skipped. The launcher UI mirror check passed for 48 files, and its focused parity tests passed 3/3. The services module passed **18 tests in each launcher tree**. The focused Cynthia builder test passed 2 tests; the canonical Cynthia-event, player-model, preferences, and services tests passed 37 tests; the maintenance preferences, services, and UI tests passed 61 tests. The storage/updater focused checks passed 30 canonical tests and 35 maintenance tests. All hard-link and symlink fixtures were isolated in `TemporaryDirectory`; no real ROM, save, or installation was accessed.

### SwissArmyKnife map-editor build check

On 2026-10-19, the SwissArmyKnife `08c997485826f8fcd1e0dffbcafb205d1b32726b` checkout was built against compatible pre-rework revisions of BeaterLibrary (`eae45a67405a9541e5676e03bfbde644f8c51162`), Hotswap (`10c74328e00dc994fd739733a6b4645504184fb5`), and NitroSharp (`2287b99b7c926eff1db237e0467f59917c0f045e`). All four were cloned from their official PlatinumMaster GitHub repositories. The previous mix of later dependency revisions failed with missing API types. A later aligned attempt hit a stale Avalonia `original.pdb` lock; after shutting down the idle .NET build servers, this serial command succeeded:

```powershell
dotnet build SwissArmyKnife/SwissArmyKnife.Avalonia.csproj `
  --configuration Release --verbosity minimal --nologo `
  --maxcpucount:1 --nodeReuse:false /p:UseSharedCompilation=false
```

**PASS:** .NET SDK 10.0.400 compiled BeaterLibrary, NitroSharp, Hotswap, and SwissArmyKnife.Avalonia. The build emitted warnings for the editor's net6.0 target and existing AES/member-hiding code. **NOT RUN:** Loading Redux into the editor and viewing a map remain unverified. The app startup window was listed, but two Windows screenshot captures failed with `FrameArrived timed out` / `window capture timed out`. The disposable configuration referenced the test ROM image (SHA-256 `c34498dc807a83e3d5a5c85a341464c24f56a1ed515db6cfc7ef4e2a71dc3df7`); no project was exported, and its hash remained identical before and after the attempt. See [Legendary Researcher research](LEGENDARY_RESEARCHER_RESEARCH.md) for placement status and remaining checks.

### Atomic installation-record staging race — 2026-10-19

`unova_storage.atomic()` validated a predictable `.pending` path and then wrote through that same path. A hard link inserted after validation could redirect the metadata write into another file. The helper now creates a UUID-named staging file with exclusive creation, writes through its open descriptor, checks the destination and staging entry again, and atomically replaces the destination. A pre-existing legacy `.pending` link is still rejected before any write. The implementation is byte-identical in the canonical and maintenance launcher trees.

**PASS:** The race-injection regression test preserves an external hard-linked sentinel and writes valid JSON to the intended metadata file. **PASS:** The negative control against pre-fix `unova_storage.py` from commit `a21c75bead764d6ed9f0a61422d8e13c6f68bc99` produced the expected failure: the sentinel was overwritten with metadata JSON. The isolated negative-control fixture was removed automatically after the run.

The exact full-suite commands were `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py' -v` (**128 passed**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py' -v` (**168 run: 162 passed, 6 skipped**). The launcher mirror check passed for 48 files, and `git diff --check` passed. Tests exercised the active checkout's Python production modules and temporary filesystem fixtures; optional ROM/RAM/external-runtime checks were skipped. No installation, ROM, save, update slot, or release artifact was modified.

The follow-up audit found the updater and standalone bootstrap still wrote activation records through fixed `.pending` paths after checking them. Both now use `unova_storage.atomic()` for activation JSON, retaining checks for legacy staging names. New race-injection tests insert a hard link after the final path check, execute the real install routines against disposable archives, and confirm the external sentinel remains unchanged. **SOURCE/UNIT VERIFIED:** Focused tests passed in the canonical launcher (20 tests) and maintenance tools (51 tests, including updater, storage, standalone bootstrap and migration). The new updater and standalone regression tests also failed as expected when run against the pre-fix production files from commit `bd8722d6af478fab54a05b868f37bcdc73ea82cb`. These tests use synthetic archives and temporary filesystem fixtures; no user installation was exercised.

After the follow-up changes, the complete canonical launcher suite passed **129 tests**; the maintenance suite passed **170 tests with six optional skips**. The UI mirror check passed for 48 files, and `git diff --check` passed. The supported `build_unova_launcher.py` packaging script built the Windows launcher with PyInstaller 6.22.3 and Python 3.12.8 on Windows 10. The temporary 2.0.17 launcher was 3,623,233 bytes with SHA-256 `d0069c9ac80b1bde1baaddb3b3d79199781e669cf4f2ecf3b0dfb792fb394b57`; its build directories were removed after verification. The standalone one-file bootstrap was not rebuilt, and no release asset, tag, ROM, save, or installed game was changed.

### Mega verification replay against the published 2.0.17 source — 2026-10-19

The Mega suite was rebuilt from a fresh extraction of the published [2.0.17 source asset](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v2.0.17). Its SHA-256 was `3d57a84e8e420dbd89b62a8e59dfda2fb4315b6113122766ccf8fc5a75180253`, matching the release asset digest. The Redux fixture was `FullSizeRoute7Test214.nds`, SHA-256 `332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a` before and after testing. CMake 4.4.1, Ninja 1.13.2, MSYS2 UCRT64 GCC 16.2.0, Qt, and ENet were used; build and extracted-source directories were held in an automatically removed temporary directory.

For a rerun, set `$sourceRoot` to the extracted `Unova-Together-Source` folder, `$buildRoot` to a fresh temporary build directory, and `$reduxRom` to a disposable supported Redux ROM copy. The equivalent PowerShell commands are:

```powershell
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
cmake -S "$sourceRoot/source/melonDS/tools" -B "$buildRoot" -G Ninja `
  -DCMAKE_BUILD_TYPE=Release `
  -DCMAKE_CXX_COMPILER=C:/msys64/ucrt64/bin/g++.exe `
  -DUNOVA_MEGA_ROM:FILEPATH="$reduxRom" `
  -DUNOVA_ENET_INCLUDE_DIR:PATH=C:/msys64/ucrt64/include `
  -DUNOVA_ENET_LIBRARY:FILEPATH=C:/msys64/ucrt64/lib/libenet.dll.a
cmake --build "$buildRoot" --parallel 4
ctest --test-dir "$buildRoot" --output-on-failure `
  -R 'mega_|gym_leaders|gen5_coop_role'
```

**PASS:** 15/15 selected CTest checks passed. The build compiled the published production Mega headers and test programs; the checks cover the 49-form roster and form data, stone/item mappings, move-selection transformation logic, ability restoration, artwork stream and icon layout, three final Gym Leader Mega teams, co-op packet handling, a synthetic host/guest ENet loopback, Redux shop/overlay resources, and Mega hook signatures. In the production battle helper test, a matching held stone plus a committed Fight action produces the expected opponent form event; a stale peer, wrong stone, missing Fight action, or invalid battle ID is rejected. The Redux cartridge tests read the fixture and left its hash unchanged.

**SOURCE/UNIT VERIFIED:** The C++ test programs compile the published production headers and exercise the Mega rules and event-selection helpers. **INTEGRATION VERIFIED:** ROM-specific tests inspect the real Redux cartridge and the generated overlay data. The LAN test uses a synthetic RAM fixture and loopback transport, not two running emulator clients. **NOT RUN:** live Gym Leader/Cynthia AI behavior, player battles, high-latency multiplayer, and two-client co-op gameplay remain unverified.

### Updater settings-copy hard-link safety — 2026-10-19

Two install paths copied `melonDS.toml` directly over staged settings files: the standalone bootstrap when reusing an installed slot, and the normal updater after extracting a verified release. Disposable regression tests injected a hard link at each destination. Before correction, both real install routines overwrote an external sentinel from `keep these controls` to `player controls`. Both paths now use the UUID-named, exclusive staging helper in `unova_storage.py`, validate the managed source and destination, then atomically replace the staged settings file. Unsafe hard links abort the install before the active-version marker changes. A separate race-injection test creates a hard link after path validation and confirms that the external file remains unchanged.

**PASS:** The new `test_updater_settings_copy.py` tests exercise the actual `install()` functions in both launcher tool trees with a synthetic, checksummed release archive and isolated temporary installation. They failed before the change with the external sentinel overwritten and passed after it, with the update left inactive and the old settings preserved. The earlier standalone regression also passes. The tests do not use a released installer or the user's installed game.

**PASS:** Full discovery with Python 3.12 ran `py -3.12 -m unittest discover -s . -p "test_*.py"` in `launcher-source/tools` (**132 tests passed**) and `maintenance-tools/tools` (**173 tests run, 6 optional fixture/runtime checks skipped**). A disposable 2.0.17 launcher build had succeeded for the preceding standalone-copy change, but the launcher was not rebuilt after this updater change and no executable was launched. No user install, ROM, save, or published release asset was accessed or changed.

### Pokémon Center overlay collision follow-up — 2026-10-19

The supplied Cynthia Route 7 save (SHA-256 `4336e7e447fa88cd39dce2b7eef44324fa43f87c5722dca1f00dc84d85635ac7`) reproduced the same `GFL_DebugAssertFail` while entering a Pokémon Center on both the Cynthia-patched ROM and a clean Redux control. Both runs used the same locally patched emulator, so this rules out the Cynthia event as the cause but does not test an unmodified emulator. The direct trigger is the Mega shop overlay patch: it advertised overlay 36 (`fieldmap`) as `0x56360` bytes instead of its original `0x561a0`, while retaining its `0x10040` BSS. The enlarged allocation ended at `0x021e59a0`, overlapping Pokémon Center overlay 65 at `0x021e5800` by `0x1a0` bytes. The original allocation ends at `0x021e57e0`, 32 bytes before overlay 65.

The rebuilt overlay's 448-byte tail contains source/assertion strings. The patched shop UI range (`0x021abb70`–`0x021adc6a`) has no disassembled or literal-pointer references into that tail. The generator now copies only that UI range and preserves overlay 36's original size. The generated delta is 232 runs, 6,732 changed bytes and 7,892 encoded bytes; its target CRC32 is `3dc1fed8`. The runtime patch therefore keeps the original RAM size, file size and BSS range while retaining the heap-backed shop routines.

**PASS — SOURCE/UNIT VERIFIED:** `python maintenance-tools/tools/test_gen5_shop_overlay_patch.py` passed 5/5 tests. The tests verify tail omission, patch parseability, the exact generated overlay size, that every delta run stays within the shop UI span, and that the resulting fieldmap allocation ends before overlay 65. `git diff --check` also passed.

**PASS — BUILD; GAMEPLAY RESULT RETRACTED:** The build issue was the missing `C:\msys64\ucrt64\bin` entry in the process `PATH`; adding the installed UCRT64 toolchain directory let CMake identify GCC 16.2.0 and compile successfully. From the authenticated 2.0.17 source archive above, the production ROM-patching targets built and the focused CTest group passed **3/3** (`mega_redux_cartridge`, `mega_rules_and_assets`, `mega_stone_preview_centering`). The complete emulator also built successfully. The local candidate executable SHA-256 was `fef29c8a13969141d6313643bdd3dd31b45f891675f6ae7c219b3f60b3ca70de`; it was a test build, not a release binary. The gameplay conclusion below is superseded by the visual recheck recorded under “Runtime probe rejects fatal game screens.”

The exact supplied save (`4336e7e447fa88cd39dce2b7eef44324fa43f87c5722dca1f00dc84d85635ac7`) was copied to a disposable sidecar beside the matching Cynthia Route 7 ROM (`1099144137c6d4026b2d06dff8723254d59456963eaaf05e093d7f377ba3a3fe`) and loaded by that candidate. The observer reached the Center interior at map 460, tile `(7, 19)`, and the emulator remained running through the 105-second probe window. At the time, those signals were treated as a successful entry; a later visual recheck found the Gen 5 fatal error screen, so the runtime result is **not a pass**. Both source and test save retained the original SHA-256.

The reusable runtime probe requires `--expect-map 460` for this entry scenario. Its output folder must contain `.disposable-test-output`; the runtime, ROM, and existing matching `.sav` sidecar must resolve inside that folder before melonDS launches. It returns a nonzero status if its observer report or either captured DS screen is missing, the expected map was not reached, input is blocked or its state is missing, a fatal screen is detected, or an assertion appears in the emulator logs. Its regression suite covers missing reports and screens, wrong map, malformed observer data, assertion markers, unreadable screenshots, and safe fixture boundaries. This prevents stale map state or a timed-out process from being treated as successful gameplay.

### Runtime probe requires complete observer state — 2026-10-19

Python treats `bool` as a subclass of `int`, so malformed reports could pass the positive-frame check with `"npcFixtureFrames": true`, or pass an expected map comparison with `"map": true` when map ID 1 was requested. The probe now requires real integer frame and map values plus an explicit boolean input-state field. Regression cases reproduced those false passes and success when input-state data was missing or malformed. A separate safety check prevents launching outside a marked disposable folder or without its save sidecar. The focused probe suite passes **13/13**, and full maintenance-tools discovery passes (**212 run, six optional skips**). This changes only test-report validation and test setup safety; it does not add gameplay evidence.

The generator regression suite still passes **5/5**. The overlay-generator unit tests verify patch layout but do not prove that the released emulator applies that patch correctly at runtime. The separate 09:31 manual backup archive (`20261019-093151-manual-ec4f49.zip`, contained save SHA-256 `54a3058d8e8b93942c193266a073a965dcd5ebfa2ca89080076729be2e8c0933`) was not independently reproduced in this run.

### Runtime probe rejects fatal game screens — 2026-10-19

The saved-game runtime probe previously treated a live emulator, the expected map ID, and an unblocked-input flag as enough to pass. That was a false positive: the game can retain the map observer state after drawing its fatal “An error has occurred. Please turn off the power.” screen. The released 2.0.17 `melonDS.exe` (SHA-256 `324d47d16526650e9f297bf7096f487fe75ee849414e22867c939190d3b20f08`) reproduced it at Center interior map 460, tile `(7, 19)`, on the exact save (SHA-256 `4336e7e447fa88cd39dce2b7eef44324fa43f87c5722dca1f00dc84d85635ac7`) and disposable Cynthia-patched ROM copy (SHA-256 `1099144137c6d4026b2d06dff8723254d59456963eaaf05e093d7f377ba3a3fe`). The top-screen PNG was 256×192, 97.44% dark, and contained only three colors; it visibly showed the Gen 5 fatal error message. A second run with the user's selected source ROM (SHA-256 `353fb0cf82c3e4eddfc8986efa8910b00eb1c4d6f106c220abef59d69d3a520a`) produced the same fatal screen. The user save was never modified.

This exposed a source/package mismatch. The release's 2.0.17 source tree has the size-preserving shop-overlay payload (target CRC `3DC1FED8`), while its Windows executable has the same SHA-256 as the earlier runtime built with the old `D48275B7` payload. The verified extracted 2.0.17 source tree and the local source tree were byte-identical across **1,839 files**. Rebuilding that source with CMake 4.4.1, Ninja 1.13.2, MSYS2 UCRT64 GCC 16.2.0 and Qt 6.11.2 produced a test-only executable (SHA-256 `09c09bcc86e8b5200e728973957e17bc9b9952b4f961009c59f483d6d6babc99`). On the same disposable ROM/save and Center-entry script, that executable reached map 460, tile `(7, 19)`, stayed responsive for 75 seconds / 4,440 observer frames, and rendered normal Center screens. The source save remained unchanged. This A/B result identifies the stale executable package as the cause; it does **not** update or validate a newly distributed release binary.

The runtime probe now requires both 256×192 screenshots and rejects low-color screens that are at least 95% dark, in addition to its observer/log checks. It specifically catches the observed Gen 5 fatal screen. Tests cover the fatal-screen false pass, normal colorful captures, and missing/unreadable screenshots.

**PASS — SOURCE/UNIT VERIFIED:** The negative regression test reproduces the old false pass using valid observer progress with synthetic fatal-screen captures; the corrected probe fails it. Colorful screenshots pass and missing/unreadable images fail. The saved-reload harness accepts explicit runtime and ROM paths and normalizes the packaged TOML correctly. Re-running it with the exact save, 2.0.17 runtime and Cynthia-patched ROM returned `normalBoot=true`, `savestateUsed=false`, and `reloadVerified=true`; the resulting party/PID/XP/level/move list and badge mask matched PKHeX.Core inspection, and the source save hash remained unchanged. The focused probe/config tests passed **18/18**; full maintenance discovery passed **221 tests with 6 optional checks skipped**. **PASS — TEST-BUILD GAMEPLAY:** The rebuilt 2.0.17 source runtime passed the exact-save Center-entry scenario with both screens captured normally. **FAIL — RELEASE GAMEPLAY:** The published 2.0.17 Windows executable still reaches the fatal screen. A corrected Windows runtime must be built and distributed before the installed release is fixed; no release binary or tag was changed here.

### Party IV/EV viewer audit — 2026-10-19

**PASS — SOURCE/UNIT VERIFIED:** `py -3.12 -B maintenance-tools/tools/test_party_stats.py` compiled the production `Data`, `crypt`, and `Inspect` function bodies extracted from the locally authenticated 2.0.17 source archive (SHA-256 `3d57a84e8e420dbd89b62a8e59dfda2fb4315b6113122766ccf8fc5a75180253`). All 96 encrypted cases passed across 24 party-record block permutations and egg/nickname flag combinations. The harness checked known IV and EV values in displayed stat order, the EV total, checksum and busy-record rejection, and byte-for-byte preservation during inspection. This exercises extracted production decoder functions, not the complete emulator UI or live save.

No decoder defect was found in these cases. **NOT RUN:** A live visual comparison against a save with independently known EV values was not available, so this does not prove the report for every Pokémon in the supplied save.

### Malformed release metadata handling — 2026-10-19

The GitHub release selector assumed every API entry had a list of assets with unique string names and official download URLs. A malformed entry could raise an uncaught `TypeError` (`assets: null` or a non-string asset name), or a `KeyError` for a missing download URL, preventing the launcher from finishing its update check. The selector now skips malformed or ambiguous candidates and continues to valid releases. When no installable release remains, the existing release-notes fallback is preserved.

**PASS — SOURCE/UNIT VERIFIED:** Before the fix, direct calls to the production selector reproduced the `TypeError` and `KeyError` cases. Afterward, both canonical and maintenance launcher tests verify malformed names, missing/non-list assets, missing or non-string URLs, duplicate required assets, fallback to a valid release, and release-note fallback when all candidates are unusable. The focused versioning suite passed **14/14** in each tree. Full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**134 tests**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**179 run, six optional skips**). `py -3.12 -B check_launcher_tree_parity.py` passed for 48 UI files, and both updater and versioning-test mirrors were byte-identical. **NOT RUN:** No live GitHub request, packaged launcher build, or installer/update operation was performed.

### Invalid save-backup manifest recovery — 2026-10-19

The restore service assumed the backup manifest decoded to a JSON object. A valid ZIP containing a JSON list reached `.get()` and raised an uncaught `AttributeError`, which the launcher restore callback did not handle. The restore path now validates the manifest, save entries, member list, size bounds, checksums, and supported compression before starting the existing pre-restore backup or writing any save. Invalid backup data raises a user-facing validation error.

**PASS — SOURCE/UNIT AND UI VERIFIED:** The production restore service now rejects five malformed manifest shapes and leaves the current save byte-for-byte unchanged. The launcher UI test confirms the error is shown in the status area without escaping the callback. Valid single-save and multi-save backup/restore tests, checksum rejection, hard-link protections, and before-restore backup behavior passed. **NOT RUN:** No user backup or live game save was opened or changed. Final full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**137 tests**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**182 run, six optional skips**). `py -3.12 -B check_launcher_tree_parity.py` passed for all 48 UI files.

### Corrupt active-update metadata recovery — 2026-10-19

The launcher resolves the active version slot during startup. A truncated or structurally invalid `.updates/active.json` could therefore raise a JSON, type, or key error before the repair UI opened. Startup now falls back to the installation root when active metadata is invalid, while strict runtime resolution still rejects it. Version reporting tolerates invalid marker and `VERSION.txt` data and falls back to a valid marker version or `0.0.0`.

**PASS — SOURCE/UNIT VERIFIED:** A production-path test covers truncated JSON, a JSON list, a missing version, a null version, and an oversized marker. Repairable startup resolves to the install root and version lookup uses that root's `VERSION.txt`; strict resolution raises `ValueError`. Existing valid slot, missing runtime, and traversal rejection tests also pass. Full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**137 tests**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**182 run, six optional skips**). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**.

### Malformed installation receipt recovery — 2026-10-19

Old-install cleanup could crash when an installation receipt contained valid JSON with a non-object top level, such as `[]`. The shared storage-record reader now rejects non-object records as invalid. Cleanup reports the affected installation as skipped and preserves its files.

**PASS — SOURCE/UNIT VERIFIED:** A production cleanup test reproduces a malformed receipt on a disposable three-version install, confirms cleanup completes with a skip report, and confirms the old runtime remains. The same test passes in both launcher trees. Final full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**138 tests**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**183 run, six optional skips**). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**.

### Deterministic reused-bundle safety test — 2026-10-19

The hard-link safety test rebuilt a ZIP fixture when asking the installer to reuse the previously installed bundle. ZIP timestamps can change the archive digest, making the test intermittently exercise a new slot instead of the reused one. It now restores and reuses the exact previously installed archive bytes and checksum in both test trees. The test-only change does not modify installer behavior.

### Standalone bootstrap recovery from damaged metadata — 2026-10-19

The standalone bootstrap re-read active-update JSON after resolving the current installation, so a corrupt marker could still fail setup before it could report a useful recovery error. It now derives the active slot from the validated install path and stops before changing files when the marker is damaged. The optional standalone sidecar is treated as advisory: malformed or oversized content no longer blocks an otherwise valid installed bundle.

**PASS — SOURCE/UNIT VERIFIED:** Production bundle-install tests cover truncated JSON, non-object JSON, and a null version in the active marker; each gets a clear error and preserves the marker and installed launcher. Separate cases cover malformed, non-object, and oversized standalone sidecars; the valid installed bundle and active marker remain unchanged. Final full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**140 tests**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**185 run, six optional skips**). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**.

### Repair rejects malformed shared-launcher metadata — 2026-10-19

Launcher migration assumed `BUILD_INFO.json` was an object; a non-object JSON value raised `AttributeError` before the repair path could present a useful validation message. The reader now bounds the file size and checks its schema, product, and version before continuing.

**PASS — SOURCE/UNIT VERIFIED:** The migration test exercises truncated JSON, a list, a null version, and an oversized metadata file. Each is rejected as `ValueError` by the production repair entrypoint. Final full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**141 tests**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**186 run, six optional skips**). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**.

### Launcher repair bounds rollback metadata reads — 2026-10-19

Launcher repair rejected sidecar records above 8 KiB when parsing them, but then used an unbounded `read_bytes()` to snapshot the same invalid file for rollback. A corrupted oversized `.launcher-home.json` could allocate its full size in memory. The rollback snapshot now reads at most 8 KiB plus one byte and aborts before staging or renaming the old launcher when the limit is exceeded. Regression tests confirm the oversized sidecar and old launcher stay unchanged and no temporary executable is left behind.

**PASS — SOURCE/UNIT VERIFIED:** Focused migration tests passed **14/14** in `launcher-source` and **15/15** in `maintenance-tools`. Full discovery passed with `py -3.12 -B -m unittest discover -s tools -p 'test_*.py'` (**167/167** in `launcher-source`; **213 run, six optional skips** in `maintenance-tools`). The packaged launcher and a live repair of an installed copy were not run.

### Diagnostics Authorization-header redaction — 2026-10-19

The diagnostics exporter redacted the `Authorization` header name and scheme but could leave the credential following `Bearer` or `Basic` in raw HTTP header lines. It now redacts the entire value of raw `Authorization` and `Proxy-Authorization` lines before applying the existing key/value, path, and IPv4 redactions.

**PASS — SOURCE/UNIT VERIFIED:** The production diagnostics-export test failed before the fix with both bearer and basic credential values present in the generated ZIP, then passed after the fix in both mirrored launcher trees. The focused test passed in each tree, and `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**. Launcher discovery initially had one unrelated UI navigation assertion fail; the test passed alone and the full rerun passed (**141/141**). Maintenance-tools discovery passed (**186 run, six optional skips**). No external logs or credentials were used.

The same export test also reproduced that IPv6 addresses (`2001:db8::1`, `::1`, and zone-qualified `fe80::abcd%12`) remained in logs. The exporter now validates IPv6-like tokens with Python's standard `ipaddress` module and redacts valid addresses, including bracketed host-and-port and zone-qualified forms. The focused diagnostics test and full 20-test launcher-services suite pass in both trees; launcher UI parity remains **48/48**.

The diagnostics test now also covers a JSON `Proxy-Authorization` field. The existing key/value matcher already removed that credential, so this was test hardening only; the focused test passed in both launcher trees and the **48-file** parity check passed.

### Integrity verifier handles malformed checksum records — 2026-10-19

The installed-file verifier indexed the parsed checksum JSON before validating its shape. A list or a missing `files` key raised `TypeError`/`KeyError`; a non-string checksum reached `re.fullmatch` and raised `TypeError`. It now validates the JSON object and entry types first and returns a clear `ValueError` for malformed records, while preserving normal missing/changed-file reports.

**PASS — SOURCE/UNIT VERIFIED:** The production integrity check reproduced malformed top-level JSON, a missing or non-dictionary `files` value, a non-string checksum, and invalid JSON. The focused cases and existing changed/missing-file checks passed in both launcher trees. Full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**143/143**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**188 run, six optional skips**). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**.

### Guide cache rejects linked paths — 2026-10-19

Guide refresh and offline-cache writes did not validate the `.updates/guides` directory against symlinks or junctions. A linked cache could redirect guide writes outside the launcher home, including replacing an existing `active.json`. The guide service now checks the cache directory and each marker, document bundle, and cached guide path against the install's managed-path policy before network access or file operations; offline reads fall back safely when the cache path is linked.

**PASS — SOURCE/UNIT VERIFIED:** The disposable symlink regression failed before the fix because refresh accepted the redirected cache path, then passed after the fix without making network requests or changing the outside sentinel. Existing guide refresh, cache, and offline behavior passed in both launcher trees. Full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**142/142**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**187 run, six optional skips**). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**.

### Cynthia patch cache rejects junctions — 2026-10-19

The Route 7 patch cache rejected symbolic links but did not reject Windows directory junctions. A junction could redirect the patched-ROM output outside the launcher home. The cache now uses the shared managed-path validator before and after creating the cache directory, and validates the ROM and manifest destinations before reading or writing them. That validator rejects junctions, symbolic links, and externally linked files.

**PASS — SOURCE/UNIT VERIFIED:** A disposable Windows junction regression pointed the cache to a temporary folder outside the launcher home; the production patch entrypoint rejected it before writing, leaving the source ROM and outside folder unchanged. The focused Cynthia event suite passed **5/5** against each launcher UI tree. Full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**144/144**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**188 run, six optional skips**). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**.

**PASS — PACKAGE VERIFIED:** A later supported launcher build and recursive archive check also covers the player-model path-safety import; its artifact identity and the remaining cleanup limitation are recorded in the following audit entry. No user ROM or save was accessed.

### Player-model cache rejects linked paths — 2026-10-19

The launcher’s player-model ROM-copy cache rejected symbolic links but missed Windows junctions, and it allowed pre-existing hard-linked output or manifest files. A redirected cache could write the prepared ROM outside the launcher home. The copy path now uses the shared managed-path validator before and after creating the cache, then checks both output destinations before reading or replacing them.

**PASS — SOURCE/UNIT VERIFIED:** The junction regression redirects the cache outside a disposable launcher home and confirms the production entrypoint rejects it without changing the source fixture or creating external files. Separate cases reject hard-linked ROM and manifest destinations while preserving their external sentinel. The focused player-model suite passed **7/7** against each mirrored production module. Full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**146/146**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**188 run, six optional skips**); launcher UI parity passed for all **48 files**.

**PASS — PACKAGE VERIFIED:** `py -3.12 tools/build_unova_launcher.py --output-dir builds/cynthia-junction-audit-20261019 --work-dir test-fixtures/cynthia-junction-audit-20261019` succeeded with Python 3.12.8 and PyInstaller 6.22.3 on Windows 10. Recursive archive inspection found `launcher_ui.player_models`, `launcher_ui.cynthia_event`, and `unova_storage`. The executable was 3,631,326 bytes (SHA-256 `90427d5af8f14ddb92d4cc202a27f0616523f2e8da42b1d81c68a8430bdd50cb`); the GUI executable was not launched. The disposable build outputs remain under the two specified `launcher-source` folders because execution policy blocked their recursive cleanup before the command ran. No user ROM or save was accessed.

### Battle-scenery cache rejects malformed and linked paths — 2026-10-19

The optional battle-scenery cache accepted junctions and hard-linked manifests, and a valid JSON value with the wrong shape (for example, `[]`) raised an uncaught `AttributeError` while the launcher prepared scenery. The cache now validates its directory, generated catalog, and manifest with the shared managed-path policy before and after generation. Manifest parsing is UTF-8 checked and requires an object with the expected format and ROM digest; malformed content returns the normal cache-validation error. The implementation is mirrored in the maintenance tools.

**PASS — SOURCE/UNIT VERIFIED:** New production-path regressions reproduce and reject an external Windows junction, a hard-linked manifest, and a non-object manifest; valid catalog creation and reuse still work, and the source ROM remains unchanged. All four focused cases passed against both production copies. Full discovery passed with `py -3.12 -B -m unittest discover -s tools -p 'test_*.py'` (**150/150** in `launcher-source/tools`; **188 run, six optional skips** in `maintenance-tools/tools`). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**.

**PASS — PACKAGE VERIFIED:** The supported launcher build succeeded with Python 3.12.8 and PyInstaller 6.22.3. Recursive archive inspection found `area_scene_cache`, `build_area_battle_catalog`, and `unova_storage`. The executable was 3,631,875 bytes (SHA-256 `8f2959fb50cc00e9fb159c96b09f25e5b4ad5453d58d2555fd278f3c0387ddfd`); the GUI executable was not launched. The disposable build outputs remain under `launcher-source/builds/cynthia-junction-audit-20261019` and `launcher-source/test-fixtures/cynthia-junction-audit-20261019` because recursive cleanup was blocked by execution policy. Tests used temporary disposable fixtures only; no user ROM or save was accessed.

### Nearby-scene worker validates requests and cache reports — 2026-10-19

The optional scenery worker assumed incoming request and cached scene JSON were objects. A list-shaped value raised an uncaught `TypeError` and terminated the background worker. Cached reports could also name an arbitrary model path, causing a file outside the generated scene to be read. The worker now validates object shapes, requires the expected generated model filename and well-formed size/checksum metadata, and returns its existing fallback response for invalid cached scenes. Failures writing that response no longer terminate the worker.

**PASS — SOURCE/UNIT VERIFIED:** New production-worker tests reproduced the old crashes for list-shaped requests and reports and confirmed the old worker read an absolute model path from a forged manifest. The worker now survives those inputs, refuses the path before reading it, and still delivers a valid cached scene. Focused tests passed **4/4** in each launcher tree. Full discovery passed with `py -3.12 -B -m unittest discover -s tools -p 'test_*.py'` (**154/154** in `launcher-source/tools`; **192 run, six optional skips** in `maintenance-tools/tools`). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**.

**PASS — PACKAGE VERIFIED:** The supported Windows launcher build completed with Python 3.12.8 and PyInstaller 6.22.3. Recursive archive inspection confirmed `battle_surroundings_worker`, `area_scene_cache`, and `unova_storage` are bundled. The executable was 3,632,329 bytes (SHA-256 `d4d30ccb885c1c25746ffcd10c12e4a8590cf1b3c56565fb615bb711b6a058a6`); the GUI executable was not launched. The build outputs remain in the previously recorded disposable build and fixture directories because execution policy blocked recursive cleanup. No user ROM or save was accessed.

### Battle scenery follows the loaded area and protects the center — 2026-10-22

The scenery selector used the tracker’s outdoor matrix-cell zone for the area's battle backdrop. The pinned B2W2 decomp shows that battle setup captures `Field_GetPlayerStateZoneID` as `BtlFieldStatus.zoneId`; on the supported Redux ROM, the tracker can report that loaded field zone separately from the matrix cell. The nearby-scene builder also rejected props by checking whether any cropped vertex entered the central square, which allowed a long polygon crossing the battlers to survive when all its vertices remained outside.

The emulator source patch now selects the fallback arena by `fieldZone`, uses cropped nearby geometry only if both zone records resolve to the same area, validates the nearby-scene report's zone and area, and samples the field every six emulated frames to reduce the chance of entering an encounter with the preceding area's scene. If zone metadata becomes invalid, it clears any prior area's replacement and restores the original background. The existing in-battle early return keeps a valid selection latched until the tracker reports a verified field position again. Nearby props are rejected by polygon/square intersection, including crossing faces and boundary contact. Worker caches now carry their area and use revision 4. The worker loads `ndspy` and ROM parsing code only when a scene needs to be generated; a valid cached scene is delivered without reopening the ROM.

**PASS — SOURCE AND FIXTURE CHECKS:** The scenery worker/clearance suite passed **9/9** in both `launcher-source/tools` and `maintenance-tools/tools`; the source-patch and metadata checks passed **3/3**. The standalone C++ area-selection helper compiled with `g++ -std=c++17 -fsyntax-only`, including the Route 7 case (matrix cell 337 and loaded zone 107 both resolve to area 38), an area mismatch fallback, and invalid-zone rejection. `git apply --numstat maintenance-tools/patches/development-polish.patch` parsed the full development patch, and the incremental scenery patch applied to a disposable copy of the 2.0.24 source snapshot. The exact local Redux output ROM used for the zone-table check was `IREO`, SHA-256 `353fb0cf82c3e4eddfc8986efa8910b00eb1c4d6f106c220abef59d69d3a520a`; the pinned decomp reference was `WhatWasMissing/pokebw2` commit `215b992f5c87bcadc4c5d7a40e78a309b2555f8b`. No ROM or save was modified.

**NOT RUN — LIVE BATTLE/BUILD:** The full emulator was not rebuilt and no live battle camera was inspected. Verify wild, trainer, double, indoor, and outdoor battles on the supported ROM in the planned playtest pass; confirm the center remains clear from all battle camera angles and that a battle launched immediately after a map transition uses the new area's scene.

### Old-install cleanup validates Windows process results — 2026-10-19

The cleanup safety check parses PowerShell's running-process JSON before deciding which versions are safe to remove. It handled a single process object and a list, but valid JSON with an unexpected shape (`null` or a list containing strings) raised an uncaught type error. The parser now validates every returned row and requires an absolute executable path; invalid output raises the existing fail-closed cleanup error before any deletion.

**PASS — SOURCE/UNIT VERIFIED:** A regression test feeds both malformed shapes through the production cleanup entrypoint and confirms it reports that cleanup was skipped while preserving an older install. Storage tests passed **16/16** in `launcher-source/tools` and **17/17** in `maintenance-tools/tools`. Full discovery passed with `py -3.12 -B -m unittest discover -s tools -p 'test_*.py'` (**155/155** canonical; **193 run, six optional skips** maintenance). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**.

**PASS — PACKAGE VERIFIED:** The supported Windows launcher build completed with Python 3.12.8 and PyInstaller 6.22.3. Archive inspection confirmed `unova_storage`, `battle_surroundings_worker`, and `area_scene_cache` are bundled. The executable was 3,632,565 bytes (SHA-256 `5d09c720bd916d65131d0bee997ab4dfeee896c25dae3ead6141d111e8a70290`); the GUI executable was not launched. Build and fixture directories remain at the previously documented disposable paths because recursive cleanup was blocked by execution policy. No user installation, ROM, or save was changed.

### Save backup creation matches restore limits — 2026-10-19

The backup path accepted more than 32 matching saves and combined payloads above the restore archive limit, then reported success even though restore rejected the resulting archive. Backup now enforces restore's 32-save, 16 MiB per-save, 16 KiB manifest, and 64 MiB complete-archive bounds. The existing restore path uses the same constants, so these limits cannot drift independently. Rejections remove the temporary archive and leave no completed backup.

**PASS — REPRODUCTION AND SOURCE/UNIT VERIFIED:** Before the correction, production-path tests failed in both launcher trees: a set of 33 saves and a 65 MiB payload were accepted. After the correction, both are rejected without publishing a backup; exactly 32 small saves still create and restore successfully. Full discovery passed with `py -3.12 -B -m unittest discover -s tools -p 'test_*.py'` (**158/158** in `launcher-source`; **196 run, six optional checks skipped** in `maintenance-tools`). `py -3.12 -B check_launcher_tree_parity.py` passed for all **48 UI files**. Tests used isolated temporary saves; no user saves were read or modified.

### Emulator version labels follow the release metadata — 2026-10-19

The development patch hard-coded `1.0.32` in the emulator window/about text while the repository and packaged launcher identified version `2.0.17`. The Multiplayer window separately used a build-name string, so its title could disagree with the emulator. Both windows now use one `ProjectCredits` version/title constant set to the current `VERSION.txt` value. A regression check extracts the changed production lines from the source patch and verifies the emulator version, title, about text, and Multiplayer title against the repository version.

**PASS — SOURCE/UNIT VERIFIED:** The new check failed against the prior `1.0.32` patch, then passed after the correction. The focused source-patch regression suite passed **6/6**; full discovery passed with `py -3.12 -B -m unittest discover -s tools -p 'test_*.py'` (**158/158** in `launcher-source`; **197 run, six optional checks skipped** in `maintenance-tools`). The patch metadata SHA-256 matches the changed patch, and `git apply --numstat` parses the complete patch. **NOT RUN:** No emulator rebuild or live window-title check was performed; the change is in the distributable source patch and needs to be present in a rebuilt emulator before players see it.

### Save backup folders reject linked paths — 2026-10-19

Backup creation, listing, and restore trusted the profile backup directory without checking whether it was a symlink or Windows junction. A linked directory could expose archives from outside the launcher's managed backup folder; backup creation could write there, and restore resolved both paths before comparing them, which allowed a valid outside archive to be treated as belonging to the profile. The launcher now validates the directory and archive with the shared managed-path policy before and after directory creation and archive writing. Listing omits linked or hard-linked archives, and restore rejects any archive outside the profile's real backup folder. No save format or configured save-directory behavior changed.

**PASS — REPRODUCTION AND SOURCE/UNIT VERIFIED:** A new production-path regression creates a disposable junction to an external directory containing a valid profile archive. The test failed against the pre-fix production module because the archive appeared in the profile's backup list. After the fix, both launcher trees return no linked archives, reject backup creation and restore, and leave the external directory and current save unchanged. Full discovery passed (**159/159** in `launcher-source`; **198 run, six optional checks skipped** in `maintenance-tools`); after a final no-empty-directory adjustment, the focused service suite passed **26/26** in both trees. `check_launcher_tree_parity.py` passed for all **48 UI files**. All test data lived under automatically cleaned temporary directories; no user saves or backups were accessed.

### Cheat settings reject linked profile storage — 2026-10-19

Opt-in cheat generation wrote `original-switches.json` and the managed `.mch` file under `.launcher-cheats/<ROM-key>` without validating the managed directory. If that profile directory was a symlink or Windows junction, the launcher followed it and wrote outside its own profile store. It now checks the directory and generated files with the shared managed-path policy before directory creation, before reading/writing managed files, and immediately before updating them. Unsupported ROM checks and emulator configuration writes keep their existing behavior.

**PASS — REPRODUCTION AND SOURCE/UNIT VERIFIED:** A disposable Windows junction regression failed before the fix because applying an opt-in code completed instead of rejecting the redirected folder. After the fix, it rejects the path and preserves the outside sentinel and emulator TOML. The focused preferences suite passed **11/11** in both launcher trees; full discovery passed (**160/160** in `launcher-source`; **199 run, six optional checks skipped** in `maintenance-tools`). `check_launcher_tree_parity.py` passed for all **48 UI files**. **NOT RUN:** No packaged launcher build or ROM/game execution was performed; this is source/unit evidence only. Fixtures were automatically cleaned, and no real ROM or save was accessed.

### Settings editor reports malformed section tables — 2026-10-19

The advanced settings editor added missing schema defaults by assuming every intermediate TOML section was a table. Valid TOML with a scalar at a section path (for example, `3D = 3` or `Instance0.Keyboard = 3`) caused an uncaught `TypeError` while opening the editor. The schema walk now identifies the malformed section and raises a normal `ValueError`, which the launcher displays as its settings-open error. It does not overwrite the malformed file.

**PASS — REPRODUCTION AND SOURCE/UNIT VERIFIED:** Two regression cases reproduced the uncaught `TypeError` in each launcher tree before the fix and now return the expected validation error. The focused settings-editor and launcher-UI suites passed **35/35** in both trees; full discovery passed (**161/161** in `launcher-source`; **200 run, six optional checks skipped** in `maintenance-tools`). `check_launcher_tree_parity.py` passed for all **48 UI files**. **NOT RUN:** No packaged launcher build or emulator run was performed.

### Failed update activation remains retryable — 2026-10-19

If an update archive downloaded and verified successfully but writing the final active-version record failed, the existing game stayed active while the extracted version directory remained behind. Retrying that version then failed with “already installed,” even though it had never been activated. The updater now removes only the verified version directory created by that failed transaction and preserves the original activation record, allowing the same update to be retried. If the path cannot be verified as safe, cleanup is skipped and the original error is retained.

**PASS — REPRODUCTION AND SOURCE/UNIT VERIFIED:** A disposable production-path test injects a failure at the activation write. Before the fix, the inactive directory remained and blocked retry; after the fix, it is removed, the current runtime remains active, and a retry installs and activates successfully. Focused launcher-service tests passed **27/27** in both source trees. Full discovery passed (**162/162** in `launcher-source`; **201 run, six optional checks skipped** in `maintenance-tools`); `check_launcher_tree_parity.py` passed for all **48 UI files**. All installer data was held in temporary directories.

**PASS — PACKAGE VERIFIED:** The supported command `py -3.12 -B tools/build_unova_launcher.py --output-dir builds/audit-updater-activation-a6117c1 --work-dir test-fixtures/audit-updater-activation-a6117c1 --revision a6117c1` succeeded with Python 3.12.8 and PyInstaller 6.22.3. The test executable was **3,634,457 bytes**, SHA-256 `B4E8DA4E515F82422D9BF68CDE3FE804E353EBA076243B8F6E82F534C0CAD885`; its archive contains `unova_updater`, `unova_storage`, and `launcher_ui.app`. The disposable build and work directories remain because the workspace rejected the verified recursive cleanup command. **NOT RUN:** No live GUI launch, external-network download, ROM, or gameplay test was performed.

### Backups-folder permission error — 2026-10-19

The launcher attempted to create `save-backups` before entering its filesystem error handler. On a read-only or restricted installation, that raised an uncaught `OSError` from the button callback. Folder creation now runs inside the handler, and the launcher shows a contextual status message if creation or opening fails. The normal profile backup path is unchanged.

**PASS — REPRODUCTION AND SOURCE/UNIT VERIFIED:** The new UI regression test failed in both launcher trees before the change with `PermissionError` escaping `_open_backups`. After the fix, the native launcher-page test confirms the failure is displayed in the status field. Full discovery passed: `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**163/163**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**202 run, six optional checks skipped**). `py -3.12 -B launcher-source/tools/check_launcher_tree_parity.py` passed for all **48 UI files**. Tests used temporary launcher profiles. **NOT RUN:** No real read-only installation or Explorer launch was tested.

**PASS — PACKAGE VERIFIED:** `py -3.12 -B tools/build_unova_launcher.py --output-dir builds/audit-backup-folder-8b36e39 --work-dir test-fixtures/audit-backup-folder-8b36e39 --revision 8b36e39` completed with Python 3.12.8 and PyInstaller 6.22.3. The executable is **3,634,479 bytes**, SHA-256 `8EAFF20AC10DCA8A5F9DB4B01B7357C24C840C4DAB2C051E1E9766036507E137`; build metadata identifies product `pokemon-together`, version `2.0.17`, revision `8b36e39`. The disposable output directories remain because the workspace rejected the verified recursive cleanup command. **NOT RUN:** The packaged executable was not launched; no real profile, ROM, or save was accessed.

### Diagnostics report-folder error — 2026-10-19

The diagnostics review window opened the report folder directly from a Tk button callback. If Explorer rejected the path or the report folder was unavailable, the `OSError` escaped to Tk's callback handler rather than giving the player useful feedback. The button now reports the problem in the launcher status area.

**PASS — REPRODUCTION AND SOURCE/UNIT VERIFIED:** The button-level UI test injects a `PermissionError` from the actual folder-opening callback. Before the fix, Tk's callback handler received the error; after the fix, no callback exception is raised and the status area explains the problem. `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` passed (**163/163**); `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` passed (**202 run, six optional checks skipped**). `py -3.12 -B launcher-source/tools/check_launcher_tree_parity.py` passed for all **48 UI files**. **NOT RUN:** Opening a diagnostics folder with a real Windows permission restriction was not tested.

**PASS — PACKAGE VERIFIED:** `py -3.12 -B tools/build_unova_launcher.py --output-dir builds/audit-report-folder-5e1a0e2 --work-dir test-fixtures/audit-report-folder-5e1a0e2 --revision 5e1a0e2` completed with Python 3.12.8 and PyInstaller 6.22.3. The executable is **3,634,609 bytes**, SHA-256 `E5E2E15D0F460F4AF54FF23C3495D2E35D0AF04F4EE7CCEC49B7578EDF7C86D4`; build metadata identifies version `2.0.17`, revision `5e1a0e2`. The disposable output directories remain because the workspace rejected the verified recursive cleanup command. **NOT RUN:** The packaged executable was not launched.

### Save-list permission errors — 2026-10-19

Opening Games & saves could raise an uncaught `OSError` while listing a profile's saves or backups. If the backup listing failed first, the UI also retained the previous profile's backup selection. The page now reports the access error, clears stale backup entries, and disables restore until both listings are readable.

**PASS — REPRODUCTION AND SOURCE/UNIT VERIFIED:** A new native-page test injects `PermissionError` through each production listing call. Both cases raised out of `_refresh_backups` before the change; after the fix the page remains open, shows the failure, clears the prior profile's selection, and keeps restore disabled. Full discovery passed: `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**164/164**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**203 run, six optional checks skipped**). `py -3.12 -B launcher-source/tools/check_launcher_tree_parity.py` passed for all **48 UI files**. `git -c core.whitespace=cr-at-eol diff --check` passed; the repository files use CRLF line endings. The tests use disposable launcher profiles. **NOT RUN:** No real restricted folder, packaged launcher, ROM, or save was used.

### Prepared player-model ROM cache verifies contents and protects its source — 2026-10-19

The launcher reused a prepared player-model ROM when the selected source hash, model ID, and cached file size matched. It did not verify the cached ROM bytes, so a same-size corruption could be mistaken for a valid model variant and launched. Cache manifests now include the generated ROM's SHA-256, and cache reuse requires the actual file hash to match. Older manifests without this field trigger a fresh prepared copy. A second path collision occurred if a player selected a cached variant as the source and requested a different model: the cached input and output paths were identical. The launcher now safely reuses that copy only for the same model when its recorded output digest matches; otherwise it asks for the original game ROM before any write. Original ROMs and saves remain untouched.

**PASS — REPRODUCTION AND SOURCE/UNIT VERIFIED:** Before correction, a production-path regression created a valid cached variant, changed its bytes without changing its length, and confirmed the launcher returned the corrupted file. A second case confirmed that selecting the cached variant for a different model entered a rebuild with identical source/output paths. After the corrections, the first case rebuilds and verifies the digest; the second reuses an unchanged matching variant or rejects a different model while preserving the selected file. Focused player-model tests passed **9/9** against both mirrored production modules. These tests exercise `prepare_variant` and real filesystem replacement using synthetic ROM objects and a stubbed ROM patch function; they do not validate actual ROM patch bytes. Full discovery passed with `py -3.12 -B -m unittest discover -s launcher-source/tools -p 'test_*.py'` (**166/166**) and `py -3.12 -B -m unittest discover -s maintenance-tools/tools -p 'test_*.py'` (**203 run, six optional skips**). `py -3.12 -B tools/check_launcher_tree_parity.py` passed for all **48 UI files**. No real ROM or save was used.

**PASS — PACKAGE VERIFIED:** The supported `tools/build_unova_launcher.py` command completed with Python 3.12.8 in isolated temporary output/work folders under the launcher's `builds/` and `test-fixtures/` roots. The 2.0.17 executable was **3,635,413 bytes**, SHA-256 `ac8a261688ae131e5643d22c3f290871e17c04cd5b48368b4ca5add68ae73c2d`; build metadata recorded revision `423ca1e-player-model-source-guard`. Temporary build and work outputs were removed after recording the result. **NOT RUN:** The packaged GUI was not launched, and no prepared ROM was loaded in melonDS.

### Opponent Mega Evolution audit — 2026-10-19

The 2.0.17 source archive used for the emulator-side tests has SHA-256 `3d57a84e8e420dbd89b62a8e59dfda2fb4315b6113122766ccf8fc5a75180253`, matching the published source asset. Against that source, `gen5_mega_battle.exe` passed its synthetic-RAM opponent-event test: a candidate is produced for matching held stone/form data in both battle copies when the opponent has a committed Fight action; stale peer data, a missing Fight action, and a zero battle ID are rejected. `gen5_gym_leader_mega_teams.exe` passed when given the launcher-managed patched ROM (SHA-256 `234079a05e5360b81b5fbe41d39815bec65193b986ac2d877e23a86d76377220`); it verified that the runtime patch generated from this supported Redux ROM includes the Mega species, matching stone, and moves for each configured late-game Gym Leader. `test_cynthia_route7_rematch.py` also passed against that ROM: Cynthia is listed in Practice as trainer 891, her six-Pokémon team is within one level of Redux Skyla's reference team, and Garchomp holds Garchompite. The unpatched selected input ROM does not contain the appended Cynthia Practice trainer; the launcher-managed patched copy does.

**OPPONENT AI VERIFICATION SCOPE:** The synthetic checks establish the event detector's conditions, not live story Gym Leader behavior. A separate two-client Practice run below confirmed Cynthia's opponent Mega path with Garchomp active in a disposable ROM copy. The unmodified Cynthia rematch roster order, full battle completion, and late-game Gym Leader story battles remain untested; do not treat the active-slot test as proof of those scenarios. No player ROM or save was modified by these checks.

### Cynthia Practice battle catalog — 2026-10-19

The appended Cynthia trainer record (ID 891) appeared in Practice's selection list but was excluded from the separate battle-start catalog. Selecting her therefore returned “Unsupported boss trainer.” The emulator patch now includes Cynthia in the major-trainer allowlist and extends the exclusive trainer-ID bound from 891 to 892, so ID 891 is available to the battle-start path.

**PASS — SOURCE, PATCH, AND TWO-CLIENT BATTLE START VERIFIED:** `test_cynthia_practice_catalog_patch.py` checks both production patch changes, verifies the patch metadata SHA-256, and rejects negative controls with either change removed. The patched `Gen5Menu.cpp` was built into the emulator test target and `gen5_mod_menu_render_from_rom` passed against the supported Cynthia-patched Redux ROM (SHA-256 `234079a05e5360b81b5fbe41d39815bec65193b986ac2d877e23a86d76377220`). An isolated two-client Practice run using the 2.0.17 source archive (SHA-256 `3d57a84e8e420dbd89b62a8e59dfda2fb4315b6113122766ccf8fc5a75180253`) and supplied save (SHA-256 `4336e7e447fa88cd39dce2b7eef44324fa43f87c5722dca1f00dc84d85635ac7`) started Cynthia #891 on both clients and reached the native battle scene; the clients reported 43 and 44 battle samples at approximately 59 FPS. Focused Python tests passed **9/9**. The 2.0.17 runtime and save were copied into the marked disposable fixture; the supplied save remained unchanged.

### Cynthia Garchomp opponent Mega — 2026-10-19

To exercise the opponent AI path before Cynthia's Garchomp would normally enter battle, a disposable copy of the supported Cynthia-patched Redux ROM was made with only its trainer-party order adjusted: Garchomp (species 445, Garchompite item 526) was moved to trainer 3's first active slot. No Pokémon, moves, levels, stats, stone, user save, or source ROM were changed. The supplied save was used unchanged.

**PASS — LIVE OPPONENT MEGA FORM VERIFIED:** The isolated two-client Practice battle started Cynthia #891. The Mega runtime reported `megaRemoteState=3`, `megaFormsAgreed=true`, and “Partner Mega form applied and confirmed in both local battle copies.” The live battle RAM showed Cynthia's trainer 3 Garchomp at Mega form 1 while holding item 526. Both clients remained near 59 FPS and reached the native battle scene. The test ROM copy SHA-256 was `d844d6b6712f8b4925c74627cb83443183b4349a121b0a91bee9e6b213e4d28e`; the unmodified supported ROM was `234079a05e5360b81b5fbe41d39815bec65193b986ac2d877e23a86d76377220`, and the supplied save remained `4336e7e447fa88cd39dce2b7eef44324fa43f87c5722dca1f00dc84d85635ac7`.

**LIMITATION:** This verifies the opponent Mega trigger when Cynthia's Garchomp is active. It does not exercise her normal team order through the entire rematch or verify late-game Gym Leader story battles. The test-only ROM and emulator copies were isolated in a marked disposable fixture.

### Mega checks rerun and Skyla Practice harness — 2026-10-19

The targeted Mega regression set was rerun from the published 2.0.17 source archive. With the local MSYS2 UCRT64 and `usr/bin` runtime paths available, **11/11** CTest checks passed: Mega assets/rules, native selection and transaction, party ability restoration, stone-preview centering, co-op packet and LAN transport, release roster, item-pocket compatibility, Redux cartridge overlays, and ARM hook signatures. The focused `gen5_gym_leader_mega_teams` executable also passed its synthetic checks and its Redux ROM check against the patched ROM whose SHA-256 is `234079A05E5360B81B5FBE41D39815BEC65193B986AC2D877E23A86D76377220`.

The first fresh Skyla Practice attempt exposed a test-harness configuration issue: the packaged TOML used nested `[InstanceN.*]` sections without declaring their parent tables, then melonDS added scalar instance defaults under those implicit tables. The serializer rejected the resulting configuration. `verify_lan_coop.py` now makes those parent tables explicit before launching either isolated client. `py -3 -B -m unittest test_lan_harness_config -v` passed **2/2**, and the transformed packaged runtime TOML parsed successfully.

**LIVE GYM AI STATUS:** A 300-second two-client Skyla Practice run using the corrected harness reached the native battle scene on both clients at approximately 59 FPS. Both reports remained at “Native opening exchange complete; battle scene running”; the captured battle screens showed “Communicating. Please stand by.” The live RAM copies showed Skyla's Pidgeot (species 18) holding Pidgeotite (item 142) in base form, with full HP, at frames 17,640 and 17,700. The battle never completed or advanced far enough to prove a Mega action, so Gym Leader AI activation remains **NOT VERIFIED**. This is inconclusive evidence, not a failure finding. The test ROM and save were copied into the disposable fixture and the source save remained unchanged. No production networking or battle behavior was changed.

### Release packaging rejects a stale Mega shop-overlay emulator — 2026-10-19

The 2.0.17 package contained a `melonDS.exe` built with an older Mega shop overlay than the source archive. The Windows resource now embeds the SHA-256 of `Gen5ShopOverlayPatch.h`; both supported release packagers compare that marker with the header in the source tree and reject missing or stale emulator binaries. The development patch generator accepts an explicit baseline archive and output root so the tracked patch can be regenerated from the verified 1.0.6 source archive without relying on a machine-specific default path.

**PASS — SOURCE/UNIT/BUILD VERIFIED:** `py -3.12 -B launcher-source/tools/test_release_validation.py` passed **2/2**, covering both packagers' fingerprint helpers and mismatched or absent markers. A rebuilt Windows `melonDS` target from `maintenance-tools/melonDS-source-1.1` embedded the expected marker (SHA-256 `0f898f6627e4a6f0f1c9f5850fb3488e8c39a6d9172356b12c44cf38c31e0131`); both helpers rejected the published 2.0.17 executable and accepted this rebuilt test executable. The first build invocation lacked Qt's app-local DLL directory and failed at `moc.exe`; rerunning the same build with the existing MSYS2 UCRT64 and Qt directories on that process's PATH passed. No system PATH was changed. The source patch was regenerated from the baseline archive whose SHA-256 is `c3833116062ed40811a252ae1945a23a7043694c1984d3c8ae3cc0ac6212dd25`; the resulting patch SHA-256 is `205590113c3faa330506e54eba2595865fa9c11d2ff185e0e391777e8ca47f97`. Applying it to the baseline and comparing all **88** changed native files passed.

**PASS — RELEASE SOURCE/RUNTIME ALIGNMENT:** The 2.0.18 release uses `maintenance-tools/tools/package_unova_release.py` with its matching `maintenance-tools/melonDS-source-1.1` tree and a freshly staged runtime. The packager now reads project documentation and patch notes from the actual repository root rather than an old nested repository copy. The alternate launcher-source packager still requires a binary matching its own selected workspace source; it was not used for this release.

The release checks caught two previously committed fixes missing from the extracted build source: the unsigned Mega activation mask and Cynthia's Practice catalog entry. Both were restored before rebuilding. The version-label structural check was updated to cover the sidecar-based `ReleaseVersion()` implementation and its title/HTML callers, and native fallback/resource metadata was aligned to 2.0.18. The refreshed source patch applies to the authenticated 1.0.6 baseline, and all **88** modified native files match the build source after newline normalization.

**PASS — SOURCE/UNIT/BUILD VERIFIED:** Full discovery passed **168/168** canonical launcher tests and **221** maintenance tests with **six optional skips**. The emulator, launcher and permanent bootstrap built on Windows 10 build 19045 with Python 3.12.8, PyInstaller 6.22.3, CMake 4.4.1, MSYS2 GCC 16.2.0 and Qt 6.11.2. Release artifact verification is recorded in `docs/RELEASE_CHECKS_2.0.18.md`.

**PASS — GAMEPLAY VERIFIED FOR CENTER ENTRY:** The final rebuilt emulator SHA-256 is `3134719eda6aa2a421bffd4142c6f4de05fb69dcfd4730f4bed4964fad9db30c`. The same exact-save Center-entry script ran for **75 seconds / 4,440 observer frames**, reached map 460 at tile `(7, 19)`, and reported input unblocked. Both captured screens were inspected visually and showed the normal Pokémon Center and C-Gear, with no fatal screen. Only disposable ROM/save copies were used. This verifies this Center-entry scenario; it does not replace the separately documented battle and two-client coverage limits.

### Mega Stone merchant list crash — 2026-10-19

**SOURCE FINDING:** The Black 2 decomp's `ShopUIWork` stores shop rows in fixed `entries[45]` and `tutorMoveIndices[45]` arrays (`src/ov036/scrcmd_shop.c`, pinned upstream source revision `81eea95ee66e9ab41dedf5ead08ff1d3222cbef5`). The old runtime patch put all 49 Mega Stones in every Poké Mart and installed a custom overlay that expanded the list storage. Opening a merchant's buy list exercised this patched path; the sell menu did not.

**LOCAL FIX:** Removed installation of the custom shop overlay and capped every Poké Mart at the decomp's native 45 rows. The 49 Mega Stones are divided between alternating marts (25/24); all 74 mart lists, including Pokémon Center marts, retain the complete roster across the region. Normal stock is preserved, and the standard mart stock used by Redux stays within the native limit after adding the Super Repel row. The source patch and metadata were regenerated from the verified 1.0.6 baseline.

**PASS — BUILD AND CARTRIDGE INTEGRATION:** The Release `gen5_mega_assets` regression executable compiled with MSVC and passed against the already patched Cynthia Route 7 ROM, read-only. Its checks replayed the asset patch in memory, verified the grouped roster in all marts, confirmed no stone duplicates or missing entries, checked the native 45-row bound, and confirmed the shop overlay table is untouched. The focused Python source-packaging suite passed **7/7**. The live merchant UI was not exercised, so this is source and ROM integration evidence rather than a live gameplay confirmation.

### Co-op battle EXP and level-up flow — 2026-10-19

**SOURCE FINDING:** In the BW2 decomp, `ServerControl_GiveExp` walks the six reward entries, queues the normal EXP/stat commands, and calls `BattleMon_AddExp`, which drives level-ups. The co-op emulator hook had been zeroing all six reward entries before this code ran in co-op story and Practice battles. That prevented EXP and level-ups entirely. The co-op runtime already waits for both battle outcomes to agree before returning and grants the partner up to 1,800 frames (30 seconds) to finish local EXP, level-up, and move-learning screens.

**LOCAL FIX:** Removed the reward-builder and setter suppression hooks, allowing each game instance to use the native EXP and level-up flow. Retained the two-player outcome agreement and the longer wait for a peer completing post-battle prompts. Added a small policy regression covering which co-op modes may earn EXP and the post-battle wait window.

**PASS — BUILD AND POLICY TEST:** The complete Windows MinGW runtime built successfully with the OpenGL renderer enabled; this also compiled the updated `NativeCoopRuntime.cpp`. The dedicated co-op reward policy, packet, and role tests passed **3/3**, and the tracked co-op source-patch check passed **1/1**. No live two-client battle was performed, so EXP, level-up, and desync behavior still need an in-game paired-session check.

### Teleport relay capability — 2026-10-19

**SOURCE FINDING:** The game client sends `fieldZone` with each active position and requires the relay's `welcome.fieldZonePresence` capability before enabling Teleport. The relay previously omitted the capability and silently discarded `fieldZone` during state validation, so every client reported that both game and relay needed updating.

**LOCAL FIX AND VERIFICATION:** Both packaged relay copies now advertise field-zone support and retain valid zone IDs in peer state. Unknown-zone sentinels are omitted, and malformed or out-of-range values are rejected. `py -B -m unittest test_presence_server -v` passed **18/18**, including the real-socket capability and zone-forwarding checks. Teleport was not exercised in a live emulator session; the host must restart its relay using the updated `presence_server.py` before testing.

### Co-op EXP suppression test switch — 2026-10-19

The launcher stores **Suppress EXP in co-op battles (testing)** per game profile and passes it to melonDS at launch. It originally defaulted off; the current implementation defaults it on for profiles without a saved choice, suppressing co-op EXP, level-up and move-learning rewards. Turning it off restores the native reward flow. When enabled, a ROM-signature-checked hook clears only the six reward records' XP amounts during co-op story/test battle phases; EV and flag bytes remain unchanged. The setting does not alter direct player battles.

**PASS — TESTS:** The launcher UI suite passed **37/37**, the preferences suite **11/11**, and launcher parity matched **48 files** at introduction. Regression coverage now verifies default-on suppression, profile persistence, restart restoration, and both environment values passed to melonDS. The C++ reward-policy/guard executable passed its opt-in phase checks, exact ROM fingerprints, XP-only clearing, EV/flag preservation, and invalid-address rejection. The complete MinGW/OpenGL emulator target built successfully. The updated development patch was regenerated from the verified 1.0.6 source archive; live two-client EXP comparison remains untested.

The co-op EXP checks are included in the source download and accept a caller-supplied melonDS source directory:

```powershell
py -3.12 -B maintenance-tools/tools/test_coop_experience_flow.py --source-root maintenance-tools/melonDS-source-1.1
py -3.12 -B maintenance-tools/tools/test_coop_reward_policy.py --source-root maintenance-tools/melonDS-source-1.1 --compiler C:\msys64\ucrt64\bin\g++.exe
```

The first check structurally inspects the production runtime call site. The second compiles the actual `CoopRewardPolicy.h` and `CoopExperienceGuard.h` with the regression fixture; it checks both valid suppression and invalid signatures/addresses. Neither runs the emulator or establishes two-client gameplay behavior. The source tree was extracted from the 1.0.6 source archive (SHA-256 `c3833116062ed40811a252ae1945a23a7043694c1984d3c8ae3cc0ac6212dd25`) and has local changes; treat this as **UNVERIFIED SOURCE** for the released emulator. The archive digest identifies the baseline bytes, not the modified tree's authenticity.

### Stale presence relay replacement — 2026-10-19

The launcher now requires a relay handshake with the same release build and the field-zone capability used by Teleport. A stale loopback relay is replaced only when Windows confirms its listener port, relay command line, executable name, and managed installation path; other computers and unrelated processes are left alone. The relay includes its release version in the welcome message.

Focused verification passed: `test_launcher_services.py` (**30/30**), `test_presence_relay_version.py` (**1/1**), `test_patchnotes_feed.py` (**5/5**), `test_release_validation.py` (**2/2**), `test_launcher_versioning.py` (**14/14**), and launcher-tree parity (**49 files**). A Windows process integration check launched the previous 2.0.19 relay from an isolated install, confirmed the new launcher identified and stopped it, then confirmed the replacement served the 2.0.20 handshake with Teleport support. The fixture was removed after the check.

The released emulator executable is unchanged from 2.0.19; this update changes launcher-side relay identity and replacement. The release package retains the corresponding 2.0.19 emulator source and carries the updated launcher and connection helpers. Live multiplayer and Teleport gameplay were not exercised in this verification.

### Teleport relay stale-build recovery — 2026-10-22

**CAUSE:** The game's readiness check previously accepted any protocol-v1 welcome. A relay from an older install could therefore keep answering on the local port while lacking the current `buildVersion` or `fieldZonePresence` capability; the game reused it and Teleport stayed unavailable. Updates and launcher restarts did not necessarily stop it because older game builds launched the relay through `python.exe`, while the launcher's cleanup recognized only its own packaged executable.

**FIX:** The game startup helper now requires the exact installed build and Teleport capability before reusing a listener. It starts the packaged launcher with `--presence-relay` when present, which gives the relay a managed process identity. For older Python-launched relays, Windows cleanup matches the interpreter and exact installed `tools/presence_server.py` plus host/port arguments, or the exact `tools/unova_launcher.py --presence-relay <port>` command used by source launchers; unrelated or remote listeners are left alone. The launcher can replace a same-build relay missing the required capability, as well as an unknown or older build, after the same ownership check. The helper and focused tests are included in both release source trees.

**PASS — FOCUSED VERIFICATION:** On Windows with Python 3.12, launcher tests passed **37/37**, maintenance-tree relay and launcher tests passed **54/54**, and launcher source parity matched **51 files**. The Windows lifecycle test launched a real legacy Python relay from a temporary install, confirmed it was stopped, then verified the replacement's current-build handshake and Teleport capability. Temporary test files were removed. No ROM, gameplay, shop, XP or battle synchronization code changed.

**LIVE TEST STILL NEEDED:** A paired in-game session was not run. Confirm that both clients use the same current game/launcher release, restart the host relay through the updated launcher, and verify Teleport on the same map and across a map transition.

### Tailscale setup review gate — 2026-10-21

Based on repository commit `784434454c8fbb2fa52d58e5ceda5081eac5180f`, the launcher blocks Tailscale host/join until the player scrolls the in-app guide to the end and checks its acknowledgment. The guide digest is stored in launcher settings; editing the guide requires a new review. The player guide, launcher guide, README, and co-op guide link to the steps and describe the LAN, ZeroTier, and group-hosted UDP choices.

**PASS — LAUNCHER UI:** Python 3.12.8 / Tk 8.6: `py -3.12 -B -m unittest test_launcher_ui` passed **41/41** in `launcher-source/tools` and **40/40** in `maintenance-tools/tools`. The focused tests cover canceled host and direct launch attempts, saved acknowledgments and re-review after guide changes, and the modal scroll/checkbox/continue flow. `py -3.12 -B launcher-source/tools/check_launcher_tree_parity.py` passed for **49 files**; `py_compile` and `git diff --check` passed.

**NOT RUN:** No packaged launcher was built, no cross-network session was started, and no live game session was tested. These tests use disposable UI profiles and placeholder ROM data; they do not establish Tailscale connectivity or game behavior.
