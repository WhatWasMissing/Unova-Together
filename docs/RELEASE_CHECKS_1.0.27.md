# Release checks — 1.0.27

- Mega Mewtwo X sprite source: supplied `PokeMMO Mega Sprites - X.zip` archive, species 150; confirmed distinct from the Y archive.
- Generated Mega Mewtwo X artwork was removed from the source tree and is not included in the release packages.
- Sprite asset import regressions: 9/9 pass, including a check that Mega Mewtwo X imports the X archive's normal and shiny art.
- Sprite asset importer: 9/9 tests pass.
- Mega regression suite: 9/9 tests pass, including the Redux cartridge overlay and the split-form sprite check.
- Windows emulator target builds successfully with the updated sprite table.
- Fresh runtime/source ZIP integrity, private-file exclusions, generated-art scan, and SHA-256 sidecar are checked during packaging.

