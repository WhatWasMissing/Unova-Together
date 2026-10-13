#include "PresenceOverlay.h"
#include <QGuiApplication>
#include <cassert>
#include <iostream>
int main(int argc,char** argv)
{
    QGuiApplication app(argc,argv);
    QVariantList view,projection;
    for(int i=0;i<12;++i) view.append(i==0||i==4||i==8 ? 1.0 : 0.0);
    for(int i=0;i<16;++i) projection.append(i==0||i==5 ? 1.0 : 0.0);
    QVariantMap sample{{"status","Experimental match"},{"map",1042},{"cameraValid",true},
        {"cameraView",view},{"cameraProjection",projection},{"worldY",0}};
    PresenceCalibration c;
    assert(c.updateCamera(sample,0));
    auto gap=sample; gap["cameraValid"]=false;
    assert(c.updateCamera(gap,50));
    assert(c.updateCamera(gap,200));
    assert(c.updateCamera(gap,201));
    assert(!c.updateCamera(gap,401));
    assert(c.updateCamera(sample,250));
    gap["map"]=1043; assert(!c.updateCamera(gap,251));
    assert(c.updateCamera(sample,300));
    gap=sample; gap["status"]="In battle"; assert(!c.updateCamera(gap,301));
    // Recovery and another reconnect-like initial missing sample.
    PresenceCalibration reopened;
    gap=sample; gap["cameraValid"]=false;
    assert(!reopened.updateCamera(gap,0));
    assert(reopened.updateCamera(sample,50));
    assert(reopened.updateCamera(gap,100));
    assert(reopened.updateCamera(sample,150));
    assert(reopened.updateCamera(gap,351));
    assert(!reopened.updateCamera(gap,551));
    PresenceCalibration manual;
    assert(manual.calibrate(1042,{128,96},{144,96},{128,112},{10,10}));
    PresenceAvatar avatar; avatar.position={11,10};
    const auto box=PresenceAvatarBounds(manual,{10,10},avatar,false);
    assert(box.contains({144,80}));
    assert(!box.contains({100,80}));
    const auto marker=PresenceAvatarBounds(manual,{10,10},avatar,true);
    assert(marker.contains({144,90}));
    const auto blank=DrawPresenceOverlay(manual,{10,10},{},false,false,0);
    QVariantMap checkpoint{{"status","active"},{"map",1042},{"x",11},{"z",10}};
    assert(DrawPresenceOverlay(manual,{10,10},{},false,false,0,checkpoint)!=blank);
    checkpoint["map"]=1043;
    assert(DrawPresenceOverlay(manual,{10,10},{},false,false,0,checkpoint)==blank);
    checkpoint["map"]=1042; checkpoint["status"]="complete";
    assert(DrawPresenceOverlay(manual,{10,10},{},false,false,0,checkpoint)==blank);
    manual.valid=false;
    assert(PresenceAvatarBounds(manual,{10,10},avatar,false).isEmpty());
    std::cout << "Camera gap, expiry, map change, battle, and recovery checks passed\n";
}
