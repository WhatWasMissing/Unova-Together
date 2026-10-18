"""Compile the read-only companion interaction code against an identified source tree."""
import argparse
import hashlib
from pathlib import Path
import os
import platform
import re
import shutil
import subprocess
import tempfile


DEFAULT_QT_ROOT = Path(os.environ.get('UNOVA_QT6_ROOT', r'C:\msys64\ucrt64'))
DEFAULT_CXX = os.environ.get('UNOVA_CXX') or shutil.which('g++') or r'C:\msys64\ucrt64\bin\g++.exe'


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path,
                        help='Root of the matching melonDS source tree')
    parser.add_argument('--source-id', required=True,
                        help='Authoritative repository URL plus immutable commit/release, or an explicit UNVERIFIED SOURCE label')
    parser.add_argument('--expected-header-sha256',
                        help='Optional expected SHA-256 for src/frontend/qt_sdl/FollowerInteraction.h')
    parser.add_argument('--cxx', type=Path, default=DEFAULT_CXX,
                        help='C++ compiler executable (default: UNOVA_CXX, PATH g++, or MSYS2 g++)')
    parser.add_argument('--qt-root', type=Path, default=DEFAULT_QT_ROOT,
                        help='Qt 6 installation root containing include/qt6 and lib (default: UNOVA_QT6_ROOT or MSYS2)')
    return parser


def inspect_source(source_root, source_id, expected_header_sha256=None):
    if not source_id or not source_id.strip():
        raise ValueError('Provide an authoritative source identity or an explicit UNVERIFIED SOURCE label.')
    source_root = Path(source_root).expanduser().resolve()
    header = source_root / 'src/frontend/qt_sdl/FollowerInteraction.h'
    if not header.is_file():
        raise ValueError(f'Source root is missing the production header: {header}')
    digest = hashlib.sha256(header.read_bytes()).hexdigest()
    if expected_header_sha256:
        if not re.fullmatch(r'[0-9a-fA-F]{64}', expected_header_sha256):
            raise ValueError('--expected-header-sha256 must be 64 hexadecimal characters.')
        if digest.lower() != expected_header_sha256.lower():
            raise ValueError(f'Production header SHA-256 mismatch: expected {expected_header_sha256}, got {digest}.')
    return {'root': source_root, 'header': header, 'source_id': source_id.strip(), 'header_sha256': digest}


def inspect_toolchain(compiler, qt_root):
    compiler = Path(compiler).expanduser().resolve()
    qt_root = Path(qt_root).expanduser().resolve()
    include = qt_root / 'include/qt6'
    core_include = include / 'QtCore'
    library = qt_root / 'lib'
    missing = [path for path in (compiler, include, core_include, library) if not path.exists()]
    if missing:
        raise ValueError('Missing compiler/Qt prerequisite(s): ' + ', '.join(map(str, missing)))
    if not compiler.is_file():
        raise ValueError(f'C++ compiler is not a file: {compiler}')
    if not any((library / name).is_file() for name in ('libQt6Core.a', 'libQt6Core.dll.a', 'Qt6Core.lib')):
        raise ValueError(f'Qt6Core link library is missing from: {library}')
    return compiler, include, core_include, library


