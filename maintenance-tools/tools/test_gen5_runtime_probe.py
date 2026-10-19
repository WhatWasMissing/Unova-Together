"""Ensure the runtime probe rejects missing or incomplete gameplay evidence."""

# Unova Together contributions: Copyright (C) 2026 mvq1303.
# GitHub: WhatWasMissing - https://github.com/WhatWasMissing/Unova-Together
# GPL-3.0-or-later. See LICENSE.

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
from unittest import mock
import unittest

from PIL import Image


MODULE_PATH = Path(__file__).with_name("run_gen5_runtime_probe.py")
SPEC = importlib.util.spec_from_file_location("run_gen5_runtime_probe", MODULE_PATH)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class RuntimeProbeReportTests(unittest.TestCase):
    def test_marked_fixture_preflight_accepts_isolated_inputs(self):
        with tempfile.TemporaryDirectory(prefix="unova-marked-probe-") as folder:
            root = Path(folder)
            (root / ".disposable-test-output").touch()
            runtime = root / "runtime" / "melonDS.exe"
            runtime.parent.mkdir()
            runtime.write_bytes(b"test executable")
            rom = root / "game.nds"
            rom.write_bytes(b"test ROM")
            rom.with_suffix(".sav").write_bytes(b"test save")
            PROBE.validate_disposable_fixture(runtime, rom, root / "probe")

    def test_fixture_preflight_rejects_runtime_outside_folder(self):
        with tempfile.TemporaryDirectory(prefix="unova-marked-probe-") as folder:
            root = Path(folder)
            fixture = root / "fixture"
            fixture.mkdir()
            (fixture / ".disposable-test-output").touch()
            runtime = root / "melonDS.exe"
            runtime.write_bytes(b"test executable")
            rom = fixture / "game.nds"
            rom.write_bytes(b"test ROM")
            rom.with_suffix(".sav").write_bytes(b"test save")
            with self.assertRaisesRegex(ValueError, "runtime must be inside"):
                PROBE.validate_disposable_fixture(runtime, rom, fixture / "probe")

    def test_fixture_preflight_requires_matching_save_sidecar(self):
        with tempfile.TemporaryDirectory(prefix="unova-marked-probe-") as folder:
            root = Path(folder)
            (root / ".disposable-test-output").touch()
            runtime = root / "melonDS.exe"
            runtime.write_bytes(b"test executable")
            rom = root / "game.nds"
            rom.write_bytes(b"test ROM")
            with self.assertRaisesRegex(ValueError, r"matching \.sav sidecar"):
                PROBE.validate_disposable_fixture(runtime, rom, root / "probe")

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

    def test_captured_gen5_fatal_error_screen_fails_even_with_observer_progress(self):
        with tempfile.TemporaryDirectory(prefix="unova-fatal-screen-") as folder:
            root = Path(folder)
            error_screen = Image.new("RGB", (256, 192), "black")
            for y in (80, 96):
                for x in range(40, 216):
                    error_screen.putpixel((x, y), (251, 251, 251))
            error_screen.save(root / "top.png")
            Image.new("RGB", (256, 192), "black").save(root / "bottom.png")

            details, failures = PROBE.inspect_captured_screens(
                [root / "top.png", root / "bottom.png"]
            )

        self.assertEqual(len(details), 2)
        self.assertTrue(any("fatal error screen" in failure for failure in failures))

    def test_colorful_gameplay_capture_passes_screen_inspection(self):
        with tempfile.TemporaryDirectory(prefix="unova-gameplay-screen-") as folder:
            root = Path(folder)
            screen = Image.new("RGB", (256, 192))
            pixels = screen.load()
            for y in range(192):
                for x in range(256):
                    pixels[x, y] = ((x * 7) % 256, (y * 11) % 256, (x + y) % 256)
            screen.save(root / "top.png")
            screen.save(root / "bottom.png")

            details, failures = PROBE.inspect_captured_screens(
                [root / "top.png", root / "bottom.png"]
            )

        self.assertEqual(len(details), 2)
        self.assertEqual(failures, [])

    def test_missing_or_invalid_screen_cannot_pass(self):
        with tempfile.TemporaryDirectory(prefix="unova-missing-screen-") as folder:
            root = Path(folder)
            Image.new("RGB", (256, 192), "red").save(root / "top.png")
            (root / "bottom.png").write_bytes(b"not an image")

            details, failures = PROBE.inspect_captured_screens(
                [root / "top.png", root / "bottom.png"]
            )

        self.assertEqual(len(details), 1)
        self.assertTrue(any("missing or unreadable" in failure for failure in failures))

    def test_cli_rejects_unmarked_rom_folder_before_launch(self):
        with tempfile.TemporaryDirectory(prefix="unova-unmarked-probe-") as folder:
            root = Path(folder)
            runtime = root / "runtime" / "melonDS.exe"
            runtime.parent.mkdir()
            runtime.write_bytes(b"test executable")
            rom = root / "game.nds"
            rom.write_bytes(b"test ROM")
            rom.with_suffix(".sav").write_bytes(b"test save")
            script = root / "input.json"
            script.write_text("[]", encoding="utf-8")
            argv = [
                "run_gen5_runtime_probe.py",
                "--runtime", str(runtime),
                "--rom", str(rom),
                "--script", str(script),
                "--prefix", str(root / "probe"),
                "--expect-map", "460",
            ]
            with mock.patch("sys.argv", argv), mock.patch.object(PROBE.subprocess, "Popen") as popen:
                popen.side_effect = AssertionError("unmarked runtime was launched")
                with self.assertRaises(SystemExit):
                    PROBE.main()
                popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
