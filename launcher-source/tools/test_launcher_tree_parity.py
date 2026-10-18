"""Tests for launcher UI tree parity checks."""
from pathlib import Path
import tempfile
import unittest

from check_launcher_tree_parity import CANONICAL_TREE, MAINTENANCE_TREE, check_launcher_trees, compare_trees


class LauncherTreeParityTests(unittest.TestCase):
    def test_equal_trees_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            canonical = root / 'canonical'
            maintenance = root / 'maintenance'
            (canonical / 'assets').mkdir(parents=True)
            (maintenance / 'assets').mkdir(parents=True)
            (canonical / 'app.py').write_text('same', encoding='utf-8')
            (maintenance / 'app.py').write_text('same', encoding='utf-8')
            (canonical / 'assets' / 'news.json').write_text('{}', encoding='utf-8')
            (maintenance / 'assets' / 'news.json').write_text('{}', encoding='utf-8')
            count = check_launcher_trees(canonical, maintenance)
            self.assertEqual(count, 2)

    def test_reports_missing_extra_and_changed_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            canonical = root / 'canonical'
            maintenance = root / 'maintenance'
            canonical.mkdir()
            maintenance.mkdir()
            (canonical / 'changed.py').write_text('canonical', encoding='utf-8')
            (canonical / 'missing.py').write_text('missing', encoding='utf-8')
            (maintenance / 'changed.py').write_text('stale', encoding='utf-8')
            (maintenance / 'extra.py').write_text('extra', encoding='utf-8')
            differences, _ = compare_trees(canonical, maintenance)
            self.assertEqual(
                differences,
                [
                    'missing from maintenance tree: missing.py',
                    'extra in maintenance tree: extra.py',
                    'content differs: changed.py',
                ],
            )

    def test_checked_in_launcher_trees_match(self):
        if not CANONICAL_TREE.is_dir() or not MAINTENANCE_TREE.is_dir():
            self.skipTest('This source archive does not include both repository launcher trees.')
        self.assertGreater(check_launcher_trees(), 0)


if __name__ == '__main__':
    unittest.main()
