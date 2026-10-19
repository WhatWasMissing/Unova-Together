#!/usr/bin/env python3
# Unova Together contributions: Copyright (C) 2026 mvq1303.
# GitHub: WhatWasMissing - https://github.com/WhatWasMissing/Unova-Together
# GPL-3.0-or-later. Preserve all upstream notices.
"""Guard the shipped emulator patch for Cynthia's Practice battle catalog."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "maintenance-tools" / "patches" / "development-polish.patch"
METADATA = ROOT / "maintenance-tools" / "patches" / "development-polish.json"
SOURCE_PATH = "source/melonDS/src/frontend/qt_sdl/Gen5Menu.cpp"


def gen5_menu_delta(patch_text: str) -> str:
    start = patch_text.find(f"--- a/{SOURCE_PATH}\n")
    if start < 0:
        return ""
    end = patch_text.find("\n--- a/", start + 1)
    if end < 0:
        end = len(patch_text)
    return patch_text[start:end]


def has_cynthia_practice_fix(delta: str) -> bool:
    return (
        '-        const QSet<QString> majorNames={"Rival","Hugh","Cheren","Roxie","Burgh","Elesa",\n'
        '+        const QSet<QString> majorNames={"Rival","Hugh","Cheren","Roxie","Burgh","Elesa","Cynthia",\n'
        in delta
        and "-        const auto trainerLimit=qMin(qMin(entryCount(trainers),entryCount(parties)),891u);\n"
        "+        const auto trainerLimit=qMin(qMin(entryCount(trainers),entryCount(parties)),892u);\n"
        in delta
    )


class CynthiaPracticeCatalogPatchTests(unittest.TestCase):
    def test_patch_exposes_appended_cynthia_record_to_battle_catalog(self):
        patch_text = PATCH.read_text(encoding="utf-8")
        self.assertTrue(has_cynthia_practice_fix(gen5_menu_delta(patch_text)))

    def test_patch_metadata_hash_matches_distributed_patch(self):
        metadata = json.loads(METADATA.read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(PATCH.read_bytes()).hexdigest(), metadata["patchSha256"]
        )

    def test_regression_guard_rejects_missing_allowlist_or_boundary_change(self):
        delta = gen5_menu_delta(PATCH.read_text(encoding="utf-8"))
        self.assertFalse(has_cynthia_practice_fix(delta.replace('"Cynthia"', '"Cynthia_removed"')))
        self.assertFalse(has_cynthia_practice_fix(delta.replace("892u", "891u")))


if __name__ == "__main__":
    unittest.main()
