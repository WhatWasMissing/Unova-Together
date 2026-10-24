# Agent tools verification for 2.0.34

Verified on 2026-10-24, based on published repository commit
`3559d38ec1b44b71bf3d395d459e965763f5bc00`. The release commit is the GitHub tag target;
asset digests and publication checks are recorded separately after upload.

## Scope and cause

- PASS: preview adapter unpacks `(frames, label)` before encoding the first image.
- PASS: private copied TOML promotes missing InstanceN parents; package generation
  also declares them. Original settings remain untouched.
- PASS: failed startup retains the original diagnostic if cleanup fails, including
  filesystem errors; uncertain sessions remain available for safe inspection.
- PASS: agent entry configures stdin/stdout/stderr as UTF-8, including frozen Windows builds.

## Source/unit evidence

CPython 3.12.8, PyInstaller 6.22.3, Windows x64. Run from launcher-source/tools:

`py -3.12 -m unittest test_unova_agent test_emulator_agent test_patchnotes_feed test_release_validation`

PASS: 31 tests, including real production preview adapter with a synthetic Pillow
image, copied settings with implicit/explicit parents and preserved source values,
cleanup PermissionError retaining original native log, and subprocess UTF-8 with
PYTHONIOENCODING=cp1252/PYTHONUTF8=0. Existing HTTP/stdio authentication, protocol,
bounds, no MCP save export and executable-selection guards remain covered.

PASS: 43 launcher UI files match their maintenance mirror. PASS: diff whitespace.
Two targeted real-ROM regressions that failed on 2.0.33 now pass against the source.

## Packaged integration evidence

PASS: first full 2.0.34 candidate built eight assets, passed archive integrity,
private-file exclusion, version/feed checks and source-fingerprint validation.
The final packaging run incorporates this record and the reusable live verifier.

PASS: `verify_unova_packaged.py` against the candidate frozen agent with forced
Windows code-page environment, the packaged runtime, and a user-owned ROM/save:

- Strict UTF-8 initialization and 13-tool listing.
- Real model 4715 and Pikachu 4121 previews returned valid PNG image content.
- Normal isolated start succeeded without modifying the temporary config manually.
- Status, wait, press, touch, pause/resume, screenshot, save/load checkpoint and stop.
- Pause confirmed via subsequent status and stable frame count.
- Original ROM/save, packaged settings and user launcher profile hashes unchanged.
- Isolated session stopped and removed, with no save export.

Run the included `tools/verify_unova_packaged.py --executable <agent.exe>
--project-root <runtime> --rom <user.nds> --save <user.sav> --output <fresh-test-dir>`.
It requires user-provided fixtures, fails on missing inputs, strictly decodes UTF-8,
and writes temporary images/report for inspection. Remove those outputs after recording results.

## Native binary and source provenance

The emulator gameplay binary is unchanged, SHA-256
`f8a6b7071f13bd151e714327c7f00a22c94fefe6e763d1b8b09307a88524d9ca`.
Matching native source was extracted from the official 2.0.33 Source ZIP, SHA-256
`915d0159d5acce4435a638a4f175b87a1b471c223a30fedfe749c3100fd75525`,
authenticated against GitHub's release asset digest. The packager verifies its
shop-patch source fingerprint against the unchanged executable. Attribution,
cleared asset notices and FreeBIOS redistribution terms are preserved.

## Preservation and limits

Original ROM SHA-256: `353fb0cf82c3e4eddfc8986efa8910b00eb1c4d6f106c220abef59d69d3a520a`.
Original save SHA-256: `54a3058d8e8b93942c193266a073a965dcd5ebfa2ca89080076729be2e8c0933`.
User launcher profile SHA-256: `996d6c66ab96f83a5010a56eb54116a11e776b25869f4bb357b361871cddec2c`.

NOT RUN: two-client multiplayer, all ROM revisions/models, endurance testing and
remote tunnels; these agent-only changes do not claim those features were tested.
Native game internals, save formats, ROM patching and networking were not changed.
NOT RUN at archive creation: publication/latest-release checks. These are mandatory
post-upload checks, performed against names, sizes and SHA-256 digests before
reporting publication complete. Temporary captures/build fixtures are cleaned only
after results are recorded; releases, original inputs and active installations remain.
