"""Build the attributed standalone Windows launcher, including static assets."""
from pathlib import Path
import argparse, subprocess, sys, shutil, json
from importlib import metadata
from launcher_ui import versioning

ROOT=Path(__file__).resolve().parents[1]
assets=ROOT/'tools/launcher_ui'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,default=ROOT/'builds/mod-hub/current')
parser.add_argument('--work-dir',type=Path,default=ROOT/'test-fixtures/mod-hub-build-20261013')
parser.add_argument('--revision',default='2026101305')
parser.add_argument('--version',default=versioning.current_version())
args=parser.parse_args()
output=args.output_dir.resolve();work=args.work_dir.resolve()
if not output.is_relative_to(ROOT/'builds') or not work.is_relative_to(ROOT/'test-fixtures'):
    parser.error('Output and work folders must stay inside builds/ and test-fixtures/.')
versioning.numbers(args.version)
work.mkdir(parents=True,exist_ok=True)
build_info={'schema':1,'product':versioning.PRODUCT,'version':args.version}
(work/'build-info.json').write_text(json.dumps(build_info),encoding='utf-8')
versioning.write_windows_version(assets/'windows-version.txt',work/'windows-version.txt',args.version)
command=[sys.executable,'-m','PyInstaller','--noconfirm','--onedir','--windowed','--noupx',
         '--exclude-module','numpy',
         '--name','Pokemon Together','--icon',str(assets/'assets/launcher.ico'),
         '--version-file',str(work/'windows-version.txt'),
         '--add-data',str(work/'build-info.json')+';launcher_ui',
         '--add-data',str(assets/'theme.json')+';launcher_ui',
         '--add-data',str(assets/'assets')+';launcher_ui/assets',
         '--distpath',str(output),
         '--workpath',str(work),
         '--specpath',str(work),
         str(ROOT/'tools/unova_launcher.py')]
if __name__=='__main__':
    subprocess.run(command,cwd=ROOT,check=True)
    destination=output/'Pokemon Together'
    (destination/'BUILD_REVISION.txt').write_text(args.revision+'\n')
    (destination/'VERSION.txt').write_text('Pokemon Together Launcher '+args.version+'\n')
    (destination/'BUILD_INFO.json').write_text(json.dumps(build_info),encoding='utf-8')
    shutil.copy2(Path(sys.base_prefix)/'LICENSE.txt',destination/'Python-LICENSE.txt')
    distribution=metadata.distribution('pyinstaller')
    license_file=next(p for p in distribution.files if str(p).endswith('/COPYING.txt'))
    shutil.copy2(distribution.locate_file(license_file),destination/'PyInstaller-COPYING.txt')

    distribution=metadata.distribution('tomlkit')
    license_file=next(p for p in distribution.files if str(p).endswith('/LICENSE'))
    shutil.copy2(distribution.locate_file(license_file),destination/'TOMLKit-LICENSE.txt')
    for package,label in [('ndspy','NDSpy-LICENSE.txt'),('Pillow','Pillow-LICENSE.txt')]:
        distribution=metadata.distribution(package)
        license_file=next(p for p in distribution.files if str(p).endswith('/LICENSE'))
        shutil.copy2(distribution.locate_file(license_file),destination/label)
