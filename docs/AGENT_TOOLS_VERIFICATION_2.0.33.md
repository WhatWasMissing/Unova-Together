# Agent tools verification for 2.0.33

This record covers the source and launcher checks completed for the 2.0.33 release candidate on 2026-10-24.

## Automated checks

- `py -3.12 -m unittest test_unova_agent test_emulator_agent test_patchnotes_feed test_release_validation` — 27 tests passed.
- `py -3.12 -m py_compile unova_agent.py emulator_agent.py package_unova_release.py` — passed.
- `py -3.12 check_launcher_tree_parity.py` — passed; all 43 mirrored launcher files matched.
- `ctest --test-dir builds/emulator-agent-protocol-2.0.32-retry -R '^emulator_agent_protocol_validation$' --output-on-failure --timeout 15` — passed. The Qt runtime directory `C:\msys64\ucrt64\bin` was added to `PATH` for this test process.
- `git diff --check` — passed; Git reported only the repository's expected CRLF normalization notices.

The MCP tests cover modern discovery and tool listing, required `tools/list` cache hints over stdio and HTTP, legacy initialization and version negotiation, malformed and mismatched HTTP metadata, tool-call errors, rejection of caller-selected emulator executables, and oversized stdio messages. The emulator tests exercise the direct native-control client and isolated-session behavior.

These checks verify interfaces and packaging inputs. They do not claim that every game feature or multiplayer scenario was tested in a live playthrough. See [the emulator agent guide](EMULATOR_AGENT_CONTROL.md) for scope and limitations.
