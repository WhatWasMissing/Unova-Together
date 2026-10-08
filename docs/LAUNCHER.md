# Unova Together launcher

Extract the complete Windows ZIP and open **Start Unova Together.cmd**. Choose your own Black 2/Redux ROM with **Browse**, then select **Play**. The ROM path is remembered locally. Made by mvq1303 / WhatWasMissing.

The launcher checks the official **WhatWasMissing/Unova-Together** GitHub releases when it opens. Turn that checkbox off for offline play, or use **Check for updates** whenever you wish. Published beta releases are included; drafts and source-only downloads are ignored.

When an update is available, select **Install update**. The download is checked against the release SHA-256 checksum before installation. GitHub HTTPS and the official repository are the trust source; checksums detect corruption, not a compromised publisher account.

Updates install into `.updates/versions/<version>` beside the bundled build. The launcher switches to the new emulator after successful verification and copies your emulator configuration, including controls. ROMs, saves and existing settings are not overwritten. Save normally and close the game before switching versions; an open game cannot transfer its unsaved progress to the new build.

The next time you open **Start Unova Together.cmd**, it forwards to the updated launcher included with that release. Keep the launcher folder together with its `_internal` folder. No separate Python installation is needed for the launcher. The connection helper scripts still need Python as described in the player guide.

If a download fails or is cancelled, the active build stays unchanged. Close the launcher to cancel an ongoing download. If GitHub is unavailable, you can still launch your installed game. Avoid installing multiple updates at once or moving installation folders while the launcher is open.

The original **Start Emulator.cmd** always starts the original bundled emulator. Use it if you need to return to that version; do not run two builds against the same save simultaneously. Previous update folders are deliberately retained and are not automatically deleted.
