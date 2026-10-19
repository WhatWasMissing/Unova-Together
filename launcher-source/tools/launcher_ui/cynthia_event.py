"""Create a private, launcher-managed copy with Cynthia's Route 7 Mega event."""
from __future__ import annotations

import hashlib
import json
import mmap
import os
from pathlib import Path
import struct
import zlib

from . import preferences as prefs


_PATCHES = {
    # Clean Redux Complete 1.4.1 and the matching Unova Together base used by
    # the project's current test save are both supported by distinct patches.
    "332d07576e2077b4ef91e394603d144108098b7624c6a918b175f90530c0036a": (
        "cynthia-route7-redux-1.4.1.bps",
        "c34498dc807a83e3d5a5c85a341464c24f56a1ed515db6cfc7ef4e2a71dc3df7",
        289387720,
    ),
    "353fb0cf82c3e4eddfc8986efa8910b00eb1c4d6f106c220abef59d69d3a520a": (
        "cynthia-route7-unova-1.0.35.bps",
        "234079a05e5360b81b5fbe41d39815bec65193b986ac2d877e23a86d76377220",
        289389256,
    ),
}


class UnsupportedRomError(ValueError):
    """The story patch is unavailable for this ROM revision."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _decode_number(data: mmap.mmap, position: int, limit: int) -> tuple[int, int]:
    value = 0
    shift = 1
    while True:
        if position >= limit:
            raise ValueError("Cynthia event patch is truncated")
        byte = data[position]
        position += 1
        value += (byte & 0x7F) * shift
        if byte & 0x80:
            return value, position
        shift <<= 7
        value += shift
        if shift > (1 << 63):
            raise ValueError("Cynthia event patch has an invalid number")


def _decode_signed(value: int) -> int:
    magnitude = value >> 1
    return -magnitude if value & 1 else magnitude


def _apply_bps(source: mmap.mmap, patch: mmap.mmap, target_size: int) -> bytearray:
    if len(patch) < 16 or patch[:4] != b"BPS1":
        raise ValueError("Cynthia event patch is not a valid BPS file")
    expected_patch_crc, = struct.unpack_from("<I", patch, len(patch) - 4)
    if zlib.crc32(patch[:-4]) & 0xFFFFFFFF != expected_patch_crc:
        raise ValueError("Cynthia event patch failed its checksum")

    cursor = 4
    limit = len(patch) - 12
    source_size, cursor = _decode_number(patch, cursor, limit)
    actual_target_size, cursor = _decode_number(patch, cursor, limit)
    metadata_size, cursor = _decode_number(patch, cursor, limit)
    if source_size != len(source) or actual_target_size != target_size:
        raise ValueError("Cynthia event patch size does not match the selected ROM")
    if cursor + metadata_size > limit:
        raise ValueError("Cynthia event patch metadata is truncated")
    cursor += metadata_size
    source_crc, target_crc, _ = struct.unpack_from("<III", patch, limit)
    if zlib.crc32(source) & 0xFFFFFFFF != source_crc:
        raise ValueError("Selected ROM failed the Cynthia event patch checksum")

    target = bytearray(target_size)
    output_position = 0
    source_relative = 0
    target_relative = 0
    while cursor < limit:
        action, cursor = _decode_number(patch, cursor, limit)
        length = (action >> 2) + 1
        mode = action & 3
        end = output_position + length
        if end > target_size:
            raise ValueError("Cynthia event patch writes beyond the output ROM")
        if mode == 0:  # SourceRead
            start = output_position
            if start + length > len(source):
                raise ValueError("Cynthia event patch reads beyond the selected ROM")
            target[output_position:end] = source[start:start + length]
        elif mode == 1:  # TargetRead
            if cursor + length > limit:
                raise ValueError("Cynthia event patch data is truncated")
            target[output_position:end] = patch[cursor:cursor + length]
            cursor += length
        elif mode == 2:  # SourceCopy
            delta, cursor = _decode_number(patch, cursor, limit)
            source_relative += _decode_signed(delta)
            if source_relative < 0 or source_relative + length > len(source):
                raise ValueError("Cynthia event patch reads outside the selected ROM")
            target[output_position:end] = source[source_relative:source_relative + length]
            source_relative += length
        else:  # TargetCopy
            delta, cursor = _decode_number(patch, cursor, limit)
            target_relative += _decode_signed(delta)
            if target_relative < 0 or target_relative >= output_position:
                raise ValueError("Cynthia event patch has an invalid output reference")
            for index in range(length):
                if target_relative + index >= output_position + index:
                    raise ValueError("Cynthia event patch has an invalid overlapping copy")
                target[output_position + index] = target[target_relative + index]
            target_relative += length
        output_position = end

    if output_position != target_size or zlib.crc32(target) & 0xFFFFFFFF != target_crc:
        raise ValueError("Patched ROM failed the Cynthia event integrity check")
    return target


def _asset_path(patch_name: str) -> Path:
    return Path(__file__).resolve().parent / "assets" / "patches" / "cynthia-route7" / patch_name


def prepare_variant(source_path, home, patch_root=None) -> Path:
    """Return a checked patch copy; the player's selected ROM remains read-only."""
    source = Path(source_path).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".nds":
        raise ValueError("Choose an existing Blaze Black 2 Redux game file first.")
    original_stat = source.stat()
    source_hash = _sha256(source)
    if any(source_hash == target_hash for _, target_hash, _ in _PATCHES.values()):
        return source
    descriptor = _PATCHES.get(source_hash)
    if descriptor is None:
        raise UnsupportedRomError(
            "The Route 7 story event supports the reviewed English Redux Complete 1.4.1 ROM "
            "or the matching Unova Together 1.0.35 ROM. Your selected ROM was not changed."
        )
    patch_name, target_hash, target_size = descriptor
    patch = Path(patch_root) if patch_root else _asset_path(patch_name)
    if not patch.is_file():
        raise ValueError("The Cynthia Route 7 patch is missing from this launcher build.")

    root = Path(home).expanduser().resolve()
    cache = root / ".launcher-cynthia-route7"
    if cache.exists() and cache.is_symlink():
        raise ValueError("The Cynthia event cache folder cannot be a symbolic link.")
    cache.mkdir(parents=True, exist_ok=True)
    cache = cache.resolve()
    target = cache / (source.stem + " - Cynthia Route 7.nds")
    manifest = target.with_suffix(".json")
    if target.is_symlink() or manifest.is_symlink():
        raise ValueError("A Cynthia event cache file is a symbolic link; remove it before continuing.")
    patch_hash = _sha256(patch)
    expected_manifest = {
        "source_sha256": source_hash,
        "patch_sha256": patch_hash,
        "output_sha256": target_hash,
        "output_bytes": target_size,
    }
    if target.is_file() and manifest.is_file():
        try:
            if json.loads(manifest.read_text(encoding="utf-8")) == expected_manifest:
                if target.stat().st_size == target_size and _sha256(target) == target_hash:
                    return target
        except (OSError, ValueError, TypeError):
            pass

    with prefs.staged_path(target) as pending:
        with source.open("rb") as source_file, patch.open("rb") as patch_file:
            source_map = mmap.mmap(source_file.fileno(), 0, access=mmap.ACCESS_READ)
            patch_map = mmap.mmap(patch_file.fileno(), 0, access=mmap.ACCESS_READ)
            try:
                output = _apply_bps(source_map, patch_map, target_size)
            finally:
                patch_map.close()
                source_map.close()
        current_stat = source.stat()
        if (current_stat.st_size, current_stat.st_mtime_ns) != (original_stat.st_size, original_stat.st_mtime_ns):
            raise ValueError("The selected ROM changed while the event copy was being prepared.")
        with pending.open("wb") as stream:
            stream.write(output)
        del output
        if _sha256(pending) != target_hash:
            raise ValueError("The generated Cynthia event copy failed verification.")
        current_stat = source.stat()
        if (current_stat.st_size, current_stat.st_mtime_ns) != (original_stat.st_size, original_stat.st_mtime_ns):
            raise ValueError("The selected ROM changed while the event copy was being checked.")
        os.replace(pending, target)
        prefs.atomic(manifest, json.dumps(expected_manifest, sort_keys=True))
    return target
