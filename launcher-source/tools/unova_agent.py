#!/usr/bin/env python3
"""Project inspection and direct emulator-control tools for AI coding agents.

The stdio MCP transport is intended for local coding clients. ``mcp-http`` is
an authenticated, loopback-only Streamable HTTP endpoint for a trusted tunnel.
"""
from __future__ import annotations

import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import hmac
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any
from urllib.parse import urlsplit

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from launcher_ui import gen5_tools, player_models, services  # noqa: E402
import unova_updater  # noqa: E402
import emulator_agent as emulator_runner  # noqa: E402

if getattr(sys, 'frozen', False):
    DEFAULT_PROJECT = Path(sys.executable).resolve().parent.parent
else:
    DEFAULT_PROJECT = (TOOLS.parent if (TOOLS.parent / 'VERSION.txt').is_file()
                       or (TOOLS.parent / 'builds/current/VERSION.txt').is_file()
                       else TOOLS.parent.parent)
PROJECT_ROOT = DEFAULT_PROJECT.resolve()
EMULATOR_SOURCE: Path | None = None
SEARCH_ROOTS: dict[str, Path] = {}
MAX_TEXT = 256 * 1024
MAX_MATCHES = 100
MAX_MCP_BODY = 1024 * 1024
ACTIVE_EMULATOR_SESSION: str | None = None
MCP_MODERN_VERSION = '2026-07-28'
MCP_LEGACY_VERSIONS = ('2025-11-25', '2025-06-18', '2025-03-26')
MCP_SUPPORTED_VERSIONS = (MCP_MODERN_VERSION, *MCP_LEGACY_VERSIONS)
MCP_VERSION_META = 'io.modelcontextprotocol/protocolVersion'
MCP_CLIENT_INFO_META = 'io.modelcontextprotocol/clientInfo'
MCP_CLIENT_CAPABILITIES_META = 'io.modelcontextprotocol/clientCapabilities'
MCP_SERVER_INFO_META = 'io.modelcontextprotocol/serverInfo'
TEXT_SUFFIXES = {'.md', '.py', '.cpp', '.h', '.hpp', '.json', '.toml', '.txt', '.yaml', '.yml', '.xml', '.csv', '.ini'}


def configure_paths(project_root: str | Path | None = None, emulator_source: str | Path | None = None) -> None:
    """Set the checked-out project and optional matching melonDS source tree."""
    global PROJECT_ROOT, EMULATOR_SOURCE, SEARCH_ROOTS
    PROJECT_ROOT = Path(project_root).expanduser().resolve() if project_root else DEFAULT_PROJECT.resolve()
    source = emulator_source or os.environ.get('UNOVA_EMULATOR_SOURCE')
    if source:
        EMULATOR_SOURCE = Path(source).expanduser().resolve()
    else:
        candidates = (PROJECT_ROOT / 'emulator-source', PROJECT_ROOT / 'melonDS-source-1.1',
                      PROJECT_ROOT / 'source' / 'melonDS', PROJECT_ROOT.parent / 'melonDS-source-1.1')
        EMULATOR_SOURCE = next((p.resolve() for p in candidates if (p / 'src').is_dir()), None)
    launcher_root = PROJECT_ROOT / 'launcher-source'
    if not launcher_root.is_dir():
        launcher_root = TOOLS / 'launcher_ui'
    assets_root = PROJECT_ROOT / 'launcher-source' / 'source-assets'
    if not assets_root.is_dir():
        assets_root = launcher_root / 'assets'
    SEARCH_ROOTS = {
        'docs': PROJECT_ROOT / 'docs',
        'launcher': launcher_root,
        'maintenance': PROJECT_ROOT / 'maintenance-tools',
        'emulator': EMULATOR_SOURCE or PROJECT_ROOT / 'emulator-source',
        'patchnotes': PROJECT_ROOT / 'patchnotes',
        'assets': assets_root,
    }


def _json(value: Any) -> dict[str, Any]:
    return {'ok': True, 'result': value}


def _walk_files(directory: Path):
    ignored = {'.git', '.venv', 'venv', 'build', 'builds', '__pycache__', 'node_modules', 'test-fixtures', 'diagnostics'}
    for current, dirs, files in os.walk(directory, followlinks=False):
        dirs[:] = [name for name in dirs if name not in ignored and not (Path(current) / name).is_symlink()]
        for name in files:
            path = Path(current) / name
            if not path.is_symlink():
                yield path


def inventory() -> dict[str, Any]:
    groups = {}
    for key, directory in SEARCH_ROOTS.items():
        if not directory.is_dir():
            continue
        count = 0
        extensions: dict[str, int] = {}
        for path in _walk_files(directory):
            count += 1
            ext = path.suffix.lower() or '[none]'
            extensions[ext] = extensions.get(ext, 0) + 1
        groups[key] = {'path': str(directory), 'files': count, 'extensions': extensions}
    external = []
    for label, path in (
        ('Pokemon DS Map Studio', PROJECT_ROOT / 'downloads' / 'map-studio' / 'editor'),
        ('Blender NSBMD reference files', PROJECT_ROOT / 'research' / 'reference' / 'blender-nsbmd'),
        ('Tinke reference source', PROJECT_ROOT / 'research' / 'reference' / 'tinke-reference'),
        ('SDSME reference source', PROJECT_ROOT / 'research' / 'reference' / 'sdsme'),
        ('Swan reference source', PROJECT_ROOT / 'research' / 'reference' / 'swan'),
        ('Beater-script reference', PROJECT_ROOT / 'research' / 'reference' / 'beater-script'),
    ):
        external.append({'name': label, 'path': str(path), 'available': path.exists(),
                         'interface': 'files at known path; no process/API control' if path.exists() else 'reference files not found at known path'})
    version = PROJECT_ROOT / 'VERSION.txt'
    if not version.is_file():
        version = PROJECT_ROOT / 'builds' / 'current' / 'VERSION.txt'
    return {'repository': 'WhatWasMissing/Unova-Together',
            'projectVersion': version.read_text(encoding='utf-8').strip() if version.is_file() else None,
            'projectRoot': str(PROJECT_ROOT), 'groups': groups, 'externalTools': external,
            'limits': ['External-tool entries detect files only at documented project paths; they do not discover applications elsewhere or control them.',
                       'Inventory reports metadata only; it does not execute third-party tools.',
                       'ROM-derived assets are read from the user copy and are not redistributed.',
                       'Emulator source is searched only when a matching source tree is available.']}


