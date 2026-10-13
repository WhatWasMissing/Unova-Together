"""Restore selected archived evidence to a new folder, without overwriting originals."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=Path('F:/pokemon-workspace-archive/2026-10-13/manifest.json'))
    parser.add_argument('--relative',required=True,help='Original workspace subfolder, e.g. test-fixtures/coop-launcher')
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args();record=json.loads(args.manifest.read_text(encoding='utf-8'))
    original=Path(record['workspace']);relative=Path(args.relative)
    if relative.is_absolute() or '..' in relative.parts:parser.error('Use a workspace-relative subfolder')
    target=args.destination.resolve()
    if target.exists():parser.error('Choose a new destination folder')
    selected=[]
    for row in record['files']:
        source_relative=Path(row['path']).relative_to(original)
        if row['action']=='archive' and source_relative.is_relative_to(relative):
            source=Path(row['archive'])
            if source.is_symlink() or source.is_junction():raise ValueError('Linked archive object')
            if row.get('entry'):
                with zipfile.ZipFile(source) as archive,archive.open(row['entry']) as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
            else:
                with source.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
            if sha!=row['sha256']:raise ValueError('Archived evidence checksum mismatch')
            selected.append((source,source_relative,row.get('entry')))
    if not selected:parser.error('No archived evidence matches that subfolder')
    target.mkdir(parents=True)
    for source,name,entry in selected:
        output=target/name;output.parent.mkdir(parents=True,exist_ok=True)
        if entry:
            with zipfile.ZipFile(source) as archive,archive.open(entry) as stream,output.open('wb') as destination:shutil.copyfileobj(stream,destination)
        else:shutil.copy2(source,output)
    print('Restored '+str(len(selected))+' verified evidence files to '+str(target))

if __name__=='__main__':main()
