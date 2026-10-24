"""Start the shipped isolated runner with a fresh, silent private config."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tomllib


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--emulator", required=True)
    parser.add_argument("--rom", required=True)
    parser.add_argument("--save")
    parser.add_argument("--boot", choices=("auto", "always", "never"), default="always")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("unova_isolated_runner", args.runner.resolve(strict=True))
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import the supplied isolated runner")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    original_prepare = runner._prepare_private_emulator
    original_environment = runner._emulator_environment
    original_popen = subprocess.Popen

    def prepare(root: Path, emulator: Path) -> Path:
        executable = original_prepare(root, emulator)
        config = executable.parent / "portable" / "melonDS.toml"
        config.write_text("[Instance0]\n\n[Instance0.Audio]\nVolume = 0\nDSiVolumeSync = false\n", encoding="utf-8")
        parsed = tomllib.loads(config.read_text(encoding="utf-8"))
        if parsed["Instance0"]["Audio"] != {"Volume": 0, "DSiVolumeSync": False}:
            raise RuntimeError("Private audio configuration failed validation")
        return executable

    def popen(*positional, **keywords):
        if os.name == "nt":
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
            keywords["startupinfo"] = startup
        return original_popen(*positional, **keywords)

    def environment(*positional):
        values = original_environment(*positional)
        values["SDL_AUDIODRIVER"] = "dummy"
        return values

    runner._prepare_private_emulator = prepare
    runner._emulator_environment = environment
    runner.subprocess.Popen = popen
    try:
        result = runner._launch(args)
    finally:
        runner.subprocess.Popen = original_popen
    result["privateAudioVolume"] = 0
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
