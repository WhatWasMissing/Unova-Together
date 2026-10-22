"""Compile and run the real follower renderer against synthetic depth frames.

Requires an explicit matching emulator source tree, C++17 compiler and Qt6Gui.
This check does not load a ROM, execute a game, or authenticate the supplied tree.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--compiler', default=shutil.which('g++'))
    parser.add_argument('--pkg-config', default=shutil.which('pkg-config'))
    args = parser.parse_args()
    if not args.compiler or not args.pkg_config:
        parser.error('Supply --compiler and --pkg-config, or put both on PATH')
    source = args.source_root.resolve()
    front = source / 'src/frontend/qt_sdl'
    for relative in ('src/PresenceOcclusion.h', 'src/frontend/qt_sdl/PresenceOverlay.h',
                     'src/frontend/qt_sdl/PresenceOverlay.cpp'):
        path = source / relative
        if not path.is_file():
            parser.error(f'Required production source is missing: {path}')
        print(f'SOURCE {relative} SHA256 {hashlib.sha256(path.read_bytes()).hexdigest()}', flush=True)
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    env['PATH'] = str(Path(args.compiler).resolve().parent) + os.pathsep + env.get('PATH', '')
    flags = shlex.split(subprocess.check_output(
        [args.pkg_config, '--cflags', '--libs', 'Qt6Gui'], env=env, text=True))
    workspace = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix='.follower-depth-test-', dir=workspace) as tmp:
        if not Path(tmp).resolve().is_relative_to(workspace):
            raise RuntimeError('Test output must remain inside this checkout')
        exe = Path(tmp) / ('follower_depth.exe' if os.name == 'nt' else 'follower_depth')
        subprocess.run([args.compiler, '-std=c++17', '-O2', '-UNDEBUG',
                        '-I' + str(front), '-I' + str(source / 'src'),
                        str(Path(__file__).with_name('check_follower_depth.cpp')),
                        str(front / 'PresenceOverlay.cpp'), '-o', str(exe), *flags],
                       env=env, check=True)
        subprocess.run([str(exe)], env=env, check=True)


if __name__ == '__main__':
    main()
