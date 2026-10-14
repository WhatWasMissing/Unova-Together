#include "CheckpointStorage.h"
#include "Platform.h"
#include <cassert>
#include <cstring>
#include <iostream>
namespace melonDS::Platform {void Log(LogLevel,const char*,...) {}}
int main() {
    QByteArray payload(8*1024*1024,'a');
    auto write=[&](melonDS::Savestate& state) {state.Section("TEST");state.VarArray(payload.data(),payload.size());return !state.Error;};
    melonDS::Savestate baseline;assert(write(baseline));baseline.Finish();
    const QByteArray expected(static_cast<const char*>(baseline.Buffer()),baseline.Length());
    CheckpointStorage storage;auto first=storage.capture(write);assert(first==expected);
    const auto retained=first;QByteArray current;
    for(int i=0;i<12;++i) {
        payload.fill(char('b'+i));current=storage.capture(write);assert(!current.isEmpty());assert(retained==expected);
        melonDS::Savestate load(current.data(),current.size(),false);load.Section("TEST");
        QByteArray restored(payload.size(),0);load.VarArray(restored.data(),restored.size());assert(!load.Error && restored==payload);
    }
    const auto before=current;
    assert(storage.capture([](melonDS::Savestate&){return false;}).isEmpty());assert(current==before);
    QByteArray survived;
    {CheckpointStorage temporary;survived=temporary.capture(write);}
    melonDS::Savestate load(survived.data(),survived.size(),false);load.Section("TEST");QByteArray restored(payload.size(),0);load.VarArray(restored.data(),restored.size());assert(!load.Error && restored==payload);
    std::cout<<"Checkpoint bytes, 12 capture/load cycles, retained snapshots, failed captures and storage lifetime passed.\n";
}
