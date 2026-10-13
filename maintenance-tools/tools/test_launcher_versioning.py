"""Regression checks for launcher build identity and update handoff. mvq1303."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from launcher_ui import versioning as v
from launcher_ui.app import Launcher
import unova_launcher


class VersioningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.hub = self.root/'launcher/Pokemon Together.exe'
        self.hub.parent.mkdir()
        self.hub.write_bytes(b'launcher fixture')
        self.home = self.root/'persistent-home'
        self.current = patch.object(v, 'current_version', return_value='1.0.8')
        self.current.start()

    def tearDown(self):
        self.current.stop()
        self.temp.cleanup()

    def info(self, version='1.0.8', product=v.PRODUCT):
        (self.hub.parent/'BUILD_INFO.json').write_text(json.dumps({'schema':1,'product':product,'version':version}))

    def test_updated_hub_is_selected_on_restart_with_same_save_home(self):
        self.info('1.0.9')
        app = type('Fixture', (), {'root':self.root,'home':self.home,'_save':lambda s:None,'destroy':lambda s:None})()
        with patch('sys.frozen', True, create=True), patch('sys.executable', str(self.root/'old.exe')), patch('launcher_ui.app.subprocess.Popen') as spawn:
            Launcher._restart_updated_launcher(app)
        self.assertEqual(spawn.call_args.args[0], [str(self.hub), '--home', str(self.home)])
        self.assertEqual(spawn.call_args.kwargs['env']['PYINSTALLER_RESET_ENVIRONMENT'], '1')

    def test_cold_start_handoff_preserves_arguments_and_home(self):
        self.info('1.0.9')
        with patch('sys.frozen', True, create=True), patch('sys.executable', str(self.root/'old.exe')), patch('unova_launcher.subprocess.Popen') as spawn:
            self.assertTrue(unova_launcher.handoff_updated_launcher(self.home,self.root,['--self-test','report.json']))
        self.assertEqual(spawn.call_args.args[0], [str(self.hub),'--self-test','report.json','--home',str(self.home)])

    def test_cold_start_does_not_loop_on_equal_or_older_versions(self):
        with patch('sys.frozen', True, create=True), patch('unova_launcher.subprocess.Popen') as spawn:
            for version in ('1.0.8','1.0.7'):
                self.info(version)
                self.assertFalse(unova_launcher.handoff_updated_launcher(self.home,self.root,[]))
            spawn.assert_not_called()

    def test_running_target_does_not_delegate_to_itself(self):
        self.info('1.0.9')
        with patch('sys.frozen',True,create=True),patch('sys.executable',str(self.hub)):
            self.assertIsNone(v.updated_launcher(self.root,newer_only=True))

    def test_legacy_or_malformed_metadata_cannot_replace_the_hub(self):
        self.assertIsNone(v.updated_launcher(self.root))
        for version, product in [('1.0.9','unova-legacy'),('bad',v.PRODUCT)]:
            self.info(version,product)
            self.assertIsNone(v.updated_launcher(self.root))
        (self.hub.parent/'BUILD_INFO.json').write_text('[]')
        self.assertIsNone(v.updated_launcher(self.root))

    def test_no_downgrade_after_old_mod_repair(self):
        self.info('1.0.7')
        old = self.root/'existing-hub.exe'
        with patch('sys.frozen',True,create=True),patch('sys.executable',str(old)):
            self.assertEqual(v.restart_executable(self.root),old)

    def test_equal_version_can_restart_into_another_installed_copy(self):
        self.info()
        self.assertEqual(v.restart_executable(self.root),self.hub)

    def test_missing_executable_is_ignored(self):
        self.info('1.0.9');self.hub.unlink()
        self.assertIsNone(v.updated_launcher(self.root))

    def test_failed_handoff_keeps_current_launcher_available(self):
        self.info('1.0.9')
        with patch('sys.frozen',True,create=True),patch('unova_launcher.subprocess.Popen',side_effect=OSError('locked')):
            self.assertFalse(unova_launcher.handoff_updated_launcher(self.home,self.root,[]))

    def test_ui_version_belongs_to_running_build_not_mod_launcher(self):
        self.info('9.0.0')
        runtime=self.root/'builds/current';runtime.mkdir(parents=True)
        (runtime/'VERSION.txt').write_text('Unova Together 1.0.9')
        app=type('Fixture',(),{'root':self.root})()
        self.assertEqual(Launcher._version_text(app),'Release 1.0.9 · Launcher 1.0.8')

    def test_windows_resource_uses_requested_build_version(self):
        output=self.root/'version.txt'
        v.write_windows_version(Path(v.__file__).parent/'windows-version.txt',output,'2.3.4')
        text=output.read_text()
        self.assertIn('filevers=(2, 3, 4, 0)',text)
        self.assertIn('prodvers=(2, 3, 4, 0)',text)
        self.assertIn("StringStruct('FileVersion', '2.3.4')",text)
        self.assertIn("StringStruct('ProductVersion', '2.3.4')",text)

    def test_portable_home_is_its_own_installation(self):
        self.assertEqual(unova_launcher.installation_home(self.hub),self.root)
        self.assertEqual(unova_launcher.installation_home(self.hub,self.home),self.home)


if __name__=='__main__':unittest.main()
