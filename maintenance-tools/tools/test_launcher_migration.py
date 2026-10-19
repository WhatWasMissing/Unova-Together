"""Client migration and permanent-entry regression tests. mvq1303."""
from pathlib import Path
import json, os
import tempfile
import unittest
from unittest.mock import patch
import launcher_migration as m


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.home=self.base/'game-home';self.home.mkdir()
        self.entry=self.base/'shared-hub/launcher/Pokemon Together.exe';self.entry.parent.mkdir(parents=True)
        self.entry.write_bytes(b'old hub 1.0.5');(self.entry.parent/'VERSION.txt').write_text('Pokemon Together Launcher 1.0.5\n')
        self.source=self.base/'bootstrap.exe';self.source.write_bytes(b'stable bootstrap fixture')
        self.root=self.release('1.0.9')
        self.save=self.home/'save-backups/keep.sav';self.save.parent.mkdir();self.save.write_bytes(b'saved data')
        self.profile=self.home/'launcher.json';self.profile.write_bytes(b'profile settings')

    def tearDown(self):self.temp.cleanup()

    def release(self, version):
        root=self.home/'.updates/versions'/version/'Unova-Together'
        (root/'builds/current').mkdir(parents=True);(root/'builds/current/melonDS.exe').write_bytes(b'game')
        (root/'builds/current/VERSION.txt').write_text(version)
        (root/'launcher').mkdir();(root/'launcher/Pokemon Together.exe').write_bytes(b'hub '+version.encode())
        (root/'launcher/BUILD_INFO.json').write_text(json.dumps({'schema':1,'product':m.PRODUCT,'version':version}))
        (root/'launcher'/m.BRIDGE).write_bytes(self.source.read_bytes())
        (self.home/'.updates/active.json').write_text(json.dumps({'version':version}))
        return root

    def test_old_exact_shortcut_target_is_replaced_and_backed_up(self):
        old=self.entry.read_bytes();m.migrate(self.home,self.entry,self.source)
        self.assertEqual(self.entry.read_bytes(),self.source.read_bytes())
        backups=list(self.entry.parent.glob('Pokemon Together.before-migration-*.exe'))
        self.assertEqual([p.read_bytes() for p in backups],[old])
        self.assertEqual(self.save.read_bytes(),b'saved data');self.assertEqual(self.profile.read_bytes(),b'profile settings')
        self.assertEqual(m.read(self.home/'.updates'/m.REPORT)['state'],'installed')

    def test_same_shortcut_tracks_two_future_updates_without_repair(self):
        m.migrate(self.home,self.entry,self.source)
        for version in ['1.0.10','1.1.0']:
            root=self.release(version)
            home,selected,target=m.bootstrap_target(self.entry)
            self.assertEqual(home,self.home);self.assertEqual(selected,root)
            self.assertEqual(target,root/'launcher/Pokemon Together.exe')

    def test_repeat_repair_is_idempotent(self):
        m.migrate(self.home,self.entry,self.source);m.migrate(self.home,self.entry,self.source)
        self.assertEqual(len(list(self.entry.parent.glob('*before-migration*.exe'))),1)

    def test_locked_entry_is_left_intact_and_retry_succeeds(self):
        original=m.os.replace
        def locked(source,target):
            if Path(source)==self.entry:raise PermissionError('fixture lock')
            return original(source,target)
        with patch.object(m.os,'replace',side_effect=locked):
            with self.assertRaisesRegex(ValueError,'Close the old launcher'):m.migrate(self.home,self.entry,self.source)
        self.assertEqual(self.entry.read_bytes(),b'old hub 1.0.5')
        self.assertFalse((self.entry.parent/m.SIDECAR).exists())
        self.assertFalse(list(self.entry.parent.glob('.launcher-update-*.exe')))
        m.migrate(self.home,self.entry,self.source)

    def test_failed_replacement_restores_previous_executable_and_metadata(self):
        original=m.os.replace
        def failure(source,target):
            if Path(source).name.startswith('.launcher-update-'):raise OSError('fixture disk failure')
            return original(source,target)
        with patch.object(m.os,'replace',side_effect=failure):
            with self.assertRaises(OSError):m.migrate(self.home,self.entry,self.source)
        self.assertEqual(self.entry.read_bytes(),b'old hub 1.0.5')
        self.assertFalse((self.entry.parent/m.SIDECAR).exists())

    def test_current_update_slot_cannot_be_replaced_with_bootstrap(self):
        with self.assertRaisesRegex(ValueError,'old launcher used by your shortcut'):
            m.migrate(self.home,self.root/'launcher/Pokemon Together.exe',self.source)

    def test_unrelated_executable_is_rejected(self):
        entry=self.base/'other/Pokemon Together.exe';entry.parent.mkdir();entry.write_bytes(b'unrelated')
        with self.assertRaisesRegex(ValueError,'recognised'):m.migrate(self.home,entry,self.source)
        self.assertEqual(entry.read_bytes(),b'unrelated')

    def test_new_default_entry_can_be_created_inside_original_home(self):
        entry=self.home/'launcher/Pokemon Together.exe'
        m.migrate(self.home,entry,self.source)
        self.assertEqual(m.bootstrap_target(entry)[0],self.home)

    def test_register_keeps_original_shortcut_when_running_updated_copy(self):
        m.register_entry(self.home,self.entry,self.root)
        m.register_entry(self.home,self.root/'launcher/Pokemon Together.exe',self.root)
        self.assertEqual(m.read(self.home/'.updates'/m.ENTRY)['entry'],str(self.entry))

    def test_update_schedules_migration_for_original_entry(self):
        m.register_entry(self.home,self.entry,self.root)
        with patch.object(m.subprocess,'Popen') as spawn:m.schedule(self.home,self.root)
        command=spawn.call_args.args[0]
        self.assertIn(str(self.entry),command);self.assertIn(str(self.home),command)
        self.assertIn('--migrate',command)
        self.assertEqual(spawn.call_args.kwargs['env']['PYINSTALLER_RESET_ENVIRONMENT'],'1')

    def test_fresh_portable_install_waits_for_first_update(self):
        m.register_entry(self.home,self.entry,self.root)
        with patch.object(m.subprocess,'Popen') as spawn:m.schedule(self.home,self.home)
        spawn.assert_not_called()

    def test_installer_can_schedule_default_entry_without_prior_record(self):
        with patch.object(m.subprocess,'Popen') as spawn:m.schedule(self.home,self.root,default_entry=True)
        self.assertIn(str(self.home/'launcher/Pokemon Together.exe'),spawn.call_args.args[0])

    def test_repair_rejects_corrupt_build_info_as_validation_error(self):
        info=self.root/'launcher/BUILD_INFO.json'
        for raw in ('[]','{','{"schema":1,"product":"pokemon-together","version":null}','x'*4097):
            info.write_text(raw,encoding='utf-8')
            with self.subTest(info=raw[:24]),self.assertRaisesRegex(ValueError,'metadata'):
                m.active_launcher(self.home)
    def test_repair_lock_rejects_hardlinked_lock_file(self):
        directory=self.home/'.updates';directory.mkdir(exist_ok=True)
        outside=self.base/'external-repair-lock';outside.write_bytes(b'')
        os.link(outside,directory/'launcher-migration.lock')
        with self.assertRaisesRegex(ValueError,'Unsafe launcher repair lock'):
            with m.repair_lock(self.home):pass
        self.assertEqual(outside.read_bytes(),b'')


if __name__=='__main__':unittest.main()
