#include "PresenceOverlay.h"
#include <QGuiApplication>
#include <cassert>

int main(int argc,char** argv)
{
    QGuiApplication app(argc,argv);
    PresenceCalibration calibration;
    assert(calibration.calibrate(1,QPointF(128,140),QPointF(144,140),QPointF(128,156),QPointF(10,10)));
    PresenceAvatar avatar{"test","Player","South",QPointF(10,10),false,0,{},false};
    const auto normal=DrawPresenceOverlay(calibration,QPointF(10,10),{avatar},false,false,0);
    avatar.inBattle=true;
    const auto battle=DrawPresenceOverlay(calibration,QPointF(10,10),{avatar},false,false,0);
    assert(normal!=battle);
    // The icon is overhead; it must not change the trainer's feet or body.
    assert(normal.copy(110,118,36,25)==battle.copy(110,118,36,25));
    assert(battle.save("research/battle-badge-preview.png"));
    return 0;
}
