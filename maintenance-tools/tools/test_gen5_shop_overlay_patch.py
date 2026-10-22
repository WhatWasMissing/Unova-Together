"""Check the Mega shop overlay keeps Redux's unrelated field-engine bytes."""

# Unova Together contributions: Copyright (C) 2026 mvq1303.
# GitHub: WhatWasMissing - https://github.com/WhatWasMissing/Unova-Together
# GPL-3.0-or-later. Preserve all upstream notices.

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = Path(__file__).with_name("build_gen5_shop_overlay_patch.py")
PATCH_PATH = ROOT / "maintenance-tools" / "patches" / "development-polish.patch"
METADATA_PATH = ROOT / "maintenance-tools" / "patches" / "development-polish.json"

spec = importlib.util.spec_from_file_location("build_gen5_shop_overlay_patch", GENERATOR_PATH)
assert spec and spec.loader
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
packager_spec = importlib.util.spec_from_file_location(
    "package_development_polish", Path(__file__).with_name("package_development_polish.py")
)
assert packager_spec and packager_spec.loader
packager = importlib.util.module_from_spec(packager_spec)
packager_spec.loader.exec_module(packager)


def packaged_shop_header() -> str:
    patch = PATCH_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^--- /dev/null\n\+\+\+ b/source/melonDS/src/Gen5ShopOverlayPatch\.h\n"
        r"@@ -0,0 \+1,\d+ @@\n(.*?)(?=^--- |\Z)",
        patch,
    )
    if not match:
        raise AssertionError("development patch does not add Gen5ShopOverlayPatch.h")
    return "\n".join(line[1:] for line in match.group(1).splitlines() if line.startswith("+"))


def added_source(path: str) -> str:
    patch = PATCH_PATH.read_text(encoding="utf-8")
    relative = re.escape(path)
    addition = re.search(
        rf"(?ms)^--- /dev/null\n\+\+\+ b/{relative}\n@@ -0,0 \+\d+,\d+ @@\n(.*?)(?=^--- |\Z)",
        patch,
    )
    if addition:
        return "\n".join(
            line[1:] for line in addition.group(1).splitlines() if line.startswith("+")
        )
    match = re.search(
        rf"(?ms)^--- a/{relative}\n\+\+\+ b/{relative}\n(.*?)(?=^--- |\Z)", patch
    )
    if not match:
        raise AssertionError(f"development patch does not change {path}")
    return "\n".join(line[1:] for line in match.group(1).splitlines() if line.startswith("+"))