def search(query: str, area: str = 'all', limit: int = 30) -> list[dict[str, Any]]:
    if not query or len(query) > 300:
        raise ValueError('Search text must be 1–300 characters.')
    if not 1 <= limit <= MAX_MATCHES:
        raise ValueError(f'Limit must be between 1 and {MAX_MATCHES}.')
    roots = list(SEARCH_ROOTS.items()) if area == 'all' else [(area, SEARCH_ROOTS[area])] if area in SEARCH_ROOTS else None
    if roots is None:
        raise ValueError('Unknown search area.')
    pattern = re.compile(query, re.IGNORECASE)
    matches = []
    for label, root in roots:
        if not root.is_dir():
            continue
        for path in _walk_files(root):
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                if path.stat().st_size > MAX_TEXT:
                    continue
                for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                    if pattern.search(line):
                        try:
                            relative = path.relative_to(PROJECT_ROOT).as_posix()
                        except ValueError:
                            relative = str(path)
                        matches.append({'area': label, 'path': relative, 'line': number, 'text': line[:500]})
                        if len(matches) >= limit:
                            return matches
            except (OSError, UnicodeError):
                continue
    return matches


def read_document(relative: str) -> dict[str, Any]:
    candidate = Path(relative)
    if candidate.is_absolute() or '..' in candidate.parts:
        raise ValueError('Use a project-relative path without parent traversal.')
    path = (PROJECT_ROOT / candidate).resolve(strict=True)
    allowed = [PROJECT_ROOT / 'docs', PROJECT_ROOT / 'patchnotes', PROJECT_ROOT / 'launcher-source' / 'docs',
               PROJECT_ROOT / 'maintenance-tools', PROJECT_ROOT / 'tools']
    if (not any(path.is_relative_to(root.resolve()) for root in allowed if root.exists())
            or path.is_symlink() or path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > MAX_TEXT):
        raise ValueError('Only bounded project documentation and maintenance text can be read.')
    return {'path': str(path), 'text': path.read_text(encoding='utf-8')}


def inspect_rom(path: str) -> dict[str, Any]:
    rom = Path(path).expanduser().resolve(strict=True)
    if not rom.is_file() or rom.suffix.lower() != '.nds' or rom.stat().st_size > 512 * 1024 * 1024:
        raise ValueError('Select an existing Nintendo DS .nds ROM no larger than 512 MiB.')
    return {'path': str(rom), 'bytes': rom.stat().st_size, 'sha256': gen5_tools.digest(rom),
            'compatibility': gen5_tools.compatibility(rom)}


def inspect_save(path: str) -> dict[str, Any]:
    save = Path(path).expanduser().resolve(strict=True)
    if not save.is_file() or save.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('Select an existing save no larger than 32 MiB.')
    return gen5_tools.inspect_save(save)


def compare_saves(first: str, second: str) -> dict[str, Any]:
    return {'comparison': gen5_tools.compare_saves(Path(first).expanduser().resolve(strict=True),
                                                     Path(second).expanduser().resolve(strict=True))}


def redux_progression(rom_path: str, lost_xp_percent: float = 0, growth_rate: int = 3) -> dict[str, Any]:
    rom = Path(rom_path).expanduser().resolve(strict=True)
    if not rom.is_file() or rom.suffix.lower() != '.nds':
        raise ValueError('Select an existing Nintendo DS .nds ROM.')
    if not 0 <= growth_rate <= 5:
        raise ValueError('Growth rate must be between 0 and 5.')
    return {'report': gen5_tools.progression(rom, loss=lost_xp_percent, growth=growth_rate),
            'evidenceLimit': 'Challenge caps are verified only for the exact Redux ROM fingerprint; this is an XP budget comparison, not a playthrough simulation.'}


def list_player_models(rom_path: str, query: str = '', category: str = 'All characters', limit: int = 100) -> list[dict[str, Any]]:
    rom = Path(rom_path).expanduser().resolve(strict=True)
    if not rom.is_file() or rom.suffix.lower() != '.nds':
        raise ValueError('Select an existing Nintendo DS .nds ROM.')
    if not 1 <= limit <= 1000:
        raise ValueError('Limit must be between 1 and 1000.')
    from launcher_ui import player_model_preferences
    models = player_models.list_models(rom)
    filtered = player_model_preferences.filter_models(models, query=query, category=category)
    return [{'id': model, 'name': player_models.display_name(model),
             'category': 'Pokémon' if model in player_models.POKEMON_MODEL_LABELS else 'People'}
            for model in filtered[:limit]]


def preview_player_model(rom_path: str, model_id: int) -> dict[str, Any]:
    rom = Path(rom_path).expanduser().resolve(strict=True)
    if not rom.is_file() or rom.suffix.lower() != '.nds':
        raise ValueError('Select an existing Nintendo DS .nds ROM.')
    frames, preview_label = player_models.load_preview(rom, model_id)
    if not frames:
        raise ValueError('This model has no supported preview frames.')
    image, duration = frames[0]
    stream = BytesIO()
    image.save(stream, format='PNG')
    return {'modelId': model_id, 'name': player_models.display_name(model_id), 'frameCount': len(frames),
            'frameDurationMs': duration, 'width': image.width, 'height': image.height,
            'animation': preview_label,
            'pngBase64': base64.b64encode(stream.getvalue()).decode('ascii'),
            'evidence': 'ROM-derived 2D field texture preview; not a live 3D scene.'}


