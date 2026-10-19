"""Disposable profile saves, connectivity, repair and diagnostic checks."""
from pathlib import Path
import hashlib, io, json, tempfile, threading, unittest, zipfile
from unittest.mock import patch
from launcher_ui import services as s
import unova_updater as u


class ServiceTests(unittest.TestCase):
    def test_companion_preference_preserves_explicit_choices_and_rejects_removed_options(self):
        item=s.profile();self.assertNotIn('companion_interactions',item['preferences'])
        self.assertNotIn('removed_option',item['preferences'])
        item['preferences']={'companion_interactions':True,'reduced_follower_motion':True,'removed_option':False}
        self.assertEqual(s.normalize(item)['preferences'],{'companion_interactions':True,'reduced_follower_motion':True})
        item['preferences']={'companion_interactions':False}
        self.assertEqual(s.normalize(item)['preferences'],{'companion_interactions':False})
        item['preferences']={'companion_interactions':'true','removed_option':1}
        self.assertEqual(s.normalize(item)['preferences'],{})

    def test_lobby_capacity_defaults_and_bounds(self):
        item=s.profile();self.assertEqual(item['lan_slots'],16)
        for value,expected in [(2,2),(16,16),(99,16),(-1,2),('8',8),('bad',16)]:
            self.assertEqual(s.normalize({**item,'lan_slots':value})['lan_slots'],expected)

    def test_guides_refresh_and_offline_cache(self):
        class Response:
            def __init__(self,url,data):self.url=url;self.data=data
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def geturl(self):return self.url
            def read(self,n):return self.data[:n]
        commit='a'*40
        guide_dir=self.home/'.updates/guides';guide_dir.mkdir(parents=True)
        outside=self.home/'keep-guide-data.bin';outside.write_bytes(b'keep this data')
        marker_pending=guide_dir/'active.pending';marker_pending.hardlink_to(outside)
        def response(request,timeout):
            if 'api.github.com' in request.full_url:
                self.assertTrue(request.full_url.endswith('/git/ref/heads/main'))
                data=json.dumps({'object':{'type':'commit','sha':commit}}).encode()
            else:data=b'# Updated guide\n'
            return Response(request.full_url,data)
        with patch.object(s.urllib.request,'urlopen',side_effect=response) as fetch:
            self.assertEqual(s.refresh_guides(self.home),commit);self.assertEqual(fetch.call_count,1+len(s.GUIDES))
            s.refresh_guides(self.home);self.assertEqual(fetch.call_count,2+len(s.GUIDES))
        self.assertEqual(outside.read_bytes(),b'keep this data');self.assertTrue(marker_pending.exists())
        guide_pending=guide_dir/'PLAYER_GUIDE.pending';guide_pending.hardlink_to(outside)
        self.assertEqual(s.cached_guide(self.home,'PLAYER_GUIDE.md').read_text(),'# Updated guide\n')
        self.assertEqual(outside.read_bytes(),b'keep this data');self.assertTrue(guide_pending.exists())
        marker=(self.home/'.updates/guides/active.json').read_bytes()
        with patch.object(s.urllib.request,'urlopen',side_effect=OSError('offline')):
            with self.assertRaises(OSError):s.refresh_guides(self.home)
        self.assertEqual((self.home/'.updates/guides/active.json').read_bytes(),marker)
        with self.assertRaises(ValueError):s.cached_guide(self.home,'../game.exe')
        with patch.object(s.urllib.request,'urlopen',return_value=Response('https://example.com/evil',b'{}')):
            with self.assertRaises(ValueError):s.refresh_guides(self.home)

    def test_check_relay_hosts_only_refused_loopback_and_verifies_protocol(self):
        start=unittest.mock.Mock()
        with patch.object(s,'probe',side_effect=[ValueError('No presence relay is listening'), 'Presence relay reachable']):
            self.assertIn('Local relay started',s.check_relay({'host':'127.0.0.1','room':'test'},start))
        start.assert_called_once_with(8765)
        start.reset_mock()
        for host,message in [('example.com','No presence relay is listening'),('localhost','Wrong protocol')]:
            with patch.object(s,'probe',side_effect=ValueError(message)):
                with self.assertRaises(ValueError):s.check_relay({'host':host,'room':'test'},start)
        start.assert_not_called()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.home=Path(self.temp.name)
        self.runtime=self.home/'builds/current';self.runtime.mkdir(parents=True)
        (self.runtime/'melonDS.exe').write_bytes(b'old');(self.runtime/'VERSION.txt').write_text('0.3.5')
        (self.runtime/'melonDS.toml').write_text('# controls\nLimitFPS = false\n')
        self.rom=self.home/'Black2.nds';self.rom.write_bytes(b'fake ROM')
        self.item=s.profile(str(self.rom));self.save=self.rom.with_suffix('.sav');self.save.write_bytes(b'original save')
    def tearDown(self):self.temp.cleanup()
    def test_backup_restore_and_before_restore_copy(self):
        self.rom.with_suffix('.ml8').write_bytes(b'not a save')
        archive=s.backup(self.home,self.item);self.save.write_bytes(b'new save')
        self.assertEqual(s.restore(self.home,self.item,archive),1);self.assertEqual(self.save.read_bytes(),b'original save')
        others=[p for p in s.backups(self.home,self.item) if p!=archive]
        self.assertEqual(len(others),1)
        with zipfile.ZipFile(others[0]) as z:self.assertEqual(z.read('Black2.sav'),b'new save')
        with zipfile.ZipFile(archive) as z:self.assertNotIn('Black2.ml8',z.namelist())
    def test_profile_separation_and_missing_save(self):
        other=s.profile(str(self.rom),str(self.home/'separate'))
        self.assertIsNone(s.backup(self.home,other));self.assertFalse(s.backups(self.home,other))
        self.assertTrue(s.backup(self.home,self.item));self.assertFalse(s.backups(self.home,other))
    def test_save_extension_instances_and_readable_backup_names(self):
        for name in ('Black2.save','Black2.2.SAVE'): (self.home/name).write_bytes(b'opaque save data')
        (self.home/'Different.save').write_bytes(b'another game')
        self.assertEqual({p.name for p in s.save_files(self.item)},{'Black2.sav','Black2.save','Black2.2.SAVE'})
        archive=s.backup(self.home,self.item)
        self.assertIn('Manual backup',s.backup_label(archive));self.assertIn('UTC',s.backup_label(archive))
        for path in s.save_files(self.item):path.write_bytes(b'changed')
        self.assertEqual(s.restore(self.home,self.item,archive),3)
        self.assertEqual((self.home/'Black2.save').read_bytes(),b'opaque save data')
        self.assertEqual((self.home/'Different.save').read_bytes(),b'another game')
    def test_restore_bad_checksum_and_wrong_profile_leave_save(self):
        archive=s.backup(self.home,self.item)
        other=s.profile(str(self.rom));
        with self.assertRaises(ValueError):s.restore(self.home,other,archive)
        with zipfile.ZipFile(archive) as z:manifest=json.loads(z.read('manifest.json'))
        manifest['files'][0]['sha256']='bad'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('Black2.sav',b'evil');z.writestr('manifest.json',json.dumps(manifest))
        with self.assertRaises(ValueError):s.restore(self.home,self.item,archive)
        self.assertEqual(self.save.read_bytes(),b'original save')
    def test_restore_does_not_follow_preexisting_hardlinked_staging_path(self):
        archive=s.backup(self.home,self.item)
        self.save.write_bytes(b'current save')
        outside=self.home/'keep-this-file.bin';outside.write_bytes(b'outside data')
        staging=self.save.with_name(self.save.name+'.restore-pending')
        try:staging.hardlink_to(outside)
        except (NotImplementedError,OSError) as exc:self.skipTest(f'hard links unavailable: {exc}')

        self.assertEqual(s.restore(self.home,self.item,archive),1)

        self.assertEqual(outside.read_bytes(),b'outside data')
        self.assertEqual(self.save.read_bytes(),b'original save')
        self.assertEqual(staging.read_bytes(),b'outside data')
    def test_restore_keeps_unowned_hardlinked_unique_staging_collision(self):
        archive=s.backup(self.home,self.item)
        outside=self.home/'keep-this-file.bin';outside.write_bytes(b'outside data')
        token='a'*32
        staging=self.save.with_name(self.save.name+'.'+token+'.launcher-pending')
        try:staging.hardlink_to(outside)
        except (NotImplementedError,OSError) as exc:self.skipTest(f'hard links unavailable: {exc}')
        with patch.object(s.prefs.uuid,'uuid4',return_value=type('Token',(),{'hex':token})()):
            with self.assertRaises(FileExistsError):s.restore(self.home,self.item,archive)
        self.assertEqual(outside.read_bytes(),b'outside data')
        self.assertTrue(staging.exists())
    def test_launch_checks_real_limitations(self):
        messages=s.checks(self.home,self.item)
        self.assertTrue(any('Frame limit' in m for m in messages));self.assertTrue(any('C-Gear' in m and 'cannot' in m for m in messages))
        self.assertTrue(any('Partner' in m or 'PARTNER' in m for m in messages))
        (self.runtime/'melonDS.exe').unlink();self.assertTrue(any(m.startswith('BLOCK:') for m in s.checks(self.home,self.item)))
    def test_network_validation_and_protocol_probe(self):
        for values in ({'host':'https://bad','room':'good'},{'host':'localhost','port':99999,'room':'good'},{'host':'localhost','room':'bad room'}):
            with self.assertRaises(ValueError):s.network(values)
        class Connection:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def settimeout(self,t):pass
            def sendall(self,data):self.data=json.loads(data)
            def recv(self,n):return b'{"type":"welcome","version":1}\n'
        with patch.object(s.socket,'create_connection',return_value=Connection()):
            self.assertIn('reachable',s.probe({'host':'localhost','room':'test'}))
    def test_diagnostic_export_excludes_game_data_and_redacts(self):
        logs=self.home/'transfer';logs.mkdir()
        (logs/'bridge.log').write_text('token=private-token\n{"access_key":"secret-key"}\n127.0.0.1 C:\\Users\\Private\\game.nds')
        (logs/'private.ramdump').write_bytes(b'private RAM')
        separate=self.home/'installed';separate.mkdir()
        output=self.home/'diagnostics.zip';s.diagnostics(separate,output,self.home)
        with zipfile.ZipFile(output) as z:
            self.assertIn('logs/1.log',z.namelist())
            contents=''.join(z.read(i).decode() for i in z.namelist())
            self.assertNotIn('private-token',contents);self.assertNotIn('secret-key',contents);self.assertNotIn('127.0.0.1',contents);self.assertNotIn('Private',contents)
            self.assertTrue(all(Path(n).suffix not in ('.sav','.nds','.ramdump') for n in z.namelist()))
    def test_diagnostic_export_preserves_preexisting_pending_file(self):
        separate=self.home/'installed';separate.mkdir()
        output=self.home/'diagnostics.zip';outside=self.home/'keep-this-file.bin';outside.write_bytes(b'outside data')
        pending=output.with_name(output.name+'.pending');pending.hardlink_to(outside)

        self.assertEqual(s.diagnostics(separate,output,self.home),output)

        self.assertEqual(outside.read_bytes(),b'outside data');self.assertTrue(pending.exists())
        with zipfile.ZipFile(output) as bundle:self.assertIn('summary.json',bundle.namelist())
    def test_same_version_repair_is_verified_and_keeps_old_runtime(self):
        current_launcher=self.home/'launcher';current_launcher.mkdir();(current_launcher/'local.txt').write_text('current launcher')
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as z:
            z.writestr('Unova-Together/builds/current/melonDS.exe',b'repaired')
            z.writestr('Unova-Together/builds/current/VERSION.txt','0.3.5')
        raw=data.getvalue();name='Unova-Together-0.3.5-Windows-x64.zip';base=f'https://github.com/{u.REPO}/releases/download/v0.3.5/'
        release={'version':'0.3.5','name':name,'size':len(raw),'url':base+name,'sums':base+'sums.txt','_repair':True}
        sums=(hashlib.sha256(raw).hexdigest()+'  '+name+'\n').encode()
        repaired=u.install(self.home,release,threading.Event(),lambda *_:None,lambda url:io.BytesIO(sums if url==release['sums'] else raw))
        self.assertEqual((repaired/'builds/current/melonDS.exe').read_bytes(),b'repaired')
        self.assertEqual((self.runtime/'melonDS.exe').read_bytes(),b'old');self.assertEqual(self.save.read_bytes(),b'original save')
        self.assertEqual((repaired/'launcher/local.txt').read_text(),'current launcher')
        self.assertEqual(u.active_root(self.home),repaired)
    def test_integrity_finds_changed_and_missing_files(self):
        u.record_integrity(self.home);self.assertIn('Verified',s.integrity(self.home))
        (self.runtime/'melonDS.exe').write_bytes(b'changed');self.assertIn('changed files',s.integrity(self.home))
        (self.runtime/'melonDS.exe').unlink();self.assertIn('melonDS.exe',s.integrity(self.home))

    def test_missing_active_runtime_still_allows_launcher_repair(self):
        directory=self.home/'.updates';directory.mkdir();(directory/'active.json').write_text('{"version":"0.3.5"}')
        with self.assertRaises(ValueError):u.active_root(self.home)
        self.assertEqual(u.installed_version(self.home),(0,3,5))
        self.assertEqual(u.active_root(self.home,allow_missing=True),self.home/'.updates/versions/0.3.5/Unova-Together')

    def test_bad_repair_marker_rejected(self):
        directory=self.home/'.updates';directory.mkdir();(directory/'active.json').write_text('{"version":"0.3.5","slot":"../../escape"}')
        with self.assertRaises(ValueError):u.active_root(self.home)

if __name__=='__main__':unittest.main()
