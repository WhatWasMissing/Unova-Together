# Unova Together 2.0.32 — Tools for AI coding agents

AI coding agents can inspect project source, docs and asset metadata through MCP tools, check user-provided ROMs and saves, list and preview field models, inspect launcher profiles, and play a game in an isolated melonDS session. Emulator input, touch, frame waits, screenshots, pause/resume and checkpoints use a direct local API, without simulating desktop keyboard or mouse events.

The release includes local MCP setup instructions, a loopback-only authenticated HTTP endpoint for trusted tunnels, emulator protocol and runner source, and repeatable tests. It also includes credited follower and Mega artwork, the cleared Mega Evolution sound cue, and independently implemented FreeBIOS replacements with their notices. No game ROM, user save or real firmware dump is included. See [AI agent tools](../docs/AGENT_TOOLS.md), [emulator agent control](../docs/EMULATOR_AGENT_CONTROL.md), [verification report](../docs/AGENT_TOOLS_VERIFICATION_2.0.32.md), and [asset permissions and notices](../docs/RELEASE_ASSET_NOTICES_2.0.32.md).

These tools help collect evidence but do not automatically determine whether a gameplay change passed. Multiplayer and game behavior still need checks appropriate to the feature.
