"""Launcher build identity and safe shared-hub handoff. mvq1303 / WhatWasMissing."""
from pathlib import Path
import json
import re
import sys

PRODUCT = 'pokemon-together'
INFO = Path(__file__).resolve().parent / 'build-info.json'


def numbers(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{1,4}\.\d{1,4}\.\d{1,4}', value):
        raise ValueError('Invalid launcher version')
    return tuple(map(int, value.split('.')))


def read_info(path):
    path = Path(path)
    if path.stat().st_size > 4096:
        raise ValueError('Invalid launcher build metadata')
    info = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(info, dict) or info.get('schema') != 1 or info.get('product') != PRODUCT:
        raise ValueError('This is not a shared Pokemon Together launcher')
    numbers(info.get('version'))
    return info


def current_version():
    # Read the metadata embedded in this running build, never the active mod slot.
    return read_info(INFO)['version']


def updated_launcher(root, *, newer_only=False):
    directory = Path(root) / 'launcher'
    executable = directory / 'Pokemon Together.exe'
    try:
        candidate = numbers(read_info(directory / 'BUILD_INFO.json')['version'])
        running = numbers(current_version())
    except (OSError, ValueError, TypeError, AttributeError):
        return None
    if not executable.is_file() or candidate < running or (newer_only and candidate == running):
        return None
    if getattr(sys, 'frozen', False) and executable.resolve() == Path(sys.executable).resolve():
        return None
    return executable


def restart_executable(root):
    updated = updated_launcher(root)
    if updated is not None:
        return updated
    if getattr(sys, 'frozen', False):
        return Path(sys.executable)
    raise OSError('Updated shared launcher executable is missing or incompatible.')


def write_windows_version(template, destination, version):
    parts = numbers(version) + (0,)
    text = Path(template).read_text(encoding='utf-8')
    text = re.sub(r'(filevers|prodvers)=\([^)]*\)', lambda m: m[1] + '=' + repr(parts), text)
    text = re.sub(r"(StringStruct\('(?:FileVersion|ProductVersion)', )'[^']*'", lambda m: m[1] + repr(version), text)
    Path(destination).write_text(text, encoding='utf-8')
