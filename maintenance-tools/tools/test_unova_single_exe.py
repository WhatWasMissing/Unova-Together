"""Test persistent single-EXE extraction with tiny disposable payloads."""
from pathlib import Path
import hashlib, json, tempfile, unittest, zipfile
from unova_single_exe import install_bundle
import unova_updater as updates

class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.home=self.base/'home'
        self.archive=self.base/'runtime.zip'
        self.metadata=self.bundle('0.3.5')
    def tearDown(self):self.temp.cleanup()
    def bundle(self,version,unsafe=False,revision=0):
        with zipfile.ZipFile(self.archive,'w') as z:
            z.writestr('Unova-Together/builds/current/melonDS.exe',b'game')
            z.writestr('Unova-Together/builds/current/VERSION.txt',version)
            z.writestr('Unova-Together/launcher/Unova Together.exe',b'launcher')
            z.writestr('Unova-Together/launcher/BUILD_REVISION.txt',str(revision))
            if unsafe:z.writestr('Unova-Together/private.sav',b'private')
        return {'version':version,'sha256':hashlib.sha256(self.archive.read_bytes()).hexdigest(),'launcher_revision':revision}
    def test_same_version_repair_cannot_pin_old_launcher_or_downgrade_revision(self):
        old=install_bundle(self.home,self.archive,self.metadata)
        (old/'builds/current/melonDS.toml').write_text('# existing controls')
        marker=self.home/'.updates/active.json'
        active=json.loads(marker.read_text());active['slot']='0.3.5-repair-aaaaaaaaaaaa'
        repaired=self.home/'.updates/versions'/active['slot']
        import shutil
        shutil.copytree(old.parent,repaired);marker.write_text(json.dumps(active))
        new=install_bundle(self.home,self.archive,self.bundle('0.3.5',revision=2))
        self.assertNotEqual(new,repaired/'Unova-Together')
        self.assertEqual((new/'builds/current/melonDS.toml').read_text(),'# existing controls')
        self.assertEqual(install_bundle(self.home,self.archive,self.bundle('0.3.5',revision=1)),new)
    def test_first_install_and_second_run_preserve_config_backups(self):
        root=install_bundle(self.home,self.archive,self.metadata)
        config=root/'builds/current/melonDS.toml';config.write_text('# user settings\n')
        backup=self.home/'save-backups/user.zip';backup.parent.mkdir();backup.write_bytes(b'save backup')
        self.assertEqual(install_bundle(self.home,self.archive,self.metadata),root)
        self.assertEqual(config.read_text(),'# user settings\n');self.assertEqual(backup.read_bytes(),b'save backup')
    def test_new_bundled_version_keeps_config_and_old_runtime(self):
        old=install_bundle(self.home,self.archive,self.metadata);(old/'builds/current/melonDS.toml').write_text('# user controls')
        new=install_bundle(self.home,self.archive,self.bundle('0.3.6'))
        self.assertNotEqual(new,old);self.assertTrue(old.exists());self.assertEqual((new/'builds/current/melonDS.toml').read_text(),'# user controls')
    def test_newer_github_update_is_not_downgraded(self):
        install_bundle(self.home,self.archive,self.metadata)
        newer=self.home/'.updates/versions/0.3.7/Unova-Together';(newer/'builds/current').mkdir(parents=True)
        (newer/'builds/current/melonDS.exe').write_bytes(b'newer');(newer/'builds/current/VERSION.txt').write_text('0.3.7')
        (self.home/'.updates/active.json').write_text('{"version":"0.3.7"}')
        self.assertEqual(install_bundle(self.home,self.archive,self.metadata),newer)
        old_slot=self.home/'.updates/versions'/('0.3.5-repair-'+self.metadata['sha256'][:12])
        import shutil
        self.assertTrue(old_slot.resolve().is_relative_to(self.home.resolve()))
        shutil.rmtree(old_slot)
        self.assertEqual(install_bundle(self.home,self.archive,self.metadata),newer)
        self.assertFalse(old_slot.exists(),'An older EXE must not recreate an unused installation.')
    def test_bad_checksum_and_private_payload_never_activate(self):
        bad=dict(self.metadata);bad['sha256']='0'*64
        with self.assertRaises(ValueError):install_bundle(self.home,self.archive,bad)
        self.assertFalse((self.home/'.updates/active.json').exists())
        with self.assertRaises(ValueError):install_bundle(self.home,self.archive,self.bundle('0.3.5',unsafe=True))
        self.assertFalse((self.home/'.updates/active.json').exists())
    def test_mismatched_version_does_not_activate(self):
        metadata=dict(self.metadata);metadata['version']='0.3.9'
        with self.assertRaises(ValueError):install_bundle(self.home,self.archive,metadata)
        self.assertFalse((self.home/'.updates/active.json').exists())

if __name__=='__main__':unittest.main()