def _launcher_config() -> tuple[Path, dict[str, Any]]:
    config = Path(os.environ.get('APPDATA', Path.home())) / 'UnovaTogether' / 'launcher.json'
    if not config.is_file() or config.stat().st_size > 65536:
        return config, {}
    loaded = json.loads(config.read_text(encoding='utf-8'))
    return config, loaded if isinstance(loaded, dict) else {}


def launcher_profiles() -> list[dict[str, Any]]:
    config, data = _launcher_config()
    profiles = [services.normalize(p) for p in data.get('profiles', [])[:16] if isinstance(p, dict)]
    active_id = data.get('active_profile')
    return [{'id': p['id'], 'label': p['label'], 'player': p['player'], 'rom': p['rom'],
             'save_dir': p['save_dir'], 'active': p['id'] == active_id, 'configFound': config.is_file()}
            for p in profiles]


def launcher_status(home: str | None = None) -> dict[str, Any]:
    install_home = Path(home or PROJECT_ROOT).expanduser().resolve(strict=True)
    root = Path(unova_updater.active_root(install_home, allow_missing=True)).resolve()
    config, data = _launcher_config()
    profiles = [services.normalize(p) for p in data.get('profiles', [])[:16] if isinstance(p, dict)]
    active = next((p for p in profiles if p['id'] == data.get('active_profile')), profiles[0] if profiles else None)
    summary = {k: active.get(k) for k in ('id', 'label', 'player', 'rom', 'save_dir', 'network', 'lan_role')} if active else None
    checks = services.checks(root, active) if active else []
    version_file = root / 'builds/current/VERSION.txt'
    return {'home': str(install_home), 'activeRoot': str(root),
            'version': version_file.read_text(encoding='utf-8').strip() if version_file.is_file() else None,
            'installation': services.integrity(root), 'profileCount': len(profiles), 'activeProfile': summary,
            'preflight': checks, 'launcherConfigFound': config.is_file()}


def _active_profile(profile_id: str | None = None) -> dict[str, Any]:
    _, data = _launcher_config()
    profiles = [services.normalize(p) for p in data.get('profiles', [])[:16] if isinstance(p, dict)]
    if profile_id:
        selected = next((p for p in profiles if p['id'] == profile_id), None)
    else:
        selected = next((p for p in profiles if p['id'] == data.get('active_profile')), profiles[0] if profiles else None)
    if not selected:
        raise ValueError('No matching launcher profile. Pass a ROM path or select/configure a profile first.')
    return selected


def _run_runner(args: list[str]) -> dict[str, Any]:
    """Call the isolated emulator adapter directly, including in frozen builds."""
    parsed = emulator_runner._make_parser().parse_args(args)
    try:
        if parsed.operation == 'start':
            return emulator_runner._launch(parsed)
        if parsed.operation == 'stop':
            return emulator_runner._stop(parsed)
        if parsed.operation == 'cleanup':
            emulator_runner._safe_remove_session(Path(parsed.session))
            return {'ok': True, 'cleaned': str(Path(parsed.session).parent)}
        return emulator_runner._run_command(parsed)
    except (emulator_runner.AgentError, OSError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(str(error)) from error


def start_emulator(rom: str | None = None, save: str | None = None, emulator: str | None = None,
                   profile_id: str | None = None, boot: str = 'auto') -> dict[str, Any]:
    global ACTIVE_EMULATOR_SESSION
    if ACTIVE_EMULATOR_SESSION:
        session = Path(ACTIVE_EMULATOR_SESSION)
        if session.is_file():
            raise ValueError('An agent emulator session is already active. Stop it before starting another.')
        ACTIVE_EMULATOR_SESSION = None
    profile = _active_profile(profile_id) if not rom else None
    rom_path = Path(rom or profile['rom']).expanduser().resolve(strict=True)
    emulator_path = Path(emulator).expanduser().resolve(strict=True) if emulator else (PROJECT_ROOT / 'builds/current/melonDS.exe').resolve(strict=True)
    if not rom_path.is_file() or rom_path.suffix.lower() != '.nds':
        raise ValueError('Select an existing .nds ROM.')
    if not emulator_path.is_file() or emulator_path.name.lower() != 'melonds.exe':
        raise ValueError('Select the built Windows melonDS.exe executable.')
    save_path = Path(save).expanduser().resolve(strict=True) if save else None
    if save_path is None and profile:
        saves = services.save_files(profile)
        save_path = max(saves, key=lambda p: p.stat().st_mtime) if saves else None
    args = ['start', '--emulator', str(emulator_path), '--rom', str(rom_path), '--boot', boot]
    if save_path:
        args.extend(['--save', str(save_path)])
    result = _run_runner(args)
    session = str(result.get('session', ''))
    if not session:
        raise ValueError('Emulator runner started without returning a session path.')
    ACTIVE_EMULATOR_SESSION = session
    return {'session': session, 'pid': result.get('pid'), 'version': result.get('version'),
            'status': result.get('status'), 'romShadowed': True, 'saveIsolated': True,
            'sourceRom': str(rom_path), 'sourceSave': str(save_path) if save_path else None,
            'note': 'Input is sent to melonDS directly; no desktop keyboard or mouse events are synthesized.'}


def control_emulator(action: str, session: str | None = None, buttons: list[str] | None = None,
                     frames: int = 8, x: int | None = None, y: int | None = None,
                     checkpoint: str | None = None, save_out: str | None = None,
                     allow_save_export: bool = False) -> dict[str, Any]:
    global ACTIVE_EMULATOR_SESSION
    session_file = session or ACTIVE_EMULATOR_SESSION
    if not session_file:
        raise ValueError('Start an emulator session or provide its session path.')
    if action not in {'status', 'press', 'wait', 'touch', 'screenshot', 'pause', 'resume',
                      'save-state', 'load-state', 'stop'}:
        raise ValueError('Unsupported emulator action.')
    args = [action, '--session', str(Path(session_file).expanduser())]
    if action in {'press', 'wait', 'touch'}:
        if not 1 <= frames <= 3600:
            raise ValueError('Frame count must be between 1 and 3600.')
    if action == 'press':
        if not buttons or len(buttons) > 12:
            raise ValueError('Specify one or more supported DS buttons.')
        args.extend(['--frames', str(frames), *buttons])
    elif action == 'wait':
        args.extend(['--frames', str(frames)])
    elif action == 'touch':
        if x is None or y is None or not 0 <= x <= 255 or not 0 <= y <= 191:
            raise ValueError('Touch coordinates must be within x=0–255 and y=0–191.')
        args.extend(['--x', str(x), '--y', str(y), '--frames', str(frames)])
    elif action in {'save-state', 'load-state'}:
        if not checkpoint or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}', checkpoint):
            raise ValueError('Checkpoint names must use 1–48 letters, digits, underscores or hyphens.')
        args.extend(['--name', checkpoint])
    elif action == 'stop' and save_out:
        if not allow_save_export:
            raise ValueError('Save export is available only through the local CLI; MCP sessions discard isolated saves on stop.')
        destination = Path(save_out).expanduser().absolute()
        if destination.exists():
            raise ValueError('Refusing to overwrite an existing save export.')
        args.extend(['--save-out', str(destination)])
    result = _run_runner(args)
    if action == 'stop' and ACTIVE_EMULATOR_SESSION == session_file:
        ACTIVE_EMULATOR_SESSION = None
    if action == 'screenshot':
        path = Path(result.get('savedTo') or result.get('path', '')).resolve(strict=True)
        if path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError('Screenshot exceeds 8 MiB.')
        result = {**result, 'path': str(path), 'pngBase64': base64.b64encode(path.read_bytes()).decode('ascii')}
    return result


