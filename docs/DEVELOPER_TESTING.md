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

**SOURCE/UNIT VERIFIED:** Five focused tests pass. The Mega asset and supported-cartridge checks also pass against the full-size Redux ROM copy, including Mega Stone stock checks. **GAMEPLAY VERIFIED:** A build from the 2.0.16 source with the narrowed overlay (SHA-256 `c3de037c3526c80b83a830b32b4e8cb9d0337151eeed7c9a5f207759b53cc3fb`) completed the scripted Continue flow into Route 7 (map 337, tile 107,237); the emulator reported input unblocked and rendered the field. The tested full-size ROM copy has SHA-256 `332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a`. The ROM and save were disposable copies, and the save copy's SHA-256 was unchanged before and after. The test used scripted DS button masks rather than physical keyboard input or the launcher, and it does not prove every save or the shop menu's visual layout. No release was published.
