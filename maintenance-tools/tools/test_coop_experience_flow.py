"""Structurally check the co-op EXP reward hook in a supplied melonDS source tree.

This checks call-site wiring only; it does not run a ROM, emulator, or two-client
session. See docs/DEVELOPER_TESTING.md for the source provenance and reproduction.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def check_source(source_root: Path) -> None:
    source_root = source_root.resolve()
    runtime_path = source_root / "src/frontend/qt_sdl/NativeCoopRuntime.cpp"
    policy_path = source_root / "src/frontend/qt_sdl/CoopRewardPolicy.h"
    guard_path = source_root / "src/frontend/qt_sdl/CoopExperienceGuard.h"
    required = (source_root / "CMakeLists.txt", runtime_path, policy_path, guard_path)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError("Source root is missing required melonDS files: " + ", ".join(missing))

    runtime = runtime_path.read_text(encoding="utf-8")
    policy = policy_path.read_text(encoding="utf-8")
    guard = guard_path.read_text(encoding="utf-8")
    checks = {
        "launcher-controlled suppression environment":
            'qEnvironmentVariableIntValue("UNOVA_COOP_EXP_SUPPRESSION")==1' in runtime,
        "production call site uses suppression policy and reward guard":
            "CoopExperienceGuard::suppress" in runtime
            and "CoopRewardPolicy::suppressionActive" in runtime,
        "suppression is limited to opted-in manual co-op tests":
            "suppressionEnabled && manualTest && !playerBattle" in policy,
        "only XP fields are cleared from six reward records":
            "std::memset(rewards+i*12,0,4)" in guard,
        "runtime exposes whether native EXP remains allowed":
            '"nativeCoopExperienceAllowed"' in runtime,
        "co-op prompt grace period is retained":
            "peerLossGraceFrames(false)==1800u" in runtime,
    }
    failed = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    if failed:
        raise SystemExit("Co-op EXP source checks failed: " + "; ".join(failed))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path,
                        help="melonDS source directory containing CMakeLists.txt and src/")
    args = parser.parse_args()
    check_source(args.source_root)


if __name__ == "__main__":
    main()
