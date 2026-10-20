# Mega Stone shop distribution — 2026-10-20

Status: **IMPLEMENTED — RUNTIME UNVERIFIED**. Base: GitHub `main` commit `5ba227c041f741df827f05d34fc6deabe0d4b204` (2.0.22). This is a source update for the next release, not a new runtime package.

## Behavior

The 20 standard Mart inventories (archive members 6–25) each receive three distinct Mega Stones. All 49 supported stones occur across those inventories; 11 occur twice. Legacy Mega Stone rows are removed before assignment. The other 54 Mart lists receive no added stones. Ordinary items retain their order. Existing Battle Point stock and stone prices are unchanged.

The native 45-row limit is retained. The custom heap-backed shop overlay remains uninstalled, preserving the merchant-crash fix in 2.0.19. No ROM or save is edited on disk.

## Evidence

- **PASS — SOURCE/UNIT VERIFIED:** `test_gen5_shop_distribution.py` compiled the policy and item IDs extracted from the distributed patch using Python 3.14.7 and MSYS2 GCC 16.2.0, C++17, `-O2 -UNDEBUG`. It exercised equal stock counts, complete coverage, per-shop uniqueness, ordinary/TM item order, idempotency, untouched non-Mart records, invalid roster/count inputs, and over-capacity rejection without partial mutation.
- **PASS — ROM DATA VERIFIED:** The same fixture exercised the packaged policy against both local Redux ROMs below. Both produced a maximum of 20 rows across the 74 Mart lists. All 20 standard inventories contained exactly three stones and all 49 stones were covered. Original ordinary stock was preserved. The fixture models the cartridge loader's power-of-two, `0xFF` memory padding for trimmed dumps; it does not execute the emulator. Its adapter supplies only the `ROMAssetPatch` transport structure, and applies returned byte ranges independently.
- **PASS:** Both ROM SHA-256 hashes were unchanged after the read-only checks: full Redux `332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a`; launcher ROM `353fb0cf82c3e4eddfc8986efa8910b00eb1c4d6f106c220abef59d69d3a520a`.
- **PASS:** Seven existing shop-overlay/package regression tests and two native-options/metadata tests, including source-patch parsing, metadata integrity, the 45-row limit, and absence of the custom overlay installation.
- **PASS — DECOMP REFERENCE:** The [current upstream shop source](https://github.com/fuddlesworth/pokebw2/blob/068abb42f92f8da5e34d07be85bc8adde8a68840/src/ov036/scrcmd_shop.c), pinned to commit `068abb42f92f8da5e34d07be85bc8adde8a68840`, confirms `fileId + 6` for standard marts and fixed `entries[45]` / `tutorMoveIndices[45]` arrays. The downloaded source SHA-256 is `914da4f93e9d37f69121e3de83206dc5ff2194225aeb931600076eb434e6ed87`. The available 62% local decomp confirms the same facts (file SHA-256 `ae7e0f3926e97cc085d5d2c753878721a615ebc75f89dda81b0880286f1c7ddd`). The supplied 92% local copy was still extracting and its shop source was not yet present; its exact archive revision was not used as evidence.
- **NOT RUN:** Emulator rebuild, launcher runtime packaging, live merchant navigation/purchase, and visual confirmation of stock at every Center.

## Reproduce

Run from the repository root on Windows with a C++17 compiler. ROM arguments are optional; omitting them runs the source/unit checks only. Missing compiler/files, malformed source, failed assertions, and changed ROM hashes fail the check.

```text
python maintenance-tools/tools/test_gen5_shop_distribution.py --cxx C:/msys64/ucrt64/bin/g++.exe --rom "<full Redux ROM>" --rom "<launcher ROM>"
python -m unittest discover -s maintenance-tools/tools -p test_gen5_shop_overlay_patch.py -v
python -m unittest discover -s maintenance-tools/tools -p test_native_options_menu.py -v
```

Generated headers and executables are confined to a verified disposable directory under the repository and removed after the checks. ROMs, saves and source fixtures are retained.
