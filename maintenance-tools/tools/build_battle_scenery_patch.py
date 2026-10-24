#!/usr/bin/env python3
# Unova Together contributions: Copyright (C) 2026 mvq1303.
# GitHub: WhatWasMissing - https://github.com/WhatWasMissing/Unova-Together
# GPL-3.0-or-later. Preserve all upstream notices.
"""Build the reproducible 2.0.36 native battle-scenery source patch."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PREFIX = "Unova-Together-Source/source/melonDS/"
BASELINE_ARCHIVE = "Unova-Together-2.0.34-Source.zip"
BASELINE_SHA256 = "de592d351d8e2ea24f8b79769bf4d7ebdb6445e1ebc23183c95c0421902ac0bb"
SOURCE_FILES = (
    "src/frontend/qt_sdl/OverworldDebug.cpp",
    "src/frontend/qt_sdl/AreaBattleScenes.h",
    "src/frontend/qt_sdl/BattleSceneryContext.h",
    "src/frontend/qt_sdl/ProjectCredits.h",
    "res/melon.rc.in",
)


def normalized_text(data: bytes) -> str:
    return data.decode("utf-8-sig").replace("\r\n", "\n")


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def unified_diff_lines(before: str, after: str, fromfile: str, tofile: str) -> list[str]:
    """Emit Git-compatible unified diffs, including files absent at baseline."""
    lines = difflib.unified_diff(
        before.splitlines(True), after.splitlines(True), fromfile=fromfile, tofile=tofile
    )
    records = []
    for index, line in enumerate(lines):
        if line.endswith(("\n", "\r")):
            records.append(line)
        elif index >= 3 and line[:1] in (" ", "+", "-"):
            records.extend((line + "\n", "\\ No newline at end of file\n"))
        else:
            records.append(line + "\n")
    return records


def build_patch(baseline_archive: Path, source_root: Path, output_root: Path) -> dict:
    if hashlib.sha256(baseline_archive.read_bytes()).hexdigest() != BASELINE_SHA256:
        raise ValueError(f"Baseline archive is not the verified 2.0.34 source: {baseline_archive}")
    patch_lines: list[str] = []
    baseline_hashes = {}
    result_hashes = {}
    with zipfile.ZipFile(baseline_archive) as archive:
        names = set(archive.namelist())
        for relative in SOURCE_FILES:
            member = SOURCE_PREFIX + relative
            if member not in names and relative != "src/frontend/qt_sdl/BattleSceneryContext.h":
                raise ValueError(f"Verified baseline is missing {member}")
            before = normalized_text(archive.read(member)) if member in names else ""
            after = normalized_text((source_root / relative).read_bytes())
            if before == after:
                raise ValueError(f"Expected a source change for {relative}")
            target = "source/melonDS/" + relative
            patch_lines.extend(
                unified_diff_lines(
                    before,
                    after,
                    "a/" + target if before else "/dev/null",
                    "b/" + target,
                )
            )
            if before:
                baseline_hashes[relative] = text_sha256(before)
            result_hashes[relative] = text_sha256(after)

    patch_path = output_root / "maintenance-tools/patches/area-battle-scenery-context.patch"
    metadata_path = output_root / "maintenance-tools/patches/area-battle-scenery-context.json"
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_bytes = "".join(patch_lines).encode("utf-8")
    patch_path.write_bytes(patch_bytes)
    metadata = {
        "schema": 1,
        "baselineRelease": "Unova Together 2.0.34 native source",
        "baselineArchive": BASELINE_ARCHIVE,
        "baselineArchiveSha256": BASELINE_SHA256,
        "baselineFiles": baseline_hashes,
        "patch": patch_path.name,
        "patchSha256": hashlib.sha256(patch_bytes).hexdigest(),
        "resultFiles": result_hashes,
        "scope": (
            "Carry the last verified field zone and coordinates into a known ordinary battle, "
            "so optional area and nearby scenery can select safely; clear stale patches and "
            "retain native scenery when the battle context is unknown."
        ),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-archive", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    metadata = build_patch(args.baseline_archive, args.source_root, args.output_root)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
