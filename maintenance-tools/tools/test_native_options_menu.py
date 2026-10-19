# Unova Together contributions: Copyright (C) 2026 mvq1303.
# GitHub: WhatWasMissing - https://github.com/WhatWasMissing/Unova-Together
# GPL-3.0-or-later. Preserve all upstream notices.
"""Ensure the native Options entry remains stock and item trades stay in Unova."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "maintenance-tools" / "patches" / "development-polish.patch"
METADATA = ROOT / "maintenance-tools" / "patches" / "development-polish.json"


def source_delta(path: str) -> str:
    escaped = re.escape(path)
    match = re.search(
        rf"(?ms)^--- a/{escaped}\n\+\+\+ b/{escaped}\n(.*?)(?=^--- |\Z)",
        PATCH.read_text(encoding="utf-8"),
    )
    return match.group(1) if match else ""


class NativeOptionsMenuTests(unittest.TestCase):
    def test_options_is_not_repurposed_and_unova_item_trade_remains(self):
        arm = source_delta("source/melonDS/src/ARM.cpp")
        panel = source_delta("source/melonDS/src/frontend/qt_sdl/MultiplayerPanel.cpp")

        self.assertTrue(arm, "development patch must include the ARM.cpp menu hook")
        self.assertIn('-        if(id==6 && marker==0x504b)', arm)
        self.assertIn('-    const char original[]="OPTIONS";const char* label=id==6?"TRADE":"UNOVA";', arm)
        self.assertIn('+    if(id!=4) return false;', arm)
        self.assertIn('+    const char* label="UNOVA";', arm)
        self.assertNotRegex(arm, r'(?m)^\+.*(?:"TRADE"|NativeItemTradeRequested=true)')
        self.assertIn('+            row("trade","Give item"', panel)
        self.assertIn('else if(action=="trade") {refreshItems();menuMode="trade";menuFocus=0;}', panel)

    def test_patch_metadata_matches_source_patch(self):
        metadata = json.loads(METADATA.read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(PATCH.read_bytes()).hexdigest(), metadata["patchSha256"]
        )


if __name__ == "__main__":
    unittest.main()
