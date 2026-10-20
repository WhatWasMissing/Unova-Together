"""Compile and exercise the shop policy extracted from the distributed source patch.

Use --cxx for a C++17 compiler and optionally repeat --rom for local read-only
Redux data checks. A POD adapter supplies only the ROMAssetPatch transport type;
the emulator/card-read implementation is not exercised. No generated executable
or copy of a ROM/save is retained.
"""
# Unova Together: Copyright (C) 2026 mvq1303. GPL-3.0-or-later.
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", required=True, type=Path)
    parser.add_argument("--rom", action="append", default=[], type=Path)
    args = parser.parse_args()
    if not args.cxx.is_file():
        parser.error("C++ compiler does not exist")
    for rom in args.rom:
        if not rom.is_file():
            parser.error(f"ROM fixture does not exist: {rom}")
    patch_path = ROOT / "maintenance-tools/patches/development-polish.patch"
    patch_bytes = patch_path.read_bytes()
    metadata = json.loads(patch_path.with_suffix(".json").read_text(encoding="utf-8"))
    if hashlib.sha256(patch_bytes).hexdigest() != metadata["patchSha256"]:
        raise RuntimeError("distributed source patch does not match its metadata")
    patch = patch_bytes.decode("utf-8")
    folder = Path(tempfile.mkdtemp(prefix="mega-shop-test-", dir=ROOT)).resolve()
    assert folder.parent == ROOT.resolve() and folder.name.startswith("mega-shop-test-")
    try:
        (folder / "ROMAssetOverlay.h").write_text(
            "#pragma once\n#include <algorithm>\n#include <cstdint>\n#include <cstring>\n#include <vector>\n"
            "namespace melonDS { struct ROMAssetPatch { uint32_t offset; std::vector<uint8_t> bytes; }; }\n",
            encoding="utf-8")
        for name in ("Gen5ShopPolicy.h", "Gen5MegaItemIds.h"):
            match = re.search(
                rf"(?ms)^--- /dev/null\n\+\+\+ b/source/melonDS/src/{re.escape(name)}\n"
                r"@@ -0,0 \+1,(\d+) @@\n(.*?)(?=^--- |\Z)", patch)
            if not match:
                raise RuntimeError(f"packaged source missing: {name}")
            lines = [line[1:] for line in match[2].splitlines() if line.startswith("+")]
            if len(lines) != int(match[1]):
                raise RuntimeError(f"incorrect packaged patch line count: {name}")
            (folder / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
        executable = folder / ("shop-test.exe" if os.name == "nt" else "shop-test")
        env = dict(os.environ)
        env["PATH"] = str(args.cxx.resolve().parent) + os.pathsep + env.get("PATH", "")
        subprocess.run([str(args.cxx.resolve()), "-std=c++17", "-O2", "-UNDEBUG",
                        "-I", str(folder), str(Path(__file__).with_name("check_gen5_shop_distribution.cpp")),
                        "-o", str(executable)], check=True, env=env)
        before = {}
        for rom in args.rom:
            with rom.open("rb") as stream:
                before[rom] = hashlib.file_digest(stream, "sha256").hexdigest()
        subprocess.run([str(executable), *(str(rom.resolve()) for rom in args.rom)], check=True, env=env)
        for rom, digest in before.items():
            with rom.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                    raise RuntimeError(f"read-only ROM fixture changed: {rom}")
            print(f"PASS: read-only ROM SHA-256 {digest}")
    finally:
        # Only this invocation's verified disposable directory is removed.
        assert folder.parent == ROOT.resolve() and folder.name.startswith("mega-shop-test-")
        shutil.rmtree(folder)


if __name__ == "__main__":
    main()