def call_tool(name: str, args: dict[str, Any]) -> Any:
    if name == 'project_inventory': return inventory()
    if name == 'search_project': return search(str(args.get('query', '')), str(args.get('area', 'all')), int(args.get('limit', 30)))
    if name == 'read_project_document': return read_document(str(args.get('path', '')))
    if name == 'inspect_rom': return inspect_rom(str(args.get('path', '')))
    if name == 'inspect_save': return inspect_save(str(args.get('path', '')))
    if name == 'compare_saves': return compare_saves(str(args.get('first', '')), str(args.get('second', '')))
    if name == 'redux_progression': return redux_progression(str(args.get('rom', '')), float(args.get('lostXpPercent', 0)), int(args.get('growthRate', 3)))
    if name == 'list_player_models': return list_player_models(str(args.get('rom', '')), str(args.get('query', '')), str(args.get('category', 'All characters')), int(args.get('limit', 100)))
    if name == 'preview_player_model': return preview_player_model(str(args.get('rom', '')), int(args.get('modelId', -1)))
    if name == 'inspect_launcher': return launcher_status(args.get('home'))
    if name == 'list_launcher_profiles': return launcher_profiles()
    if name == 'start_emulator':
        if not isinstance(args, dict) or 'emulator' in args:
            raise ValueError('MCP callers cannot select an emulator executable; the configured project build is used.')
        allowed = {'rom', 'save', 'profileId', 'boot'}
        if set(args) - allowed:
            raise ValueError('Unsupported start_emulator argument.')
        return start_emulator(args.get('rom'), args.get('save'), None, args.get('profileId'), str(args.get('boot', 'auto')))
    if name == 'control_emulator': return control_emulator(str(args.get('action', '')), args.get('session'), args.get('buttons'), int(args.get('frames', 8)), args.get('x'), args.get('y'), args.get('checkpoint'), args.get('saveOut'))
    raise ValueError('Unknown agent tool.')


