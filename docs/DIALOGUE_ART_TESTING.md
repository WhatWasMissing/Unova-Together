# Test the custom dialogue boxes

The release includes an authoring tool; the normal launcher does not add dialogue art automatically. The sample profile targets the Lentimas Town Pokémon Center nurse (zone 460, actor UID 6) and keeps her original text and event script.

## Build a separate test ROM

Use your own English Blaze Black 2 Redux Complete v1.4.1 IREO ROM. The patcher checks the exact source fingerprint listed in [the dialogue workflow](ROMHACK_DIALOGUE_WORKFLOW.md), refuses other builds, and will not overwrite an existing output.

From the extracted Windows ZIP or source checkout, create a private Python environment and install the listed dependencies:

```powershell
py -3.12 -m venv .venv-dialogue
.\.venv-dialogue\Scripts\python.exe -m pip install -r maintenance-tools/tools/rom/requirements.txt
```

Then write the derived ROM to a new path:

```powershell
.\.venv-dialogue\Scripts\python.exe maintenance-tools/tools/rom/dialogue_art_patch.py `
  --base-rom "<your source ROM>" `
  --speaker-profiles maintenance-tools/assets/dialogue-art/speaker-profiles.example.json `
  --output-rom "<new test folder>\Dialogue Art Demo.nds"
```

The ARM GNU toolchain (gcc, objcopy, and nm) must be available on PATH or in the path documented by the workflow. Keep the new ROM and a copied test save in a separate folder. The release does not contain either file.

## Run a silent, isolated test

Use a copied save whose player can reach Lentimas Town. The helper creates a private emulator profile, sets emulator volume to zero, disables DSi volume synchronization, uses SDL's dummy audio driver, and does not export the test save:

```powershell
.\.venv-dialogue\Scripts\python.exe maintenance-tools/tools/rom/run_muted_dialogue_test.py `
  --runner "<Unova Together folder>\tools\emulator_agent.py" `
  --emulator "<Unova Together folder>\builds\current\melonDS.exe" `
  --rom "<new test folder>\Dialogue Art Demo.nds" `
  --save "<copied test save>"
```

The command returns a private session description. Use the Unova Together MCP emulator controls to inspect the screen, wait, press native game buttons, and stop the session without a save-export path. No desktop keyboard or mouse simulation is needed. Keep waits short; 480 frames was reliable in the tested runtime.

## What to check

1. In the Pokémon Center, speak to the nurse. Confirm the Emma portrait, nameplate, frame, and readable native text appear together.
2. Advance through the pages with A. At the rest prompt, press B to decline, then A to close.
3. Reopen the nurse conversation and confirm the art appears again.
4. Speak with a nearby unconfigured character. Confirm their stock white dialogue window remains intact.
5. Walk outside and confirm the art has cleared. Stop the isolated session with no save export.

The same desktop scenario was verified against the exact build in [the renderer record](verification/ROM_DIALOGUE_ART_RENDERER_2026-10-24.md). DSi mode, real hardware, multiplayer, and every NPC/window style remain untested.
