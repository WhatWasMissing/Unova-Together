"""Verify the public latest release and GitHub's uploaded asset digests."""
from pathlib import Path
import hashlib, json, urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-fixtures/release-1.0.4'
api='https://api.github.com/repos/WhatWasMissing/Unova-Together'
def get(path):
    request=urllib.request.Request(api+path,headers={'Accept':'application/vnd.github+json','User-Agent':'Unova-Together-release-verifier'})
    with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)

def main():
    release=get('/releases/latest')
    assert release['tag_name']=='v1.0.4' and not release['draft'] and not release['prerelease']
    expected=json.loads((OUT/'package.json').read_text())['assets']
    checksums=ROOT/'downloads/releases/release-1.0.4-final/SHA256SUMS-Unova-Together-1.0.4.txt'
    expected.append(dict(name=checksums.name,bytes=checksums.stat().st_size,sha256=hashlib.sha256(checksums.read_bytes()).hexdigest()))
    assets={asset['name']:asset for asset in release['assets']}
    assert set(assets)=={asset['name'] for asset in expected}
    for asset in expected:
        remote=assets[asset['name']]
        assert remote['size']==asset['bytes'] and remote['digest']=='sha256:'+asset['sha256']
        assert remote['state']=='uploaded'
    previous=get('/releases/tags/v1.0.0')
    previous_assets={asset['name']:asset for asset in previous['assets']}
    for asset in json.loads((ROOT/'test-fixtures/release-1.0.0/package.json').read_text())['assets']:
        assert previous_assets[asset['name']]['digest']=='sha256:'+asset['sha256']
    report=dict(url=release['html_url'],version='1.0.4',draft=False,prerelease=False,latest=True,assets=expected,previousReleasePreserved=True)
    (OUT/'published.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