_EMPTY = {'type': 'object', 'properties': {}, 'additionalProperties': False}
MCP_TOOLS = [
    {'name': 'project_inventory', 'description': 'Inventory project source, docs, assets and references to external tools. Metadata only.', 'inputSchema': _EMPTY},
    {'name': 'search_project', 'description': 'Search bounded text source, docs, patch notes and asset metadata.', 'inputSchema': {'type': 'object', 'properties': {'query': {'type': 'string'}, 'area': {'type': 'string', 'enum': ['all', 'docs', 'launcher', 'maintenance', 'emulator', 'patchnotes', 'assets']}, 'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100}}, 'required': ['query'], 'additionalProperties': False}},
    {'name': 'read_project_document', 'description': 'Read bounded project-relative documentation or maintenance notes.', 'inputSchema': {'type': 'object', 'properties': {'path': {'type': 'string'}}, 'required': ['path'], 'additionalProperties': False}},
    {'name': 'inspect_rom', 'description': 'Read-only hash and supported-version checks for a user-selected Nintendo DS ROM.', 'inputSchema': {'type': 'object', 'properties': {'path': {'type': 'string'}}, 'required': ['path'], 'additionalProperties': False}},
    {'name': 'inspect_save', 'description': 'Read-only checksum-verified Redux party summary for a user-selected save.', 'inputSchema': {'type': 'object', 'properties': {'path': {'type': 'string'}}, 'required': ['path'], 'additionalProperties': False}},
    {'name': 'compare_saves', 'description': 'Read-only comparison of checksum-verified Redux party blocks in two user-selected saves.', 'inputSchema': {'type': 'object', 'properties': {'first': {'type': 'string'}, 'second': {'type': 'string'}}, 'required': ['first', 'second'], 'additionalProperties': False}},
    {'name': 'redux_progression', 'description': 'Compare documented challenge level caps with exact XP growth thresholds in the reviewed Redux ROM.', 'inputSchema': {'type': 'object', 'properties': {'rom': {'type': 'string'}, 'lostXpPercent': {'type': 'number', 'minimum': 0, 'maximum': 100}, 'growthRate': {'type': 'integer', 'minimum': 0, 'maximum': 5}}, 'required': ['rom'], 'additionalProperties': False}},
    {'name': 'list_player_models', 'description': 'List animated character and Pokémon field models found in a compatible user ROM.', 'inputSchema': {'type': 'object', 'properties': {'rom': {'type': 'string'}, 'query': {'type': 'string'}, 'category': {'type': 'string', 'enum': ['All characters', 'People', 'Trainer outfits', 'Pokémon', 'Favorites']}, 'limit': {'type': 'integer', 'minimum': 1, 'maximum': 1000}}, 'required': ['rom'], 'additionalProperties': False}},
    {'name': 'preview_player_model', 'description': 'Decode a native 2D walk-animation texture frame from a user-selected ROM.', 'inputSchema': {'type': 'object', 'properties': {'rom': {'type': 'string'}, 'modelId': {'type': 'integer', 'minimum': 0, 'maximum': 65535}}, 'required': ['rom', 'modelId'], 'additionalProperties': False}},
    {'name': 'inspect_launcher', 'description': 'Read launcher installation integrity, configured profile and preflight checks.', 'inputSchema': {'type': 'object', 'properties': {'home': {'type': 'string'}}, 'additionalProperties': False}},
    {'name': 'list_launcher_profiles', 'description': 'List configured launcher profiles without exposing save contents.', 'inputSchema': _EMPTY},
    {'name': 'start_emulator', 'description': 'Start the configured project Windows emulator against an isolated hard-linked ROM copy and copied save. MCP callers cannot choose an executable path. Uses the selected launcher profile when ROM is omitted.', 'inputSchema': {'type': 'object', 'properties': {'rom': {'type': 'string'}, 'save': {'type': 'string'}, 'profileId': {'type': 'string'}, 'boot': {'type': 'string', 'enum': ['auto', 'always', 'never']}}, 'additionalProperties': False}},
    {'name': 'control_emulator', 'description': 'Send native button/touch input, wait for emulated frames, capture both screens, pause, resume, save/load a session checkpoint, or stop the isolated emulator. MCP sessions discard isolated saves on stop. No desktop input events are synthesized.', 'inputSchema': {'type': 'object', 'properties': {'action': {'type': 'string', 'enum': ['status', 'press', 'wait', 'touch', 'screenshot', 'pause', 'resume', 'save-state', 'load-state', 'stop']}, 'session': {'type': 'string'}, 'buttons': {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 12}, 'frames': {'type': 'integer', 'minimum': 1, 'maximum': 3600}, 'x': {'type': 'integer', 'minimum': 0, 'maximum': 255}, 'y': {'type': 'integer', 'minimum': 0, 'maximum': 191}, 'checkpoint': {'type': 'string'}}, 'required': ['action'], 'additionalProperties': False}},
]


def _mcp_error(identifier: Any, code: int, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {'code': code, 'message': message}
    if data is not None:
        error['data'] = data
    return {'jsonrpc': '2.0', 'id': identifier, 'error': error}


def _mcp_response(message: dict[str, Any], protocol_version: str | None = None) -> dict[str, Any] | None:
    if not isinstance(message, dict) or message.get('jsonrpc') != '2.0':
        return _mcp_error(message.get('id') if isinstance(message, dict) else None,
                          -32600, 'Invalid JSON-RPC request.')
    method = message.get('method')
    identifier = message.get('id')
    has_identifier = 'id' in message
    if not isinstance(method, str) or not method:
        return _mcp_error(identifier, -32600, 'Invalid JSON-RPC request method.')
    if has_identifier and (identifier is None or isinstance(identifier, bool)
                           or not isinstance(identifier, (str, int))):
        return _mcp_error(None, -32600, 'Invalid JSON-RPC request identifier.')
    if not has_identifier and not method.startswith('notifications/'):
        return _mcp_error(None, -32600, 'JSON-RPC requests must include an identifier.')
    if has_identifier and method.startswith('notifications/'):
        return _mcp_error(identifier, -32600, 'JSON-RPC notifications must not include an identifier.')
    params = message.get('params', {})
    if not isinstance(params, dict):
        return _mcp_error(identifier, -32602, 'MCP request params must be an object.')
    metadata = params.get('_meta')
    if metadata is not None and not isinstance(metadata, dict):
        return _mcp_error(identifier, -32602, 'MCP request metadata must be an object.')
    if protocol_version is None and metadata is not None:
        protocol_version = metadata.get(MCP_VERSION_META)
    if metadata is not None and metadata.get(MCP_VERSION_META) in MCP_LEGACY_VERSIONS:
        return _mcp_error(identifier, -32602, 'Legacy MCP versions use the initialize handshake, not per-request protocol metadata.')
    modern = (protocol_version == MCP_MODERN_VERSION
              or (metadata is not None and
                  (MCP_VERSION_META in metadata or MCP_CLIENT_CAPABILITIES_META in metadata))
              or (protocol_version is None and method == 'server/discover'))
    if protocol_version is not None and protocol_version not in MCP_SUPPORTED_VERSIONS:
        return _mcp_error(identifier, -32022, 'Unsupported protocol version',
                          {'supported': list(MCP_SUPPORTED_VERSIONS), 'requested': protocol_version})
    if modern:
        if protocol_version != MCP_MODERN_VERSION:
            return _mcp_error(identifier, -32602, 'Modern MCP requests require a protocol version in params._meta.')
        if (metadata is None or metadata.get(MCP_VERSION_META) != MCP_MODERN_VERSION
                or not isinstance(metadata.get(MCP_CLIENT_CAPABILITIES_META), dict)):
            return _mcp_error(identifier, -32602, 'Modern MCP requests require protocol version and client capabilities in params._meta.')
        if MCP_CLIENT_INFO_META in metadata:
            client_info = metadata[MCP_CLIENT_INFO_META]
            if (not isinstance(client_info, dict)
                    or not isinstance(client_info.get('name'), str) or not client_info['name'].strip()
                    or not isinstance(client_info.get('version'), str) or not client_info['version'].strip()):
                return _mcp_error(identifier, -32602, 'Invalid MCP client information in params._meta.')
    def success(value: dict[str, Any]) -> dict[str, Any]:
        if modern:
            value = {'resultType': 'complete', **value}
            value['_meta'] = {MCP_SERVER_INFO_META: {'name': 'unova-together-agent-tools', 'version': '1.0.0'}}
        return {'jsonrpc': '2.0', 'id': identifier, 'result': value}

    if modern and method == 'initialize':
        return _mcp_error(identifier, -32601, 'Method not found')
    if method in {'notifications/initialized', 'notifications/cancelled'}:
        return None
    if method == 'initialize':
        requested_version = params.get('protocolVersion')
        client_info = params.get('clientInfo')
        if (not isinstance(requested_version, str) or not isinstance(params.get('capabilities'), dict)
                or not isinstance(client_info, dict)
                or not isinstance(client_info.get('name'), str) or not client_info['name'].strip()
                or not isinstance(client_info.get('version'), str) or not client_info['version'].strip()):
            return _mcp_error(identifier, -32602, 'Legacy initialize requires protocolVersion, capabilities and clientInfo.')
        negotiated_version = requested_version if requested_version in MCP_LEGACY_VERSIONS else MCP_LEGACY_VERSIONS[0]
        result = {'protocolVersion': negotiated_version,
                  'capabilities': {'tools': {'listChanged': False}},
                  'serverInfo': {'name': 'unova-together-agent-tools', 'version': '1.0.0'}}
        return {'jsonrpc': '2.0', 'id': identifier, 'result': result}
    elif method == 'server/discover' and modern:
        return success({'supportedVersions': list(MCP_SUPPORTED_VERSIONS),
                        'capabilities': {'tools': {}},
                        'instructions': 'Use project inspection tools for source and documentation. Emulator control sends native emulated input and operates only on isolated ROM and save copies. The emulator executable is selected from the configured project build.',
                        'ttlMs': 3600000, 'cacheScope': 'public'})
    elif method == 'ping': result = {}
    elif method == 'tools/list':
        result = {'tools': MCP_TOOLS}
        if modern:
            result.update({'ttlMs': 3600000, 'cacheScope': 'public'})
    elif method == 'tools/call':
        try:
            output = call_tool(str(params.get('name', '')), params.get('arguments', {}))
        except Exception as exc:
            result = {'content': [{'type': 'text', 'text': str(exc)[:1000]}], 'isError': True}
            return success(result) if identifier is not None else None
        if params.get('name') == 'preview_player_model':
            png = base64.b64decode(output.pop('pngBase64'), validate=True)
            result = {'content': [{'type': 'image', 'data': base64.b64encode(png).decode('ascii'), 'mimeType': 'image/png'},
                                  {'type': 'text', 'text': json.dumps(output, ensure_ascii=False)}],
                      'isError': False}
        elif params.get('name') == 'control_emulator' and output.get('pngBase64'):
            png = base64.b64decode(output.pop('pngBase64'), validate=True)
            result = {'content': [{'type': 'image', 'data': base64.b64encode(png).decode('ascii'), 'mimeType': 'image/png'},
                                  {'type': 'text', 'text': json.dumps(output, ensure_ascii=False)}],
                      'isError': False}
        else:
            result = {'content': [{'type': 'text', 'text': json.dumps(output, ensure_ascii=False)}],
                      'isError': False}
        if modern:
            result = {'resultType': 'complete', **result,
                      '_meta': {MCP_SERVER_INFO_META: {'name': 'unova-together-agent-tools', 'version': '1.0.0'}}}
            return {'jsonrpc': '2.0', 'id': identifier, 'result': result} if identifier is not None else None
    else:
        if identifier is None: return None
        return {'jsonrpc': '2.0', 'id': identifier, 'error': {'code': -32601, 'message': 'Method not found'}}
    return success(result) if identifier is not None else None


def serve_mcp() -> int:
    """Run MCP over standard input and output for local coding clients."""
    legacy_initialized = False
    legacy_protocol_version: str | None = None
    while True:
        raw = sys.stdin.buffer.readline(MAX_MCP_BODY + 1)
        if not raw:
            break
        if len(raw) > MAX_MCP_BODY:
            while raw and not raw.endswith(b'\n'):
                raw = sys.stdin.buffer.readline(MAX_MCP_BODY + 1)
            response = _mcp_error(None, -32600, 'MCP request exceeds the 1 MiB message limit.')
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + '\n')
            sys.stdout.flush()
            continue
        identifier = None
        try:
            message = json.loads(raw)
            if not isinstance(message, dict):
                raise ValueError('JSON-RPC request must be an object.')
            identifier = message.get('id')
            method = message.get('method')
            params = message.get('params') if isinstance(message.get('params'), dict) else {}
            metadata = params.get('_meta') if isinstance(params.get('_meta'), dict) else {}
            request_version = metadata.get(MCP_VERSION_META)
            modern_request = (request_version is not None or MCP_CLIENT_CAPABILITIES_META in metadata
                              or method == 'server/discover')
            if method == 'initialize':
                response = _mcp_response(message)
                if isinstance(response, dict) and isinstance(response.get('result'), dict):
                    legacy_initialized = True
                    legacy_protocol_version = response['result'].get('protocolVersion')
            elif modern_request or request_version is not None:
                response = _mcp_response(message)
            elif not legacy_initialized and not (isinstance(method, str) and method.startswith('notifications/')):
                response = _mcp_error(identifier, -32600, 'Legacy MCP clients must initialize before making requests.')
            else:
                response = _mcp_response(message, legacy_protocol_version)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + '\n')
                sys.stdout.flush()
        except Exception as exc:
            if identifier is None:
                code = -32700 if isinstance(exc, json.JSONDecodeError) else -32600
            else:
                code = -32600
            sys.stdout.write(json.dumps({'jsonrpc': '2.0', 'id': identifier,
                'error': {'code': code, 'message': str(exc)[:1000]}}) + '\n')
            sys.stdout.flush()
    return 0


def serve_http(host: str, port: int) -> int:
    token = os.environ.get('UNOVA_AGENT_HTTP_TOKEN', '')
    if len(token) < 32:
        raise ValueError('Set UNOVA_AGENT_HTTP_TOKEN to a random value of at least 32 characters before starting mcp-http.')
    if host not in {'127.0.0.1', 'localhost'}:
        raise ValueError('The MCP HTTP endpoint must bind to loopback. Use a trusted secure tunnel for remote clients.')
    allowed_origins = {'http://127.0.0.1', 'http://localhost', 'http://[::1]'}
    allowed_origins.update(origin.strip() for origin in os.environ.get('UNOVA_AGENT_ALLOWED_ORIGINS', '').split(',') if origin.strip())
    allowed_hosts = {'127.0.0.1', 'localhost', '::1'}
    allowed_hosts.update(hostname.strip().lower() for hostname in os.environ.get('UNOVA_AGENT_ALLOWED_HOSTS', '').split(',') if hostname.strip())

    def rpc_error(identifier: Any, code: int, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        return _mcp_error(identifier, code, message, data)

    def rpc_status(response: dict[str, Any] | None) -> int:
        if not isinstance(response, dict) or not isinstance(response.get('error'), dict):
            return 200
        code = response['error'].get('code')
        return 404 if code == -32601 else 400 if code in {-32600, -32602, -32020, -32022} else 200

    class Handler(BaseHTTPRequestHandler):
        server_version = 'UnovaAgentMCP/1.0'
        def log_message(self, _format: str, *_args: Any) -> None:
            return
        def do_GET(self) -> None:
            self.send_response(405)
            self.send_header('Allow', 'POST')
            self.end_headers()
        def do_DELETE(self) -> None:
            self.send_response(405)
            self.send_header('Allow', 'POST')
            self.end_headers()
        def do_POST(self) -> None:
            if self.path != '/mcp':
                self.send_error(404)
                return
            host_header = self.headers.get('Host', '')
            request_host = urlsplit('//' + host_header).hostname
            if not request_host or request_host.lower() not in allowed_hosts:
                self.send_error(403)
                return
            if self.headers.get_content_type().lower() != 'application/json':
                self.send_error(415)
                return
            accepted = set()
            for value in self.headers.get('Accept', '').split(','):
                parts = [part.strip() for part in value.split(';')]
                try:
                    quality = next((float(part.split('=', 1)[1]) for part in parts[1:]
                                    if part.lower().startswith('q=')), 1.0)
                except (ValueError, IndexError):
                    quality = 0.0
                if quality > 0:
                    accepted.add(parts[0].lower())
            if not {'application/json', 'text/event-stream'} <= accepted:
                self.send_error(406)
                return
            origin = self.headers.get('Origin')
            if origin and origin not in allowed_origins:
                self.send_error(403)
                return
            authorization = self.headers.get('Authorization', '')
            scheme, _, supplied = authorization.partition(' ')
            if scheme.lower() != 'bearer' or not supplied:
                self.send_error(401)
                return
            if not hmac.compare_digest(supplied.encode(), token.encode()):
                self.send_error(401)
                return
            message: dict[str, Any] | None = None
            protocol_version = '2025-03-26'
            body_version: Any = None
            modern = False
            status = 400
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= MAX_MCP_BODY:
                    self.send_error(413)
                    return
                message = json.loads(self.rfile.read(length))
                if not isinstance(message, dict):
                    raise ValueError('JSON-RPC request must be an object.')
                identifier = message.get('id')
                method = message.get('method')
                params = message.get('params')
                params = params if isinstance(params, dict) else {}
                metadata = params.get('_meta')
                metadata = metadata if isinstance(metadata, dict) else {}
                header_version = self.headers.get('MCP-Protocol-Version')
                body_version = metadata.get(MCP_VERSION_META)
                method_header = self.headers.get('Mcp-Method')
                name_header = self.headers.get('Mcp-Name')
                modern = (header_version == MCP_MODERN_VERSION or body_version is not None
                          or method_header is not None or name_header is not None
                          or MCP_CLIENT_CAPABILITIES_META in metadata)
                if modern:
                    if body_version is None and header_version and header_version not in MCP_SUPPORTED_VERSIONS:
                        response = rpc_error(identifier, -32022, 'Unsupported protocol version',
                            {'supported': list(MCP_SUPPORTED_VERSIONS), 'requested': header_version})
                        status = 400
                    elif body_version is None:
                        response = rpc_error(identifier, -32602, 'Modern MCP requests require a protocol version in params._meta.')
                        status = 400
                    elif body_version not in MCP_SUPPORTED_VERSIONS:
                        response = rpc_error(identifier, -32022, 'Unsupported protocol version',
                            {'supported': list(MCP_SUPPORTED_VERSIONS), 'requested': body_version})
                        status = 400
                    elif body_version in MCP_LEGACY_VERSIONS:
                        response = rpc_error(identifier, -32602, 'Legacy MCP versions use the initialize handshake, not per-request protocol metadata.')
                        status = 400
                    elif header_version != body_version:
                        response = rpc_error(identifier, -32020, 'MCP protocol version header does not match request metadata.',
                            {'header': header_version, 'body': body_version})
                        status = 400
                    elif method_header != method:
                        response = rpc_error(identifier, -32020, 'Mcp-Method header does not match the JSON-RPC method.',
                            {'header': method_header, 'body': method})
                        status = 400
                    elif not isinstance(metadata.get(MCP_CLIENT_CAPABILITIES_META), dict):
                        response = rpc_error(identifier, -32602, 'Modern MCP requests require client capabilities in params._meta.')
                        status = 400
                    elif method in {'tools/call', 'prompts/get', 'resources/read'} and (
                            not isinstance(params.get('name') if method != 'resources/read' else params.get('uri'), str)
                            or not (params.get('name') if method != 'resources/read' else params.get('uri'))
                            or name_header != (params.get('uri') if method == 'resources/read' else params.get('name'))):
                        expected_name = params.get('uri') if method == 'resources/read' else params.get('name')
                        response = rpc_error(identifier, -32020, 'Mcp-Name header does not match the request name or URI.',
                            {'header': name_header, 'body': expected_name})
                        status = 400
                    elif name_header is not None and method not in {'tools/call', 'prompts/get', 'resources/read'}:
                        response = rpc_error(identifier, -32020, 'Mcp-Name is only valid for requests with a named resource, prompt or tool.',
                            {'header': name_header, 'body': None})
                        status = 400
                    else:
                        response = _mcp_response(message, MCP_MODERN_VERSION)
                        status = rpc_status(response)
                else:
                    protocol_version = header_version or '2025-03-26'
                    if protocol_version not in MCP_LEGACY_VERSIONS:
                        response = rpc_error(identifier, -32022, 'Unsupported protocol version',
                            {'supported': list(MCP_SUPPORTED_VERSIONS), 'requested': protocol_version})
                        status = 400
                    elif method_header is not None or name_header is not None:
                        response = rpc_error(identifier, -32020, 'Modern MCP request headers require modern request metadata.')
                        status = 400
                    else:
                        response = _mcp_response(message, protocol_version)
                        status = rpc_status(response)
            except json.JSONDecodeError as exc:
                request_id = message.get('id') if isinstance(message, dict) else None
                response = {'jsonrpc': '2.0', 'id': request_id,
                            'error': {'code': -32700, 'message': str(exc)[:500]}}
                status = 400
            except ValueError as exc:
                request_id = message.get('id') if isinstance(message, dict) else None
                response = {'jsonrpc': '2.0', 'id': request_id,
                            'error': {'code': -32600, 'message': str(exc)[:500]}}
                status = 400
            except Exception as exc:
                request_id = message.get('id') if isinstance(message, dict) else None
                response = {'jsonrpc': '2.0', 'id': request_id,
                            'error': {'code': -32600, 'message': str(exc)[:500]}}
                status = 400
            if response is None:
                self.send_response(202 if status in {200, 404} else status)
                self.end_headers()
                return
            payload = json.dumps(response, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            negotiated = (response.get('result', {}).get('protocolVersion')
                          if isinstance(response.get('result'), dict) else None)
            self.send_header('MCP-Protocol-Version', negotiated or (body_version if modern else protocol_version))
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer((host, port), Handler)
    try:
        print(f'Unova Together MCP endpoint listening at http://{host}:{server.server_port}/mcp', file=sys.stderr, flush=True)
        server.serve_forever()
    finally:
        server.server_close()
    return 0


def main(argv: list[str] | None = None) -> int:
    # MCP stdio is UTF-8 even when a frozen Windows process defaults to ACP.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', help='project checkout to inspect (defaults to this installation)')
    parser.add_argument('--emulator-source', help='matching unpacked melonDS source tree, when available')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('mcp', help='serve MCP tools on standard input/output')
    http = sub.add_parser('mcp-http', help='serve authenticated MCP over loopback HTTP for a trusted tunnel')
    http.add_argument('--host', default='127.0.0.1', choices=['127.0.0.1', 'localhost'])
    http.add_argument('--port', type=int, default=8765)
    sub.add_parser('inventory', help='describe project source and installed tool references')
    q = sub.add_parser('search'); q.add_argument('query'); q.add_argument('--area', choices=['all', 'docs', 'launcher', 'maintenance', 'emulator', 'patchnotes', 'assets'], default='all'); q.add_argument('--limit', type=int, default=30)
    d = sub.add_parser('document'); d.add_argument('path')
    r = sub.add_parser('rom'); r.add_argument('path')
    s = sub.add_parser('save'); s.add_argument('path')
    c = sub.add_parser('compare-saves'); c.add_argument('first'); c.add_argument('second')
    m = sub.add_parser('models'); m.add_argument('rom'); m.add_argument('--query', default=''); m.add_argument('--category', choices=['All characters', 'People', 'Trainer outfits', 'Pokémon', 'Favorites'], default='All characters'); m.add_argument('--limit', type=int, default=100)
    v = sub.add_parser('model-preview'); v.add_argument('rom'); v.add_argument('model_id', type=int); v.add_argument('--out', required=True)
    l = sub.add_parser('launcher'); l.add_argument('--home')
    profiles = sub.add_parser('profiles'); profiles.set_defaults()
    start = sub.add_parser('emulator-start'); start.add_argument('--rom'); start.add_argument('--save'); start.add_argument('--emulator'); start.add_argument('--profile-id'); start.add_argument('--boot', choices=['auto', 'always', 'never'], default='auto')
    control = sub.add_parser('emulator-control'); control.add_argument('action', choices=['status', 'press', 'wait', 'touch', 'screenshot', 'pause', 'resume', 'save-state', 'load-state', 'stop']); control.add_argument('--session'); control.add_argument('--buttons', nargs='*'); control.add_argument('--frames', type=int, default=8); control.add_argument('--x', type=int); control.add_argument('--y', type=int); control.add_argument('--checkpoint'); control.add_argument('--save-out')
    args = parser.parse_args(argv)
    configure_paths(args.project_root, args.emulator_source)
    try:
        if args.command == 'mcp': return serve_mcp()
        if args.command == 'mcp-http': return serve_http(args.host, args.port)
        if args.command == 'inventory': value = inventory()
        elif args.command == 'search': value = search(args.query, args.area, args.limit)
        elif args.command == 'document': value = read_document(args.path)
        elif args.command == 'rom': value = inspect_rom(args.path)
        elif args.command == 'save': value = inspect_save(args.path)
        elif args.command == 'compare-saves': value = compare_saves(args.first, args.second)
        elif args.command == 'models': value = list_player_models(args.rom, args.query, args.category, args.limit)
        elif args.command == 'model-preview':
            value = preview_player_model(args.rom, args.model_id)
            destination = Path(args.out).expanduser().absolute()
            if destination.exists(): raise ValueError('Refusing to overwrite the preview output.')
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(base64.b64decode(value.pop('pngBase64'), validate=True))
            value['previewPath'] = str(destination)
        elif args.command == 'launcher': value = launcher_status(args.home)
        elif args.command == 'profiles': value = launcher_profiles()
        elif args.command == 'emulator-start': value = start_emulator(args.rom, args.save, args.emulator, args.profile_id, args.boot)
        else: value = control_emulator(args.action, args.session, args.buttons, args.frames, args.x, args.y, args.checkpoint, args.save_out, allow_save_export=True)
        print(json.dumps(_json(value), indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
