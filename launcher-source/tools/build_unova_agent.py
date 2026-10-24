"""Build the self-contained Windows agent-tools executable."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[3]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True)
    parser.add_argument('--pyinstaller-python', type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    work = args.work_dir.resolve()
    if not output.is_relative_to(WORKSPACE / 'builds') or not work.is_relative_to(WORKSPACE / 'builds'):
        raise ValueError('Agent build output and work directories must stay within workspace builds.')
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f'Agent output directory must be fresh: {output}')
    if work.exists() and any(work.iterdir()):
        raise FileExistsError(f'Agent build work directory must be fresh: {work}')
    python = args.pyinstaller_python.resolve() if args.pyinstaller_python else Path(sys.executable)
    if not python.is_file():
        raise FileNotFoundError(f'PyInstaller Python executable does not exist: {python}')
    output.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        str(python), '-m', 'PyInstaller', '--noconfirm', '--onefile', '--console', '--noupx',
        '--name', 'Unova Agent Tools', '--collect-all', 'ndspy', '--collect-all', 'PIL',
        '--collect-all', 'tomlkit', '--collect-all', 'launcher_ui', '--distpath', str(output),
        '--workpath', str(work / 'pyinstaller'), '--specpath', str(work), str(ROOT / 'unova_agent.py'),
    ], check=True, cwd=ROOT)
    executable = output / 'Unova Agent Tools.exe'
    if not executable.is_file() or executable.stat().st_size < 1024 * 1024:
        raise RuntimeError('PyInstaller did not produce the expected self-contained agent executable.')
    print(f'Built {executable} ({executable.stat().st_size} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
