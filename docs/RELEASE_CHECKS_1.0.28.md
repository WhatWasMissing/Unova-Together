# Release checks — 1.0.28

- Converted supplied animated Mega sprite sheets into frame sequences; Salamence front and back each contain 67 frames.
- Sprite conversion tests: 14/14 passed.
- Mega regression tests: 10/10 CTest cases passed, including the Black 2 Redux cartridge overlay.
- Windows Qt emulator target rebuilt successfully; executable version resource reports 1.0.28.
- Live in-game animation playback has not yet been checked. This release is for the user to test Mega Salamence in battle.
- Release packaging verifies the complete Windows ZIP, corresponding source ZIP, standalone launcher, repair launcher, Qt platform plugin, and SHA-256 sidecar.
- Windows ZIP: 173,778,626 bytes; SHA-256 `6088814e909657410c3c435048822d5784707e07b015b011aefb88c7ea588b2f`.
- Source ZIP: 15,065,588 bytes; SHA-256 `f152d16b2837303c0ae234e1a8d5f63a686a622616a364a21f582d6b1820da78`.
- Standalone launcher: 197,020,934 bytes; SHA-256 `f299662c96108630ff51001ab39f0a3274a31ba4b0b28633d7ee29f005dfde4d`.
- Repair launcher: 12,211,137 bytes; SHA-256 `5ab142631fa59dcba3db4bb20a43456cdf9b89776c97c2df4efeca07c00cd16d`.
- ROMs, saves, firmware, and RAM dumps are excluded.
