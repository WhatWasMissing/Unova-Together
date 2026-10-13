# Unova Together 1.0.8 — Launcher update fix

Fixes the case where installing a mod update showed the new release number while reopening the old shared launcher.

- Updates restart into the installed Pokémon Together launcher. Opening an earlier compatible hub forwards to a newer installed hub, preserving the same profile/save home and mod library.
- The Updates page and footer read the running launcher's embedded build metadata. Windows file/product versions and packaged launcher metadata come from the requested build version.
- Handoff rejects older launchers, legacy per-mod launchers and invalid metadata. Equal versions do not loop on startup. A failed handoff leaves the current launcher available.
- Portable launchers use their own installation folder. Shared shortcuts and update handoffs pass the original home explicitly, avoiding an unrelated hardcoded drive path.
- Corrected the emulator's version/credit labels. Gameplay is unchanged from 1.0.7, including the optional experimental native-Fly shortcut; ORAS-style free-flight Soaring remains unfinished.

## Upgrading a launcher older than 1.0.8

Older shared launchers cannot apply this restart fix to their already-running code. After installing 1.0.8 through Updates, close the launcher and run **launcher/Pokemon Together.exe** inside the new `.updates/versions/1.0.8/Unova-Together` folder with `--home` pointing to your original installation. A new portable installation or the standalone download also opens the corrected launcher. Keep the same home to retain profiles and backups. Future updates from this launcher switch automatically.

The release includes the Windows runtime, matching GPL source, standalone launcher and SHA-256 manifest. No ROM, firmware, save or RAM capture is distributed. Original Unova Together contributions by **mvq1303 / WhatWasMissing**, built on melonDS; upstream/dependency notices remain included.