CPP=r'''#include "FollowerInteraction.h"
#include <iostream>
#include <set>
#define CHECK(condition) do { if (!(condition)) { std::cerr << "CHECK failed at " << __FILE__ << ':' << __LINE__ << ": " << #condition << '\n'; return 1; } } while (false)
int main() {
 qunsetenv("UNOVA_COMPANION_INTERACTIONS");qunsetenv("UNOVA_EXPERIMENTAL_COMPANION");
 CHECK(FollowerInteraction::enabledByEnvironment());
 qputenv("UNOVA_EXPERIMENTAL_COMPANION","0");CHECK(!FollowerInteraction::enabledByEnvironment());
 qputenv("UNOVA_EXPERIMENTAL_COMPANION","1");CHECK(FollowerInteraction::enabledByEnvironment());
 qputenv("UNOVA_COMPANION_INTERACTIONS","0");CHECK(!FollowerInteraction::enabledByEnvironment());
 qputenv("UNOVA_EXPERIMENTAL_COMPANION","0");qputenv("UNOVA_COMPANION_INTERACTIONS","1");
 CHECK(FollowerInteraction::enabledByEnvironment());
 qunsetenv("UNOVA_COMPANION_INTERACTIONS");qunsetenv("UNOVA_EXPERIMENTAL_COMPANION");
 QVariantMap p{{"ok",true},{"species",381},{"name","Latios"},{"hp",80},{"maxHp",100},{"friendship",240}};
 const auto unchanged=p;
 CHECK(FollowerInteraction::available(p));
 CHECK(FollowerInteraction::reaction(p,"talk").contains("happy"));
 CHECK(FollowerInteraction::reaction(p,"talk",1).contains("close"));
 CHECK(FollowerInteraction::reaction(p,"pet").contains("hand"));
 CHECK(FollowerInteraction::reaction(p,"play").contains("hops"));
 CHECK(FollowerInteraction::reaction(p,"play",1).contains("turns"));
 CHECK(p==unchanged);
 p["hp"]=25;CHECK(FollowerInteraction::reaction(p,"play").contains("tired"));
 p["hp"]=0;CHECK(FollowerInteraction::reaction(p,"pet").contains("rest"));
 p["hp"]=100;p["friendship"]=20;CHECK(FollowerInteraction::reaction(p,"talk").contains("carefully"));
 p["friendship"]=100;for(unsigned i=0;i<6;++i)CHECK(!FollowerInteraction::reaction(p,"talk",i).isEmpty());
 const QStringList actions{"talk","pet","play","praise","story","ask","sit","trick","joke","sing"};
 const std::array<unsigned,5> bonds{{0,50,100,150,220}};
 const QStringList motions{"bounce","run","peek","sway","hop","spin"};
 const QStringList emotes{"?","!","heart","...","star","music"};
 unsigned combinations=0;bool sawRun=false;
 for(unsigned nature=0;nature<25;++nature) {
  p["nature"]=nature;
  for(unsigned band=0;band<bonds.size();++band) {
   p["friendship"]=bonds[band];
   for(const auto& action:actions) {
    std::set<QString> variants;
    for(unsigned variation=0;variation<4;++variation) {
     const auto before=p;
     const auto line=FollowerInteraction::reaction(p,action,variation);
     const auto cue=FollowerInteraction::visualCue(p,action,variation);
     CHECK(line.startsWith("Latios ") && !line.isEmpty());
     CHECK(motions.contains(cue.motion) && emotes.contains(cue.emote));
     CHECK(cue.durationMs==1700 || (cue.motion=="run" && cue.durationMs==2400));
     variants.insert(line);sawRun=sawRun || cue.motion=="run";++combinations;
     CHECK(p==before);
    }
    CHECK(variants.size()==4);
   }
  }
 }
 CHECK(combinations==5000 && sawRun);
 for(unsigned nature=0;nature<25;++nature) {
  p["nature"]=nature;p["friendship"]=240;std::set<QString> lines;
  for(unsigned i=0;i<60;++i) lines.insert(FollowerInteraction::reaction(p,"talk",i));
  CHECK(lines.size()>=16);
 }
 p["type1"]=10;p["type2"]=10;
 const QVariantMap context{{"area","Undella Bay"},{"hour",23},{"month",4},{"recentBattle",true}};
 const auto beforeContext=p;std::set<QString> contexts;
 for(unsigned i=1;i<80;i+=2) contexts.insert(FollowerInteraction::contextNote(p,context,i));
 CHECK(contexts.size()>=10 && p==beforeContext);
 bool water=false,night=false,battle=false;
 for(const auto& line:contexts) {water|=line.contains("water");night|=line.contains("night");battle|=line.contains("battle");}
 CHECK(water && night && battle);
 CHECK(FollowerInteraction::contextNote(p,context,0).isEmpty());
 p["nature"]=0;const auto firstNature=FollowerInteraction::reaction(p,"talk");
 p["nature"]=1;CHECK(FollowerInteraction::reaction(p,"talk")!=firstNature);
 p["egg"]=true;CHECK(!FollowerInteraction::available(p));
 p["egg"]=false;p["species"]=650;CHECK(!FollowerInteraction::available(p));
 CHECK(!FollowerInteraction::available({}));
 for(unsigned n=1;n<=649;++n) {p["species"]=n;CHECK(FollowerInteraction::available(p));}
 std::cout<<"Companion interaction matrix: "<<combinations<<" nature/action/friendship/variation combinations passed; all 649 species, read-only data, cues and running reactions passed.\n";
}
'''
def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        source = inspect_source(args.source_root, args.source_id, args.expected_header_sha256)
        compiler, qt_include, qt_core_include, qt_library = inspect_toolchain(args.cxx, args.qt_root)
    except ValueError as error:
        parser.error(str(error))

    print('UNVERIFIED SOURCE: this runner records the supplied identity but does not authenticate its origin.')
    print(f"Source ID supplied: {source['source_id']}")
    print(f"Source root: {source['root']}")
    print(f"FollowerInteraction.h SHA-256: {source['header_sha256']}")
    print(f"Compiler: {compiler}")
    compiler_version = subprocess.run(
        [str(compiler), '--version'], capture_output=True, text=True, timeout=15, check=False,
    )
    if compiler_version.returncode:
        raise RuntimeError(f'C++ compiler version check failed: {compiler_version.stderr.strip()}')
    print(f"Compiler version: {compiler_version.stdout.splitlines()[0] if compiler_version.stdout else 'unknown'}")
    print(f"Operating system: {platform.platform()}")
    print(f"Qt root: {Path(args.qt_root).expanduser().resolve()}")
    print('C++ flags: -std=c++17 -Wall -Wextra -Werror; link: -lQt6Core')

    env = os.environ.copy()
    env['PATH'] = str(compiler.parent) + os.pathsep + env.get('PATH', '')
    with tempfile.TemporaryDirectory(prefix='unova-companion-') as folder:
        cpp = Path(folder) / 'test.cpp'
        exe = Path(folder) / 'test.exe'
        cpp.write_text(CPP, encoding='utf-8')
        subprocess.run([
            str(compiler), '-std=c++17', '-Wall', '-Wextra', '-Werror', str(cpp),
            '-I' + str(source['header'].parent), '-I' + str(qt_include),
            '-I' + str(qt_core_include), '-L' + str(qt_library), '-lQt6Core', '-o', str(exe),
        ], env=env, check=True)
        subprocess.run([str(exe)], env=env, check=True)


if __name__ == '__main__':
    main()
