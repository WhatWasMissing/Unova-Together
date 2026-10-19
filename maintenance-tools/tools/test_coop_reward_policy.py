"""Compile and run the production co-op reward policy and ROM-signature guard."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path,
                        help="melonDS source directory containing CMakeLists.txt and src/")
    parser.add_argument("--compiler", default="g++", help="C++17 compiler executable")
    parser.add_argument("--test-source", type=Path,
                        default=Path(__file__).with_name("test_coop_reward_policy.cpp"))
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    include_dir = source_root / "src/frontend/qt_sdl"
    required = (source_root / "CMakeLists.txt",
                include_dir / "CoopExperienceGuard.h",
                include_dir / "CoopRewardPolicy.h",
                args.test_source.resolve())
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        parser.error("Source root or test source is missing required files: " + ", ".join(missing))

    with tempfile.TemporaryDirectory(prefix="unova-coop-reward-test-") as temp:
        executable = Path(temp) / "coop-reward-policy-test.exe"
        compile_command = [args.compiler, "-std=c++17", "-UNDEBUG",
                           "-I", str(include_dir), str(args.test_source.resolve()),
                           "-o", str(executable)]
        subprocess.run(compile_command, check=True)
        result = subprocess.run([str(executable)], check=True, text=True,
                                capture_output=True)
        print(result.stdout.strip())


if __name__ == "__main__":
    main()
