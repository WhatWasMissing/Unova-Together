"""ROM-specific local scenery cache. Unova Together by mvq1303."""
from pathlib import Path
import hashlib, json, os, uuid
from build_area_battle_catalog import catalog
import unova_storage as storage


def prepare_catalog(rom, cache):
    rom=Path(rom).resolve();cache=Path(cache).expanduser().absolute();base=cache.parent.resolve()
    if not storage.safe_managed_path(cache,base):raise ValueError('Unsafe scenery cache path.')
    with rom.open('rb') as file:
        if file.read(16)[12:16]!=b'IREO': raise ValueError('Area scenery requires an English Blaze Black 2 Redux game')
        file.seek(0);digest=hashlib.file_digest(file,'sha256').hexdigest()
    destination=cache/digest
    manifest=destination/'catalog.json'
    if not storage.safe_managed_path(destination,base) or not storage.safe_managed_path(manifest,base):
        raise ValueError('Unsafe scenery cache path.')
    if manifest.is_file():
        try:report=json.loads(manifest.read_text(encoding='utf-8'))
        except (OSError,UnicodeError,ValueError) as error:raise ValueError('Scenery cache is invalid; use a fresh cache directory') from error
        if isinstance(report,dict) and report.get('romSHA256')==digest and type(report.get('format')) is int and report['format']==1:return manifest
        raise ValueError('Scenery cache is invalid; use a fresh cache directory')
    cache.mkdir(parents=True,exist_ok=True)
    if not storage.safe_managed_path(cache,base):raise ValueError('Unsafe scenery cache path.')
    temporary=cache/('pending-'+uuid.uuid4().hex)
    if not storage.safe_managed_path(temporary,base):raise ValueError('Unsafe scenery cache path.')
    catalog(rom,temporary)
    if (not storage.safe_managed_path(temporary,base) or
            not storage.safe_managed_path(destination,base) or
            not storage.safe_managed_path(manifest,base)):
        raise ValueError('Unsafe scenery cache path.')
    os.replace(temporary,destination)
    return manifest
