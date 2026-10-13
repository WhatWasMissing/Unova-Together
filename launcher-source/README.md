# Pokemon Together launcher

Shared mod library for Unova Together and the prepared Pokemon X prototype.
Unova's original multiplayer work is by mvq1303 / WhatWasMissing, built on melonDS.
This launcher retains upstream attribution and licensing.

Install the Windows launcher overlay into your existing Unova Together folder,
then run Start Pokemon Together.cmd. It opens Mod library on every launch.
Pokemon X requires your separately prepared modified emulator, own ROM and checkpoints.
No ROM, save, firmware, room credential or game checkpoint is included.

Source: Python 3.12, tomlkit, ndspy, Pillow and PyInstaller.
Run python tools/unova_launcher.py --home <your-Unova-installation>.
Build with python tools/build_unova_launcher.py; UI/routing tests run from tools.
Cleanup scripts are development utilities; they preview by default.

Launcher 1.0.6, build revision 2026101302, updates the Features tab and moves companion interactions to **Settings → Following Pokémon**, enabled by default when unset. Explicit off choices remain saved. The launcher passes both new and legacy runtime switches for compatibility. Nearby battle scenery remains experimental and off by default. This source/local update is newer than the launcher in public v1.0.6 release assets.

See the [feature guide](../docs/FEATURES.md), [roadmap](../docs/ROADMAP.md), and [native default-policy patch](../maintenance-tools/README.md#follower-defaults-and-feature-review--13-october-2026).
