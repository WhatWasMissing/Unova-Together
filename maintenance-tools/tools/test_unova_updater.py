"""Disposable update transactions: no GitHub requests or user files."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
import zipfile
import unova_updater as u

class UpdaterTests(unittest.TestCase):
    def test_full_release_preferred_to_newer_preview(self):
        def release(label, prerelease):
            base=f'https://github.com/{u.REPO}/releases/download/v{label}/'
            names=[f'Unova-Together-{label}-Windows-x64.zip',f'SHA256SUMS-Unova-Together-{label}.txt']
            return {'tag_name':'v'+label,'published_at':'2026-10-11','prerelease':prerelease,
                    'assets':[{'name':n,'size':100,'browser_download_url':base+n} for n in names]}
        self.assertEqual(u.select_latest([release('1.0.0',False),release('1.1.0',True)])['version'],'1.0.0')
        self.assertEqual(u.select_latest([release('0.4.0',True)])['version'],'0.4.0')

    def test_news_is_plain_bounded_and_official(self):
        raw=[{'tag_name':'v0.3.5','name':'Title\x00','body':'x'*20000,'published_at':'2026-10-08',
              'html_url':'https://evil.test'}, {'tag_name':'v0.3.6','draft':True,'published_at':'2026-10-08'}]
        news=u.release_news(raw)
        self.assertEqual(len(news),1);self.assertEqual(len(news[0]['body']),16000)
        self.assertEqual(news[0]['title'],'Title')
        self.assertEqual(news[0]['url'],f'https://github.com/{u.REPO}/releases/tag/v0.3.5')

    def test_shared_feed_makes_one_request(self):
        label='0.3.5';base=f'https://github.com/{u.REPO}/releases/download/v{label}/'
        names=[f'Unova-Together-{label}-Windows-x64.zip',f'SHA256SUMS-Unova-Together-{label}.txt']
        calls=[]
        raw=[{'tag_name':'v'+label,'published_at':'2026-10-08','body':'Real release notes',
              'assets':[{'name':n,'size':10,'browser_download_url':base+n} for n in names]}]
        def open_feed(url):calls.append(url);return io.BytesIO(json.dumps(raw).encode())
        feed=u.launcher_feed(open_feed)
        self.assertEqual(calls,[u.API]);self.assertEqual(feed['release']['version'],label)
        self.assertEqual(feed['news'][0]['body'],'Real release notes')
    def bundle(self, names=None):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            for name,data in (names or {
                'Unova-Together/builds/current/melonDS.exe':b'fixture executable',
                'Unova-Together/builds/current/VERSION.txt':b'Unova Together 0.3.5',
                'Unova-Together/builds/current/melonDS.toml':b'packaged settings',
            }).items():z.writestr(name,data)
        return out.getvalue()

    def test_versions_and_official_urls(self):
        self.assertEqual(u.version('v0.3.5'),(0,3,5))
        for bad in ('../0.3.5','0.3','0.3.5-x','0.3.5/','-1.3.5'):
            with self.assertRaises(ValueError):u.version(bad)
        for bad in ('http://github.com/WhatWasMissing/Unova-Together/releases/download/v0.3.5/a',
                    'https://evil.test/a','https://github.com/other/repo/releases/download/v0.3.5/a',
                    'https://user@github.com/WhatWasMissing/Unova-Together/releases/download/a',
                    'https://github.com:443/WhatWasMissing/Unova-Together/releases/download/a'):
            with self.assertRaises(ValueError):u.asset_url(bad)

    def test_latest_published_beta_not_draft_or_source_only(self):
        def release(tag,draft=False,complete=True):
            tag_number=tag.lstrip('v');base=f'https://github.com/{u.REPO}/releases/download/{tag}/'
            names=[f'Unova-Together-{tag_number}-Windows-x64.zip',f'SHA256SUMS-Unova-Together-{tag_number}.txt'] if complete else []
            return {'tag_name':tag,'draft':draft,'published_at':'2026-10-08','prerelease':True,
                    'assets':[{'name':n,'size':100,'browser_download_url':base+n} for n in names]}
        data=[release('v0.3.4'),release('v0.3.5'),release('v0.4.0',True),release('v0.5.0',complete=False)]
        self.assertEqual(u.latest_release(lambda _:io.BytesIO(json.dumps(data).encode()))['version'],'0.3.5')

    def test_ambiguous_checksum_rejected(self):
        line=('0'*64+'  release.zip\n').encode()
        with self.assertRaises(ValueError):u.checksum(line+line,'release.zip')

    def test_archive_rejects_unsafe_paths_and_game_files(self):
        for name in ('../outside','Unova-Together/../../outside','C:/outside',
                     'Unova-Together\\outside','Unova-Together/NUL.txt',
                     'Unova-Together/file.','Unova-Together/rom.nds','Unova-Together/save.sav'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temp:
                raw=self.bundle({name:b'bad'});p=Path(temp)/'a.zip';p.write_bytes(raw)
                with self.assertRaises(ValueError):u.extract_verified(p,Path(temp)/'out',hashlib.sha256(raw).hexdigest())

    def test_checksum_mismatch_extracts_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'a.zip';p.write_bytes(self.bundle());out=Path(temp)/'out'
            with self.assertRaises(ValueError):u.extract_verified(p,out,'0'*64)
            self.assertFalse(out.exists())

    def install_fixture(self, corrupt=False, cancelled=False, wrong_version=False):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp);current=home/'builds/current';current.mkdir(parents=True)
            (current/'melonDS.exe').write_bytes(b'old executable')
            (current/'VERSION.txt').write_text('Unova Together 0.3.4')
            (current/'melonDS.toml').write_text('my controls')
            save=home/'game-files/player.sav';save.parent.mkdir();save.write_bytes(b'private save')
            raw=self.bundle();name='Unova-Together-0.3.5-Windows-x64.zip'
            base=f'https://github.com/{u.REPO}/releases/download/v0.3.5/'
            release={'version':'0.3.6' if wrong_version else '0.3.5','name':name,'size':len(raw),'url':base+name,'sums':base+'SHA256SUMS-Unova-Together-0.3.5.txt'}
            sums=(('0'*64 if corrupt else hashlib.sha256(raw).hexdigest())+'  '+name+'\n').encode()
            opener=lambda url:io.BytesIO(sums if url==release['sums'] else raw)
            cancel=threading.Event()
            if cancelled:cancel.set()
            if corrupt or cancelled or wrong_version:
                with self.assertRaises((ValueError,InterruptedError)):u.install(home,release,cancel,lambda *_:None,opener)
                self.assertFalse((home/'.updates/active.json').exists())
                self.assertEqual(u.active_root(home),home)
            else:
                root=u.install(home,release,cancel,lambda *_:None,opener)
                self.assertEqual(u.local_version(root),(0,3,5))
                self.assertEqual((root/'builds/current/melonDS.toml').read_text(),'my controls')
                self.assertEqual(u.active_root(home),root)
                with self.assertRaises(ValueError):u.install(home,release,cancel,lambda *_:None,opener)
            self.assertEqual(save.read_bytes(),b'private save')
            self.assertEqual((current/'melonDS.exe').read_bytes(),b'old executable')
            self.assertEqual((current/'melonDS.toml').read_text(),'my controls')

    def test_verified_install_preserves_original_and_settings(self):self.install_fixture()
    def test_corrupt_download_rolls_back(self):self.install_fixture(corrupt=True)
    def test_cancel_keeps_current(self):self.install_fixture(cancelled=True)
    def test_archive_version_must_match_release(self):self.install_fixture(wrong_version=True)

    def test_active_version_path_cannot_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp);(home/'.updates').mkdir()
            (home/'.updates/active.json').write_text(json.dumps({'version':'../../../outside'}))
            with self.assertRaises(ValueError):u.active_root(home)

if __name__=='__main__':unittest.main()
