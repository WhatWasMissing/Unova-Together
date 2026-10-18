"""Portable validation tests for the source-dependent companion test runner."""
from pathlib import Path
import tempfile
import unittest

import test_companion_interactions as runner


class CompanionRunnerValidationTests(unittest.TestCase):
    def test_requires_source_root_and_source_identity(self):
        with self.assertRaises(SystemExit):
            runner.main([])

    def test_accepts_identified_source_and_records_header_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            header = root / 'src/frontend/qt_sdl/FollowerInteraction.h'
            header.parent.mkdir(parents=True)
            header.write_bytes(b'known production header fixture')
            evidence = runner.inspect_source(root, 'https://example.invalid/source@0123456789abcdef')
            self.assertEqual(evidence['root'], root.resolve())
            self.assertEqual(evidence['header_sha256'], 'b104efb3b0ba277df806a5dcd2225ab83e089d0f3c1c9825518bc74ac4e37449')

    def test_expected_hash_mismatch_is_a_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            header = root / 'src/frontend/qt_sdl/FollowerInteraction.h'
            header.parent.mkdir(parents=True)
            header.write_bytes(b'header')
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                runner.inspect_source(root, 'UNVERIFIED SOURCE: local archive', '0' * 64)

    def test_missing_production_header_is_a_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'missing the production header'):
                runner.inspect_source(folder, 'UNVERIFIED SOURCE: missing fixture')

    def test_missing_compiler_or_qt_root_is_a_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'Missing compiler/Qt prerequisite'):
                runner.inspect_toolchain(Path(folder) / 'missing-cxx', Path(folder) / 'missing-qt')

    def test_missing_qt_core_library_is_a_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            compiler = root / 'g++'
            compiler.write_bytes(b'compiler fixture')
            (root / 'include/qt6/QtCore').mkdir(parents=True)
            (root / 'lib').mkdir()
            with self.assertRaisesRegex(ValueError, 'Qt6Core link library is missing'):
                runner.inspect_toolchain(compiler, root)


if __name__ == '__main__':
    unittest.main()
