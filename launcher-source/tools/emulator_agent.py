#!/usr/bin/env python3
"""Launch melonDS in an isolated test profile and control it over localhost JSON."""

# Copyright (C) 2026 mvq1303 / WhatWasMissing. GPL-3.0-or-later.
# Unova Together agent-control runner, developed with Codex assistance.

from __future__ import annotations

import argparse
import base64
import binascii
import ctypes
import json
import os
import re
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any


MARKER_NAME = ".unova-agent-session"
SESSION_NAME = "session.json"
MAX_RESPONSE_BYTES = 16 * 1024 * 1024


class AgentError(RuntimeError):
    pass


def _canonical(path: Path) -> Path:
    return path.expanduser().resolve(strict=True)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    temporary.replace(path)


def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_session_file(session_file: Path) -> tuple[dict[str, Any], Path]:
    session_file = _canonical(session_file)
    data = json.loads(session_file.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise AgentError("Unsupported emulator-agent session file.")
    root = Path(data.get("root", "")).resolve(strict=True)
    temp_root = Path(tempfile.gettempdir()).resolve(strict=True)
    marker = root / MARKER_NAME
    if root == temp_root or not _under(root, temp_root) or root.is_symlink():
        raise AgentError("Refusing to operate outside the temporary test-session directory.")
    if session_file.parent != root or marker.is_symlink() or not marker.is_file():
        raise AgentError("Session path or marker is invalid.")
    if marker.read_text(encoding="utf-8").strip() != data.get("marker"):
        raise AgentError("Session marker does not match; refusing cleanup or control.")
    if not isinstance(data.get("pid"), int) or not isinstance(data.get("token"), str):
        raise AgentError("Session metadata is incomplete.")
    endpoint_file = Path(data.get("endpoint_file", "")).resolve(strict=False)
    if endpoint_file.parent != root:
        raise AgentError("Agent endpoint is outside the session directory.")
    return data, root


def _endpoint(session: dict[str, Any]) -> dict[str, Any]:
    _, root = _validate_session_file(Path(session["session_file"]))
    endpoint_file = root / "endpoint.json"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if endpoint_file.is_file() and not endpoint_file.is_symlink():
            try:
                endpoint = json.loads(endpoint_file.read_text(encoding="utf-8"))
                if (endpoint.get("protocol") == 1 and endpoint.get("host") == "127.0.0.1"
                        and 1 <= int(endpoint.get("port", 0)) <= 65535
                        and endpoint.get("token") == session["token"]):
                    return endpoint
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        time.sleep(0.05)
    raise AgentError("Emulator agent endpoint is unavailable or failed authentication.")


class EmulatorAgent:
    """Synchronous JSON client. Keep one instance open to preserve held buttons."""

    def __init__(self, session_file: Path, timeout: float = 12.0):
        self.session_file = _canonical(session_file)
        self.session, self.root = _validate_session_file(self.session_file)
        self.endpoint = _endpoint({**self.session, "session_file": str(self.session_file)})
        self.timeout = timeout
        self.connection = socket.create_connection(
            (self.endpoint["host"], int(self.endpoint["port"])), timeout=timeout)
        self.connection.settimeout(timeout)
        self.read_buffer = bytearray()

    def close(self) -> None:
        if self.connection:
            try:
                self.connection.sendall(b'{"command":"release","token":"'
                    + self.session["token"].encode("ascii") + b'"}\n')
            except OSError:
                pass
            try:
                self.connection.close()
            except OSError:
                pass
            self.connection = None

    def __enter__(self) -> "EmulatorAgent":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def request(self, command: str, **fields: Any) -> dict[str, Any]:
        if not self.connection:
            raise AgentError("Agent connection is closed.")
        payload = {"command": command, **fields, "token": self.session["token"]}
        self.connection.sendall(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")
        while b"\n" not in self.read_buffer:
            chunk = self.connection.recv(65536)
            if not chunk:
                raise AgentError("Emulator closed the agent connection.")
            self.read_buffer.extend(chunk)
            if len(self.read_buffer) > MAX_RESPONSE_BYTES:
                raise AgentError("Emulator response exceeded the 16 MiB safety limit.")
        line, _, remainder = self.read_buffer.partition(b"\n")
        self.read_buffer = bytearray(remainder)
        try:
            response = json.loads(line)
        except json.JSONDecodeError as error:
            raise AgentError("Emulator returned invalid JSON.") from error
        if not isinstance(response, dict) or not response.get("ok"):
            raise AgentError(str(response.get("error", "Emulator command failed.")))
        return response

    def status(self) -> dict[str, Any]:
        return self.request("status")

    def press_for(self, buttons: list[str], frames: int = 8) -> dict[str, Any]:
        return self.request("press_for", pressed=buttons, frames=frames)

    def wait_frames(self, frames: int) -> dict[str, Any]:
        return self.request("wait_frames", frames=frames)

    def touch(self, x: int, y: int, frames: int = 8) -> dict[str, Any]:
        return self.request("touch", x=x, y=y, frames=frames)

    def set_buttons(self, buttons: list[str]) -> dict[str, Any]:
        return self.request("set_buttons", pressed=buttons)

    def release(self) -> dict[str, Any]:
        return self.request("release")

    def screenshot(self, destination: Path) -> dict[str, Any]:
        response = self.request("screenshot")
        try:
            image = base64.b64decode(response["imageBase64"], validate=True)
        except (KeyError, binascii.Error, ValueError) as error:
            raise AgentError("Emulator screenshot data was not valid base64.") from error
        if not image.startswith(b"\x89PNG\r\n\x1a\n"):
            raise AgentError("Emulator screenshot is not a PNG image.")
        destination = destination.expanduser().absolute()
        if destination.exists():
            raise AgentError(f"Refusing to overwrite screenshot: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".tmp")
        temporary.write_bytes(image)
        temporary.replace(destination)
        response.pop("imageBase64", None)
        response["savedTo"] = str(destination)
        return response


def _process_matches(session: dict[str, Any]) -> bool | None:
    pid = session["pid"]
    if os.name == "nt":
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.QueryFullProcessImageNameW.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel32.QueryFullProcessImageNameW.restype = ctypes.c_int
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            # OpenProcess reports ERROR_INVALID_PARAMETER for a PID that no
            # longer exists. Treat that as a confirmed exit so a timed-out
            # graceful shutdown can still clean its isolated session safely.
            if ctypes.get_last_error() == 87:  # ERROR_INVALID_PARAMETER
                return False
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return False
            except OSError:
                return None
            return None
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            size = ctypes.c_ulong(len(buffer))
            if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return None
            image = Path(buffer.value).resolve(strict=False)
        finally:
            kernel32.CloseHandle(handle)
    elif sys.platform.startswith("linux"):
        process_link = Path(f"/proc/{pid}/exe")
        try:
            image = process_link.resolve(strict=True)
        except FileNotFoundError:
            return False
        except OSError:
            return None
    else:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except OSError:
            return None
        return None  # Cannot prove process identity on this platform.
    expected = Path(session["emulator"]).resolve(strict=False)
    return os.path.normcase(str(image)) == os.path.normcase(str(expected))


def _safe_remove_session(session_file: Path) -> None:
    session, root = _validate_session_file(session_file)
    if _process_matches(session) is not False:
        raise AgentError("The emulator is still running; stop it before removing its test session.")
    shutil.rmtree(root)


def _prepare_private_emulator(root: Path, emulator: Path) -> Path:
    """Give the test instance a private application directory and config."""
    source = _canonical(emulator)
    if not source.is_file():
        raise AgentError("The emulator executable must be an existing file.")

    app_dir = root / "emulator"
    app_dir.mkdir()
    private_executable = app_dir / source.name
    shutil.copy2(source, private_executable)

    portable = app_dir / "portable"
    portable.mkdir()
    source_portable = source.parent / "portable"
    source_config = (source_portable / "melonDS.toml" if source_portable.is_dir()
                     else source.parent / "melonDS.toml")
    private_config = portable / "melonDS.toml"
    if source_config.is_file():
        # Explicit parents let melonDS add scalar defaults before serializing.
        config = source_config.read_text(encoding="utf-8-sig")
        parents = set(re.findall(r"(?m)^\s*\[(Instance\d+)\.[^\]]+\]", config))
        for parent in sorted(parents):
            if not re.search(r"(?m)^\s*\[" + re.escape(parent) + r"\]\s*(?:#.*)?$", config):
                config = re.sub(r"(?m)^(\s*\[" + re.escape(parent) + r"\.)",
                                lambda match: f"[{parent}]\n" + match.group(1), config, count=1)
        private_config.write_text(config, encoding="utf-8")
    else:
        # An explicit table lets a first-run session persist its normal
        # defaults without depending on an implicit table from a TOML child.
        private_config.write_text("[Instance0]\n", encoding="utf-8")
    return private_executable


def _emulator_environment(source: Path, root: Path, endpoint_file: Path, token: str) -> dict[str, str]:
    """Keep DLL and Qt plugin resolution pointed at the trusted install."""
    environment = os.environ.copy()
    environment.update({
        "APPDATA": str(root / "profile" / "Roaming"),
        "LOCALAPPDATA": str(root / "profile" / "Local"),
        "USERPROFILE": str(root / "profile"),
        "UNOVA_AGENT_CONTROL": "1",
        "UNOVA_AGENT_WORKSPACE": str(root),
        "UNOVA_AGENT_ENDPOINT": str(endpoint_file),
        "UNOVA_AGENT_TOKEN": token,
    })
    install_dir = str(source.parent)
    if os.name == "nt":
        environment["PATH"] = install_dir + os.pathsep + environment.get("PATH", "")
    elif sys.platform.startswith("linux"):
        environment["LD_LIBRARY_PATH"] = install_dir + os.pathsep + environment.get("LD_LIBRARY_PATH", "")
    environment["QT_PLUGIN_PATH"] = install_dir
    platform_plugins = source.parent / "platforms"
    if platform_plugins.is_dir():
        environment["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platform_plugins)
    return environment


def _launch(args: argparse.Namespace) -> dict[str, Any]:
    emulator = _canonical(Path(args.emulator))
    rom = _canonical(Path(args.rom))
    save = _canonical(Path(args.save)) if args.save else None
    if not emulator.is_file() or not rom.is_file() or (save and not save.is_file()):
        raise AgentError("Emulator, ROM, and optional save must be existing files.")

    root = Path(tempfile.mkdtemp(prefix="unova-melonds-agent-")).resolve(strict=True)
    marker = secrets.token_hex(16)
    (root / MARKER_NAME).write_text(marker + "\n", encoding="ascii")
    (root / "profile" / "Roaming").mkdir(parents=True)
    (root / "profile" / "Local").mkdir(parents=True)
    (root / "rom").mkdir()
    shadow_rom = root / "rom" / rom.name
    try:
        # A hard link avoids a second full-size ROM copy. Saves and config are
        # created alongside the shadow path and in the private profile.
        os.link(rom, shadow_rom)
    except OSError as error:
        shutil.rmtree(root)
        raise AgentError("Could not create a same-volume ROM hard link in the temporary session; "
            "no ROM copy was made. Put the ROM and system temp folder on the same volume, then retry.") from error

    save_shadow = shadow_rom.with_suffix(".sav")
    if save:
        if os.path.normcase(str(save)) == os.path.normcase(str(rom)):
            shutil.rmtree(root)
            raise AgentError("A save path cannot be the ROM path.")
        try:
            shutil.copy2(save, save_shadow)
        except OSError as error:
            shutil.rmtree(root)
            raise AgentError(f"Could not create an isolated save copy: {error}") from error

    try:
        private_emulator = _prepare_private_emulator(root, emulator)
    except (OSError, AgentError) as error:
        shutil.rmtree(root)
        raise AgentError(f"Could not prepare a private emulator profile: {error}") from error

    token = secrets.token_hex(32)
    session_file = root / SESSION_NAME
    endpoint_file = root / "endpoint.json"
    data: dict[str, Any] = {
        "schema": 1,
        "root": str(root),
        "marker": marker,
        "pid": 0,
        "emulator": str(private_emulator),
        "emulator_source": str(emulator),
        "rom_source": str(rom),
        "shadow_rom": str(shadow_rom),
        "save_source": str(save) if save else None,
        "save_shadow": str(save_shadow),
        "token": token,
        "endpoint_file": str(endpoint_file),
        "session_file": str(session_file),
    }
    _write_json(session_file, data)

    environment = _emulator_environment(emulator, root, endpoint_file, token)
    log_file = (root / "emulator.log").open("wb")
    try:
        process = subprocess.Popen(
            [str(private_emulator), "--boot", args.boot, str(shadow_rom)],
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            close_fds=True,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    except OSError as error:
        log_file.close()
        shutil.rmtree(root)
        raise AgentError(f"Could not start the emulator: {error}") from error
    finally:
        if not log_file.closed:
            log_file.close()

    data["pid"] = process.pid
    _write_json(session_file, data)
    agent = {**data}
    deadline = time.monotonic() + 30
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            try:
                with EmulatorAgent(session_file) as client:
                    status = client.status()
                if status.get("pid") == process.pid:
                    return {"ok": True, "session": str(session_file), "pid": process.pid,
                        "version": status.get("version"), "status": status,
                        "romShadowed": True, "saveIsolated": True}
            except (AgentError, OSError, json.JSONDecodeError):
                pass
            time.sleep(0.1)
        log_text = (root / "emulator.log").read_text(encoding="utf-8", errors="replace")[-3000:]
        if process.poll() is None:
            try:
                with EmulatorAgent(session_file, timeout=2) as client:
                    client.request("shutdown")
            except Exception:
                pass
            raise AgentError("Emulator started but its control endpoint did not become ready. "
                f"Session left at {session_file} for safe inspection.\n{log_text}")
        try:
            _safe_remove_session(session_file)
            cleanup_note = ""
        except (AgentError, OSError) as cleanup_error:
            cleanup_note = f"\nSession retained at {session_file}: {cleanup_error}"
        raise AgentError(f"Emulator exited before its control endpoint became ready.\n{log_text}{cleanup_note}")
    except Exception:
        # Keep a live or uncertain process's session so cleanup never races it.
        raise


def _stop(args: argparse.Namespace) -> dict[str, Any]:
    session_file = Path(args.session)
    session, root = _validate_session_file(session_file)
    process_state = _process_matches(session)
    if process_state is None:
        raise AgentError("Cannot verify the emulator process identity on this platform; session kept intact.")
    if process_state:
        # melonDS flushes firmware/config and joins the emulation thread during
        # shutdown. On some machines that teardown takes longer than the old
        # 20-second bound even though the authenticated shutdown was accepted.
        # Retry the idempotent request while the API remains available: a
        # desktop event loop can be busy with startup or teardown work when the
        # first request arrives.
        deadline = time.monotonic() + 60
        next_shutdown_at = 0.0
        last_shutdown_error = None
        while time.monotonic() < deadline:
            process_state = _process_matches(session)
            if process_state is False:
                break
            now = time.monotonic()
            if now >= next_shutdown_at:
                try:
                    with EmulatorAgent(session_file, timeout=3) as agent:
                        agent.request("shutdown")
                    last_shutdown_error = None
                except (AgentError, OSError) as error:
                    last_shutdown_error = str(error)
                next_shutdown_at = now + 5
            time.sleep(0.2)
        if _process_matches(session) is not False:
            detail = f" Last shutdown error: {last_shutdown_error}." if last_shutdown_error else ""
            raise AgentError("Emulator did not exit within 60 seconds. The session remains intact." + detail)

    exported = None
    if args.save_out:
        destination = Path(args.save_out).expanduser().absolute()
        if destination.exists():
            raise AgentError(f"Refusing to overwrite save output: {destination}")
        source = Path(session["save_shadow"])
        if not source.is_file():
            raise AgentError("The isolated test session has no save file to export.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".tmp")
        shutil.copy2(source, temporary)
        temporary.replace(destination)
        exported = str(destination)
    _safe_remove_session(session_file)
    return {"ok": True, "cleaned": str(root), "exportedSave": exported}


def _run_command(args: argparse.Namespace) -> dict[str, Any]:
    with EmulatorAgent(Path(args.session)) as agent:
        if args.action == "status":
            return agent.status()
        if args.action == "press":
            return agent.press_for(args.buttons, args.frames)
        if args.action == "wait":
            return agent.wait_frames(args.frames)
        if args.action == "touch":
            return agent.touch(args.x, args.y, args.frames)
        if args.action == "screenshot":
            output = Path(args.output) if args.output else agent.root / f"screen-{int(time.time())}.png"
            return agent.screenshot(output)
        if args.action == "pause":
            return agent.request("pause")
        if args.action == "resume":
            return agent.request("resume")
        if args.action == "save-state":
            return agent.request("save_state", name=args.name)
        if args.action == "load-state":
            return agent.request("load_state", name=args.name)
    raise AgentError("Unknown command.")


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)

    start = commands.add_parser("start", help="launch a temporary, isolated emulator session")
    start.add_argument("--emulator", required=True, help="built melonDS executable")
    start.add_argument("--rom", required=True, help="user-provided patched or unpatched ROM")
    start.add_argument("--save", help="optional user save; copied into the disposable session")
    start.add_argument("--boot", choices=("auto", "always", "never"), default="auto")

    for action in ("status", "pause", "resume"):
        command = commands.add_parser(action)
        command.add_argument("--session", required=True)
        command.set_defaults(action=action)
    press = commands.add_parser("press", help="press one or more buttons for a frame count")
    press.add_argument("--session", required=True)
    press.add_argument("--frames", type=int, default=8)
    press.add_argument("buttons", nargs="+", help="A, B, Start, Select, directions, L/R/X/Y")
    press.set_defaults(action="press")
    wait = commands.add_parser("wait", help="wait for a number of emulated frames")
    wait.add_argument("--session", required=True)
    wait.add_argument("--frames", type=int, required=True)
    wait.set_defaults(action="wait")
    touch = commands.add_parser("touch", help="tap a Nintendo DS touch-screen point for a frame count")
    touch.add_argument("--session", required=True)
    touch.add_argument("--x", type=int, required=True, help="0-255")
    touch.add_argument("--y", type=int, required=True, help="0-191")
    touch.add_argument("--frames", type=int, default=8)
    touch.set_defaults(action="touch")
    shot = commands.add_parser("screenshot", help="capture both current game screens as PNG")
    shot.add_argument("--session", required=True)
    shot.add_argument("--out", dest="output", help="optional destination; defaults to the temp session")
    shot.set_defaults(action="screenshot")
    for action in ("save-state", "load-state"):
        command = commands.add_parser(action)
        command.add_argument("--session", required=True)
        command.add_argument("--name", required=True, help="safe session-local checkpoint name")
        command.set_defaults(action=action)
    stop = commands.add_parser("stop", help="close melonDS and remove its isolated temp session")
    stop.add_argument("--session", required=True)
    stop.add_argument("--save-out", help="optional new destination for the temporary .sav")
    commands.add_parser("cleanup", help="remove an already stopped marked test session").add_argument(
        "--session", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _make_parser().parse_args(argv)
    try:
        if args.operation == "start":
            result = _launch(args)
        elif args.operation == "stop":
            result = _stop(args)
        elif args.operation == "cleanup":
            _safe_remove_session(Path(args.session))
            result = {"ok": True, "cleaned": str(Path(args.session).parent)}
        else:
            result = _run_command(args)
        print(json.dumps(result, indent=2))
        return 0
    except (AgentError, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
