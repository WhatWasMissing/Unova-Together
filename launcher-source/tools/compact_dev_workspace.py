"""Compact historical development outputs; verified private evidence is archived on F:."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DISPOSABLE={'.exe','.dll','.pyd','.obj','.lib','.a','.pdb','.pch','.pyc'}

def files(root):
    if root.is_symlink() or root.is_junction():raise ValueError('Linked cleanup root')
    for directory,dirs,names in os.walk(root):
        dirs[:]=[name for name in dirs if not (Path(directory)/name).is_symlink() and not (Path(directory)/name).is_junction()]
        for name in names:
            path=Path(directory)/name
            if not path.is_symlink() and not path.is_junction():yield path

def plan():
    rows={}
    def add(path,action):
        stat=path.stat()
        rows[str(path)]={'path':str(path),'action':action,'bytes':stat.st_size,'mtime':stat.st_mtime_ns}
    for relative in ('test-fixtures','backups','builds/archive','designs/backups'):
        root=ROOT/relative
        if not root.is_dir():continue
        for path in files(root):
            if relative=='test-fixtures' and (path.relative_to(root).parts[0] in {'mod-hub-final-ui-20261013','mod-hub-frozen-20261013.json','mod-hub-ui-20261013'}):continue
            regenerated=relative=='test-fixtures' and (path.suffix.lower() in DISPOSABLE or '_internal' in path.parts)
            add(path,'discard' if regenerated else 'archive')
    # Generated release downloads are already published or reproducible from source.
    for path in files(ROOT/'downloads/releases'):
        if 'mod-hub-20261013' in path.parts:continue
        if path.suffix.lower() in {'.zip','.exe','.7z','.mp4'}:add(path,'discard')
    # Keep the native runtime, user directory and Qt toolchain; only compiler outputs go.
    for relative in ('builds/azahar-x/src','builds/azahar-x/CMakeFiles','builds/azahar-x/externals','melonDS-source-1.1/build'):
        root=ROOT/relative
        if not root.is_dir():continue
        for path in files(root):
            if relative.endswith('/externals') and path.relative_to(root).parts[0]=='qt':continue
            if path.suffix.lower() in {'.obj','.lib','.a','.pdb','.pch','.o','.pyc'}:add(path,'discard')
    return list(rows.values())

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--staging',action='store_true',help='Archive obsolete build stages; retain active/dev/3DS/hub runtimes')
    parser.add_argument('--resume',action='store_true',help='Verify an already completed evidence ZIP before deletion')
    parser.add_argument('--archive',type=Path,default=Path('F:/pokemon-workspace-archive/2026-10-13'))
    args=parser.parse_args();rows=plan()
    if args.staging:
        running=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-CimInstance Win32_Process | Where-Object ExecutablePath | Select-Object -ExpandProperty ExecutablePath | ConvertTo-Json -Compress'],capture_output=True,text=True,check=True)
        paths=json.loads(running.stdout) if running.stdout.strip() else []
        if isinstance(paths,str):paths=[paths]
        rows=[]
        for folder in (ROOT/'builds').iterdir():
            if not folder.is_dir() or folder.name in {'current','azahar-x','mod-hub','archive'}:continue
            if any(p.lower().startswith(str(folder).lower()+'\\') for p in paths):continue
            for path in files(folder):
                stat=path.stat();rows.append({'path':str(path),'action':'archive','bytes':stat.st_size,'mtime':stat.st_mtime_ns})
        args.archive=args.archive/'build-stages'
    print(json.dumps({'files':len(rows),'logicalGiB':round(sum(r['bytes'] for r in rows)/2**30,2),'archive':str(args.archive),'mode':'apply' if args.apply else 'preview'}),flush=True)
    if not args.apply:return
    running=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-CimInstance Win32_Process | Where-Object ExecutablePath | Select-Object -ExpandProperty ExecutablePath | ConvertTo-Json -Compress'],capture_output=True,text=True,check=True)
    processes=json.loads(running.stdout) if running.stdout.strip() else []
    if isinstance(processes,str):processes=[processes]
    candidates=[str(ROOT/'test-fixtures'),str(ROOT/'backups'),str(ROOT/'builds/archive')]
    if args.staging:candidates=list({str(Path(r['path']).parents[len(Path(r['path']).relative_to(ROOT/'builds').parts)-2]) for r in rows})
    if any(p.lower().startswith(c.lower()+'\\') for p in processes for c in candidates):raise RuntimeError('Close a running historical fixture before cleanup')
    destination=args.archive.resolve()
    if destination.drive.lower()!='f:' or destination==Path('F:/'):raise ValueError('Archive must be a named folder on F:')
    destination.mkdir(parents=True,exist_ok=True)
    archive_path=destination/'evidence.zip'
    if archive_path.exists() and not args.resume:raise ValueError('Evidence ZIP already exists; originals preserved')
    if (destination/'manifest.json').exists():raise ValueError('Manifest already exists; use its native apply helper rather than overwriting recovery data')
    if args.resume and not archive_path.is_file():raise ValueError('No evidence ZIP to resume')
    copied=0;checkpoint=0;start=time.monotonic();verified_objects=set()
    # One sequential ZIP avoids tens of thousands of tiny writes to the external drive.
    with zipfile.ZipFile(archive_path,'r' if args.resume else 'w',compression=zipfile.ZIP_STORED,allowZip64=True) as archive:
        for index,row in enumerate(rows):
            path=Path(row['path'])
            if path.stat().st_mtime_ns!=row['mtime'] or path.stat().st_size!=row['bytes']:raise ValueError('Source changed: '+str(path))
            if row['action']=='archive':
                sha=digest(path);entry=sha+path.suffix.lower()
                if entry not in verified_objects:
                    if not args.resume:archive.write(path,entry)
                    with archive.open(entry) as stream:
                        if hashlib.file_digest(stream,'sha256').hexdigest()!=sha:raise ValueError('Archive verification failed; originals preserved')
                    copied+=row['bytes'];verified_objects.add(entry)
                row.update(archive=str(archive_path),entry=entry,sha256=sha)
            if time.monotonic()-checkpoint>20:
                print('Verified '+str(index+1)+'/'+str(len(rows))+' files; '+str(round(copied/2**30,2))+' GiB of distinct evidence.',flush=True);checkpoint=time.monotonic()
    report=destination/'manifest.json'
    with archive_path.open('r+b') as stream:stream.flush();os.fsync(stream.fileno())
    report.write_text(json.dumps({'workspace':str(ROOT),'files':rows},indent=2),encoding='utf-8')
    # Native PowerShell owns deletion; no recursive shell-generated delete command.
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/apply_workspace_compaction.ps1'),'-Manifest',str(report)],check=True)
    print(json.dumps({'archivedDistinctGiB':round(copied/2**30,2),'removedFiles':len(rows),'manifest':str(report)}),flush=True)

if __name__=='__main__':main()
