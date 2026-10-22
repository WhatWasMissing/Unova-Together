"""Patch-note directory and launcher feed checks; uses no UI dependencies."""
from pathlib import Path
import io
import json
import re
import unittest

import unova_updater as updater


class PatchNotesFeedTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.index = json.loads((self.root / 'patchnotes/index.json').read_text(encoding='utf-8'))
        version_text = (self.root / 'VERSION.txt').read_text(encoding='utf-8')
        self.latest_version = re.search(r'\d+\.\d+\.\d+', version_text).group(0)

    def test_repository_index_lists_every_note_in_new_folder(self):
        notes = updater.patch_note_news(self.index['notes'])
        self.assertEqual(len(notes), len(self.index['notes']))
        note_versions = {note['version'] for note in notes}
        self.assertIn(self.latest_version, note_versions)
        self.assertEqual(
            [note['version'] for note in notes],
            sorted(note_versions, key=updater.version, reverse=True),
        )
        self.assertEqual(notes[-1]['version'], '0.3.5')
        disk_versions = {
            match.group(1)
            for path in (self.root / 'patchnotes').glob('RELEASE_NOTES_*.md')
            if (match := re.fullmatch(r'RELEASE_NOTES_(\d+\.\d+\.\d+)\.md', path.name))
        }
        self.assertEqual({note['version'] for note in notes}, disk_versions)
        for item in notes:
            self.assertTrue((self.root / 'patchnotes' / item['file']).is_file())
            self.assertIn('/blob/main/patchnotes/' + item['file'], item['url'])

        # Notes left out of the index disappear from the launcher even though
        # the Markdown file exists in GitHub. Keep the generated index complete.
        self.assertIn('1.0.23', {note['version'] for note in notes})
        readme = (self.root / 'patchnotes/README.md').read_text(encoding='utf-8')
        self.assertTrue(all(item['file'] in readme for item in notes))

        bundled = json.loads((self.root / 'launcher-source/tools/launcher_ui/assets/news.json').read_text(encoding='utf-8'))
        self.assertEqual({note['version'] for note in updater.patch_note_news(bundled['notes'])}, disk_versions)

    def test_launcher_feed_reads_github_index_separately_from_releases(self):
        version = self.latest_version
        name = f'Unova-Together-{version}-Windows-x64.zip'
        sums_name = f'SHA256SUMS-Unova-Together-{version}.txt'
        base = f'https://github.com/{updater.REPO}/releases/download/v{version}/'
        release = {'tag_name': 'v' + version, 'name': 'Latest', 'body': 'Fallback text',
                   'published_at': '2026-10-15T00:00:00Z', 'draft': False, 'prerelease': False,
                   'assets': [{'name': name, 'size': 1024, 'browser_download_url': base + name},
                              {'name': sums_name, 'size': 80, 'browser_download_url': base + sums_name}]}
        requests = []

        class Response:
            def __init__(self, url, data): self.url, self.data = url, data
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def geturl(self): return self.url
            def read(self, limit): return self.data[:limit]

        def opener(url):
            requests.append(url)
            if url == updater.API:
                return Response(url, json.dumps([release]).encode())
            if url == updater.PATCHNOTES_URL:
                return Response(url, json.dumps(self.index).encode())
            raise AssertionError(f'Unexpected launcher request: {url}')

        feed = updater.launcher_feed(opener)
        self.assertEqual(requests, [updater.API, updater.PATCHNOTES_URL])
        self.assertEqual(feed['release']['version'], version)
        self.assertEqual(feed['newsSource'], 'patchnotes')
        self.assertEqual(len(feed['news']), len(self.index['notes']))
        self.assertTrue(all('/blob/main/patchnotes/' in note['url'] for note in feed['news']))

    def test_launcher_build_metadata_matches_current_release(self):
        for relative in (
            'launcher-source/tools/launcher_ui/build-info.json',
            'maintenance-tools/tools/launcher_ui/build-info.json',
        ):
            with self.subTest(path=relative):
                info = json.loads((self.root / relative).read_text(encoding='utf-8'))
                self.assertEqual(info['version'], self.latest_version)

    def test_unavailable_index_falls_back_to_release_notes(self):
        version = self.latest_version
        name = f'Unova-Together-{version}-Windows-x64.zip'
        sums_name = f'SHA256SUMS-Unova-Together-{version}.txt'
        base = f'https://github.com/{updater.REPO}/releases/download/v{version}/'
        release = {'tag_name': 'v' + version, 'name': 'Latest',
                   'body': 'Available from the release page', 'published_at': '2026-10-15T00:00:00Z',
                   'assets': [{'name': name, 'size': 1024, 'browser_download_url': base + name},
                              {'name': sums_name, 'size': 80, 'browser_download_url': base + sums_name}]}

        def opener(url):
            if url == updater.API:
                return io.BytesIO(json.dumps([release]).encode())
            raise OSError('Offline test')

        feed = updater.launcher_feed(opener)
        self.assertEqual(feed['newsSource'], 'releases-fallback')
        self.assertEqual(feed['news'][0]['body'], 'Available from the release page')

    def test_patch_notes_remain_available_when_release_history_is_unavailable(self):
        requests = []

        class Response:
            def __init__(self, url, data): self.url, self.data = url, data
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def geturl(self): return self.url
            def read(self, limit): return self.data[:limit]

        def opener(url):
            requests.append(url)
            if url == updater.API:
                raise OSError('Release history unavailable')
            if url == updater.PATCHNOTES_URL:
                return Response(url, json.dumps(self.index).encode())
            raise AssertionError(f'Unexpected launcher request: {url}')

        feed = updater.launcher_feed(opener)
        self.assertIsNone(feed['release'])
        self.assertEqual(feed['newsSource'], 'patchnotes')
        self.assertEqual(len(feed['news']), len(self.index['notes']))
        self.assertEqual(requests, [updater.API, updater.PATCHNOTES_URL])


if __name__ == '__main__':
    unittest.main()
