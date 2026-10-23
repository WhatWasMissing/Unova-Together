"""Focused checks for the data-driven dialogue preview and Gen 5 text bounds."""
from __future__ import annotations

import copy
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import dialogue_preview
from dialogue_preview import DialogueError, build_preview, validate_scene


SCENE = Path(__file__).resolve().parents[1] / "dialogue-demo" / "field_researcher.json"


class DialoguePreviewTests(unittest.TestCase):
    def setUp(self):
        self.scene = json.loads(SCENE.read_text(encoding="utf-8"))

    def test_demo_has_valid_branches_and_expressions(self):
        self.assertEqual(validate_scene(self.scene), [])
        self.assertEqual(len(self.scene["nodes"]), 4)

    def test_rejects_text_outside_native_dialogue_budget(self):
        scene = copy.deepcopy(self.scene)
        scene["nodes"][0]["text"] = "X" * 29
        self.assertTrue(any("28 display cells" in issue for issue in validate_scene(scene)))
        scene["nodes"][0]["text"] = "one\ntwo\nthree"
        self.assertTrue(any("2-line" in issue for issue in validate_scene(scene)))
        scene["nodes"][0]["text"] = "界" * 15
        self.assertTrue(any("28 display cells" in issue for issue in validate_scene(scene)))
        scene["nodes"][0]["text"] = "Unsupported 😀 glyph."
        self.assertTrue(any("unsupported glyph" in issue for issue in validate_scene(scene)))

    def test_rejects_missing_branch_and_unsupported_condition(self):
        scene = copy.deepcopy(self.scene)
        scene["nodes"][0]["choices"][0]["next"] = "missing"
        scene["nodes"][0]["choices"][0]["when"] = {"field": "badge", "equals": 1}
        issues = validate_scene(scene)
        self.assertTrue(any("missing node" in issue for issue in issues))
        self.assertTrue(any("boolean event flag" in issue for issue in issues))

    def test_rejects_unsupported_choice_glyphs(self):
        scene = copy.deepcopy(self.scene)
        scene["nodes"][0]["choices"][0]["label"] = "Ask about 😀"
        self.assertTrue(any("choice" in issue and "unsupported glyph" in issue
                            for issue in validate_scene(scene)))

    def test_malformed_json_shapes_report_issues_without_crashing(self):
        scene = copy.deepcopy(self.scene)
        scene["start"] = []
        scene["nodes"][0]["speaker"] = []
        scene["nodes"][0]["expression"] = []
        scene["nodes"][0]["next"] = []
        scene["nodes"][0]["choices"][0]["when"] = {"flag": [], "equals": True}
        self.assertTrue(validate_scene(scene))

    def test_preview_is_self_contained_and_has_missing_art_fallback(self):
        html = build_preview(self.scene)
        self.assertIn("makeFallback", html)
        self.assertIn("HAS_MEGA_STONE", html)
        self.assertIn("portrait expression", html)
        self.assertIn("\"portrait\": null", html)
        self.assertNotIn("__SCENE_DATA__", html)

    def test_scene_text_is_embedded_as_data_not_executable_markup(self):
        scene = copy.deepcopy(self.scene)
        scene["nodes"][0]["text"] = "<script>alert(1)</script>"
        html = build_preview(scene)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("\\u003cscript>", html)

    def test_portrait_paths_cannot_escape_assets_folder(self):
        scene = copy.deepcopy(self.scene)
        scene["speakers"]["nia"]["expressions"]["happy"]["portrait"] = "../outside.png"
        scene["speakers"]["nia"]["expressions"]["happy"]["credit"] = "Test artist"
        scene["speakers"]["nia"]["expressions"]["happy"]["license"] = "CC0-1.0"
        scene["speakers"]["nia"]["expressions"]["happy"]["sourceUrl"] = "https://example.org/art"
        with tempfile.TemporaryDirectory(prefix="unova-dialogue-assets-") as folder:
            with self.assertRaisesRegex(DialogueError, "stay inside"):
                build_preview(scene, Path(folder))

    def test_absent_portrait_file_uses_the_expression_fallback(self):
        scene = copy.deepcopy(self.scene)
        art = scene["speakers"]["nia"]["expressions"]["happy"]
        art.update(portrait="nia/happy.png", credit="Demo artist", license="CC0-1.0",
                   sourceUrl="https://example.org/art")
        with tempfile.TemporaryDirectory(prefix="unova-dialogue-assets-") as folder:
            html = build_preview(scene, Path(folder))
        self.assertIn("makeFallback", html)
        self.assertNotIn("data:image/png;base64", html)

    def test_cli_writes_preview_and_preserves_replaced_file(self):
        with tempfile.TemporaryDirectory(prefix="unova-dialogue-preview-test-") as folder:
            output = Path(folder) / "preview.html"
            with mock.patch.object(sys, "argv", ["dialogue_preview", "render", str(SCENE), str(output)]):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(dialogue_preview.main(), 0)
            self.assertIn("Field dialogue preview", output.read_text(encoding="utf-8"))
            output.write_text("old preview", encoding="utf-8")
            with mock.patch.object(sys, "argv", ["dialogue_preview", "render", str(SCENE), str(output)]):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(dialogue_preview.main(), 2)
            with mock.patch.object(sys, "argv", ["dialogue_preview", "render", str(SCENE), str(output), "--backup"]):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(dialogue_preview.main(), 0)
            self.assertEqual(output.with_name("preview.html.bak").read_text(encoding="utf-8"), "old preview")


if __name__ == "__main__":
    unittest.main()
