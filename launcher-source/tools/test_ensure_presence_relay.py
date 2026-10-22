"""Regression coverage for relay capability checks and stale local relay replacement."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
import warnings
from unittest.mock import Mock, patch

import ensure_presence_relay as relay


class RelayReadinessTests(unittest.TestCase):
    class Connection:
        def __init__(self, welcome):
            self.welcome = welcome

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def settimeout(self, _timeout):
            pass

        def sendall(self, data):
            self.request = json.loads(data)

        def recv(self, _size):
            return (json.dumps(self.welcome) + '\n').encode()

    def test_relay_must_match_build_and_teleport_capability(self):
        expected = {'type': 'welcome', 'version': 1, 'id': 'peer-1',
                    'buildVersion': '2.0.25', 'fieldZonePresence': True}
        cases = (
            (expected, 'ready'),
            ({**expected, 'buildVersion': '2.0.19'}, 'stale'),
            ({**expected, 'fieldZonePresence': False}, 'stale'),
            ({key: value for key, value in expected.items() if key != 'fieldZonePresence'}, 'stale'),
        )
        for welcome, state in cases:
            with self.subTest(welcome=welcome), patch.object(
                    relay.socket, 'create_connection', return_value=self.Connection(welcome)):
                self.assertEqual(relay.relay_state(8765, '2.0.25'), state)

    def test_launcher_command_gives_relay_a_managed_executable_identity(self):
        with tempfile.TemporaryDirectory(prefix='unova-relay-command-') as directory:
            root = Path(directory)
            executable = root / 'launcher' / 'Pokemon Together.exe'
            executable.parent.mkdir()
            executable.touch()
            self.assertEqual(relay.relay_command(root, 9876),
                             [str(executable), '--presence-relay', '9876'])

    def test_compatible_relay_is_reused_without_restarting(self):
        with tempfile.TemporaryDirectory(prefix='unova-relay-reuse-') as directory:
            root = Path(directory)
            with patch.object(relay, 'expected_build', return_value='2.0.25'), \
                    patch.object(relay, 'relay_state', return_value='ready'), \
                    patch.object(relay, 'stop_owned_listener') as stop, \
                    patch.object(relay.subprocess, 'Popen') as spawn:
                self.assertEqual(relay.ensure_local_relay(8765, root), 'ready')
            stop.assert_not_called()
            spawn.assert_not_called()

    def test_stale_relay_is_stopped_before_current_relay_starts(self):
        with tempfile.TemporaryDirectory(prefix='unova-relay-replace-') as directory:
            root = Path(directory)
            process = Mock()
            process.poll.return_value = None
            with patch.object(relay, 'expected_build', return_value='2.0.25'), \
                    patch.object(relay, 'relay_state', side_effect=('stale', 'absent', 'absent', 'absent')), \
                    patch.object(relay, 'stop_owned_listener', return_value=True) as stop, \
                    patch.object(relay, 'relay_command', return_value=['current-relay']), \
                    patch.object(relay, '_wait_for_relay', return_value=True), \
                    patch.object(relay.subprocess, 'Popen', return_value=process) as spawn:
                self.assertEqual(relay.ensure_local_relay(8765, root), 'started')
            stop.assert_called_once_with(root.resolve(), 8765)
            spawn.assert_called_once()
            self.assertEqual(spawn.call_args.args[0], ['current-relay'])

    def test_stale_unowned_relay_is_left_running_and_not_shadowed(self):
        with tempfile.TemporaryDirectory(prefix='unova-relay-unowned-') as directory:
            root = Path(directory)
            with patch.object(relay, 'expected_build', return_value='2.0.25'), \
                    patch.object(relay, 'relay_state', side_effect=('stale', 'stale')), \
                    patch.object(relay, 'stop_owned_listener', return_value=False), \
                    patch.object(relay.subprocess, 'Popen') as spawn:
                with self.assertRaisesRegex(RuntimeError, 'not started by this installation'):
                    relay.ensure_local_relay(8765, root)
            spawn.assert_not_called()


@unittest.skipUnless(os.name == 'nt' and shutil.which('powershell.exe'),
                     'Windows process-lifecycle check requires PowerShell and Get-CimInstance')
class WindowsRelayLifecycleTests(unittest.TestCase):
    def test_legacy_python_relay_is_replaced_with_the_installed_build(self):
        source_tools = Path(__file__).resolve().parent
        package_root = source_tools / 'test-fixtures'
        package_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.teleport-relay-lifecycle-', dir=package_root) as directory:
            root = Path(directory)
            tools = root / 'tools'
            ui = tools / 'launcher_ui'
            ui.mkdir(parents=True)
            for name in ('presence_server.py', 'item_trading_relay.py',
                         'pokemon_trading_relay.py', 'coop_social.py'):
                shutil.copy2(source_tools / name, tools / name)
            (ui / '__init__.py').write_text('', encoding='utf-8')
            shutil.copy2(source_tools / 'launcher_ui' / 'versioning.py', ui / 'versioning.py')
            info = {'schema': 1, 'product': 'pokemon-together', 'version': '2.0.19'}
            info_path = ui / 'build-info.json'
            info_path.write_text(json.dumps(info), encoding='utf-8')

            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                port = listener.getsockname()[1]
            old_process = subprocess.Popen(
                [sys.executable, str(tools / 'presence_server.py'), '--host', '0.0.0.0',
                 '--port', str(port)], cwd=root, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            try:
                deadline = relay.time.monotonic() + 8
                while relay.relay_state(port, '2.0.19') != 'ready' and relay.time.monotonic() < deadline:
                    if old_process.poll() is not None:
                        self.fail('The legacy relay exited before its handshake was ready.')
                    relay.time.sleep(0.1)
                self.assertEqual(relay.relay_state(port, '2.0.19'), 'ready')

                info['version'] = relay.versioning.current_version()
                info_path.write_text(json.dumps(info), encoding='utf-8')
                # A ready relay is intentionally detached and outlives this
                # helper process; Python otherwise warns when its Popen wrapper
                # is collected while the service is still running.
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', ResourceWarning)
                    self.assertEqual(relay.ensure_local_relay(port, root, timeout=8), 'started')
                self.assertEqual(relay.relay_state(port, info['version']), 'ready')
                old_process.wait(timeout=3)
            finally:
                try:
                    relay.stop_owned_listener(root, port)
                finally:
                    if old_process.poll() is None:
                        old_process.terminate()
                        try:
                            old_process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            old_process.kill()


if __name__ == '__main__':
    unittest.main()
