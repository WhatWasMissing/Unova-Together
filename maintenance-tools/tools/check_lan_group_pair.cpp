// Unova Together group pairing regression fixture. mvq1303 / WhatWasMissing.
// Uses real ENet sockets; no trainer outcomes or saves are fabricated.
#include <mutex>
#include <queue>
#include <array>
#include <atomic>
#include <thread>
#include <enet/enet.h>
#define private public
#include "LAN.h"
#undef private
#include <mutex>
#include <thread>
#include <atomic>
#include <chrono>
#include <cassert>
#include <iostream>
namespace melonDS::Platform {
struct Mutex {std::mutex value;};
Mutex* Mutex_Create() {return new Mutex;}
void Mutex_Free(Mutex* m) {delete m;}
void Mutex_Lock(Mutex* m) {m->value.lock();}
void Mutex_Unlock(Mutex* m) {m->value.unlock();}
void Log(LogLevel,const char*,...) {}
u64 GetMSCount() {return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
}
int main() {
    using namespace melonDS;
    LAN host,first,second;
    assert(host.StartHost("group-host",16));
    std::recursive_mutex lock;std::atomic<bool> stop{false};
    std::thread worker([&]{while(!stop) {{std::lock_guard guard(lock);host.Process();first.Process();second.Process();}std::this_thread::sleep_for(std::chrono::milliseconds(2));}});
    assert(first.StartClient("first-spectator","127.0.0.1"));
    auto wait=[&](const auto& condition) {
        for(int n=0;n<100;++n) {{std::lock_guard guard(lock);host.Process();first.Process();second.Process();if(condition()) return true;}
            std::this_thread::sleep_for(std::chrono::milliseconds(2));}return false;
    };
    assert(wait([&]{return host.GetNumPlayers()==2;}));
    assert(second.StartClient("second-partner","127.0.0.1"));
    stop=true;worker.join();
    assert(wait([&]{return host.GetNumPlayers()==3 && first.GetNumPlayers()==3 && second.GetNumPlayers()==3;}));
    std::array<u8,32> digest{};digest.fill(42);
    std::cerr<<"connected\n";host.BeginCoopChallenge(156,digest);
    assert(wait([&]{return first.CoopInvitation()==156 && second.CoopInvitation()==156;}));
    first.DeclineCoopInvitation();
    assert(wait([&]{return first.CoopInvitation()==0;}));
    assert(host.CoopChallengeStatus()==0);
    std::cerr<<"invited\n";second.BeginCoopChallenge(156,digest);
    assert(wait([&]{return host.CoopChallengeStatus()==1 && second.CoopChallengeStatus()==1 && first.CoopInvitation()==0;}));
    assert(host.CoopPartnerID()==2 && second.CoopPartnerID()==0);
    std::cerr<<"paired\n";first.BeginCoopChallenge(156,digest);first.ClearCoopChallenge();
    assert(wait([&]{return host.CoopChallengeStatus()==1 && second.CoopChallengeStatus()==1;}));
    host.SetCoopStoryReady();second.SetCoopStoryReady();
    assert(wait([&]{return host.CoopStoryReady() && second.CoopStoryReady();}));
    std::cerr<<"ready\n";host.Begin(0);first.Begin(0);second.Begin(0);
    u8 payload[5]={1,2,3,4,5},incoming[2048]{};u64 timestamp=0;
    host.SendPacket(0,payload,5,123);
    assert(wait([&]{return second.RecvPacket(0,incoming,&timestamp)==5;}));
    assert(timestamp==123 && std::equal(payload,payload+5,incoming));
    for(unsigned i=0;i<30;++i) {first.Process();assert(first.RecvPacket(0,incoming,&timestamp)==0);}
    first.SendReply(0,payload,5,456,1);second.SendReply(0,payload,5,456,1);
    u8 replies[15*1024]{};
    assert(wait([&]{return host.RecvReplies(0,replies,456,2)==2;}));
    std::cerr<<"radio\n";host.SetCoopStoryResult(1);second.SetCoopStoryResult(1);
    assert(wait([&]{return host.CoopStoryResultStatus()==1 && second.CoopStoryResultStatus()==1;}));
    std::cerr<<"result\n";host.SetCoopStoryCleanupDone();second.SetCoopStoryCleanupDone();
    assert(wait([&]{return host.CoopRemoteStoryCleanupDone() && second.CoopRemoteStoryCleanupDone();}));
    host.ClearCoopChallenge();second.ClearCoopChallenge();
    assert(host.CoopInvitation()==0 && second.CoopInvitation()==0);
    host.BeginCoopChallenge(764,digest);
    assert(wait([&]{return first.CoopInvitation()==764;}));
    first.BeginCoopChallenge(764,digest);
    assert(wait([&]{return host.CoopChallengeStatus()==1 && first.CoopChallengeStatus()==1;}));
    assert(host.CoopPartnerID()==1);
    host.SetCoopStoryResult(1);first.SetCoopStoryResult(2);
    assert(wait([&]{return host.CoopStoryResultStatus()==-1 && first.CoopStoryResultStatus()==-1;}));
    assert(!host.CoopRemoteStoryCleanupDone());
    host.ClearCoopChallenge();first.ClearCoopChallenge();
    host.BeginCoopChallenge(156,digest);
    assert(wait([&]{return second.CoopInvitation()==156;}));
    second.BeginCoopChallenge(156,digest);
    assert(wait([&]{return host.CoopChallengeStatus()==1 && second.CoopChallengeStatus()==1;}));
    for(auto* peer:first.RemotePeers) if(peer) enet_peer_disconnect_now(peer,0);
    std::cerr<<"end first start\n";first.EndSession();std::cerr<<"end first done\n";
    // EndSession destroys its socket; service the surviving cores until ENet
    // reports the lost peer, rather than processing a core from two threads.
    assert(wait([&]{return host.GetNumPlayers()==2 && second.GetNumPlayers()==2;}));
    std::cerr<<"remaining "<<host.GetNumPlayers()<<" "<<second.GetNumPlayers()<<"\n";
    assert(host.CoopChallengeStatus()==1 && host.CoopPartnerConnected());
    for(auto* peer:second.RemotePeers) if(peer) enet_peer_disconnect_now(peer,0);
    second.EndSession();assert(wait([&]{return !host.CoopPartnerConnected();}));
    host.EndSession();std::cout<<"Three-player lobby: second guest pairs; readiness/result/cleanup, radio isolation and partner disconnect pass.\n";
}
