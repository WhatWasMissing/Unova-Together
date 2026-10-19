// Exercise the production client event handler with hostile ENet records.
#include <string>
#include <vector>
#include <map>
#include <queue>
#include <array>
#include <thread>
#include <mutex>
#include <atomic>
#include <condition_variable>
#define private public
#include "LAN.h"
#undef private
#include <cassert>
#include <cstring>
#include <iostream>
#include <chrono>
namespace melonDS::Platform {
struct Mutex {std::mutex value;};
Mutex* Mutex_Create(){return new Mutex;}
void Mutex_Free(Mutex* m){delete m;}
void Mutex_Lock(Mutex* m){m->value.lock();}
void Mutex_Unlock(Mutex* m){m->value.unlock();}
void Log(LogLevel,const char*,...){}
u64 GetMSCount(){return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
}
int main() {
    using namespace melonDS;LAN guest;ENetPeer host{},outsider{};
    guest.RemotePeers[0]=&host;guest.MyPlayer.ID=1;
    std::array<LAN::Player,16> players{};players[0].Status=LAN::Player_Host;
    auto send=[&](ENetPeer* peer){
        std::array<unsigned char,2+sizeof(players)> wire{};wire[0]=3;wire[1]=1;
        std::memcpy(wire.data()+2,players.data(),sizeof(players));
        ENetEvent event{};event.type=ENET_EVENT_TYPE_RECEIVE;event.peer=peer;
        event.packet=enet_packet_create(wire.data(),wire.size(),0);
        guest.ProcessClientEvent(event);
    };
    for(int id:{-1,16,0x7fffffff}) {
        players[0].ID=id;send(&host);assert(guest.NumPlayers==0);
    }
    players[0].ID=0;players[0].Status=static_cast<LAN::PlayerStatus>(999);
    send(&host);assert(guest.NumPlayers==0);
    players[0].Status=LAN::Player_Host;send(&outsider);assert(guest.NumPlayers==0);
    send(&host);assert(guest.NumPlayers==1 && guest.Players[0].ID==0);
    // Defense in depth: even stale/corrupted ID fields cannot index peers.
    guest.Players[0].ID=0x7fffffff;host.data=&guest.Players[0];
    ENetEvent gone{};gone.type=ENET_EVENT_TYPE_DISCONNECT;gone.peer=&host;
    guest.ProcessClientEvent(gone);assert(guest.RemotePeers[0]==nullptr);
    assert(guest.RecoveryState==1);
    std::cout<<"Malformed/source-spoofed player lists rejected; disconnect indexes owned slot\n";
}
