"""Ensure the runtime probe rejects missing or incomplete gameplay evidence."""

# Unova Together contributions: Copyright (C) 2026 mvq1303.
# GitHub: WhatWasMissing - https://github.com/WhatWasMissing/Unova-Together
# GPL-3.0-or-later. See LICENSE.

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("run_gen5_runtime_probe.py")
SPEC = importlib.util.spec_from_file_location("run_gen5_runtime_probe", MODULE_PATH)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class RuntimeProbeReportTests(unittest.TestCase):
    def test_missing_report_fails(self):
        failures = PROBE.check_report(None, 460, "", True, 1)
        self.assertTrue(failures)

    def test_wrong_map_fails(self):
        report = {"npcFixtureFrames": 40, "npcFixturePosition": {"map": 458}}
        failures = PROBE.check_report(report, 460, "", True, 1)
        self.assertTrue(any("expected map" in failure for failure in failures))

    def test_boolean_map_id_fails(self):
        report = {
            "npcFixtureFrames": 40,
            "npcFixturePosition": {"map": True},
            "npcFixtureInputBlocked": False,
        }
        failures = PROBE.check_report(report, 1, "", True, 1)
        self.assertTrue(any("map ID" in failure for failure in failures))

    def test_boolean_frame_count_fails(self):
        report = {
            "npcFixtureFrames": True,
            "npcFixturePosition": {"map": 460},
            "npcFixtureInputBlocked": False,
        }
        failures = PROBE.check_report(report, 460, "", True, 1)
        self.assertTrue(any("fixture frames" in failure for failure in failures))

    def test_assertion_log_fails(self):
        report = {"npcFixtureFrames": 40, "npcFixturePosition": {"map": 460}}
        failures = PROBE.check_report(report, 460, "GFL_DebugAssertFail", True, 1)
        self.assertTrue(any("GFL_DebugAssertFail" in failure for failure in failures))

    def test_expected_map_after_probe_timeout_passes(self):
        report = {
            "npcFixtureFrames": 6240,
            "npcFixturePosition": {"map": 460},
            "npcFixtureInputBlocked": False,
        }
        self.assertEqual(PROBE.check_report(report, 460, "", True, 1), [])

    def test_missing_input_state_fails(self):
        report = {"npcFixtureFrames": 6240, "npcFixturePosition": {"map": 460}}
        failures = PROBE.check_report(report, 460, "", True, 1)
        self.assertTrue(any("input state" in failure for failure in failures))

    def test_malformed_input_state_fails(self):
        report = {
            "npcFixtureFrames": 6240,
            "npcFixturePosition": {"map": 460},
            "npcFixtureInputBlocked": 0,
        }
        failures = PROBE.check_report(report, 460, "", True, 1)
        self.assertTrue(any("input state" in failure for failure in failures))

    def test_blocked_input_fails(self):
        report = {
            "npcFixtureFrames": 6240,
            "npcFixturePosition": {"map": 460},
            "npcFixtureInputBlocked": True,
        }
        failures = PROBE.check_report(report, 460, "", True, 1)
        self.assertTrue(any("blocked game input" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
