"""Compile actual production decompression/crop code in isolated boundary tests."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'melonDS-source-1.1/src'
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
with tempfile.TemporaryDirectory(prefix='unova-input-boundary-') as temp:
    path=Path(temp);(path/'check.cpp').write_text(program,encoding='utf-8')
    subprocess.run(['g++','-std=c++20','-O2','-Wall','-Wextra','-Werror',str(path/'check.cpp'),'-lzstd','-o',str(path/'check.exe')],check=True)
    subprocess.run([str(path/'check.exe')],check=True)
