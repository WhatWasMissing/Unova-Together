#include "OverworldDebug.h"
#include "BattlePresenceState.h"
#include <QCoreApplication>
#include <QFile>
#include <cassert>
#include <iostream>
int main(int argc,char** argv) {
    QCoreApplication app(argc,argv);
    assert(argc>1);
    for(int i=1;i<argc;++i) {
        QFile file(QString::fromLocal8Bit(argv[i]));assert(file.open(QIODevice::ReadOnly));
        const auto ram=file.readAll();OverworldTracker tracker;
        BattlePresenceState presence;
        presence.update({{"status","Experimental match"},{"map",439},{"battleStateKnown",true}});
        presence.update({{"status","In battle"},{"battleStateKnown",true},{"inBattle",true}});
        for(int frame=0;frame<10;++frame) {
            const auto sample=tracker.Sample(reinterpret_cast<const unsigned char*>(ram.constData()),ram.size());
            assert(sample.value("status")=="Experimental match");
            assert(sample.value("fieldPositionOwned").toBool());
            assert(!sample.value("inBattle").toBool());presence.update(sample);
        }
        assert(!presence.inBattle && presence.anchor.value("map").toInt()>0);
        std::cout<<argv[i]<<": owned field returned, battle flag cleared\n";
    }
}
