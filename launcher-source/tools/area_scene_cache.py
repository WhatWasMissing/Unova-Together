"""ROM-specific local scenery cache. Unova Together by mvq1303."""
from pathlib import Path
import hashlib, json, os, uuid
from build_area_battle_catalog import catalog


def prepare_catalog(rom, cache):
    rom=Path(rom).resolve();cache=Path(cache).resolve()
    with rom.open('rb') as file:
        if file.read(16)[12:16]!=b'IREO': raise ValueError('Area scenery requires English Black 2')
        file.seek(0);digest=hashlib.file_digest(file,'sha256').hexdigest()
    destination=cache/digest
    manifest=destination/'catalog.json'
    if manifest.is_file():
        report=json.loads(manifest.read_text())
        if report.get('romSHA256')==digest and report.get('format')==1:return manifest
        raise ValueError('Scenery cache is invalid; use a fresh cache directory')
    cache.mkdir(parents=True,exist_ok=True)
    temporary=cache/('pending-'+uuid.uuid4().hex)
    catalog(rom,temporary)
    os.replace(temporary,destination)
    return manifest
