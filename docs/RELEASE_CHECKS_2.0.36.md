# Unova Together 2.0.36 release verification

Published: 2026-10-24  
Release: https://github.com/WhatWasMissing/Unova-Together/releases/tag/v2.0.36  
Latest release discovery: GitHub `/releases/latest` returned `v2.0.36`.  
Release commit: `afd6189496e821587aa584d43f75aa18b3cba8e9`  
Merged change: https://github.com/WhatWasMissing/Unova-Together/pull/3

## Verification performed

- Native Windows Release build completed; binary reports version 2.0.36.
- Area battle scenery context regression tests passed (10 cases).
- Native source patch suite passed (5 cases) against the exact 2.0.34 source archive.
- Launcher test suite passed (112 tests).
- Launcher UI parity, release validation, and patchnote feed checks passed.
- Packaged source and Windows ZIPs passed archive integrity, payload, and private-file checks.
- Live emulator gameplay was not run for this release. The active emulator and all saves were left untouched.
- The main profile ROM is unpatched, so it does not exercise the separate custom dialogue-art renderer. Follow [Dialogue art testing](DIALOGUE_ART_TESTING.md) to build and run the isolated demo with a copied save.

## Remote asset verification

The asset name, byte size, and GitHub SHA-256 digest were checked against each local release asset after upload.

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| Repair-Launcher.exe | 12,216,876 | c3023fa319fea067824ec684b9855502b0469fb85fe04064fe876580342135ad |
| SHA256SUMS-Unova-Together-2.0.36.txt | 665 | da4cdd06a0a042d14b11532a4ddbbd48cd21dfd6441f32e636c004cc21ade621 |
| Unova-Agent-Tools-LICENSES.txt | 185,370 | 5e1ab8057be3e3b04436d63eaca9f338b05619cb3b347f87c9e5bb31f690618e |
| Unova-Agent-Tools.exe | 54,981,194 | 48c75bf7e237d4ebc444b817605179f9b605f15d1fbd6a57fb7f62975d9dd273 |
| Unova-Together-2.0.36-Source.zip | 33,621,420 | 524758e9d9ef7fd3606db9e26f36d7be72d9b627473343089881a8670f2fa7cc |
| Unova-Together-2.0.36-Windows-x64.zip | 262,742,703 | a6ddf7fb685f47734c8206c6d95aeb6cf0a4cdea6662682639efd5d7b4d2d977 |
| Unova-Together-ASSET-NOTICES.txt | 5,010 | fd0a776eb6aa03dcc099cd83d64cb70067663b4bb1f8b7529e213f541c092b02 |
| Unova-Together.exe | 302,621,771 | ab5f44c26c796f5e8d190429eeb05f30f2f3869f73f0e50ea57a898ae91a113e |
