"""Ensure the local presence relay matches this installed game's Teleport support."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import uuid

from launcher_ui import versioning
from launcher_ui.relay_process import RelayProcessError, stop_owned_listener

MAX_WELCOME = 8192


def relay_state(port: int, expected_build: str) -> str:
    """Return ``ready``, ``stale`` or ``absent`` for a local relay listener."""
    request = {'type': 'join', 'version': 1, 'name': 'teleport-readiness',
               'room': 'teleport-check-' + uuid.uuid4().hex[:12]}
    try:
        connection = socket.create_connection(('127.0.0.1', port), timeout=0.75)
    except OSError:
        return 'absent'
    with connection:
        connection.settimeout(0.75)
        try:
            connection.sendall((json.dumps(request, separators=(',', ':')) + '\n').encode())
            response = bytearray()
            while len(response) <= MAX_WELCOME and b'\n' not in response:
                chunk = connection.recv(min(1024, MAX_WELCOME + 1 - len(response)))
                if not chunk:
                    break
                response.extend(chunk)
            if len(response) > MAX_WELCOME:
                return 'stale'
            message = json.loads(bytes(response).split(b'\n', 1)[0])
        except (OSError, UnicodeError, json.JSONDecodeError, TimeoutError):
            return 'stale'
    if (isinstance(message, dict) and message.get('type') == 'welcome' and
            message.get('version') == 1 and isinstance(message.get('id'), str) and
            message['id'] and message.get('buildVersion') == expected_build and
            message.get('fieldZonePresence') is True):
        return 'ready'
    return 'stale'


def expected_build(root: Path) -> str:
    metadata = versioning.read_info(Path(root) / 'tools' / 'launcher_ui' / 'build-info.json')
    return metadata['version']


def relay_command(root: Path, port: int) -> list[str]:
    """Prefer the packaged launcher so the relay has a stable, owned identity."""
    for name in ('Pokemon Together.exe', 'Unova Together.exe'):
        executable = root / 'launcher' / name
        if executable.is_file():
            return [str(executable), '--presence-relay', str(port)]
    script = root / 'tools' / 'presence_server.py'
    if not script.is_file():
        raise RuntimeError('The installed presence relay is missing. Repair game files, then try again.')
    return [sys.executable, str(script), '--host', '0.0.0.0', '--port', str(port)]


def _wait_for_relay(port: int, build: str, process: subprocess.Popen, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if relay_state(port, build) == 'ready':
            return True
        if process.poll() is not None:
            return False
        time.sleep(0.1)
    return False


def ensure_local_relay(port: int, root: str | Path | None = None, *, timeout: float = 8.0) -> str:
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('Invalid relay port')
    install_root = Path(root or Path(__file__).resolve().parents[1]).resolve(strict=True)
    build = expected_build(install_root)
    state = relay_state(port, build)
    if state == 'ready':
        return 'ready'
    if state == 'stale':
        try:
            stopped = stop_owned_listener(install_root, port)
        except RelayProcessError as exc:
            raise RuntimeError(str(exc) + ' Stop the old relay on this computer, then reconnect.') from exc
        if not stopped and relay_state(port, build) == 'stale':
            raise RuntimeError('An outdated relay is using this port, but it was not started by this installation. Stop it on this computer, then reconnect.')
        deadline = time.monotonic() + min(timeout, 4.0)
        while relay_state(port, build) == 'stale' and time.monotonic() < deadline:
            time.sleep(0.1)
        if relay_state(port, build) == 'stale':
            raise RuntimeError('The outdated relay could not be stopped. Check the port and try again.')
        if relay_state(port, build) == 'ready':
            return 'ready'

    logs = install_root / 'transfer'
    logs.mkdir(exist_ok=True)
    log_path = logs / 'presence-relay.log'
    command = relay_command(install_root, port)
    with log_path.open('ab') as output:
        try:
            process = subprocess.Popen(command, cwd=install_root, stdout=output, stderr=output,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except OSError as exc:
            raise RuntimeError('The local presence relay could not start. Check transfer/presence-relay.log.') from exc
    if _wait_for_relay(port, build, process, timeout):
        return 'started'
    if process.poll() is None:
        # Keep a failed process from lingering and shadowing the next attempt.
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
    raise RuntimeError('The current presence relay did not become ready. Check transfer/presence-relay.log and try again.')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    port = parser.parse_args().port
    try:
        ensure_local_relay(port)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
