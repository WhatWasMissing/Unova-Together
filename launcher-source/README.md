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

Launcher 1.0.20, build revision 2026101502, is paired with the 1.0.20 emulator package. Updates can stage beside a running game, and Play remains blocked only while an emulator from the same installation is open. News reads the simple version notes from the GitHub `patchnotes/` folder, even if old GitHub Releases are removed.
