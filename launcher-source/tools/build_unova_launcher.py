"""Build the attributed standalone Windows launcher, including static assets."""
from pathlib import Path
import subprocess, sys, shutil
from importlib import metadata

ROOT=Path(__file__).resolve().parents[1]
assets=ROOT/'tools/launcher_ui'
command=[sys.executable,'-m','PyInstaller','--noconfirm','--onedir','--windowed','--noupx',
         '--exclude-module','numpy',
         '--name','Pokemon Together','--icon',str(assets/'assets/launcher.ico'),
         '--version-file',str(assets/'windows-version.txt'),
         '--add-data',str(assets/'theme.json')+';launcher_ui',
         '--add-data',str(assets/'assets')+';launcher_ui/assets',
         '--distpath',str(ROOT/'builds/mod-hub/current'),
         '--workpath',str(ROOT/'test-fixtures/mod-hub-build-20261013'),
         '--specpath',str(ROOT/'test-fixtures/mod-hub-build-20261013'),
         str(ROOT/'tools/unova_launcher.py')]
if __name__=='__main__':
    subprocess.run(command,cwd=ROOT,check=True)
    destination=ROOT/'builds/mod-hub/current/Pokemon Together'
    (destination/'BUILD_REVISION.txt').write_text('2026101302\n')
    (destination/'VERSION.txt').write_text('Pokemon Together Launcher 1.0.6\n')
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
