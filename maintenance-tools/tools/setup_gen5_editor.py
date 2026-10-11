"""Download the reviewed Frost release and verify every installed archive file."""
from pathlib import Path
import argparse
import hashlib
import json
import urllib.request
import zipfile
import io

URL = 'https://github.com/FrostFalcon/FrostsGen5Editor/releases/download/5.0.1/FrostsGen5Editor.zip'
SHA256 = '56f50a4b0f4d9b7e13df16d3b66fc55e5e243447be705f34b4d76c84dfde0a27'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parent / 'external/gen5/Frost-5.0.1')
    args = parser.parse_args()
    root = args.directory.resolve()
    root.mkdir(parents=True, exist_ok=True)
    archive = root / 'FrostsGen5Editor.zip'
    raw = archive.read_bytes() if archive.exists() else urllib.request.urlopen(URL, timeout=60).read()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError('Frost archive differs from the reviewed GitHub release')
    files = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        for info in bundle.infolist():
            if info.is_dir():
                continue
            relative = Path(info.filename.replace('\\', '/'))
            if relative.is_absolute() or '..' in relative.parts or ':' in info.filename:
                raise ValueError('Unsafe archive entry: ' + info.filename)
            target = root / 'app' / relative
            data = bundle.read(info)
            if target.exists() and target.read_bytes() != data:
                raise ValueError('Installed editor file was modified: ' + info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files[relative.as_posix()] = hashlib.sha256(data).hexdigest()
    archive.write_bytes(raw)
    manifest = dict(project='FrostFalcon/FrostsGen5Editor', version='5.0.1', url=URL,
                    sha256=SHA256, digestVerifiedAgainstGitHub=True, files=files)
    (root / 'download.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Frost 5.0.1: verified archive and {len(files)} installed files at {root / "app"}')


if __name__ == '__main__':
    main()
