"""Check that the maintenance launcher UI mirrors the canonical launcher UI."""
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_TREE = REPOSITORY_ROOT / 'launcher-source' / 'tools' / 'launcher_ui'
MAINTENANCE_TREE = REPOSITORY_ROOT / 'maintenance-tools' / 'tools' / 'launcher_ui'


def snapshot(root):
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f'Launcher UI tree does not exist: {root}')
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob('*')
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'
    }


def compare_trees(canonical, maintenance):
    left = snapshot(canonical)
    right = snapshot(maintenance)
    differences = []
    for name in sorted(left.keys() - right.keys()):
        differences.append(f'missing from maintenance tree: {name}')
    for name in sorted(right.keys() - left.keys()):
        differences.append(f'extra in maintenance tree: {name}')
    for name in sorted(left.keys() & right.keys()):
        if left[name] != right[name]:
            differences.append(f'content differs: {name}')
    return differences, len(left)


def check_launcher_trees(canonical=CANONICAL_TREE, maintenance=MAINTENANCE_TREE):
    differences, count = compare_trees(canonical, maintenance)
    if differences:
        details = '\n'.join(f'  - {item}' for item in differences)
        raise RuntimeError(f'Launcher UI trees differ ({len(differences)} issue(s)):\n{details}')
    return count


def main():
    try:
        count = check_launcher_trees()
    except (FileNotFoundError, RuntimeError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print(f'PASS: launcher UI trees match ({count} files).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
