#!/usr/bin/env python3
"""Safe JSON front end for the pinned BW2 decomp's event and text archive packers.

The packer sources remain in WhatWasMissing/pokebw2; this command validates the
checkout and paths, stages output, and emits one JSON result on stdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


PINNED_COMMIT = "215b992f5c87bcadc4c5d7a40e78a309b2555f8b"
DEFAULT_DECOMP = Path(r"F:\gen5decomps\black2-92%\pokebw2-current")
REPOSITORY_URLS = {
    "https://github.com/WhatWasMissing/pokebw2.git",
    "https://github.com/WhatWasMissing/pokebw2",
    "git@github.com:WhatWasMissing/pokebw2.git",
}
PACKERS = {
    "pack-events": Path("tools/data/event_data.py"),
    "pack-script-text": Path("tools/text/text_data.py"),
}
TOOL_INVENTORY = [
    {"name": "event_data.py", "repository": "WhatWasMissing/pokebw2", "path": "tools/data/event_data.py", "license": "GPL-3.0",
     "safety": "Reads event JSON; writes the requested NARC path directly.", "selected": True},
    {"name": "text_data.py", "repository": "WhatWasMissing/pokebw2", "path": "tools/text/text_data.py", "license": "GPL-3.0",
     "safety": "Reads text banks; writes the requested NARC path directly.", "selected": True},
    {"name": "species_data.py", "repository": "WhatWasMissing/pokebw2", "path": "tools/data/species_data.py", "license": "GPL-3.0",
     "safety": "Large multi-file data packer; changes archive output and depends on generated constants.", "selected": False},
    {"name": "trainer_data.py", "repository": "WhatWasMissing/pokebw2", "path": "tools/data/trainer_data.py", "license": "GPL-3.0",
     "safety": "Packs trainer records and parties; direct output write and game-specific IDs.", "selected": False},
    {"name": "narc.py", "repository": "WhatWasMissing/pokebw2", "path": "tools/data/narc.py", "license": "GPL-3.0",
     "safety": "Archive library; callers control arbitrary source and destination paths.", "selected": False},
    {"name": "romdiff.py", "repository": "WhatWasMissing/pokebw2", "path": "tools/build/romdiff.py", "license": "GPL-3.0",
     "safety": "Read-only binary comparison; suitable for validation, not content authoring.", "selected": False},
    {"name": "bw2_rom_reference_audit.py", "repository": "WhatWasMissing/Unova-Together", "path": "maintenance-tools/tools/research/bw2_rom_reference_audit.py",
     "license": "GPL-3.0-or-later", "safety": "Read-only ROM hashes, NARC members, and ARM9 overlays; requires ndspy.", "selected": False},
    {"name": "build_bps_patch.py", "repository": "WhatWasMissing/Unova-Together", "path": "launcher-source/tools/build_bps_patch.py",
     "license": "GPL-3.0-or-later", "safety": "Reads two ROMs and directly writes a patch; no overwrite or dry-run guard.", "selected": False},
]


class WorkflowError(ValueError):
    """An expected validation or operation failure suitable for JSON output."""


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise WorkflowError(f"Git could not verify the decomp checkout: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_decomp(root_arg: Path) -> tuple[Path, str]:
    try:
        root = root_arg.expanduser().resolve(strict=True)
    except OSError as error:
        raise WorkflowError(f"Decomp directory is unavailable: {error}") from error
    if not root.is_dir():
        raise WorkflowError("Decomp path must be a directory")
    top_level = Path(_git(root, "rev-parse", "--show-toplevel")).resolve(strict=True)
    if os.path.normcase(str(top_level)) != os.path.normcase(str(root)):
        raise WorkflowError("Decomp path must be the repository root")
    remote = _git(root, "remote", "get-url", "origin").rstrip("/")
    if remote not in REPOSITORY_URLS:
        raise WorkflowError("Decomp origin must be WhatWasMissing/pokebw2")
    revision = _git(root, "rev-parse", "HEAD")
    if revision != PINNED_COMMIT:
        raise WorkflowError(
            f"Unsupported decomp revision {revision}; expected pinned commit {PINNED_COMMIT}"
        )
    if not (root / "LICENSE").is_file():
        raise WorkflowError("Decomp checkout is missing its root license")
    dirty_tools = _git(root, "status", "--porcelain", "--untracked-files=all", "--", "tools")
    if dirty_tools:
        raise WorkflowError("Decomp tools/ is modified or contains untracked files; use a clean pinned toolchain")
    return root, revision


def _input_directory(path_arg: Path, operation: str) -> Path:
    expanded = path_arg.expanduser()
    try:
        path = expanded.resolve(strict=True)
    except OSError as error:
        raise WorkflowError(f"Input directory is unavailable: {error}") from error
    if not path.is_dir():
        raise WorkflowError("Input must be a directory")
    if expanded.is_symlink():
        raise WorkflowError("Input directory must not be a symbolic link")
    if operation == "pack-events":
        required = ("order.json", "events.schema.json")
        missing = [name for name in required if not (path / name).is_file()]
        if missing:
            raise WorkflowError(f"Event input is missing required files: {', '.join(missing)}")
    elif path.name not in {"script", "system"}:
        raise WorkflowError("Text input directory must be named 'script' or 'system'")
    # The upstream tools follow child symlinks. Reject them so the validated input
    # tree cannot silently pull in data from outside the selected directory.
    for parent, directories, files in os.walk(path, followlinks=False):
        parent_path = Path(parent)
        for child in directories + files:
            if (parent_path / child).is_symlink():
                raise WorkflowError("Input tree contains a symbolic link")
    return path


def _output_path(path_arg: Path, root: Path, source: Path) -> Path:
    expanded = path_arg.expanduser()
    if expanded.is_symlink():
        raise WorkflowError("Output must not be a symbolic link")
    path = expanded.resolve(strict=False)
    if not path.parent.is_dir():
        raise WorkflowError("Output parent directory must already exist")
    if path == source or source in path.parents:
        raise WorkflowError("Output cannot replace or be inside its input directory")
    if path == root or root in path.parents:
        raise WorkflowError("Output cannot be written inside the decomp checkout")
    if path.exists() and not path.is_file():
        raise WorkflowError("Existing output must be a regular file")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pack_archive(
    operation: str,
    input_arg: Path,
    output_arg: Path,
    decomp_arg: Path = DEFAULT_DECOMP,
    *,
    write: bool = False,
    backup: bool = False,
) -> dict:
    if operation not in PACKERS:
        raise WorkflowError(f"Unsupported operation: {operation}")
    root, revision = validate_decomp(decomp_arg)
    source = _input_directory(input_arg, operation)
    output = _output_path(output_arg, root, source)
    if output.exists() and write and not backup:
        raise WorkflowError("Output already exists; pass --backup to preserve it before replacement")
    if backup and not write:
        raise WorkflowError("--backup is only valid with --write")
    if backup and not output.exists():
        raise WorkflowError("--backup requires an existing output to preserve")

    tool = root / PACKERS[operation]
    if not tool.is_file():
        raise WorkflowError(f"Pinned decomp tool is not checked out yet: {PACKERS[operation]}")
    backup_path = output.with_name(output.name + ".bak")
    if output.exists() and (backup_path.exists() or backup_path.is_symlink()):
        raise WorkflowError(f"Backup already exists; refusing to replace it: {backup_path.name}")

    temp_parent = output.parent if write else None
    with tempfile.TemporaryDirectory(prefix="unova-romhack-pack-") as scratch:
        scratch_root = Path(scratch)
        if write:
            fd, staged_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=temp_parent)
            os.close(fd)
            staged = Path(staged_name)
        else:
            staged = scratch_root / "staged-archive.narc"
        try:
            # The reference checkout is read-only for this workflow. Prevent
            # Python from leaving __pycache__ files beside its upstream tools.
            command = [sys.executable, "-B", str(tool), "pack", str(source), str(staged)]
            result = subprocess.run(
                command,
                cwd=root,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout).strip()
                raise WorkflowError(
                    f"Upstream packer failed with exit code {result.returncode}: {detail[-1200:]}"
                )
            if not staged.is_file():
                raise WorkflowError("Upstream packer reported success but created no archive")
            result_data = {
                "ok": True,
                "operation": operation,
                "dryRun": not write,
                "written": False,
                "input": str(source),
                "output": str(output),
                "archiveBytes": staged.stat().st_size,
                "sha256": _sha256(staged),
                "sourceRepository": "WhatWasMissing/pokebw2",
                "sourceRevision": revision,
                "tool": PACKERS[operation].as_posix(),
                "toolLicense": "GPL-3.0",
                "toolStdout": result.stdout.strip(),
            }
            if write:
                if output.exists():
                    backup_created = False
                    try:
                        with output.open("rb") as original:
                            with backup_path.open("xb") as saved:
                                backup_created = True
                                shutil.copyfileobj(original, saved)
                    except OSError:
                        if backup_created:
                            backup_path.unlink(missing_ok=True)
                        raise
                    if backup_path.stat().st_size != output.stat().st_size or _sha256(backup_path) != _sha256(output):
                        backup_path.unlink(missing_ok=True)
                        raise WorkflowError("Could not verify the output backup; original output was left unchanged")
                    result_data["backup"] = str(backup_path)
                os.replace(staged, output)
                result_data["written"] = True
            return result_data
        finally:
            if write:
                staged.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inventory", help="show the reviewed packer inventory as JSON")
    for operation in PACKERS:
        command = commands.add_parser(operation, help=f"run the pinned {operation} command")
        command.add_argument("input", type=Path)
        command.add_argument("output", type=Path)
        command.add_argument("--decomp", type=Path, default=DEFAULT_DECOMP)
        command.add_argument("--write", action="store_true", help="atomically write the validated archive")
        command.add_argument("--backup", action="store_true", help="keep output.bak before replacing an output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "inventory":
            project_root = Path(__file__).resolve().parents[2]
            project_revision = _git(project_root, "rev-parse", "HEAD")
            result = {
                "ok": True,
                "decompRevision": PINNED_COMMIT,
                "projectRevision": project_revision,
                "toolsReviewed": [
                    {
                        **tool,
                        "revision": PINNED_COMMIT if tool["repository"] == "WhatWasMissing/pokebw2" else project_revision,
                    }
                    for tool in TOOL_INVENTORY
                ],
                "selectedTools": [
                    {"name": name, "path": path.as_posix(), "sourceRevision": PINNED_COMMIT}
                    for name, path in PACKERS.items()
                ],
            }
        else:
            result = pack_archive(
                args.command, args.input, args.output, args.decomp,
                write=args.write, backup=args.backup,
            )
    except (WorkflowError, OSError, subprocess.SubprocessError) as error:
        result = {"ok": False, "error": str(error), "command": args.command}
        print(json.dumps(result, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
