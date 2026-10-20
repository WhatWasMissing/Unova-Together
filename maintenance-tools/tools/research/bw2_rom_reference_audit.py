#!/usr/bin/env python3
"""Read-only comparison of selected BW2 NDS archives and ARM9 overlays.

This script only opens ROMs for reading. It reports ROM identity hashes, NARC
member differences, and decompressed ARM9 overlay load addresses, sizes, and
hashes. It does not extract files, write ROMs, or inspect or change save data.

Requires ndspy (tested with Python 3.12 and the ndspy package available on this
workstation). The package is intentionally not vendored or installed by this
script.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Iterable


DEFAULT_ARCHIVES = (
    "a/0/5/6",  # field scripts
    "a/1/6/9",  # trainer AI scripts
    "a/0/9/1",  # trainer records
    "a/0/9/2",  # trainer parties
    "a/0/1/2",  # zone headers
    "a/0/2/1",  # moves
    "a/0/2/4",  # items
    "a/0/4/8",  # field actor graphics
)
DEFAULT_OVERLAYS = (12, 36, 167, 170)


def digest(data: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def file_hash(path: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def display_rom(label: str, path: Path, rom: object) -> None:
    print(f"{label}: {path.name}")
    print(f"  SHA-1:   {file_hash(path, 'sha1')}")
    print(f"  SHA-256: {file_hash(path, 'sha256')}")
    print(
        "  Header:  "
        f"title={getattr(rom, 'name', '<unknown>')!r}, "
        f"gameCode={getattr(rom, 'idCode', '<unknown>')!r}, "
        f"unitCode={getattr(rom, 'unitCode', '<unknown>')}, "
        f"version={getattr(rom, 'version', '<unknown>')}"
    )


def narc_members(rom: object, archive: str, narc_type: type) -> list[bytes]:
    raw = rom.getFileByName(archive)
    return list(narc_type(raw).files)


def compare_archives(base: object, target: object, archive: str, narc_type: type) -> bool:
    try:
        base_members = narc_members(base, archive, narc_type)
        target_members = narc_members(target, archive, narc_type)
    except Exception as error:
        print(f"NARC {archive}: ERROR ({type(error).__name__}: {error})")
        return False

    common = min(len(base_members), len(target_members))
    changed = [
        index
        for index in range(common)
        if digest(base_members[index]) != digest(target_members[index])
    ]
    added = max(0, len(target_members) - len(base_members))
    removed = max(0, len(base_members) - len(target_members))
    print(
        f"NARC {archive}: members {len(base_members)} -> {len(target_members)}; "
        f"changed common indices={len(changed)}, added={added}, removed={removed}; "
        f"SHA-256 {digest(rom_file(base, archive))} -> {digest(rom_file(target, archive))}"
    )
    if changed:
        preview = ", ".join(str(index) for index in changed[:12])
        suffix = ", ..." if len(changed) > 12 else ""
        print(f"  First changed member indices: {preview}{suffix}")
    return True


def rom_file(rom: object, archive: str) -> bytes:
    return rom.getFileByName(archive)


def compare_overlays(base: object, target: object, overlay_ids: Iterable[int]) -> bool:
    ids = tuple(overlay_ids)
    try:
        base_overlays = base.loadArm9Overlays(ids)
        target_overlays = target.loadArm9Overlays(ids)
    except Exception as error:
        print(f"ARM9 overlays: ERROR ({type(error).__name__}: {error})")
        return False

    success = True
    for overlay_id in ids:
        left = base_overlays.get(overlay_id)
        right = target_overlays.get(overlay_id)
        if left is None or right is None:
            print(f"Overlay {overlay_id:03}: missing from {('baseline' if left is None else 'target')}")
            success = False
            continue
        left_data = bytes(left.data)
        right_data = bytes(right.data)
        print(
            f"Overlay {overlay_id:03}: RAM 0x{left.ramAddress:08X} -> 0x{right.ramAddress:08X}; "
            f"decompressed size {len(left_data)} -> {len(right_data)}; "
            f"SHA-256 {digest(left_data)} -> {digest(right_data)}"
        )
    return success


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only comparison of selected BW2 NARC archives and ARM9 overlays."
    )
    parser.add_argument("baseline", type=Path, help="baseline BW2 .nds file")
    parser.add_argument("target", type=Path, help="target BW2 .nds file")
    parser.add_argument(
        "--archive",
        action="append",
        dest="archives",
        help="archive path to compare; repeat to select archives (defaults to the research set)",
    )
    parser.add_argument(
        "--overlay",
        action="append",
        type=lambda value: int(value, 0),
        dest="overlays",
        help="ARM9 overlay ID to compare; repeat to select overlays (defaults to 12, 36, 167, 170)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for path in (args.baseline, args.target):
        if not path.is_file():
            print(f"ROM file not found: {path.name}", file=sys.stderr)
            return 2

    try:
        from ndspy.narc import NARC
        from ndspy.rom import NintendoDSRom
    except ImportError as error:
        print(f"ndspy is required but unavailable: {error}", file=sys.stderr)
        return 2

    try:
        base = NintendoDSRom.fromFile(args.baseline)
        target = NintendoDSRom.fromFile(args.target)
    except Exception as error:
        print(f"Could not parse ROM ({type(error).__name__}).", file=sys.stderr)
        return 2

    display_rom("BASELINE", args.baseline, base)
    display_rom("TARGET", args.target, target)
    try:
        parser_version = version("ndspy")
    except PackageNotFoundError:
        parser_version = "unknown"
    print(f"Parser: ndspy {parser_version}")
    print("\nSelected NARC comparisons (member indices are zero-based):")
    success = True
    for archive in args.archives or DEFAULT_ARCHIVES:
        success = compare_archives(base, target, archive, NARC) and success
    print("\nSelected ARM9 overlay comparisons (RAM addresses are load addresses):")
    success = compare_overlays(base, target, args.overlays or DEFAULT_OVERLAYS) and success
    if success:
        print("\nRead-only audit complete; no ROM or save data was written.")
        return 0
    print("\nRead-only audit incomplete; resolve the reported error before relying on this comparison.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
