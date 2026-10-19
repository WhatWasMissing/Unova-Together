#!/usr/bin/env python3
# Unova Together contributions: Copyright (C) 2026 mvq1303.
# GPL-3.0-or-later. See LICENSE.
"""Run one isolated melonDS gameplay probe and summarize its observer report.

The ROM, save sidecar, emulator config, and output prefix should belong to a
disposable test directory. This runner does not copy or modify those inputs.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def check_report(
    data: dict[str, object] | None,
    expected_map: int,
    log_text: str,
    timed_out: bool,
    returncode: int | None,
) -> list[str]:
    failures: list[str] = []
    if data is None:
        failures.append("observer report is missing or invalid")
        return failures

    frames = data.get("npcFixtureFrames")
    # bool is an int subclass in Python; accepting `true` would let a malformed
    # observer report satisfy the positive-frame requirement.
    if type(frames) is not int or frames <= 0:
        failures.append("observer did not record any fixture frames")
    position = data.get("npcFixturePosition")
    if not isinstance(position, dict):
        failures.append("observer report has no fixture position")
    elif position.get("map") != expected_map:
        failures.append(
            f"expected map {expected_map}, observer reported {position.get('map')!r}"
        )
    input_blocked = data.get("npcFixtureInputBlocked")
    if type(input_blocked) is not bool:
        failures.append("observer did not report input state")
    elif input_blocked:
        failures.append("observer reported blocked game input")
    if "GFL_DebugAssertFail" in log_text:
        failures.append("emulator log contains GFL_DebugAssertFail")
    if not timed_out and returncode not in (0, None):
        failures.append(f"emulator exited unexpectedly with code {returncode}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, type=Path, help="melonDS executable")
    parser.add_argument("--rom", required=True, type=Path, help="ROM with a matching disposable save sidecar")
    parser.add_argument("--script", required=True, type=Path, help="JSON input script for the private runtime fixture")
    parser.add_argument("--prefix", required=True, type=Path, help="Fresh output-file prefix")
    parser.add_argument("--expect-map", required=True, type=int, help="Map ID the scripted input must reach")
    parser.add_argument("--seconds", type=float, default=70, help="Maximum run time")
    args = parser.parse_args()

    runtime = args.runtime.resolve(strict=True)
    rom = args.rom.resolve(strict=True)
    script = args.script.resolve(strict=True)
    prefix = args.prefix.resolve()
    if not runtime.is_file() or not rom.is_file() or not script.is_file():
        parser.error("runtime, ROM, and script must be files")
    if args.seconds <= 0:
        parser.error("--seconds must be positive")

    outputs = [Path(f"{prefix}{suffix}") for suffix in (
        ".npc.json", ".npc.ramdump", ".stdout", ".stderr",
    )]
    outputs.extend(Path(f"{prefix}.npc-screen-{screen}.png") for screen in range(2))
    existing = [str(path) for path in outputs if path.exists()]
    if existing:
        parser.error("refusing to overwrite existing probe outputs: " + ", ".join(existing))
    prefix.parent.mkdir(parents=True, exist_ok=True)

    env = {key: value for key, value in os.environ.items() if not key.startswith("POKEPLAY_")}
    env.update(
        POKEPLAY_COOP_PREPARATION_CHECK="1",
        POKEPLAY_NPC_STORY_CHECK="1",
        POKEPLAY_COOP_BATTLE_SCRIPT=str(script),
        POKEPLAY_COOP_PREPARATION_REPORT=str(prefix),
        POKEPLAY_COOP_BOOT_CAPTURE="1",
    )

    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        creationflags = subprocess.CREATE_NO_WINDOW

    report_path = Path(f"{prefix}.npc.json")
    timed_out = False
    process = None
    with Path(f"{prefix}.stdout").open("w", encoding="utf-8") as stdout, Path(
        f"{prefix}.stderr"
    ).open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(
            [str(runtime), str(rom)],
            cwd=runtime.parent,
            env=env,
            stdout=stdout,
            stderr=stderr,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        deadline = time.monotonic() + args.seconds
        try:
            while time.monotonic() < deadline and process.poll() is None:
                time.sleep(0.2)
            timed_out = process.poll() is None
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    data: dict[str, object] | None = None
    if report_path.exists():
        try:
            parsed = json.loads(report_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                data = parsed
        except (OSError, json.JSONDecodeError):
            pass
    position = data.get("npcFixturePosition", {}) if data is not None else {}
    if not isinstance(position, dict):
        position = {}
    report_data = data or {}
    log_text = "\n".join(
        Path(f"{prefix}.{suffix}").read_text(encoding="utf-8", errors="replace")
        for suffix in ("stdout", "stderr")
    )
    failures = check_report(
        data, args.expect_map, log_text, timed_out, process.returncode if process else None
    )
    result = {
        "pid": process.pid if process else None,
        "returncode": process.returncode if process else None,
        "timedOut": timed_out,
        "frames": report_data.get("npcFixtureFrames"),
        "status": position.get("status"),
        "map": position.get("map"),
        "tileX": position.get("tileX"),
        "tileZ": position.get("tileZ"),
        "facing": position.get("facing"),
        "moving": position.get("moving"),
        "inBattle": position.get("inBattle"),
        "inputBlocked": report_data.get("npcFixtureInputBlocked"),
        "screens": [
            str(Path(f"{prefix}.npc-screen-{screen}.png"))
            for screen in range(2)
            if Path(f"{prefix}.npc-screen-{screen}.png").exists()
        ],
        "report": str(report_path) if report_path.exists() else None,
        "stdout": str(Path(f"{prefix}.stdout")),
        "stderr": str(Path(f"{prefix}.stderr")),
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