class ShopOverlayPatchTests(unittest.TestCase):
    def test_shop_lists_fit_native_storage_without_installing_overlay(self):
        policy = added_source("source/melonDS/src/Gen5ShopPolicy.h")
        mega = added_source("source/melonDS/src/Gen5MegaEvolution.h")
        self.assertRegex(policy, r"MaxShopUIEntries\s*=\s*45\s*;")
        self.assertRegex(policy, r"MegaStonesPerPokemonCenterMart\s*=\s*3\s*;")
        self.assertNotIn("appendHeapBackedShopOverlay(combined, rom)", mega)

    def test_packager_keeps_no_final_newline_diffs_separate(self):
        lines = packager.unified_diff_lines(
            "before", "after", "a/sample.cpp", "b/sample.cpp"
        )
        self.assertTrue(all(line.endswith("\n") for line in lines))
        patch = "".join(lines)
        self.assertIn(
            "-before\n\\ No newline at end of file\n"
            "+after\n\\ No newline at end of file\n",
            patch,
        )
        with tempfile.TemporaryDirectory(prefix="unova-patch-newline-") as folder:
            temporary = Path(folder)
            source = temporary / "sample.cpp"
            source.write_bytes(b"before")
            patch_file = temporary / "sample.patch"
            patch_file.write_text(patch, encoding="utf-8", newline="\n")
            result = subprocess.run(
                ["git", "apply", str(patch_file)],
                cwd=temporary,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(source.read_bytes(), b"after")

    def test_emulator_and_multiplayer_titles_use_the_packaged_release_version(self):
        version_text = (ROOT / "VERSION.txt").read_text(encoding="utf-8")
        version_match = re.search(r"\b(\d+\.\d+\.\d+)\b", version_text)
        self.assertIsNotNone(version_match)
        version = version_match.group(1)
        credits = added_source("source/melonDS/src/frontend/qt_sdl/ProjectCredits.h")
        panel = added_source("source/melonDS/src/frontend/qt_sdl/MultiplayerPanel.cpp")
        self.assertRegex(credits, r'inline constexpr char Version\[\] = "\d+\.\d+\.\d+";')
        self.assertIn('inline QString ReleaseVersion()', credits)
        self.assertIn('filePath("VERSION.txt")', credits)
        self.assertIn('const QString prefix = QString::fromLatin1(Name) + \' \';', credits)
        self.assertIn('return candidate;', credits)
        self.assertIn('return QString::fromLatin1(Version);', credits)
        self.assertIn('inline QString WindowTitle()', credits)
        self.assertIn("QString::fromLatin1(Name) + ' ' + ReleaseVersion()", credits)
        self.assertIn('WindowTitle().toHtmlEscaped()', credits)
        self.assertIn('setWindowTitle("Multiplayer ["+identifier+"] - "+ProjectCredits::WindowTitle());', panel)
        for relative in ('Window.cpp', 'PokePlayIntro.h', 'AboutDialog.cpp'):
            self.assertIn('ProjectCredits::', added_source('source/melonDS/src/frontend/qt_sdl/' + relative))

    def test_distributed_source_patch_is_parseable(self):
        result = subprocess.run(
            ["git", "apply", "--numstat", "--", str(PATCH_PATH)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_filter_preserves_field_engine_and_replaces_shop_section(self):
        source_size = generator.Gen5ShopOverlayPatchSourceSize
        source = bytes((i * 17 + 29) & 0xFF for i in range(source_size))
        rebuilt = bytes((value ^ 0xFF) for value in source) + bytes(range(256)) + bytes(range(192))
        filtered = generator.filter_shop_ui_overlay(source, rebuilt)

        start = generator.SHOP_UI_START - generator.RAM_BASE
        end = generator.SHOP_UI_END - generator.RAM_BASE
        self.assertEqual(filtered[:start], source[:start])
        self.assertEqual(filtered[start:end], rebuilt[start:end])
        self.assertEqual(filtered[end:source_size], source[end:])
        self.assertEqual(len(filtered), source_size)

    def test_filter_rejects_a_different_overlay_size(self):
        with self.assertRaises(ValueError):
            generator.filter_shop_ui_overlay(b"short", b"longer")

    def test_distributed_patch_keeps_shop_delta_inside_original_overlay(self):
        header = packaged_shop_header()
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(PATCH_PATH.read_bytes()).hexdigest(), metadata["patchSha256"]
        )

        def constant(name: str) -> int:
            match = re.search(rf"\b{name}\s*=\s*(0x[0-9A-Fa-f]+|\d+)", header)
            self.assertIsNotNone(match, f"missing {name}")
            return int(match.group(1), 0)

        source_size = constant("SourceOverlaySize")
        target_size = constant("TargetOverlaySize")
        run_count = constant("DeltaRunCount")
        self.assertEqual(constant("SourceOverlayCrc32"), 0xA7CF9125)
        self.assertEqual(constant("TargetOverlayCrc32"), 0x3DC1FED8)
        self.assertEqual(source_size, generator.Gen5ShopOverlayPatchSourceSize)
        self.assertEqual(target_size, source_size)
        self.assertEqual(run_count, 232)
        fieldmap_end = generator.RAM_BASE + target_size + 0x10040
        self.assertLessEqual(fieldmap_end, 0x021E5800)

        array = re.search(r"EncodedDelta\{\{(.*?)\}\};", header, re.DOTALL)
        self.assertIsNotNone(array)
        encoded = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", array.group(1)))
        self.assertEqual(len(encoded), 7892)

        start = generator.SHOP_UI_START - generator.RAM_BASE
        end = generator.SHOP_UI_END - generator.RAM_BASE
        cursor = 0
        previous_end = 0
        changed_bytes = 0
        for _ in range(run_count):
            offset = int.from_bytes(encoded[cursor : cursor + 3], "little")
            size = int.from_bytes(encoded[cursor + 3 : cursor + 5], "little")
            cursor += 5
            self.assertGreater(size, 0)
            self.assertGreaterEqual(offset, previous_end)
            self.assertLessEqual(offset + size, target_size)
            is_shop_code = start <= offset and offset + size <= end
            self.assertTrue(is_shop_code, (offset, size))
            cursor += size
            changed_bytes += size
            previous_end = offset + size
        self.assertEqual(cursor, len(encoded))
        self.assertEqual(changed_bytes, 6732)


if __name__ == "__main__":
    unittest.main()
