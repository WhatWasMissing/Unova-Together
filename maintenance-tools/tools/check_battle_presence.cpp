#include "BattlePresence.h"
#include "BattlePresenceState.h"
#include "OverworldDebug.h"
#include "NativeCoopBattle.h"
#include <QFile>
#include <QFileInfo>
#include <QCoreApplication>
#include <cassert>
#include <iostream>
#include <vector>

int main(int argc, char** argv)
{
    QCoreApplication app(argc,argv);
    std::vector<unsigned char> ram(0x400000);
    auto set=[&](quint32 a,quint32 value) { qToLittleEndian(value,ram.data()+a-0x02000000); };
    assert(!InspectBattlePresence(ram.data(),ram.size()).value("battleStateKnown").toBool());
    set(0x02141858,0x02200000); set(0x02200008,0x02200100);
    set(0x02200100,0x02090010); set(0x02200104,0xFFFFFFFF); set(0x02200114,0x02200200);
    set(0x02200208,0x02200300); set(0x02200308,0x02200400);
    set(0x02200400,0x021C9EB8); set(0x02200404,36); set(0x02200408,2);
    auto field=InspectBattlePresence(ram.data(),ram.size());
    assert(field.value("battleStateKnown").toBool() && !field.value("inBattle").toBool());
    set(0x021418b0,0x02201000);
    assert(InspectNativeCoopBattle(ram.data(),ram.size()).value("cgearWirelessActive").toBool());
    set(0x02201000,0x0216d8fc);set(0x02201004,8);set(0x02201340,0x021756a0);
    assert(!InspectNativeCoopBattle(ram.data(),ram.size()).value("cgearWirelessActive").toBool());
    set(0x021418b0,0);
    assert(!InspectNativeCoopBattle(ram.data(),ram.size()).value("cgearWirelessActive").toBool());
    set(0x02200404,167);
    assert(InspectBattlePresence(ram.data(),ram.size()).value("inBattle").toBool());
    set(0x02200404,36);
    assert(!InspectBattlePresence(ram.data(),ram.size()).value("inBattle").toBool());
    // Intro still runs the field overlay, but BattleCall must freeze the anchor.
    set(0x02200218,0x02200500);
    set(0x02200504,0x02168BAD); set(0x02200510,0x02200200);
    assert(InspectBattlePresence(ram.data(),ram.size()).value("inBattle").toBool());
    set(0x02200504,0x021684BD); // Wild-battle caller before the core child starts.
    assert(InspectBattlePresence(ram.data(),ram.size()).value("inBattle").toBool());
    set(0x02200504,0x0215B50D); // Ordinary Pokemon menu callback.
    assert(!InspectBattlePresence(ram.data(),ram.size()).value("inBattle").toBool());
    set(0x02200504,0x0215A875);
    set(0x0220021c,0x02200600);set(0x022007b0,0x02200800);
    set(0x02200800,383u<<16);
    assert(InspectBattlePresence(ram.data(),ram.size()).value("inMenu").toBool());
    assert(InspectBattlePresence(ram.data(),ram.size()).value("menuMap").toInt()==383);
    set(0x02200510,0); // A stale parent cannot retain a menu position.
    assert(!InspectBattlePresence(ram.data(),ram.size()).value("inMenu").toBool());
    set(0x02200510,0x02200200);
    set(0x02200218,0);
    set(0x02200418,0x02200400); // Cycle must fail closed.
    assert(!InspectBattlePresence(ram.data(),ram.size()).value("battleStateKnown").toBool());
    set(0x02200418,0xFFFFFFFF);
    assert(!InspectBattlePresence(ram.data(),ram.size()).value("battleStateKnown").toBool());
    // Same-map renderer rebuild: the old player allocation may still look
    // valid and sit within a tile of its replacement. Follow ownership.
    set(0x02200418,0);set(0x02200218,0);
    set(0x02200220,0x02201000);set(0x02201004,0x02200200);
    set(0x02201008,0x02200600);set(0x02200600+0x1b0,0x02200800);
    set(0x022010e0,439);set(0x02200800,439u<<16);
    set(0x02200808,1u|(1u<<16));set(0x02200810,1);set(0x02200814,439);
    set(0x02201094,0x02202000);set(0x02202000,0x02201000);
    set(0x02202004,0x02202100);set(0x02202104,0x02200200);
    set(0x02202108,0x02201000);set(0x0220211c,0x02203000);
    set(0x02201040,0x02204000);set(0x02203088,0x02204000);
    set(0x0220303c,10);set(0x02203040,20);
    set(0x02203044,10*65536+32768);set(0x0220304c,20*65536+32768);
    OverworldTracker rebuilt;
    auto first=rebuilt.Sample(ram.data(),ram.size());
    assert(first.value("fieldPositionOwned").toBool() && first.value("map").toInt()==439);
    set(0x0220211c,0x02203100);set(0x02203188,0x02204000);
    set(0x0220313c,11);set(0x02203140,20);
    set(0x02203144,11*65536+32768);set(0x0220314c,20*65536+32768);
    auto replacement=rebuilt.Sample(ram.data(),ram.size());
    assert(replacement.value("tileX").toInt()==11);
    assert(replacement.value("actorAddress").toString()=="0X02203144");
    assert(!replacement.value("moving").toBool());
    // Outdoor cell changes must override both cached entry zones. Reject a
    // damaged grid rather than advertising either stale map.
    set(0x022010e0,430);set(0x02200800,437u<<16);
    set(0x02200814,446);
    auto currentCell=rebuilt.Sample(ram.data(),ram.size());
    assert(currentCell.value("map").toInt()==446);
    set(0x02200810,2);
    assert(rebuilt.Sample(ram.data(),ram.size()).value("map").toInt()==0);
    set(0x02200810,1);set(0x02200814,439);
    set(0x022010e0,439);set(0x02200800,439u<<16);
    replacement=rebuilt.Sample(ram.data(),ram.size());
    BattlePresenceState absentSprite;
    absentSprite.update(replacement);
    absentSprite.update({{"status","In battle"},{"battleStateKnown",true},{"inBattle",true}});
    // Preserve the owned field/map dispatcher but remove its player during
    // allocation rebuilding. The retained pose is not fresh actor evidence.
    set(0x02201094,0);set(0x0223B448,0xffffffff);set(0x0223B450,0xffffffff);
    for(int i=0;i<3;++i) {
        const auto sample=rebuilt.Sample(ram.data(),ram.size());
        assert(sample.value("fieldMapOwned").toBool());
        assert(!sample.value("fieldPositionOwned").toBool());
        absentSprite.update(sample);
    }
    assert(!absentSprite.inBattle && absentSprite.anchor.isEmpty());
    set(0x022010e0,440);set(0x02200800,440u<<16);
    const auto unresolvedMap=rebuilt.Sample(ram.data(),ram.size());
    assert(unresolvedMap.value("map").toInt()==440 && unresolvedMap.value("fieldMapOwned").toBool());
    assert(unresolvedMap.value("status")!="Experimental match");
    BattlePresenceState presence;
    const QVariantMap overworld{{"status","Experimental match"},{"map",1042},{"battleStateKnown",true},{"inBattle",false}};
    const QVariantMap fighting{{"status","In battle"},{"battleStateKnown",true},{"inBattle",true}};
    const QVariantMap unknown{{"status","No actor match / transitioning"},{"battleStateKnown",false}};
    auto arena=overworld; arena["map"]=1129;
    presence.update(overworld);
    // Known field return with an unresolved sprite must not retain the old
    // battle/map. Unknown transitions and arena overlays cannot qualify.
    BattlePresenceState missingActor;missingActor.update(overworld);missingActor.update(fighting);
    QVariantMap ownedMap{{"status","No actor match / transitioning"},{"map",439},
        {"fieldMapOwned",true},{"battleStateKnown",true},{"inBattle",false}};
    auto uncertainMap=ownedMap;uncertainMap["battleStateKnown"]=false;
    for(int i=0;i<10;++i) missingActor.update(uncertainMap);
    assert(missingActor.inBattle);
    missingActor.update(ownedMap);missingActor.update(ownedMap);
    assert(missingActor.inBattle);
    missingActor.update(ownedMap);
    assert(!missingActor.inBattle && missingActor.anchor.isEmpty());
    assert(missingActor.mapForComparison(ownedMap,true)==439);
    assert(missingActor.mapForComparison(ownedMap,false)==0);
    assert(missingActor.mapForComparison(uncertainMap,true)==439);
    assert(missingActor.mapForComparison(unknown,true)==0);
    BattlePresenceState comparing;
    comparing.update(overworld);comparing.update(fighting);
    assert(comparing.mapForComparison(fighting,true)==1042);
    assert(comparing.mapForComparison(fighting,false)==0);
    for (int repeat=0; repeat<3; ++repeat)
    {
        presence.update(fighting);
        for (int transition=0; transition<100; ++transition)
        {
            presence.update(unknown); presence.update(arena);
            assert(presence.inBattle && presence.anchor.value("map").toInt()==1042);
        }
        presence.update(fighting);
        assert(presence.inBattle);
        presence.update(overworld);
        assert(!presence.inBattle && presence.anchor.value("map").toInt()==1042);
    }
    // Independent ordinary battles: no native result flags on either peer.
    BattlePresenceState other;
    auto otherField=overworld; otherField["map"]=489;
    other.update(otherField); other.update(fighting);
    presence.update(fighting);
    auto returned=arena; returned["fieldPositionOwned"]=true;
    auto transient=returned; transient["presenceTransient"]=true;
    for(int i=0;i<20;++i) presence.update(transient);
    assert(presence.inBattle);
    presence.update(returned); presence.update(unknown);
    presence.update(returned); presence.update(returned);
    assert(presence.inBattle);
    presence.update(returned);
    assert(!presence.inBattle && other.inBattle);
    otherField["fieldPositionOwned"]=true; otherField["map"]=490;
    for(int i=0;i<3;++i) other.update(otherField);
    assert(!other.inBattle && other.anchor.value("map").toInt()==490);
    // Dispatcher inspection can be unknown after cleanup even though the
    // current owned player and field camera are already live. Do not latch.
    auto cameraReturn=returned;cameraReturn["battleStateKnown"]=false;
    cameraReturn["cameraValid"]=true;cameraReturn["map"]=437;
    presence.update(fighting);
    for(int i=0;i<3;++i) presence.update(cameraReturn);
    assert(!presence.inBattle && presence.anchor.value("map").toInt()==437);
    presence.update(fighting);auto menuReturn=cameraReturn;menuReturn["inMenu"]=true;
    for(int i=0;i<100;++i) presence.update(menuReturn);
    assert(presence.inBattle);
    for(int i=0;i<3;++i) presence.update(cameraReturn);
    assert(!presence.inBattle);
    // Tilted/off-screen camera cannot keep a live returned field in battle.
    cameraReturn["cameraValid"]=false;
    for(int cycle=0;cycle<1000;++cycle) {
        presence.update(fighting);
        for(int gap=0;gap<5;++gap) presence.update(unknown);
        for(int frame=0;frame<3;++frame) presence.update(cameraReturn);
        assert(!presence.inBattle && presence.anchor.value("map").toInt()==437);
    }
    returned["map"]=1130; presence.update(returned);
    assert(presence.anchor.value("map").toInt()==1130);
    presence.update(fighting);
    auto completed=arena;
    completed["nativeCoopBattleCompleted"]=true;
    completed["nativeCoopCanStart"]=false;
    presence.update(completed);
    assert(presence.inBattle); // Outcome alone does not finish cleanup.
    completed["nativeCoopCanStart"]=true;
    completed["nativeCoopBattleEventQueued"]=true;
    presence.update(completed);
    assert(presence.inBattle);
    completed["nativeCoopBattleEventQueued"]=false;
    presence.update(completed);
    assert(!presence.inBattle && presence.anchor.value("map")==completed.value("map"));
    presence.update(fighting);
    presence.update({{"status","No active game"}});
    assert(!presence.inBattle && presence.anchor.isEmpty());
    std::cout << "Repeated battle transition checks passed\n";
    for (int i=1;i<argc;++i)
    {
        QFile file(QString::fromLocal8Bit(argv[i])); assert(file.open(QIODevice::ReadOnly));
        const auto bytes=file.readAll();
        const auto result=InspectBattlePresence(reinterpret_cast<const unsigned char*>(bytes.constData()),bytes.size());
        const auto name=QFileInfo(file).fileName();
        if (name=="laptop-host-multi-command.ramdump" || name=="pc-guest-multi-command.ramdump")
        {
            assert(result.value("battleStateKnown").toBool() && result.value("inBattle").toBool());
            OverworldTracker tracker;
            const auto sample=tracker.Sample(reinterpret_cast<const unsigned char*>(bytes.constData()),bytes.size());
            assert(sample.value("status")=="In battle");
            // A bad setup must never classify an unrelated dispatcher as battle.
            auto damaged=bytes;
            qToLittleEndian<quint32>(0, reinterpret_cast<unsigned char*>(damaged.data())+0x24e650+0x30);
            assert(!InspectBattlePresence(reinterpret_cast<const unsigned char*>(damaged.constData()),damaged.size()).value("inBattle").toBool());
        }
        if (name.contains("between-battles") || name.contains("multi-after") || name.contains("error"))
            assert(!result.value("inBattle").toBool());
        std::cout << argv[i] << ": known=" << result.value("battleStateKnown").toBool()
                  << " battle=" << result.value("inBattle").toBool() << '\n';
    }
    if (argc==5)
    {
        OverworldTracker tracker;
        for (int i=1;i<argc;++i)
        {
            QFile file(QString::fromLocal8Bit(argv[i])); assert(file.open(QIODevice::ReadOnly));
            const auto bytes=file.readAll();
            const auto sample=tracker.Sample(reinterpret_cast<const unsigned char*>(bytes.constData()),bytes.size());
            assert(sample.value("battleStateKnown").toBool());
            assert(sample.value("inBattle").toBool() == (i==2));
            if (i==2) assert(sample.value("status")=="In battle");
            if (i==1 || i==3) assert(sample.value("status")=="Experimental match");
            std::cout << "Tracker: " << sample.value("status").toString().toStdString() << '\n';
        }
    }
    if (argc==3)
    {
        QFile fieldFile(QString::fromLocal8Bit(argv[1])),menuFile(QString::fromLocal8Bit(argv[2]));
        assert(fieldFile.open(QIODevice::ReadOnly) && menuFile.open(QIODevice::ReadOnly));
        const auto fieldBytes=fieldFile.readAll(),menuBytes=menuFile.readAll();
        OverworldTracker tracker;
        const auto before=tracker.Sample(reinterpret_cast<const unsigned char*>(fieldBytes.constData()),fieldBytes.size());
        assert(before.value("status")=="Experimental match");
        // Unresolved transition publishes no cached location, but must not
        // destroy the anchor needed once menu ownership becomes valid.
        QByteArray gap(0x400000,0);
        const auto transient=tracker.Sample(reinterpret_cast<const unsigned char*>(gap.constData()),gap.size());
        assert(transient.value("map").toInt()==0 && !transient.value("inMenu").toBool());
        for(int i=0;i<100;++i)
        {
            const auto menu=tracker.Sample(reinterpret_cast<const unsigned char*>(menuBytes.constData()),menuBytes.size());
            assert(menu.value("status")=="Experimental match" && menu.value("inMenu").toBool());
            assert(menu.value("map")==before.value("map") && !menu.value("moving").toBool());
        }
        // The menu matrix entry zone may be stale after outdoor travel. Its
        // grid must preserve the verified field tile and never revert its map.
        const auto menuState=InspectBattlePresence(reinterpret_cast<const unsigned char*>(menuBytes.constData()),menuBytes.size());
        const auto matrix=menuState.value("menuMatrixAddress").toUInt();
        assert(matrix>=0x02000000);
        auto staleMenu=menuBytes;
        qToLittleEndian<quint16>(437,reinterpret_cast<unsigned char*>(staleMenu.data())+matrix-0x02000000+2);
        const auto retained=tracker.Sample(reinterpret_cast<const unsigned char*>(staleMenu.constData()),staleMenu.size());
        assert(retained.value("inMenu").toBool() && retained.value("map")==before.value("map"));
        assert(retained.value("menuMap")==before.value("map"));
        const auto after=tracker.Sample(reinterpret_cast<const unsigned char*>(fieldBytes.constData()),fieldBytes.size());
        assert(after.value("status")=="Experimental match" && !after.value("inMenu").toBool());
        std::cout<<"Owned native menu retains field presence and returns correctly\n";
    }
    return 0;
}
