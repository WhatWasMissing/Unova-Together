# 1.0.16 release checks

- Windows x64 Release emulator rebuilt from the matching source with native file/product versions set to 1.0.16.
- Standalone launcher and Repair-Launcher file metadata report 1.0.16. The standalone smoke test created its window, showed `Release 1.0.16 · Launcher 1.0.16`, detected update checking, and kept Play disabled without a ROM.
- Runtime and corresponding-source archives passed ZIP integrity and source-content checks. All four downloadable files match their SHA-256 manifest; the repair executable embedded in the Windows ZIP matches the separate Repair-Launcher download.
- Native full-state Serperior replay passed: Serperior (species 497) held Serperiorite (item 113), the native ChangeForm handler ran after Fight was committed, and client/server battle copies agreed on form 1.
- The replay verified battle stats changed from `[73, 97, 95, 92, 113]` to `[94, 115, 121, 102, 131]`; Contrary (ability 126) and 147 HP were preserved, and the saved party record remained unchanged.
- Battle-end cleanup replay passed and reported the saved party record restored to its original bytes.
- All seven Release CTest regressions pass, including the Redux ROM overlay and paired Mega co-op call/packet path. Five sprite-generator Python tests pass.
- Real two-emulator Mega activation, live co-op recovery and physical playtest were not performed. Paired event tests are deterministic LAN/native-call regressions, not a live battle.
- The supplied Mega Serperior artwork's author and public reuse terms remain unconfirmed; this test build uses the same art asset already present in 1.0.15.
