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
