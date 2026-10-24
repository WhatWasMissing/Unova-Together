# AI agent tools verification — 2.0.32

## Source identity

The Git checkout used for the release was based on `origin/main` commit `b061df853eeee7f05f5d000401aa7e3141a4a68e`. The release's helper and test files were fingerprinted during verification:

| File | SHA-256 |
| --- | --- |
| `launcher-source/tools/unova_agent.py` | `c3de803e418687a6d4767081acd682bccbe344838689576a48bd7edd54fae652` |
| `launcher-source/tools/emulator_agent.py` | `ed5d9b933cb49694ac7e1542dd485deedfccb61b0b2bfc3d60e422aa10256c5d` |
| `launcher-source/tools/test_unova_agent.py` | `5902e21a49591331af41e6b5175af01222175009868b7d23197973c219931dec` |
| `launcher-source/tools/test_emulator_agent.py` | `083af380bbc04e61d4a01f99c280daba7429e8e5f1c430cf633829edf04bc519` |
| `source/melonDS/tools/test_emulator_agent_protocol.cpp` | `ff56bfb06501817cca36575b3d0c29bb08668cc34e14f393d0a435e6540006ee` |

The corresponding native source tree is shipped at `source/melonDS/` in the 2.0.32 source asset. Its package-input manifest digest is `1b1d4d6e6e97892c69ae981d95b036a5db093f89ce1900d5472105fca872710d` across 2,371 included native-source files. The packager checks that the staged emulator executable contains the fingerprint from the matching Mega shop patch source and copies that exact source tree into the archive.

## Checks

The checks ran on Windows 10 (build 19045) with Python 3.12.8 and PyInstaller 6.22.3.

| Check | Result | Evidence |
| --- | --- | --- |
| Agent dispatcher, HTTP/MCP authentication, bounds, profile isolation, and failure cleanup | **PASS** | `python -m unittest test_unova_agent test_emulator_agent` — 16 tests |
| Python syntax | **PASS** | `python -m py_compile` for `unova_agent.py`, `emulator_agent.py`, and `package_unova_release.py` |
| Mirrored launcher tree | **PASS** | `check_launcher_tree_parity.py` — 43 files match |
| Native protocol implementation | **PASS** | `emulator_agent_protocol_validation` CTest from the matching native source tree |
| Frozen agent executable | **PASS** | Release packager ran `Unova Agent Tools.exe --project-root <checkout> inventory` and checked its JSON version/result |
| Release archives | **PASS** | ZIP integrity, required agent sources/notices, version metadata, and SHA256SUMS checks passed; the full FreeBIOS binary notice is present in runtime docs and the standalone notice sidecar; generated `*.latest.json` outputs and `.release-build-input` are excluded from the runtime/source ZIPs and the standalone EXE’s embedded corresponding-source archive, and ROM, save, firmware-dump, key, and bytecode extensions are rejected |
| Isolated emulator control smoke | **PASS** | The staged emulator reported its local API ready; status, button input, frame wait, and screenshot calls succeeded in an isolated session, then the runner stopped and cleaned that session |
| Multiplayer/gameplay assertions | **NOT RUN** | These agent-interface checks do not establish game-feature correctness or multiplayer synchronization |

Reproduce the Python and mirror checks from `launcher-source/tools/` with Python 3.12:

```powershell
python -m unittest test_unova_agent test_emulator_agent
python -m py_compile unova_agent.py emulator_agent.py package_unova_release.py
python check_launcher_tree_parity.py
```

See [AI agent tools](AGENT_TOOLS.md), [emulator agent control](EMULATOR_AGENT_CONTROL.md), and [asset permissions and notices](RELEASE_ASSET_NOTICES_2.0.32.md) for setup, isolation boundaries, and included asset terms.
