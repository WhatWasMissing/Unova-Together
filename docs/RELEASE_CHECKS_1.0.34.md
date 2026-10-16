# Release checks — 1.0.34

- Rebuilt the Windows x64 emulator from the updated source with CMake.
- `pokemon_follower_trail` passes. Its regression checks matching sprite art with different transparent margins and confirms that the normalized frames are identical, retain their original pixels, and share the same ground alignment.
- Launcher patch-note feed and update-version regression tests pass (16 tests).
- PyInstaller built the updated Windows launcher with Mega Evolution featured first on the Features page.
- Release packaging verifies the launcher identity, latest patch note, Qt platform plugin, runtime executable, portable controls, and corresponding source archive.

The follower pose fix has automated coverage, but still needs visual confirmation in a live game. Soaring remains unfinished and experimental.

