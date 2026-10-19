"""Storage retention, ownership, rollback and user-data safety on disposable installs."""
from pathlib import Path
import json, os, subprocess, tempfile, unittest
from unittest.mock import patch
import unova_storage as s
import unova_updater as u

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.home=Path(self.temp.name)/'home';self.base=self.home/'.updates/versions';self.base.mkdir(parents=True)
    def tearDown(self):self.temp.cleanup()
    def test_process_detection_includes_shared_launcher_and_bootstrap(self):
        path=self.base/'1.0.1/Unova-Together/launcher/Pokemon Together.exe'
        response=subprocess.CompletedProcess([],0,json.dumps({'Name':'Pokemon Together.exe','ExecutablePath':str(path)}),'')
        with patch.object(s.os,'name','nt'),patch.object(s.subprocess,'run',return_value=response) as run:
            detected=s.running_paths()
        self.assertIn(path.resolve(),detected)
        command=run.call_args.args[0][-1]
        for name in ('Pokemon Together.exe','Pokemon Together Bootstrap.exe','Repair-Launcher.exe'):
            self.assertIn(name,command)
    def slot(self,name,receipt=True):
        root=self.base/name/'Unova-Together';(root/'builds/current').mkdir(parents=True);(root/'launcher').mkdir()
        for name,data in {'builds/current/melonDS.exe':b'game','builds/current/shared.dll':b'identical library','builds/current/VERSION.txt':name.split('-')[0].encode(),'builds/current/melonDS.toml':b'# user config','launcher/Unova Together.exe':b'launcher sentinel','launcher/python.dll':b'identical Python','README.md':b'packaged readme'}.items():(root/name).write_bytes(data)
        u.record_integrity(root)
        if receipt:s.record_package(root)
        return root
    def active(self,slot):s.atomic(self.home/'.updates/active.json',{'version':slot.split('-')[0],'slot':slot})
    def test_retention_preserves_saves_modified_and_unknown_files(self):
        old=self.slot('1.0.1');previous=self.slot('1.0.2');active=self.slot('1.0.3');self.active('1.0.3');s.remember_previous(self.home,previous,'1.0.3')
        for name in ('Redux.save','Redux.sav','Redux.2.dsv','Redux.ml8','my-picture.png','README.md'):(old/name).write_bytes(b'user data')
        backup=self.home/'save-backups/save.zip';backup.parent.mkdir();backup.write_bytes(b'backup')
        report=s.cleanup(self.home,processes=[])
        self.assertEqual(report['keptSlots'],['1.0.2','1.0.3']);self.assertEqual(report['prunedSlots'],['1.0.1'])
        self.assertFalse((old/'builds/current/melonDS.exe').exists());self.assertTrue((old/'launcher/Unova Together.exe').exists())
        for name in ('Redux.save','Redux.sav','Redux.2.dsv','Redux.ml8','my-picture.png','README.md'):self.assertEqual((old/name).read_bytes(),b'user data')
        self.assertEqual(backup.read_bytes(),b'backup');self.assertTrue((active/'builds/current/melonDS.exe').exists());self.assertTrue((previous/'builds/current/melonDS.exe').exists())
        self.assertEqual(s.cleanup(self.home,processes=[])['removedFiles'],0)
    def test_cleanup_reports_progress_and_absolute_deleted_paths(self):
        old=self.slot('1.0.1');previous=self.slot('1.0.2');self.slot('1.0.3');self.active('1.0.3');s.remember_previous(self.home,previous,'1.0.3')
        events=[];report=s.cleanup(self.home,processes=[],progress=events.append)
        start=next(event for event in events if event.get('phase')=='delete' and event.get('stage')=='start')
        deleted=[event for event in events if event.get('phase')=='delete' and event.get('stage')=='deleted']
        self.assertEqual(start['total'],report['removedFiles']);self.assertEqual(len(deleted),report['removedFiles'])
        self.assertTrue(deleted);self.assertTrue(all(Path(event['path']).is_absolute() for event in deleted))
        self.assertTrue(all(event['path'].startswith(str(old)) for event in deleted))
        self.assertEqual(events[-1]['stage'],'complete')
    def test_legacy_removes_only_verified_files_and_duplicate_launcher_binaries(self):
        old=self.slot('1.0.1',False);self.slot('1.0.2');self.slot('1.0.3');self.active('1.0.3')
        (old/'builds/current/user.dll').write_bytes(b'custom DLL');(old/'builds/current/shared.dll').write_bytes(b'modified DLL')
        report=s.cleanup(self.home,processes=[])
        self.assertIn('1.0.1',report['prunedSlots']);self.assertEqual((old/'builds/current/shared.dll').read_bytes(),b'modified DLL');self.assertEqual((old/'builds/current/user.dll').read_bytes(),b'custom DLL')
        self.assertFalse((old/'launcher/python.dll').exists());self.assertTrue((old/'README.md').exists())
    def test_running_old_build_is_protected(self):
        old=self.slot('1.0.1');self.slot('1.0.2');self.slot('1.0.3');self.active('1.0.3')
        report=s.cleanup(self.home,processes=[old/'launcher/Unova Together.exe'])
        self.assertIn('1.0.1',report['keptSlots']);self.assertTrue((old/'builds/current/melonDS.exe').exists())
    def test_unrecognised_build_is_not_deleted(self):
        old=self.slot('1.0.1');(old/s.RECEIPT).unlink();(old/'.launcher-integrity.json').unlink();self.slot('1.0.2');self.slot('1.0.3');self.active('1.0.3')
        self.assertTrue(s.cleanup(self.home,processes=[])['skipped']);self.assertTrue((old/'builds/current/melonDS.exe').exists())
    def test_process_check_failure_prevents_all_cleanup(self):
        old=self.slot('1.0.1');self.slot('1.0.2');self.slot('1.0.3');self.active('1.0.3')
        with patch.object(s,'running_paths',side_effect=OSError('cannot inspect')):
            with self.assertRaises(OSError):s.cleanup(self.home)
        self.assertTrue((old/'builds/current/melonDS.exe').exists())
    def test_manifest_traversal_cannot_delete_outside_slot(self):
        old=self.slot('1.0.1');self.slot('1.0.2');self.slot('1.0.3');self.active('1.0.3');outside=self.home/'outside.dll';outside.write_bytes(b'external')
        s.atomic(old/s.RECEIPT,{'schema':1,'files':{'../../../outside.dll':s.digest(outside),str(outside):s.digest(outside)}})
        s.cleanup(self.home,processes=[]);self.assertEqual(outside.read_bytes(),b'external')
    def test_integrity_record_rejects_hardlinked_pending_path(self):
        root=self.home/'integrity-test';runtime=root/'builds/current';runtime.mkdir(parents=True)
        (runtime/'melonDS.exe').write_bytes(b'launcher runtime')
        outside=self.home/'keep-integrity-sentinel.bin';outside.write_bytes(b'preserve this file')
        pending=root/'.launcher-integrity.pending'
        try:pending.hardlink_to(outside)
        except (NotImplementedError,OSError) as exc:self.skipTest(f'hard links unavailable: {exc}')
        u.record_integrity(root)
        self.assertEqual(outside.read_bytes(),b'preserve this file');self.assertTrue(pending.exists())
        self.assertTrue((root/'.launcher-integrity.json').is_file())
    def test_junction_outside_installation_is_never_followed(self):
        old=self.slot('1.0.1');self.slot('1.0.2');self.slot('1.0.3');self.active('1.0.3');outside=self.home/'outside';outside.mkdir();victim=outside/'victim.dll';victim.write_bytes(b'external')
        link=old/'linked'
        if os.name=='nt':
            def quote(value):return "'"+str(value).replace("'","''")+"'"
            result=subprocess.run(['powershell.exe','-NoProfile','-Command',f'New-Item -ItemType Junction -Path {quote(link)} -Target {quote(outside)} | Out-Null'],capture_output=True)
            self.assertEqual(result.returncode,0)
        else:link.symlink_to(outside,target_is_directory=True)
        s.atomic(old/s.RECEIPT,{'schema':1,'files':{'linked/victim.dll':s.digest(victim)}})
        s.cleanup(self.home,processes=[]);self.assertEqual(victim.read_bytes(),b'external')
    def test_unchanged_binaries_shared_but_config_and_changed_files_not_shared(self):
        old=self.slot('1.0.1');new=self.slot('1.0.2');(new/'builds/current/melonDS.exe').write_bytes(b'new game')
        freed=s.share_binaries(new,old)
        self.assertGreater(freed,0);self.assertTrue((old/'builds/current/shared.dll').samefile(new/'builds/current/shared.dll'))
        self.assertFalse((old/'builds/current/melonDS.exe').samefile(new/'builds/current/melonDS.exe'));self.assertFalse((old/'builds/current/melonDS.toml').samefile(new/'builds/current/melonDS.toml'))
    def test_unsupported_hardlinks_leave_original_copy(self):
        old=self.slot('1.0.1');new=self.slot('1.0.2')
        with patch.object(s.os,'link',side_effect=OSError('unsupported')):self.assertEqual(s.share_binaries(new,old),0)
        self.assertEqual((new/'builds/current/shared.dll').read_bytes(),b'identical library');self.assertFalse(list(new.rglob('*.share-pending')))

if __name__=='__main__':unittest.main()
