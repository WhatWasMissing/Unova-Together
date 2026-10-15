# 1.0.17 release checks

## Mega Serperior

- Release-only emulator built with `UNOVA_MEGA_LOCAL_DRAFTS=OFF` and native
  product version 1.0.17.
- Cold-booted the exact supported Redux ROM from a disposable battery save,
  entered a genuine battle, and saved a full-state checkpoint at Serperior's
  move list. Diagnostics confirmed species 497, Serperiorite item 113, and all
  five reviewed native battle entry points.
- Full-state replay passed on the matching release executable: native
  ChangeForm handler completed, both battle copies changed form 0→1 and agreed
  on stats and Contrary (126), max HP remained 147, and the saved party record
  stayed unchanged.
- Verified release executable SHA-256: `F30728CE149A014E94753CB467F868F520B6166561C83F96E501F7ECCF10ECB6`.
- Battle-end cleanup completed. The test injects the end-of-battle transition;
  it does not test a natural knockout or victory.
- Client battle HP was 147 and server battle HP was 84 at the verification
  boundary, while both max-HP values remained 147. This is ordinary damage
  observed at different turn-animation boundaries; validation rejects HP
  gains and max-HP changes but permits damage in either copy.
- The fresh-state evidence, including the exact ROM and checkpoint hashes, is
  retained in the local source workspace's Mega verification record.

## Regression and release packaging

- All six Release CTest checks pass: Mega rules/assets, native selection,
  native call transaction, co-op packet, public roster, and the Redux ROM
  cartridge overlay.
- The launcher versioning suite passes 12 tests.
- Launcher, bootstrap, Windows runtime ZIP, corresponding-source ZIP,
  standalone launcher, Repair-Launcher, version labels, asset checksums, and
  forbidden private-file exclusions are checked by the release packaging
  pipeline. Final artifact hashes and sizes are added after packaging.
- No live two-emulator Mega battle or physical playtest was performed. The
  custom Mega Serperior artwork's original artist and public reuse terms are
  still unconfirmed.
