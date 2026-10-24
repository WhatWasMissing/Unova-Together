# Unova Together 2.0.35 release verification

Release URL: https://github.com/WhatWasMissing/Unova-Together/releases/tag/v2.0.35

- Release state: published, stable (`draft: false`, `prerelease: false`).
- Tag and release commit: `v2.0.35` → `a77b50875bef3c81937186c0ba1630b518f977e5`.
- Latest-release discovery: GitHub `/releases/latest` returned `v2.0.35`.
- Launcher feed: `main/patchnotes/index.json` returned HTTP 200 with 2.0.35 as its first note.
- Package validation: portable controls present; private files excluded.
- ZIP integrity: Windows package (1,373 entries) and source package (2,532 entries) passed CRC checks. Neither contains ROM, save, firmware, key, or Python bytecode files.
- Source checks: 15 dialogue-renderer tests passed; 70 launcher/feed/release tests passed; all 43 mirrored launcher UI files match.
- No emulator was launched during release packaging or verification.

## Published assets

| Asset | Bytes | SHA-256 |
|---|---:|---|
| `Repair-Launcher.exe` | 12,216,876 | `c3023fa319fea067824ec684b9855502b0469fb85fe04064fe876580342135ad` |
| `SHA256SUMS-Unova-Together-2.0.35.txt` | 665 | `ddf330fb3273cfa1406bc1c926eb1e773debbfeeaaa478aeb179620659d55513` |
| `Unova-Agent-Tools-LICENSES.txt` | 185,370 | `5e1ab8057be3e3b04436d63eaca9f338b05619cb3b347f87c9e5bb31f690618e` |
| `Unova-Agent-Tools.exe` | 54,979,848 | `9c967e46f6eaff8bf8086caf30abbaa4d2bde21945871280b57b43b310933a79` |
| `Unova-Together-2.0.35-Source.zip` | 33,609,031 | `dd135910a2599a1b0177c2872a68a3067b39da92ec80fdb580e39b2e3c540cf6` |
| `Unova-Together-2.0.35-Windows-x64.zip` | 262,726,889 | `81b9e2248c7f888c7d9e5b4b7843788629c3c8f05d0bb4a314cc6ad960df90ef` |
| `Unova-Together-ASSET-NOTICES.txt` | 4,844 | `908a68c4618edf6b235adbb37639f74d59e2b4d08b07064385b756f4e2e038b2` |
| `Unova-Together.exe` | 302,616,164 | `e7e684da296211a8c80973a9eca3b8dea6cc408f812c4f382ad74150fd800b52` |

GitHub's release API sizes and SHA-256 digests matched every local asset.
