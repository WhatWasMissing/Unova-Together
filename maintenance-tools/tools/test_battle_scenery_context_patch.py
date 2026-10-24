#!/usr/bin/env python3
# Unova Together contributions: Copyright (C) 2026 mvq1303.
# GitHub: WhatWasMissing - https://github.com/WhatWasMissing/Unova-Together
# GPL-3.0-or-later. Preserve all upstream notices.
"""Verify the battle-scenery fix patch and optionally apply it to its source baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

from build_battle_scenery_patch import (
    BASELINE_ARCHIVE,
    BASELINE_SHA256,
    SOURCE_PREFIX,
    normalized_text,
    text_sha256,
)


ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "maintenance-tools/patches/area-battle-scenery-context.patch"
METADATA = ROOT / "maintenance-tools/patches/area-battle-scenery-context.json"
HELPER = ROOT / "maintenance-tools/tools/battle_scenery_context.h"


def metadata() -> dict:
    return json.loads(METADATA.read_text(encoding="utf-8"))


def added_file_text(patch_text: str, source_path: str) -> str:
    header = f"--- /dev/null\n+++ b/source/melonDS/{source_path}\n"
    start = patch_text.find(header)
    if start < 0:
        raise AssertionError(f"Patch does not add {source_path}")
    body_start = patch_text.find("\n", start + len(header)) + 1
    next_file = patch_text.find("\n--- ", body_start)
    body = patch_text[body_start:] if next_file < 0 else patch_text[body_start:next_file]
    return "\n".join(line[1:] for line in body.splitlines() if line.startswith("+")) + "\n"


class BattleSceneryPatchTests(unittest.TestCase):
    def test_patch_digest_and_exact_scope_match_metadata(self):
        data = metadata()
        self.assertEqual(data["baselineArchive"], BASELINE_ARCHIVE)
        self.assertEqual(data["baselineArchiveSha256"], BASELINE_SHA256)
        self.assertEqual(
            hashlib.sha256(PATCH.read_bytes()).hexdigest(), data["patchSha256"]
        )
        self.assertEqual(
            set(data["resultFiles"]),
            {
                "src/frontend/qt_sdl/OverworldDebug.cpp",
                "src/frontend/qt_sdl/AreaBattleScenes.h",
                "src/frontend/qt_sdl/BattleSceneryContext.h",
                "src/frontend/qt_sdl/ProjectCredits.h",
                "res/melon.rc.in",
            },
        )

    def test_added_native_helper_is_the_tested_helper(self):
        patch_text = PATCH.read_text(encoding="utf-8")
        added = added_file_text(
            patch_text, "src/frontend/qt_sdl/BattleSceneryContext.h"
        )
        expected = normalized_text(HELPER.read_bytes())
        self.assertEqual(added, expected)
        self.assertIn("battleStateKnown && retainedFieldContext", added)
        self.assertIn("verifiedFieldSample ||", added)

    def test_tracker_and_renderer_pass_fail_closed_context(self):
        patch_text = PATCH.read_text(encoding="utf-8")
        self.assertIn('lastResolved.value("fieldZone",-1)', patch_text)
        self.assertIn('result["areaFieldContext"]=true;', patch_text)
        self.assertIn('sample.value("battleStateKnown").toBool()', patch_text)
        self.assertIn('cart->SetAssetPatches({});currentArea=-1;currentSelection.clear();', patch_text)
        self.assertNotIn('result["fieldPositionOwned"]=true;', patch_text)

    def test_patch_is_accepted_by_git_apply_parser(self):
        result = subprocess.run(
            ["git", "apply", "--numstat", "--", str(PATCH)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_patch_applies_to_the_verified_baseline_when_supplied(self):
        archive_path = os.environ.get("UNOVA_BATTLE_SCENERY_BASELINE_SOURCE_ZIP")
        if not archive_path:
            self.skipTest("Set UNOVA_BATTLE_SCENERY_BASELINE_SOURCE_ZIP to the verified 2.0.34 source ZIP")
        archive_path = Path(archive_path)
        data = metadata()
        self.assertEqual(hashlib.sha256(archive_path.read_bytes()).hexdigest(), BASELINE_SHA256)
        with tempfile.TemporaryDirectory(prefix="unova-battle-scenery-source-") as temporary:
            root = Path(temporary)
            with zipfile.ZipFile(archive_path) as archive:
                for relative, expected_hash in data["baselineFiles"].items():
                    raw = archive.read(SOURCE_PREFIX + relative)
                    text = normalized_text(raw)
                    self.assertEqual(text_sha256(text), expected_hash, relative)
                    target = root / "source/melonDS" / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(text, encoding="utf-8", newline="\n")
            result = subprocess.run(
                ["git", "apply", "--check", str(PATCH)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            applied = subprocess.run(
                ["git", "apply", str(PATCH)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            for relative, expected_hash in data["resultFiles"].items():
                result_text = normalized_text((root / "source/melonDS" / relative).read_bytes())
                self.assertEqual(text_sha256(result_text), expected_hash, relative)


if __name__ == "__main__":
    unittest.main()
