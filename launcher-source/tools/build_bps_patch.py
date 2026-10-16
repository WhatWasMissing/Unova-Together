"""Create a compact BPS patch from two Nintendo DS ROMs without embedding either ROM."""
from __future__ import annotations

import argparse
import mmap
import struct
import zlib
from pathlib import Path


def _number(value: int) -> bytes:
    if value < 0:
        raise ValueError("BPS numbers cannot be negative")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value == 0:
            out.append(byte | 0x80)
            return bytes(out)
        out.append(byte)
        value -= 1


def _signed(value: int) -> bytes:
    return _number((abs(value) << 1) | (1 if value < 0 else 0))


def _fat(path: Path, data: mmap.mmap) -> list[tuple[int, int]]:
    if len(data) < 0x50:
        raise ValueError(f"{path} is too short to be a Nintendo DS ROM")
    fat_offset, fat_size = struct.unpack_from("<II", data, 0x48)
    if fat_size % 8 or fat_offset + fat_size > len(data):
        raise ValueError(f"{path} has an invalid FAT table")
    entries = [struct.unpack_from("<II", data, fat_offset + i)
               for i in range(0, fat_size, 8)]
    for start, end in entries:
        if start > end or end > len(data):
            raise ValueError(f"{path} contains an invalid file range")
    return entries


def build(source: Path, target: Path, output: Path) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    actions = bytearray()
    with source.open("rb") as source_file, target.open("rb") as target_file:
        src = mmap.mmap(source_file.fileno(), 0, access=mmap.ACCESS_READ)
        dst = mmap.mmap(target_file.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            src_fat = _fat(source, src)
            dst_fat = _fat(target, dst)
            if len(src_fat) != len(dst_fat):
                raise ValueError("Source and target ROMs have different file counts")

            header = bytearray(b"BPS1")
            header += _number(len(src)) + _number(len(dst)) + _number(0)
            cursor = 0
            source_copy_end = 0
            unchanged = changed = literal_bytes = 0

            def target_read(start: int, end: int) -> None:
                nonlocal cursor, literal_bytes
                if end <= start:
                    return
                length = end - start
                actions.extend(_number(((length - 1) << 2) | 1))
                actions.extend(dst[start:end])
                cursor += length
                literal_bytes += length

            target_files = sorted((start, end, index)
                                  for index, (start, end) in enumerate(dst_fat)
                                  if end > start)
            first_file = target_files[0][0] if target_files else len(dst)
            target_read(0, first_file)
            for start, end, index in target_files:
                if start < cursor:
                    raise ValueError("Target ROM file ranges overlap")
                target_read(cursor, start)
                source_start, source_end = src_fat[index]
                is_same = (source_end - source_start == end - start
                           and src[source_start:source_end] == dst[start:end])
                length = end - start
                if is_same:
                    actions.extend(_number(((length - 1) << 2) | 2))
                    actions.extend(_signed(source_start - source_copy_end))
                    source_copy_end = source_start + length
                    unchanged += 1
                else:
                    actions.extend(_number(((length - 1) << 2) | 1))
                    actions.extend(dst[start:end])
                    literal_bytes += length
                    changed += 1
                cursor = end
            target_read(cursor, len(dst))

            patch = header + actions
            patch += struct.pack("<II", zlib.crc32(src) & 0xFFFFFFFF,
                                 zlib.crc32(dst) & 0xFFFFFFFF)
            patch += struct.pack("<I", zlib.crc32(patch) & 0xFFFFFFFF)
            output.write_bytes(patch)
            return {
                "source": str(source.resolve()),
                "source_bytes": len(src),
                "target": str(target.resolve()),
                "target_bytes": len(dst),
                "patch": str(output.resolve()),
                "patch_bytes": len(patch),
                "unchanged_files_copied": unchanged,
                "changed_files_embedded": changed,
                "literal_bytes": literal_bytes,
            }
        finally:
            src.close()
            dst.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    import json
    print(json.dumps(build(args.source, args.target, args.output), indent=2))


if __name__ == "__main__":
    main()
