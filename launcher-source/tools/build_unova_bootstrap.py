"""Build the stable launcher entry and client repair download. mvq1303."""
from pathlib import Path
import argparse
import subprocess
import sys
import shutil
from importlib import metadata
from launcher_ui import versioning

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent.parent.parent
REPO=ROOT.parent

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--work-dir',type=Path,required=True)
    args=parser.parse_args();output=args.output_dir.resolve();work=args.work_dir.resolve()
    if not output.is_relative_to(WORKSPACE/'builds') or not work.is_relative_to(WORKSPACE/'test-fixtures'):raise ValueError('Build directories must stay in the workspace build/fixture folders.')
    work.mkdir(parents=True,exist_ok=True)
    (work/'.disposable-test-output').write_text('Temporary bootstrap build work.',encoding='utf-8')
    licenses=work/'bootstrap-licenses';licenses.mkdir(exist_ok=True)
    shutil.copy2(Path(sys.base_prefix)/'LICENSE.txt',licenses/'Python-LICENSE.txt')
    package=metadata.distribution('pyinstaller');copying=next(p for p in package.files if str(p).endswith('/COPYING.txt'))
    shutil.copy2(package.locate_file(copying),licenses/'PyInstaller-COPYING.txt')
    notice_roots=[REPO,WORKSPACE,ROOT/'source/melonDS',WORKSPACE/'melonDS-source-1.1']
    project_license=next(p/'LICENSE' for p in notice_roots if (p/'LICENSE').is_file())
    authorship=next(p/'AUTHORSHIP.md' for p in notice_roots if (p/'AUTHORSHIP.md').is_file())
    shutil.copy2(project_license,licenses/'Unova-Together-GPL.txt')
    shutil.copy2(authorship,licenses/'AUTHORSHIP.md')
    versioning.write_windows_version(ROOT/'tools/launcher_ui/windows-version.txt',work/'windows-version.txt',versioning.current_version())
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--onefile','--windowed','--noupx','--name','Pokemon Together Bootstrap',
        '--icon',str(ROOT/'tools/launcher_ui/assets/launcher.ico'),'--version-file',str(work/'windows-version.txt'),
        '--add-data',str(licenses)+';bootstrap-licenses',
        '--distpath',str(output),'--workpath',str(work/'pyinstaller'),'--specpath',str(work),str(ROOT/'tools/unova_launcher_bootstrap.py')],cwd=ROOT,check=True)

if __name__=='__main__':main()
