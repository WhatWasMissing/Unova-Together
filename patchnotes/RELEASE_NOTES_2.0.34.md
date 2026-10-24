# Unova Together 2.0.34 — Reliable AI agent previews and startup

- Field-model previews now handle the animation helper's returned frames correctly.
- Isolated emulator sessions prepare copied settings with explicit instance sections, avoiding the startup crash caused by implicit TOML tables. Failed launches report useful diagnostics.
- The Windows agent server uses UTF-8 for MCP messages so clients can discover tools containing Pokémon names and other non-ASCII text.

Emulator testing continues to use native DS button and touch controls with a private profile and copied save. Original ROMs, saves and normal settings remain separate from the isolated session.

This patch retains the existing emulator gameplay implementation and credited assets. No game ROM, user save, real firmware dump or generated gameplay capture is included. See [AI agent tools](../docs/AGENT_TOOLS.md), [emulator agent control](../docs/EMULATOR_AGENT_CONTROL.md), [verification report](../docs/AGENT_TOOLS_VERIFICATION_2.0.34.md), and [asset permissions and notices](../docs/RELEASE_ASSET_NOTICES_2.0.34.md).
