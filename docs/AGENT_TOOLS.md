# AI agent tools

The release includes project-aware tools that call the launcher's Python APIs and melonDS's native agent-control API directly. An agent can inspect the mod, search source and documentation, read ROM-derived model assets, inspect supported saves, check launcher profiles, and play through a private emulator session without synthesizing desktop keyboard or mouse events. The corresponding-source archive includes the agent adapter, emulator protocol, tests, dependency list, and the launcher and maintenance sources used to discover project tools.

## Local coding agents

The Windows runtime release includes a self-contained **Unova Agent Tools.exe** in `tools/`. It bundles the Python runtime and ROM-inspection dependencies, so a local agent can start MCP without installing Python packages:

```powershell
& '.\tools\Unova Agent Tools.exe' mcp
```

Point a local MCP-capable coding client at that command. From a source checkout, use the Python helper instead:

```powershell
python launcher-source/tools/unova_agent.py --project-root . mcp
```

The separate `Unova-Agent-Tools.exe` download is intended for use with an existing checkout or extracted runtime package. Pass that project's root explicitly because the standalone executable is not inside the project tree:

```powershell
& "$env:USERPROFILE\Downloads\Unova-Agent-Tools.exe" --project-root "C:\path\to\Unova-Together" mcp
```

Use the same `--project-root` option before `mcp-http` or any direct command when launching the standalone download.

The same agent executable also provides direct commands: `inventory`, `search`, `document`, `rom`, `save`, `compare-saves`, `models`, `model-preview`, `launcher`, `profiles`, `emulator-start`, and `emulator-control`. The source helper needs Python 3.12 and the pinned packages in `launcher-source/tools/requirements-agent-tools.txt`; install them with `python -m pip install -r launcher-source/tools/requirements-agent-tools.txt`. The release executable bundles them and ships their license notices in `Unova-Agent-Tools-LICENSES.txt`.

The server's MCP tools are `project_inventory`, `search_project`, `read_project_document`, `inspect_rom`, `inspect_save`, `compare_saves`, `redux_progression`, `list_player_models`, `preview_player_model`, `inspect_launcher`, `list_launcher_profiles`, `start_emulator`, and `control_emulator`. Model previews and emulator screenshots are returned as image content when the client supports MCP image results.

## ChatGPT connection

ChatGPT's custom MCP connection needs an HTTP endpoint; it cannot connect directly to a local stdio process. This release includes an authenticated Streamable HTTP endpoint that binds only to loopback. Start it from PowerShell with a random bearer token:

```powershell
$tokenBytes = New-Object byte[] 48
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($tokenBytes)
$env:UNOVA_AGENT_HTTP_TOKEN = [Convert]::ToBase64String($tokenBytes)
& '.\tools\Unova Agent Tools.exe' mcp-http
```

The endpoint is `http://127.0.0.1:8765/mcp`. The server supports current stateless MCP `2026-07-28` requests and legacy handshake clients using `2025-11-25`, `2025-06-18`, or `2025-03-26`. Modern requests include protocol version and client capabilities in `params._meta`; HTTP requests also provide the matching `MCP-Protocol-Version`, `Mcp-Method`, and (for `tools/call`) `Mcp-Name` headers. See the [MCP versioning rules](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning) and [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http).

Modern `server/discover` and `tools/list` results include cache hints. The fixed tool list is shared across callers and advertises a one-hour freshness period.

The endpoint validates Host and Origin, requires bearer authentication, and binds only to loopback. For a trusted tunnel with different forwarding values, set `UNOVA_AGENT_ALLOWED_HOSTS` to comma-separated hostnames and `UNOVA_AGENT_ALLOWED_ORIGINS` to comma-separated exact Origin values. Connect through a trusted Secure MCP Tunnel, or host behind HTTPS with authentication. Keep the bearer token private. Do not bind this server to a public network interface. In ChatGPT, add a custom MCP server/plugin using the tunnel endpoint and configure bearer-token authentication. Workspace plan and administrator settings control availability; see [OpenAI's current MCP connection instructions](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt).

When the emulator is running on the same machine as the server, the MCP `start_emulator` and `control_emulator` tools can drive it through the local native API. Exposing emulator controls through a remote tunnel grants whoever can call that MCP endpoint the ability to play in the isolated session. Limit access to a trusted agent and stop the session when done.

## Emulator play without desktop input

The Windows emulator exposes an opt-in API on `127.0.0.1`. The MCP server starts the configured project executable through `tools/emulator_agent.py`; an MCP caller cannot supply an executable path. The runner gives it a fresh melonDS profile, a temporary ROM hard link, and a copied save. It never points the isolated instance at the user's live save. If the launcher has a selected profile, its ROM and newest matching save are used by default. Pass `rom`, `save`, or `profileId` to choose inputs explicitly.

An agent can use `control_emulator` to:

- check status and pause or resume;
- press supported DS buttons for a bounded frame count;
- touch a coordinate on the 256×192 lower screen;
- advance a bounded number of emulated frames;
- capture both DS screens as a PNG;
- create or restore a named session-local save-state checkpoint;
- stop the emulator and remove its marked temporary profile.

The MCP `stop` tool discards the isolated save with the session. The local CLI can export that isolated save to a new path that does not already exist; the original save remains unchanged. See [EMULATOR_AGENT_CONTROL.md](EMULATOR_AGENT_CONTROL.md) for the lower-level runner and native protocol, setup, and limitations.

Build matching emulator source is provided in the corresponding-source release asset at `source/melonDS`. To search or build that source, unpack it and pass its path with `--emulator-source`, or set `UNOVA_EMULATOR_SOURCE`. A runtime-only installation does not contain the complete emulator source tree.

## ROM assets and external tools

`project_inventory` and `search_project` describe repository docs, launcher code, maintenance utilities, patch notes, asset metadata and an optional matching melonDS source tree. The inventory reports reference files only at documented paths beneath the configured project root; it does not search the whole computer, discover applications installed elsewhere, launch tools, or imply that those tools are bundled. Existing project workflows remain available as source and command-line utilities, and agents can read their docs and inspect their code directly.

ROM inspection reads the user-selected file and returns compatibility fingerprints and SHA-256. Save inspection checks supported Redux party records and checksums. Model listing and preview decode ROM-resident field assets through the same implementation used by the launcher. The releases contain the mod's credited follower and Mega artwork, the cleared Mega Evolution sound cue, and independently implemented FreeBIOS replacements with their notices. They contain no game ROM, user save, real firmware dump, or generated gameplay capture. See [2.0.33 asset permissions and notices](RELEASE_ASSET_NOTICES_2.0.33.md) for the included asset terms and credits.

These tools make evidence easier to collect; they do not provide a game-state oracle. A successful input request, screenshot, source test, or ROM fingerprint does not by itself prove a feature works in multiplayer or in every part of a playthrough. Record the exact ROM and build, and verify gameplay claims with appropriate live checks.
