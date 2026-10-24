# Programmatic emulator playtesting

Unova Together's melonDS frontend includes an **opt-in local agent-control API**. It lets a test script press DS buttons, tap the touch screen, wait for emulated frames, capture both screens, and save or restore a checkpoint without synthesizing operating-system keyboard or mouse events.

## Build

Build the modified emulator with the project's normal CMake build, then configure the standalone protocol test from `tools/`:

```powershell
cmake --build build --target melonDS
cmake -S tools -B build/emulator-agent-protocol-check -G Ninja -DCMAKE_PREFIX_PATH=C:/msys64/ucrt64
cmake --build build/emulator-agent-protocol-check --target emulator_agent_protocol
ctest --test-dir build/emulator-agent-protocol-check -R emulator_agent_protocol_validation --output-on-failure
```

The API is disabled in ordinary launches. `tools/emulator_agent.py start` enables it only for the emulator process it starts.

## Start an isolated session

```powershell
$started = python tools/emulator_agent.py start `
  --emulator build/melonDS.exe `
  --rom "C:\path\to\your\patched-game.nds" `
  --save "C:\path\to\a\copy-of-your-test-save.sav" | ConvertFrom-Json
$session = $started.session
```

The runner opens the ROM through a temporary hard link, copies an optional save into that temporary directory, and gives melonDS a separate temporary settings profile. The user's ROM, original save, and normal melonDS settings are left in place. A same-volume hard link is required; the runner fails without copying the ROM when that cannot be created. The temporary session remains until `stop` succeeds.

## Drive and inspect the game

```powershell
python tools/emulator_agent.py status --session $session
python tools/emulator_agent.py press --session $session Up --frames 12
python tools/emulator_agent.py press --session $session A --frames 8
python tools/emulator_agent.py touch --session $session --x 128 --y 96 --frames 8
python tools/emulator_agent.py wait --session $session --frames 60
python tools/emulator_agent.py screenshot --session $session --out "$env:TEMP\unova-test.png"
python tools/emulator_agent.py save-state --session $session --name before-menu
python tools/emulator_agent.py load-state --session $session --name before-menu
```

Screenshots are native 256×384 PNGs with both DS screens stacked vertically. An explicit screenshot destination is never overwritten; if `--out` is omitted, the image is written inside the disposable session. Save-state names are restricted to safe local filenames and all checkpoint files remain inside the session. Use `EmulatorAgent` from the same Python module to hold multiple buttons across calls; closing its connection releases input.

Stop and remove the isolated profile when finished:

```powershell
python tools/emulator_agent.py stop --session $session
```

If melonDS has already exited, `cleanup --session $session` removes the marked temporary session. Both operations verify the session marker and temporary-directory boundary; cleanup refuses to remove a live or unverifiable process. An optional `stop --save-out <new-path.sav>` exports the isolated test save to a new path before cleanup and refuses to overwrite an existing file.

## Control protocol and limits

The emulator listens only on `127.0.0.1`, requires a random 256-bit token, accepts one client at a time, and removes its endpoint file on shutdown. Each request and response is one JSON object per line. Supported commands are `status`, `set_buttons`, `press_for`, `release`, `touch`, `wait_frames`, `screenshot`, `pause`, `resume`, `save_state`, `load_state`, and `shutdown`. Button and touch requests are bounded to 3,600 frames; touch coordinates are restricted to the DS panel's 256×192 input area.

This is an input and screen-capture interface, not a game-specific oracle. It does not read or interpret game memory, infer whether a feature passed, automate network multiplayer, or replace live playtester verification. A screenshot provides the visible evidence; feature behavior still needs an explicit assertion or human review.
