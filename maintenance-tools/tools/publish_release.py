"""Publish an explicitly prepared Unova Together release using cached credentials."""
from pathlib import Path
import argparse
import json
import hashlib
import mimetypes
import os
import re
import subprocess
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO = 'WhatWasMissing/Unova-Together'

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
                   'User-Agent': 'Unova-Together-release-publisher'}
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

def build_parser():
    parser=argparse.ArgumentParser()
    parser.add_argument('--version',required=True,help='Release version without a leading v (for example 2.0.16)')
    parser.add_argument('--repo',required=True,help='Must be WhatWasMissing/Unova-Together')
    parser.add_argument('--commit',required=True,help='Full commit SHA already present in the target repository')
    parser.add_argument('--notes',required=True,type=Path,help='User-facing release notes file')
    parser.add_argument('--title',required=True,help='User-facing GitHub release title')
    parser.add_argument('--prerelease',action='store_true')
    parser.add_argument('--asset',required=True,action='append',type=Path,help='Release asset path; repeat for every asset')
    return parser

def validate_args(parser, args):
    if args.repo != REPO:
        parser.error(f'--repo must be {REPO}')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?', args.version):
        parser.error('--version must be a semantic version without a leading v')
    if not re.fullmatch(r'[0-9a-fA-F]{40}', args.commit):
        parser.error('--commit must be a full 40-character commit SHA')
    if not args.title.strip():
        parser.error('--title must not be empty')
    if not args.notes.is_file():
        parser.error(f'Release notes file does not exist: {args.notes}')
    if not args.notes.read_text(encoding='utf-8').strip():
        parser.error('--notes must contain release notes')
    if not args.asset:
        parser.error('Supply every release asset with one or more --asset arguments')
    missing = [str(path) for path in args.asset if not path.is_file()]
    if missing:
        parser.error('Release asset file(s) do not exist: ' + ', '.join(missing))
    names = [path.name for path in args.asset]
    if len(set(names)) != len(names):
        parser.error('Release asset names must be unique')
    return args

def parse_args(argv=None):
    parser = build_parser()
    return validate_args(parser, parser.parse_args(argv))

def verify_remote_commit(request, api, commit_sha):
    commit = request(f'{api}/commits/{commit_sha}')
    if not isinstance(commit, dict) or commit.get('sha', '').lower() != commit_sha.lower():
        raise RuntimeError(f'GitHub did not confirm commit {commit_sha} in {REPO}; refusing to create or update a release.')

def main(argv=None):
    args = parse_args(argv)
    version_tag = 'v' + args.version
    credential_cwd = ROOT/'tools/github-release'
    headers = cached_github_headers(args.repo, credential_cwd if credential_cwd.is_dir() else ROOT)

    def request(url, method='GET', data=None, content_type='application/json'):
        payload = json.dumps(data).encode() if isinstance(data, dict) else data
        req = urllib.request.Request(url, data=payload, method=method,
                                     headers={**headers, 'Content-Type': content_type})
        with urllib.request.urlopen(req, timeout=180) as response:
            return json.load(response)

    api = f'https://api.github.com/repos/{args.repo}'
    verify_remote_commit(request, api, args.commit)
    releases = request(api + '/releases')
    release = next((r for r in releases if r['tag_name'] == version_tag), None)
    if release is None:
        release = request(api + '/releases', 'POST', {
            'tag_name': version_tag, 'target_commitish': args.commit,
            'name': args.title, 'draft': True,
            'prerelease': args.prerelease,
            'body': args.notes.read_text(encoding='utf-8')})
    assets=args.asset
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
        if asset.get('size') != path.stat().st_size:
            raise RuntimeError(f'Uploaded asset size mismatch for {name}')
        if asset.get('digest') != digest:
            raise RuntimeError(f'Uploaded asset checksum mismatch for {name}')
        print('Uploaded ' + name, flush=True)
    release = request(api + '/releases/' + str(release['id']), 'PATCH', {'draft': False})
    print(release['html_url'], flush=True)
    for asset in release['assets']:
        print(asset['browser_download_url'], flush=True)

if __name__ == '__main__':
    main()
