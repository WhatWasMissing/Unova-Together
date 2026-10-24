"""Safety tests for temporary emulator-agent sessions."""

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import emulator_agent
from emulator_agent import (AgentError, MARKER_NAME, SESSION_NAME, _emulator_environment,
    _launch, _prepare_private_emulator, _process_matches, _safe_remove_session, _validate_session_file)


class EmulatorAgentSessionTests(unittest.TestCase):
    def test_failed_start_keeps_diagnostic_when_cleanup_cannot_confirm_exit(self):
        import argparse
        import shutil
        root = Path(tempfile.mkdtemp(prefix='unova-agent-exit-diagnostic-'))
        try:
            source = root / 'melonDS.exe'
            source.write_bytes(b'fixture; never executed')
            rom = root / 'test.nds'
            rom.write_bytes(b'fixture')
            session_root = root / 'session'
            session_root.mkdir()
            process = mock.Mock(pid=12345)
            process.poll.return_value = 1
            def failed_process(*args, **kwargs):
                kwargs['stdout'].write(b'original native failure diagnostic\n')
                kwargs['stdout'].flush()
                return process
            with mock.patch.object(emulator_agent.tempfile, 'mkdtemp', return_value=str(session_root)), \
                 mock.patch.object(emulator_agent.subprocess, 'Popen', side_effect=failed_process), \
                 mock.patch.object(emulator_agent, '_safe_remove_session', side_effect=PermissionError('identity uncertain')):
                with self.assertRaisesRegex(AgentError, 'Emulator exited before its control endpoint became ready') as caught:
                    _launch(argparse.Namespace(emulator=str(source), rom=str(rom), save=None, boot='auto'))
            self.assertIn('Session retained at', str(caught.exception))
            self.assertIn('identity uncertain', str(caught.exception))
            self.assertIn('original native failure diagnostic', str(caught.exception))
            self.assertTrue((session_root / SESSION_NAME).is_file())
        finally:
            shutil.rmtree(root)

    def test_private_config_promotes_only_missing_instance_parents(self):
        import shutil
        import tomllib
        root = Path(tempfile.mkdtemp(prefix='unova-agent-parent-tables-'))
        try:
            install = root / 'installed'
            install.mkdir()
            source = install / 'melonDS.exe'
            source.write_bytes(b'fixture; never executed')
            text = ('[Instance0.Keyboard]\nA = 1\n[Instance0.Joystick]\nA = 2\n'
                    '[Instance1] # explicit\nVolume = 100\n[Instance1.Keyboard]\nB = 3\n')
            config = install / 'melonDS.toml'
            config.write_text(text, encoding='utf-8')
            private = _prepare_private_emulator(root, source)
            copied = (private.parent / 'portable/melonDS.toml').read_text(encoding='utf-8')
            self.assertIn('[Instance0]\n', copied)
            self.assertEqual(copied.count('[Instance0]'), 1)
            self.assertEqual(copied.count('[Instance1]'), 1)
            self.assertEqual(tomllib.loads(copied), tomllib.loads(text))
            self.assertEqual(config.read_text(encoding='utf-8'), text)
        finally:
            shutil.rmtree(root)

    def make_session(self, pid: int, executable: str) -> tuple[Path, Path]:
        root = Path(tempfile.mkdtemp(prefix="unova-agent-test-"))
        marker = "test-marker"
        (root / MARKER_NAME).write_text(marker + "\n", encoding="ascii")
        endpoint = root / "endpoint.json"
        session = {
            "schema": 1,
            "root": str(root),
            "marker": marker,
            "pid": pid,
            "emulator": executable,
            "token": "a" * 64,
            "endpoint_file": str(endpoint),
            "session_file": str(root / SESSION_NAME),
        }
        (root / SESSION_NAME).write_text(json.dumps(session), encoding="utf-8")
        return root, root / SESSION_NAME

    def test_valid_marked_session_is_accepted(self) -> None:
        root, session_file = self.make_session(2147483647, sys.executable)
        try:
            data, checked_root = _validate_session_file(session_file)
            self.assertEqual(data["marker"], "test-marker")
            self.assertEqual(checked_root, root.resolve())
        finally:
            if root.exists():
                import shutil
                shutil.rmtree(root)

    def test_marker_mismatch_is_refused(self) -> None:
        root, session_file = self.make_session(2147483647, sys.executable)
        try:
            (root / MARKER_NAME).write_text("different\n", encoding="ascii")
            with self.assertRaises(AgentError):
                _validate_session_file(session_file)
        finally:
            import shutil
            shutil.rmtree(root)

    def test_cleanup_refuses_the_running_python_process(self) -> None:
        root, session_file = self.make_session(os.getpid(), sys.executable)
        try:
            self.assertIs(_process_matches(json.loads(session_file.read_text(encoding="utf-8"))), True)
            with self.assertRaises(AgentError):
                _safe_remove_session(session_file)
            self.assertTrue(root.exists())
        finally:
            import shutil
            shutil.rmtree(root)

    def test_missing_process_is_confirmed_stopped(self) -> None:
        root, session_file = self.make_session(2147483647, sys.executable)
        try:
            session = json.loads(session_file.read_text(encoding="utf-8"))
            self.assertIs(_process_matches(session), False)
            _safe_remove_session(session_file)
            self.assertFalse(root.exists())
        finally:
            if root.exists():
                import shutil
                shutil.rmtree(root)

    def test_private_emulator_copies_active_portable_config(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="unova-agent-private-build-"))
        try:
            install = root / "installed"
            install.mkdir()
            source = install / "melonDS.exe"
            source.write_bytes(b"emulator binary")
            (install / "melonDS.toml").write_text("[Instance0]\nsource = true\n", encoding="utf-8")
            portable = install / "portable"
            portable.mkdir()
            active_config = portable / "melonDS.toml"
            active_config.write_text("[Instance0]\nportable = true\n", encoding="utf-8")

            private = _prepare_private_emulator(root, source)

            self.assertEqual(private.read_bytes(), source.read_bytes())
            self.assertNotEqual(private, source)
            private_config = private.parent / "portable" / "melonDS.toml"
            self.assertEqual(private_config.read_text(encoding="utf-8"), active_config.read_text(encoding="utf-8"))
            self.assertEqual(source.read_bytes(), b"emulator binary")
            self.assertEqual(active_config.read_text(encoding="utf-8"), "[Instance0]\nportable = true\n")
        finally:
            import shutil
            shutil.rmtree(root)

    def test_private_profile_fallback_is_a_valid_explicit_instance_table(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="unova-agent-private-build-"))
        try:
            source = root / "melonDS.exe"
            source.write_bytes(b"emulator binary")
            private = _prepare_private_emulator(root, source)
            config = private.parent / "portable" / "melonDS.toml"
            self.assertEqual(config.read_text(encoding="utf-8"), "[Instance0]\n")
        finally:
            import shutil
            shutil.rmtree(root)

    def test_private_emulator_keeps_runtime_dll_and_qt_plugin_search_paths(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="unova-agent-private-build-"))
        try:
            install = root / "installed"
            (install / "platforms").mkdir(parents=True)
            source = install / "melonDS.exe"
            source.write_bytes(b"emulator binary")
            previous_path = os.environ.get("PATH", "")
            environment = _emulator_environment(source, root, root / "endpoint.json", "a" * 64)
            if os.name == "nt":
                self.assertEqual(environment["PATH"].split(os.pathsep, 1)[0], str(install))
            self.assertEqual(environment["QT_PLUGIN_PATH"], str(install))
            self.assertEqual(environment["QT_QPA_PLATFORM_PLUGIN_PATH"], str(install / "platforms"))
            self.assertIn(previous_path, environment.get("PATH", ""))
        finally:
            import shutil
            shutil.rmtree(root)

    def test_failed_save_copy_removes_partial_session_and_rom_link(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="unova-agent-launch-failure-"))
        session_root = root / "session"
        emulator = root / "melonDS.exe"
        rom = root / "test.nds"
        save = root / "test.sav"
        emulator.write_bytes(b"emulator")
        rom.write_bytes(b"rom")
        save.write_bytes(b"save")

        def create_private_tempdir(prefix: str) -> str:
            session_root.mkdir()
            return str(session_root)

        try:
            args = type("Args", (), {"emulator": str(emulator), "rom": str(rom), "save": str(save)})()
            with mock.patch.object(emulator_agent.tempfile, "mkdtemp", side_effect=create_private_tempdir):
                with mock.patch.object(emulator_agent.shutil, "copy2", side_effect=PermissionError("test failure")):
                    with self.assertRaisesRegex(AgentError, "isolated save copy"):
                        _launch(args)
            self.assertFalse(session_root.exists())
            self.assertTrue(rom.is_file())
            self.assertTrue(save.is_file())
        finally:
            import shutil
            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
