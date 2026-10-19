"""Compile actual production decompression/crop code in isolated boundary tests."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]


def run_boundary_check():
    source_root = Path(os.environ.get('UNOVA_MELONDS_SOURCE_ROOT', ROOT/'melonDS-source-1.1'))
    src = source_root/'src'
    text=(src/'frontend/qt_sdl/EmuInstance.cpp').read_text(encoding='utf-8')
    start=text.index('u32 EmuInstance::decompressROM(')
    decompress=text[start:text.index('\nvoid EmuInstance::clearBackupState',start)].replace('EmuInstance::','')
    wifi=(src/'Wifi.cpp').read_text(encoding='utf-8')
    start=wifi.index('        // TODO: what are the maximum crop values?')
    crop=wifi[start:wifi.index('\n        break;',start)]
    program=r'''
#include <zstd.h>
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <memory>
#include <vector>
using u8=uint8_t;using u32=uint32_t;using u64=uint64_t;
using std::unique_ptr;using std::make_unique;
'''+decompress+r'''
int main(){
  for(size_t size:{size_t(1),size_t(256),size_t(4096),size_t(16*1024*1024+512)}) {
    std::vector<u8> original(size,42),compressed(ZSTD_compressBound(size));
    auto* context=ZSTD_createCCtx();assert(context);
    for(int known:{0,1}) {
      assert(!ZSTD_isError(ZSTD_CCtx_setParameter(context,ZSTD_c_contentSizeFlag,known)));
      auto length=ZSTD_compress2(context,compressed.data(),compressed.size(),original.data(),size);
      assert(!ZSTD_isError(length));
      unique_ptr<u8[]> out;auto actual=decompressROM(compressed.data(),u32(length),out);
      assert(actual==size && !std::memcmp(out.get(),original.data(),size));
      out.reset();assert(decompressROM(compressed.data(),u32(length-1),out)==0);
    }
    ZSTD_freeCCtx(context);
  }
  for(int rxlen=40;rxlen<=2048;++rxlen) for(int cropRegister=0;cropRegister<=255;++cropRegister) {
    std::array<u8,2112> guarded;guarded.fill(0xA5);auto* RXBuffer=guarded.data()+32;
    for(int i=0;i<rxlen;++i) RXBuffer[i]=u8(i);
    const auto before=guarded;int framelen=rxlen-12;int framectl=1<<14;
#define IOPORT(ignored) (cropRegister<<7)
    for(int once=0;once<1;++once) {
'''+crop+r'''
    }
#undef IOPORT
    assert(std::equal(guarded.begin(),guarded.begin()+32,before.begin()));
    assert(std::equal(guarded.begin()+32+rxlen,guarded.end(),before.begin()+32+rxlen));
    assert(framelen>=0 && framelen<=rxlen-16);
    if(framelen>24) assert(!std::memcmp(RXBuffer+36,before.data()+72,framelen-24));
  }
  std::cout<<"Production zstd known/unknown/truncated/reallocation and 514304 wireless crop bounds passed\n";
}
'''
    compiler = os.environ.get('UNOVA_CXX') or shutil.which('g++')
    if not compiler:
        raise RuntimeError('Set UNOVA_CXX or add g++ to PATH to run this native boundary test.')
    compile_env=os.environ.copy()
    compiler_path=Path(compiler)
    if compiler_path.is_file():
        compile_env['PATH']=str(compiler_path.parent)+os.pathsep+compile_env.get('PATH','')
    with tempfile.TemporaryDirectory(prefix='unova-input-boundary-') as temp:
        path=Path(temp);(path/'check.cpp').write_text(program,encoding='utf-8')
        subprocess.run([compiler,'-std=c++20','-O2','-Wall','-Wextra','-Werror',str(path/'check.cpp'),'-lzstd','-o',str(path/'check.exe')],check=True,env=compile_env)
        subprocess.run([str(path/'check.exe')],check=True,env=compile_env)


class ReleaseInputBoundsTests(unittest.TestCase):
    def test_production_decompression_and_wireless_crop_bounds(self):
        source_root = Path(os.environ.get('UNOVA_MELONDS_SOURCE_ROOT', ROOT/'melonDS-source-1.1'))
        required = (source_root/'src/frontend/qt_sdl/EmuInstance.cpp', source_root/'src/Wifi.cpp')
        if not all(path.is_file() for path in required):
            if os.environ.get('UNOVA_MELONDS_SOURCE_ROOT'):
                self.fail(f'UNOVA_MELONDS_SOURCE_ROOT lacks required files: {required}')
            self.skipTest('optional melonDS source tree is unavailable; set UNOVA_MELONDS_SOURCE_ROOT')
        if not (os.environ.get('UNOVA_CXX') or shutil.which('g++')):
            self.skipTest('g++ is unavailable; set UNOVA_CXX or add it to PATH')
        env = os.environ.copy()
        env['UNOVA_MELONDS_SOURCE_ROOT'] = str(source_root)
        compiler=env.get('UNOVA_CXX') or shutil.which('g++')
        if compiler and Path(compiler).is_file():
            env['PATH']=str(Path(compiler).parent)+os.pathsep+env.get('PATH','')
        result = subprocess.run([sys.executable, str(Path(__file__).resolve())], cwd=ROOT,
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Production zstd known/unknown/truncated/reallocation and 514304 wireless crop bounds passed', result.stdout)


if __name__ == '__main__':
    run_boundary_check()
