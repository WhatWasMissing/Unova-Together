"""Tests for safe, noninteractive wrappers around the two selected decomp packers."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import romhack_workflow as workflow


class RomhackWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="unova-romhack-workflow-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.decomp = self.base / "decomp"
        self.decomp.mkdir()
        (self.decomp / ".git").mkdir()
        (self.decomp / "LICENSE").write_text("GPL-3.0 test fixture", encoding="utf-8")
        (self.decomp / "tools/data").mkdir(parents=True)
        (self.decomp / "tools/text").mkdir(parents=True)
        self.source = self.base / "events"
        self.source.mkdir()
        (self.source / "order.json").write_text("[]", encoding="utf-8")
        (self.source / "events.schema.json").write_text("{}", encoding="utf-8")
        self.output = self.base / "events.narc"
        fake_packer = "import pathlib,sys,packer_helper; pathlib.Path(sys.argv[-1]).write_bytes(packer_helper.ARCHIVE)\n"
        for relative in workflow.PACKERS.values():
            tool = self.decomp / relative
            tool.parent.mkdir(parents=True, exist_ok=True)
            tool.write_text(fake_packer, encoding="utf-8")
            (tool.parent / "packer_helper.py").write_text("ARCHIVE = b'fixture-archive'\n", encoding="utf-8")
        self.validate_patcher = mock.patch.object(workflow, "validate_decomp", return_value=(self.decomp, workflow.PINNED_COMMIT))
        self.validate_patcher.start()
        self.addCleanup(self.validate_patcher.stop)

    def test_dry_run_validates_and_does_not_write(self):
        result = workflow.pack_archive("pack-events", self.source, self.output, self.decomp)
        self.assertTrue(result["ok"])
        self.assertTrue(result["dryRun"])
        self.assertFalse(result["written"])
        self.assertEqual(result["archiveBytes"], len(b"fixture-archive"))
        self.assertFalse(self.output.exists())

    def test_dry_run_can_validate_an_existing_target_without_touching_it(self):
        self.output.write_bytes(b"keep-me")
        result = workflow.pack_archive("pack-events", self.source, self.output, self.decomp)
        self.assertTrue(result["dryRun"])
        self.assertEqual(self.output.read_bytes(), b"keep-me")

    def test_write_is_atomic_and_replacement_requires_verified_backup(self):
        first = workflow.pack_archive("pack-events", self.source, self.output, self.decomp, write=True)
        self.assertTrue(first["written"])
        self.assertEqual(self.output.read_bytes(), b"fixture-archive")
        self.output.write_bytes(b"old-archive")
        with self.assertRaisesRegex(workflow.WorkflowError, "--backup"):
            workflow.pack_archive("pack-events", self.source, self.output, self.decomp, write=True)
        second = workflow.pack_archive("pack-events", self.source, self.output, self.decomp,
                                       write=True, backup=True)
        self.assertEqual(Path(second["backup"]).read_bytes(), b"old-archive")
        self.assertEqual(self.output.read_bytes(), b"fixture-archive")

    def test_backup_option_requires_an_existing_output(self):
        with self.assertRaisesRegex(workflow.WorkflowError, "requires an existing output"):
            workflow.pack_archive("pack-events", self.source, self.output, self.decomp,
                                  write=True, backup=True)

    def test_output_cannot_overwrite_source_or_live_decomp(self):
        with self.assertRaisesRegex(workflow.WorkflowError, "inside its input"):
            workflow.pack_archive("pack-events", self.source, self.source / "order.json", self.decomp)
        with self.assertRaisesRegex(workflow.WorkflowError, "inside the decomp"):
            workflow.pack_archive("pack-events", self.source, self.decomp / "out.narc", self.decomp)

    def test_text_packer_requires_expected_source_directory_name(self):
        with self.assertRaisesRegex(workflow.WorkflowError, "named 'script' or 'system'"):
            workflow.pack_archive("pack-script-text", self.source, self.output, self.decomp)

    def test_text_packer_runs_noninteractively(self):
        text_source = self.base / "script"
        text_source.mkdir()
        (text_source / "demo.txt").write_text("Demo_Text_Hello = Hello!\n", encoding="utf-8")
        result = workflow.pack_archive("pack-script-text", text_source, self.output, self.decomp)
        self.assertTrue(result["ok"])
        self.assertEqual(result["operation"], "pack-script-text")
        self.assertFalse(self.output.exists())

    def test_upstream_imports_do_not_create_bytecode_in_reference_checkout(self):
        self.assertTrue(workflow.pack_archive("pack-events", self.source, self.output, self.decomp)["ok"])
        for relative in workflow.PACKERS.values():
            self.assertFalse((self.decomp / relative).parent.joinpath("__pycache__").exists())

    def test_pinned_reference_and_clean_packer_tree_are_required(self):
        self.validate_patcher.stop()
        try:
            validate = workflow.validate_decomp
            with mock.patch.object(workflow, "_git", side_effect=[str(self.decomp),
                    "https://github.com/WhatWasMissing/pokebw2.git", "0" * 40]):
                with self.assertRaisesRegex(workflow.WorkflowError, "Unsupported decomp revision"):
                    validate(self.decomp)
            with mock.patch.object(workflow, "_git", side_effect=[str(self.decomp),
                    "https://github.com/WhatWasMissing/pokebw2.git", workflow.PINNED_COMMIT, "?? tools/changed.py"]):
                with self.assertRaisesRegex(workflow.WorkflowError, "modified or contains untracked"):
                    validate(self.decomp)
            with mock.patch.object(workflow, "_git", side_effect=[str(self.decomp),
                    "https://github.com/WhatWasMissing/pokebw2.git", workflow.PINNED_COMMIT, ""]):
                self.assertEqual(validate(self.decomp), (self.decomp, workflow.PINNED_COMMIT))
        finally:
            self.validate_patcher.start()

    def test_failed_packer_cleans_staged_file(self):
        tool = self.decomp / workflow.PACKERS["pack-events"]
        tool.write_text("import sys; print('fixture error', file=sys.stderr); raise SystemExit(3)\n", encoding="utf-8")
        with self.assertRaisesRegex(workflow.WorkflowError, "exit code 3"):
            workflow.pack_archive("pack-events", self.source, self.output, self.decomp, write=True)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.base.glob(".events.narc.*.tmp")), [])

    def test_nested_symlinks_are_rejected(self):
        nested = self.source / "external"
        try:
            nested.symlink_to(self.base, target_is_directory=True)
        except OSError:
            self.skipTest("symbolic links are unavailable in this environment")
        with self.assertRaisesRegex(workflow.WorkflowError, "symbolic link"):
            workflow.pack_archive("pack-events", self.source, self.output, self.decomp)


if __name__ == "__main__":
    unittest.main()
