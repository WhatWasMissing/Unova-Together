"""Compile the production encrypted-record decoder; IV/EV reads change no bytes."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'melonDS-source-1.1' if (ROOT/'melonDS-source-1.1').is_dir() else ROOT/'source/melonDS'

def main():
    source=(SOURCE/'src/frontend/qt_sdl/PokemonTrading.cpp').read_text()
    data=source[source.index('struct Data {'):source.index('bool valid(')]
    decoding=source[source.index('void crypt('):source.index('unsigned partyCount(')]
    tradeable=source[source.index('void tradeable('):source.index('QByteArray archiveEntry(')] if 'QByteArray archiveEntry(' in source else ''
    # Inspect's trade eligibility helper is unrelated to stats. Include its
    # actual production definition and cut at the following helper.
    start=source.index('void tradeable(')
    end=source.index('\n}',start)+2
    tradeable=source[start:end]
    inspect=source[source.index('QVariantMap Inspect('):source.index('QString CheckTradeable(')]
    cpp='''#include <QString>
#include <QByteArray>
#include <QVariantMap>
#include <QVariantList>
#include <QtEndian>
#include <array>
#include <algorithm>
#include <cstring>
#include <stdexcept>
#include <cassert>
#include <iostream>
namespace PokemonTrading {constexpr unsigned RecordSize=220;}
'''+data+decoding+tradeable+inspect+r'''
int main() {
    const unsigned values[6]={31,0,17,9,30,1};
    const unsigned evs[6]={255,0,4,1,250,0};
    for(unsigned permutation=0;permutation<24;++permutation) for(unsigned flags:{0u,0x80000000u,0x40000000u,0xc0000000u}) {
        QByteArray blocks(128,0);qToLittleEndian<quint16>(495,blocks.data());
        const unsigned pid=permutation<<13;
        blocks[57]=char((pid%25+7)%25);blocks[56]=char((3<<3)|(1<<1));
        qToLittleEndian<quint16>(quint16((pid>>16)^(pid&65535)),blocks.data()+4);
        unsigned packed=flags;for(unsigned i=0;i<6;++i) {packed|=values[i]<<(5*i);blocks[16+i]=char(evs[i]);}
        qToLittleEndian<quint32>(packed,blocks.data()+48);
        qToLittleEndian<quint16>('S',blocks.data()+64);
        unsigned checksum=0;for(int i=0;i<128;i+=2) checksum+=qFromLittleEndian<quint16>(blocks.constData()+i);
        checksum&=65535;std::array<unsigned,4> order{0,1,2,3};
        for(unsigned i=0;i<permutation;++i) std::next_permutation(order.begin(),order.end());
        QByteArray shuffled(128,0);for(unsigned i=0;i<4;++i) shuffled.replace(i*32,32,blocks.mid(order[i]*32,32));
        crypt(shuffled,checksum);
        QByteArray extension(84,0);extension[4]=5;
        qToLittleEndian<quint16>(10,extension.data()+6);qToLittleEndian<quint16>(20,extension.data()+8);crypt(extension,pid);
        QByteArray record(8,0);qToLittleEndian<quint32>(pid,record.data());qToLittleEndian<quint16>(checksum,record.data()+6);record+=shuffled;record+=extension;
        const auto before=record;const auto result=Inspect(record);assert(result.value("ok").toBool());
        const auto iv=result.value("ivs").toList(),ev=result.value("evs").toList();unsigned total=0;
        assert(iv.size()==6 && ev.size()==6);unsigned display=0;
        for(unsigned raw:{0u,1u,2u,4u,5u,3u}) {assert(iv[display].toUInt()==values[raw]);assert(ev[display].toUInt()==evs[raw]);total+=evs[raw];++display;}
        assert(result.value("evTotal").toUInt()==total);assert(record==before);
        assert(result.value("nature").toUInt()==(pid%25+7)%25);
        assert(result.value("gender").toUInt()==1 && result.value("form").toUInt()==3);
        assert(result.value("shiny").toBool());
        assert(result.value("egg").toBool()==bool(flags&0x40000000u));
        auto corrupt=record;corrupt[8]=char(corrupt[8]^1);assert(!Inspect(corrupt).value("ok").toBool());
        auto busy=record;busy[4]=1;assert(!Inspect(busy).value("ok").toBool());
    }
    assert(!Inspect(QByteArray(219,0)).value("ok").toBool());
    std::cout<<"96 encrypted IV/EV cases passed: 24 shuffles, egg/nickname flags, checksum/busy refusal, no writes.\n";
}
'''
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env['PATH']
    flags=shlex.split(subprocess.check_output(['C:/msys64/ucrt64/bin/pkg-config.exe','--cflags','--libs','Qt6Core'],env=env,text=True))
    with tempfile.TemporaryDirectory(prefix='unova-party-stats-') as temporary:
        directory=Path(temporary);path=directory/'stats.cpp';path.write_text(cpp)
        exe=directory/'stats.exe'
        subprocess.run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Wall','-Wextra','-Werror',str(path),'-o',str(exe),*flags],env=env,check=True)
        subprocess.run([str(exe)],env=env,check=True)

if __name__=='__main__':main()
