"""Publish the prepared portable ZIP using the existing Git credential manager."""
from pathlib import Path
import argparse
import json
import hashlib
import mimetypes
import os
import subprocess
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO = 'WhatWasMissing/PokePlay'
VERSION = 'v0.2.0'

def cached_github_headers(repo, credential_cwd):
    """Use a valid cached API credential without opening a sign-in window."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
    account = repo.split('/')[0]
    # A stale repository-specific entry must not hide a working account credential.
    for path in ('', repo + '.git'):
        query = f'protocol=https\nhost=github.com\nusername={account}\n'
        if path:
            query += f'path={path}\n'
        result = subprocess.run(['git', 'credential', 'fill'], input=query + '\n',
                                cwd=credential_cwd, timeout=30, text=True,
                                capture_output=True, env=env)
        credentials = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
        if result.returncode or not credentials.get('password'):
            continue
        headers = {'Authorization': 'Bearer ' + credentials['password'],
                   'Accept': 'application/vnd.github+json',
                   'X-GitHub-Api-Version': '2022-11-28',
                   'User-Agent': 'PokePlay-release-publisher'}
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    'https://api.github.com/user', headers=headers), timeout=30) as response:
                json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 401:
                continue
            raise
        return headers
    raise RuntimeError('No usable cached GitHub API credential; no interactive sign-in was opened.')

def main():
    global VERSION, REPO
    parser=argparse.ArgumentParser()
    parser.add_argument('--version',default='0.2.0')
    parser.add_argument('--repo', default=REPO, help='GitHub owner/repository for this release')
    parser.add_argument('--commit',default='cf1e51fc6c280a33e8ee3192b82abc941a81091b')
    parser.add_argument('--notes',type=Path)
    parser.add_argument('--title')
    parser.add_argument('--prerelease',action='store_true')
    parser.add_argument('--asset',action='append',type=Path,help='Explicit assets instead of the standard Windows ZIP/checksum')
    args=parser.parse_args()
    REPO=args.repo
    VERSION='v'+args.version
    credential_cwd = ROOT/'tools/github-release'
    headers = cached_github_headers(REPO, credential_cwd if credential_cwd.is_dir() else ROOT)

    def request(url, method='GET', data=None, content_type='application/json'):
        payload = json.dumps(data).encode() if isinstance(data, dict) else data
        req = urllib.request.Request(url, data=payload, method=method,
                                     headers={**headers, 'Content-Type': content_type})
        with urllib.request.urlopen(req, timeout=180) as response:
            return json.load(response)

    api = f'https://api.github.com/repos/{REPO}'
    releases = request(api + '/releases')
    release = next((r for r in releases if r['tag_name'] == VERSION), None)
    if release is None:
        release = request(api + '/releases', 'POST', {
            'tag_name': VERSION, 'target_commitish': args.commit,
            'name': args.title or 'PokePlay '+args.version+' - Multiplayer and battle presence', 'draft': True,
            'prerelease': args.prerelease,
            'body': args.notes.read_text(encoding='utf-8') if args.notes else 'Download PokePlay-0.2.0-Windows-x64.zip below and extract the whole folder. Run melonDS.exe and load your own ROM. No multipart downloads or older build installation are required.\n\nIncludes the complete Windows x64 runtime, updated LAN relay, dedicated Multiplayer panel, trade/battle request coordination, setup instructions, and matching modified melonDS source. Python 3 is required on the relay host. Update both computers.\n\nActual trades and battles use native wireless setup and the game Union Room. Build compilation and six relay tests pass; the new panel and native handoff still need two-computer in-game verification. ROMs, saves, firmware, and personal settings are excluded.\n\nSHA256SUMS.txt contains the ZIP checksum.'})
    assets=args.asset or [ROOT/'downloads/releases'/f'PokePlay-{args.version}-Windows-x64.zip', ROOT/'downloads/releases'/('SHA256SUMS.txt' if args.version=='0.2.0' else f'SHA256SUMS-{args.version}.txt')]
    if len({path.name for path in assets})!=len(assets):
        raise RuntimeError('Release asset names must be unique')
    for path in assets:
        name=path.name
        content_type='application/vnd.android.package-archive' if path.suffix=='.apk' else mimetypes.guess_type(name)[0] or 'application/octet-stream'
        digest='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()
        existing = next((a for a in release['assets'] if a['name'] == name), None)
        if existing:
            if existing['size'] != path.stat().st_size or existing.get('digest')!=digest:
                raise RuntimeError('Existing release asset differs; refusing to replace it silently.')
            continue
        upload = release['upload_url'].split('{')[0] + '?name=' + name
        asset = request(upload, 'POST', path.read_bytes(), content_type)
        assert asset['size'] == path.stat().st_size
        assert asset.get('digest')==digest, 'Uploaded asset checksum mismatch'
        print('Uploaded ' + name, flush=True)
    release = request(api + '/releases/' + str(release['id']), 'PATCH', {'draft': False})
    print(release['html_url'], flush=True)
    for asset in release['assets']:
        print(asset['browser_download_url'], flush=True)

if __name__ == '__main__':
    main()
