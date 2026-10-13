#include "PresenceOverlay.h"
#include <QGuiApplication>
#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>

static QVariantMap state(double x,double z,int map=1,bool moving=false,bool battle=false)
{
    return {{"active",true},{"map",map},{"smoothX",x},{"smoothZ",z},{"worldY",0.0},{"moving",moving},{"inBattle",battle},{"facing","East"}};
}
static PresenceCalibration camera(bool rotate=false)
{
    PresenceCalibration c;c.valid=true;c.automatic=true;c.map=1;
    const double s=std::sqrt(0.5),v[12]={1,0,0,0,s,s,0,-s,s,-168,-30+s*168,-150-s*168};
    const double rotated[12]={0,-s,s,0,s,s,-1,0,0,168,-30+s*168,-150-s*168};
    for(int i=0;i<12;++i) c.view[i]=rotate?rotated[i]:v[i];
    c.projection[0]=1.2;c.projection[5]=1.6;c.projection[10]=-1.002;c.projection[11]=-1;c.projection[14]=-2.002;
    return c;
}

int main(int argc,char** argv) {
    PresenceAvatar animation;animation.facing="East";animation.moving=true;
    assert(PresenceSpriteFrame(animation,140)==10);
    animation.inBattle=true;assert(PresenceSpriteFrame(animation,140)==9);
    animation.inBattle=false;animation.activity="busy";assert(PresenceSpriteFrame(animation,140)==10); // Availability does not freeze a walking player.
    animation.activity.clear();animation.moving=false;
    for(int ms=0;ms<2000;ms+=140) assert(PresenceSpriteFrame(animation,ms)==9);

    QGuiApplication app(argc,argv);
    for(int i=0;i<24;++i) animation.sprites.append(QImage(32,32,QImage::Format_ARGB32));
    animation.moving=true;animation.running=true;animation.positionDrivenStride=true;animation.position={10.6,10};
    assert(PresenceSpriteFrame(animation,0)==22);
    assert(PresenceSpriteFrame(animation,9999)==22); // No clock-driven sliding.
    animation.position={11.6,10};assert(PresenceSpriteFrame(animation,0)==23);
    animation.moving=false;assert(PresenceSpriteFrame(animation,0)==9);
    animation.moving=true;animation.inBattle=true;assert(PresenceSpriteFrame(animation,0)==9);
    animation.inBattle=false;animation.sprites=animation.sprites.mid(0,12);
    assert(PresenceSpriteFrame(animation,0)==11); // Older replacement textures.
    PresenceCalibration c;assert(c.calibrate(1,{128,140},{144,140},{128,156},{10,10}));
    PresenceAvatar a{"a","","South",{10,10},false,0,{},false,{}};
    for(int i=0;i<12;++i) {QImage frame(32,32,QImage::Format_ARGB32);frame.fill(i%3==0?Qt::red:i%3==1?Qt::green:Qt::blue);a.sprites.append(frame);}
    auto idle=DrawPresenceOverlay(c,{10,10},{a},false,false,140);
    assert(idle.pixelColor(128,125)==QColor(Qt::red));
    a.moving=true;auto walking=DrawPresenceOverlay(c,{10,10},{a},false,false,140);
    assert(walking.pixelColor(128,125)==QColor(Qt::green));a.moving=false;
    auto local=a;auto behind=DrawPresenceOverlay(c,{10,10},{a},false,false,0,{},local);
    assert(behind.pixelColor(128,125).alpha()==0);
    a.position={10,10.4};auto front=DrawPresenceOverlay(c,{10,10},{a},false,false,0,{},local);
    assert(front.pixelColor(128,125)==QColor(Qt::red));
    a.position={10,14};auto offscreen=DrawPresenceOverlay(c,{10,10},{a},false,false,0);
    assert(offscreen!=DrawPresenceOverlay(c,{10,10},{},false,false,0)); // Feet off-screen; upper sprite is still visible.
    assert(!PresenceAvatarBounds(c,{10,10},a,false).isEmpty());
    a.position={10,16};assert(PresenceAvatarBounds(c,{10,10},a,false).isEmpty());
    for(const auto& position: {QPointF(-10,10),QPointF(30,10),QPointF(10,-10),QPointF(10,30)})
    {
        a.position=position;const auto hint=FollowPresenceAvatar(c,{10,10},a);
        assert(hint.valid && !hint.onScreen);
        assert(hint.anchor.x()>=12 && hint.anchor.x()<=244 && hint.anchor.y()>=14 && hint.anchor.y()<=178);
        assert(std::abs(std::hypot(hint.direction.x(),hint.direction.y())-1)<1e-6);
        assert(DrawPresenceOverlay(c,{10,10},{a},false,false,0,{}, {},"a")!=DrawPresenceOverlay(c,{10,10},{},false,false,0));
    }
    a.position={10,10};assert(FollowPresenceAvatar(c,{10,10},a).onScreen);
    assert(DrawPresenceOverlay(c,{10,10},{a},false,false,0,{}, {},"a")!=idle);
    a.activity="busy";const auto busy=DrawPresenceOverlay(c,{10,10},{a},false,false,0);
    a.activity="ready";const auto ready=DrawPresenceOverlay(c,{10,10},{a},false,false,0);assert(busy!=ready);
    a.inMenu=true;const auto menuBadge=DrawPresenceOverlay(c,{10,10},{a},false,false,0);assert(menuBadge!=ready && menuBadge!=busy);a.inMenu=false;
    a.inBattle=true;assert(DrawPresenceOverlay(c,{10,10},{a},false,false,0)!=ready);a.inBattle=false;
    a.position={std::numeric_limits<double>::quiet_NaN(),10};assert(!FollowPresenceAvatar(c,{10,10},a).valid);
    assert(PresenceAvatarBounds(c,{10,10},a,false).isEmpty());
    a.position={10,10};a.activity={};
    auto straight=camera(),rotated=camera(true);
    const auto straightBounds=PresenceAvatarBounds(straight,{10,10},a,false),rotatedBounds=PresenceAvatarBounds(rotated,{10,10},a,false);
    assert(!straightBounds.isEmpty() && std::abs(straightBounds.width()-rotatedBounds.width())<1e-6);
    a.height=16;assert(PresenceAvatarBounds(straight,{10,10},a,false).top()<straightBounds.top());a.height=0;
    // Far trainers stay behind the local silhouette under a rotated camera.
    a.position={9.7,10};const auto hidden=DrawPresenceOverlay(rotated,{10,10},{a},false,false,0,{},local);
    assert(hidden.pixelColor(128,115).alpha()==0);
    a.position={10.3,10};const auto foreground=DrawPresenceOverlay(rotated,{10,10},{a},false,false,0,{},local);
    assert(foreground.pixelColor(128,115)==QColor(Qt::red));
    // Ties and invalid projections must not depend on peer arrival order.
    auto b=a;b.id="b";for(auto& image:b.sprites) image.fill(Qt::blue);
    auto bad=a;bad.id="invalid";bad.position.setX(std::numeric_limits<double>::quiet_NaN());
    assert(DrawPresenceOverlay(rotated,{10,10},{a,b,bad},false,false,0)==DrawPresenceOverlay(rotated,{10,10},{bad,b,a},false,false,0));
    auto sample=QVariantMap{{"status","Experimental match"},{"map",1},{"cameraValid",true},{"worldY",0.0}};
    QVariantList view,projection;for(double number:straight.view)view.append(number);for(double number:straight.projection)projection.append(number);
    sample["cameraView"]=view;sample["cameraProjection"]=projection;PresenceCalibration retained;
    assert(retained.updateCamera(sample,1000));
    view[0]=std::numeric_limits<double>::quiet_NaN();sample["cameraView"]=view;
    assert(retained.updateCamera(sample,1100) && retained.view[0]==1);
    assert(retained.updateCamera(sample,1250));
    assert(!retained.updateCamera(sample,1450));sample["map"]=2;assert(!retained.updateCamera(sample,1100));
    QList<PresenceMotionFrame> frames{{100,state(10,10)},{200,state(11,10,1,true)}};
    auto pose=SamplePresenceMotion(frames,250);assert(pose.value("active").toBool() && std::abs(pose.value("smoothX").toDouble()-10.5)<1e-6 && pose.value("moving").toBool());
    frames.append({300,state(11,10)});pose=SamplePresenceMotion(frames,400);assert(!pose.value("moving").toBool());
    assert(!SamplePresenceMotion(frames,2300).value("active").toBool());
    frames.append({400,state(40,30,2,true)});pose=SamplePresenceMotion(frames,450);assert(pose.value("map")==2 && pose.value("smoothX")==40.0 && !pose.value("moving").toBool());
    frames.append({500,state(50,30,2,true)});pose=SamplePresenceMotion(frames,550);assert(pose.value("smoothX")==50.0 && !pose.value("moving").toBool());
    frames.append({600,state(50,30,2,true,true)});assert(!SamplePresenceMotion(frames,700).value("moving").toBool());
    auto corrupt=state(50,30);corrupt["smoothX"]=std::numeric_limits<double>::quiet_NaN();frames.append({700,corrupt});assert(!SamplePresenceMotion(frames,750).value("active").toBool());
    frames={{100,state(10,10)},{200,state(11,10,1,true)}};frames[0].state["worldY"]=0;frames[1].state["worldY"]=16;
    assert(std::abs(SamplePresenceMotion(frames,250).value("worldY").toDouble()-8)<1e-6);
    assert(!SamplePresenceMotion(frames,550).value("moving").toBool());
    frames={{0,state(10,10)},{50,state(10.2,10,1,true)},{100,state(10.4,10,1,true)},{150,state(10.6,10,1,true)},{200,state(10.8,10,1,true)}};
    assert(!SamplePresenceMotion(frames,250).value("running").toBool());
    for(int i=0;i<frames.size();++i) frames[i].state["smoothX"]=10+i*0.4;
    assert(SamplePresenceMotion(frames,250).value("running").toBool());
    frames.append({250,state(11.6,10)});assert(!SamplePresenceMotion(frames,350).value("running").toBool());
    // Companion art preserves large dimensions and reduced motion suppresses
    // idle breathing while retaining the image and reaction symbols.
    auto companion=a;companion.id="companion";companion.position={10,10};companion.companion=true;companion.moving=false;
    companion.sprites.clear();QImage large(64,66,QImage::Format_ARGB32);large.fill(Qt::transparent);
    for(int y=2;y<64;++y) for(int x=1;x<63;++x) large.setPixelColor(x,y,Qt::red);
    for(int i=0;i<12;++i) companion.sprites.append(large);
    companion.companionMotionScale=0;
    assert(PresenceAvatarBounds(c,{10,10},companion,false).width()>40);
    assert(DrawPresenceOverlay(c,{10,10},{companion},false,false,0)==DrawPresenceOverlay(c,{10,10},{companion},false,false,700));
    companion.companionReactionStarted=0;companion.companionReactionUntil=2000;companion.companionEmote="!";companion.companionMotion="run";
    assert(DrawPresenceOverlay(c,{10,10},{companion},false,false,100)==DrawPresenceOverlay(c,{10,10},{companion},false,false,700));
    // The union of local gait silhouettes makes occlusion independent of
    // whichever stride pose is showing this frame.
    local.sprites[1].fill(Qt::transparent);local.moving=true;a.position={10,10};a.moving=false;
    assert(DrawPresenceOverlay(c,{10,10},{a},false,false,0,{},local)==DrawPresenceOverlay(c,{10,10},{a},false,false,140,{},local));
    std::cout<<"Standing/walking, stable depth, rotated camera sizing, screen edges, follow/status markers, camera gaps, large companions, reduced motion and continuous motion checks pass\n";
}
