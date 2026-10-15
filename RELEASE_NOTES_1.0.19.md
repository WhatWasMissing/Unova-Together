# Unova Together 1.0.19 — Windows startup repair

Version 1.0.18 could show a melonDS error saying the Qt Windows platform plugin
could not be initialized. Its runtime archive contained the Qt libraries but
omitted `platforms/qwindows.dll`. Version 1.0.19 packages the matching Windows
plugin with the emulator, including inside the standalone download. The release
packager now refuses to build a Windows package if that plugin is missing or
invalid, then verifies the archive copy matches the staged runtime.

There are no Mega gameplay changes in this hotfix. Mega Serperior remains the
only playable Mega profile in the public build. See
[`docs/MEGA_EVOLUTION.md`](docs/MEGA_EVOLUTION.md) for its test steps.

Update from the launcher or download the complete Windows x64 ZIP from the
[1.0.19 release page](https://github.com/WhatWasMissing/Unova-Together/releases/tag/v1.0.19).
If melonDS is still running, close it before launching the updated emulator.
