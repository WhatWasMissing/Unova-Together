"""Disposable settings/code checks. Never modifies user ROMs or saves."""
from pathlib import Path
import tempfile, unittest
from unittest.mock import patch
import tomlkit
from launcher_ui import preferences as p

class PreferencesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.home=Path(self.temp.name)
        self.runtime=self.home/'runtime';self.runtime.mkdir()
        self.config=self.runtime/'melonDS.toml'
        self.original='# custom controls\n[Instance0]\nEnableCheats = false\n[Instance0.Audio]\nVolume = 128\n[Instance0.Keys]\nA = 99\n'
        self.config.write_text(self.original)
        self.rom=self.home/'reviewed.nds';self.rom.write_bytes(b'fixture')
        self.profile={'key':'fixture','digest':'reviewed','profile':'Test'}
        self.guard=patch.object(p,'running',return_value=False);self.guard.start()
    def tearDown(self):self.guard.stop();self.temp.cleanup()
    def apply(self,settings=None,codes=None):
        with patch.object(p,'identify',return_value=self.profile):
            p.apply(self.runtime,self.rom,settings or {},codes or {},self.profile,self.home)
    def test_settings_preserve_controls_comments_and_backup(self):
        self.apply({'volume':50,'pause':False,'filter':False})
        text=self.config.read_text();doc=tomlkit.parse(text)
        self.assertIn('# custom controls',text);self.assertEqual(doc['Instance0']['Keys']['A'],99)
        self.assertEqual(doc['Instance0']['Audio']['Volume'],128);self.assertFalse(doc['Screen']['Filter'])
        self.assertEqual(self.config.with_name('melonDS.toml.before-launcher-settings').read_text(),self.original)
    def test_no_choices_does_not_modify_config(self):
        self.apply();self.assertEqual(self.config.read_text(),self.original)
    def test_codes_on_off_preserve_user_file(self):
        original='ROOT\nCODE 1 User code\nD2000000 00000000\n'
        self.rom.with_suffix('.mch').write_text(original)
        self.apply(codes={'money':True})
        path=self.home/'.launcher-cheats/fixture/reviewed.mch'
        self.assertIn('CODE 1 Max money',path.read_text());self.assertIn('CODE 0 Refill repel',path.read_text())
        self.apply(codes={'money':False})
        self.assertIn('CODE 0 Max money',path.read_text());self.assertEqual(path.read_text().count(p.MARKER),1)
        self.assertIn(original.rstrip(),path.read_text());self.assertEqual(self.rom.with_suffix('.mch').read_text(),original)
        self.assertFalse(tomlkit.parse(self.config.read_text())['Instance0']['EnableCheats'])
    def test_unsupported_profile_and_running_fail_without_writes(self):
        with patch.object(p,'identify',return_value=None),self.assertRaises(ValueError):
            p.apply(self.runtime,self.rom,{}, {'money':True},self.profile,self.home)
        self.assertEqual(self.config.read_text(),self.original)
        with patch.object(p,'running',return_value=True),self.assertRaises(ValueError):self.apply({'pause':True})
        self.assertEqual(self.config.read_text(),self.original)
    def test_invalid_toml_and_bad_volume_fail_without_writes(self):
        self.config.write_text('not valid TOML')
        with self.assertRaises(Exception):self.apply({'volume':50})
        self.assertEqual(self.config.read_text(),'not valid TOML')
        self.config.write_text(self.original)
        with self.assertRaises(ValueError):self.apply({'volume':200})
        self.assertEqual(self.config.read_text(),self.original)
    def test_incomplete_managed_category_rejected(self):
        with self.assertRaises(ValueError):p.managed_codes('CAT 0 '+p.MARKER+'\nCODE 1 Edited\n',{})
    def test_unknown_rom_not_accepted_by_filename(self):
        self.assertIsNone(p.identify(self.rom));self.assertIsNone(p.identify(self.home/'missing.nds'))

if __name__=='__main__':unittest.main()
