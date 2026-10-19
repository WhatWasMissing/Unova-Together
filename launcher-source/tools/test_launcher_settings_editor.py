"""Schema-aware emulator settings editor input handling."""
from pathlib import Path
import tempfile
import unittest

from launcher_ui.settings_editor import document


class SettingsEditorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Path(self.temp.name)
        self.config = self.runtime / 'melonDS.toml'

    def tearDown(self):
        self.temp.cleanup()

    def test_document_reports_non_table_schema_parents(self):
        for raw in ('3D = 3\n', '[Instance0]\nKeyboard = 3\n'):
            with self.subTest(raw=raw):
                self.config.write_text(raw, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'settings table'):
                    document(self.runtime)


if __name__ == '__main__':
    unittest.main()
