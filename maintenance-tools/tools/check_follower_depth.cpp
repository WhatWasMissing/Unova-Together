// Unova Together: Copyright (C) 2026 mvq1303. GPL-3.0-or-later.
// Exercises the actual frontend renderer with synthetic scene depth; no ROM required.
#include "PresenceOverlay.h"
#include "PresenceOcclusion.h"
#include <QGuiApplication>
#include <algorithm>
#include <array>
#include <iostream>
#include <limits>
#include <stdexcept>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
int pixels(const QImage& image) {
    int count=0;
    for(int y=0;y<image.height();++y) for(int x=0;x<image.width();++x)
        count+=image.pixelColor(x,y).alpha()!=0;
    return count;
}
int spritePixels(const QImage& image) {
    int count=0;
    for(int y=0;y<image.height();++y) for(int x=0;x<image.width();++x)
        count+=image.pixelColor(x,y)==QColor(Qt::red);
    return count;
}
PresenceCalibration camera(bool rotated=false) {
    PresenceCalibration c;c.valid=true;c.automatic=true;c.map=1;
    const double tilt=std::sqrt(0.5);
    c.view[0]=1;c.view[4]=c.view[5]=c.view[8]=tilt;c.view[7]=-tilt;
    c.view[9]=-168;c.view[10]=-8+tilt*168;c.view[11]=-150-tilt*168;
    if(rotated) {
        c.view[0]=c.view[7]=c.view[8]=0;c.view[1]=-tilt;c.view[2]=tilt;c.view[6]=-1;c.view[9]=168;
    }
    // The native field camera's near/far planes are 1 and 1024.
    c.projection[0]=2.0606;c.projection[5]=2.7475;
    c.projection[10]=-1025.0/1023;c.projection[11]=-1;c.projection[14]=-2048.0/1023;
    return c;
}
PresenceAvatar follower() {
    PresenceAvatar a;a.id="local/companion";a.position={10,10};a.companion=true;
    a.facing="South";
    QImage sprite(32,32,QImage::Format_ARGB32);sprite.fill(Qt::red);
    for(int i=0;i<12;++i) a.sprites.append(sprite);
    return a;
}
}

int main(int argc,char** argv) {
    QGuiApplication app(argc,argv);
    int failed=0,passed=0;
    auto test=[&](const char* name,auto run) {
        try {run();++passed;std::cout<<"PASS "<<name<<'\n';}
        catch(const std::exception& e) {++failed;std::cerr<<"FAIL "<<name<<": "<<e.what()<<'\n';}
    };
    test("nearby foreground and invalid scene depths",[] {
        require(melonDS::IsPresenceOccludedByDepth(0.9928f,0.9933f),"nearby object does not occlude follower");
        require(!melonDS::IsPresenceOccludedByDepth(0.9938f,0.9933f),"background hides follower");
        require(!melonDS::IsPresenceOccludedByDepth(0.9933f,0.9933f),"equal depth hides follower");
        for(float bad:{-1.f,2.f,std::numeric_limits<float>::infinity(),-std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN()})
            require(!melonDS::IsPresenceOccludedByDepth(bad,0.5f),"invalid depth treated as foreground");
    });
    test("projected depth matches native Z quantization",[] {
        const auto c=camera();const auto a=follower();
        const double z=-150*c.projection[10]+c.projection[14];
        const auto native=(std::trunc(z/150*0x4000)+0x3FFF)/32768.0;
        require(std::abs(c.projectWorldDepth(a.position,0)-native)<1e-12,"actor uses idealized GL depth instead of native Z depth");
    });
    test("foreground covers image, shadow and reactions",[] {
        const auto c=camera();auto a=follower();std::array<float,256*192> depth;
        depth.fill(float(c.projectWorldDepth(a.position,a.height)-0.0005));
        for(const auto* motion:{"","spin","hop","sway"}) {
            a.companionMotion=motion;a.companionReactionStarted=0;a.companionReactionUntil=2000;
            const auto image=DrawPresenceOverlay(c,a.position,{a},false,false,100,{}, {},{},depth.data());
            // Reaction bubbles are UI; the actor and its ground shadow are scenery-clipped.
            require(*motion?spritePixels(image)==0:pixels(image)==0,
                    "foreground leaves follower or its shadow visible");
        }
    });
    test("screen-space edges under fractional and rotated projection",[] {
        for(bool companion:{false,true}) for(bool rotated:{false,true}) for(double height:{0.0,16.0}) for(double offset:{-0.04,-0.015,0.0,0.015,0.04}) {
            const auto c=camera(rotated);auto a=follower();a.position.rx()+=offset;
            a.companion=companion;a.height=height;
            std::array<float,256*192> depth;depth.fill(1);
            const float near=float(c.projectWorldDepth(a.position,a.height)-0.0005);
            for(int y=0;y<192;++y) for(int x=0;x<128;++x) depth[y*256+x]=near;
            const auto baseline=DrawPresenceOverlay(c,a.position,{a},false,false,0);
            const auto clipped=DrawPresenceOverlay(c,a.position,{a},false,false,0,{}, {},{},depth.data());
            require(pixels(baseline)>100,"fixture does not render follower");
            for(int y=0;y<192;++y) for(int x=0;x<256;++x)
                require(x<128?clipped.pixelColor(x,y).alpha()==0:clipped.pixel(x,y)==baseline.pixel(x,y),
                        "clip boundary shifts or leaks across screen pixels");
        }
    });
    test("co-op player sprites and shadows use scene depth",[] {
        const auto c=camera();auto a=follower();a.companion=false;a.id="peer";
        std::array<float,256*192> depth;
        depth.fill(float(c.projectWorldDepth(a.position,a.height)-0.0005));
        require(pixels(DrawPresenceOverlay(c,a.position,{a},false,false,0,{}, {},{},depth.data()))==0,
                "co-op player overlays foreground objects");
        require(pixels(DrawPresenceOverlay(c,a.position,{a},true,false,0,{}, {},{},depth.data()))>0,
                "navigation marker was hidden by actor depth clipping");
        a.name="Peer";a.inMenu=true;
        const auto labelled=DrawPresenceOverlay(c,a.position,{a},false,false,0,{}, {},{},depth.data());
        require(pixels(labelled)>0 && spritePixels(labelled)==0,
                "co-op status label hidden, or hidden player art remains visible");
        a.name.clear();a.inMenu=false;
        depth.fill(1);
        require(DrawPresenceOverlay(c,a.position,{a},false,false,0,{}, {},{},depth.data())==
                DrawPresenceOverlay(c,a.position,{a},false,false,0),"co-op player pose changed on clear scene");
    });
    test("ground, background and missing depth preserve pose",[] {
        const auto c=camera();const auto a=follower();std::array<float,256*192> depth;
        const auto baseline=DrawPresenceOverlay(c,a.position,{a},false,false,0);
        require(pixels(baseline)>100,"fixture is empty");
        for(float value:{1.f,float(c.projectWorldDepth(a.position,a.height)),float(c.projectWorldDepth(a.position,a.height)+0.0005)}) {
            depth.fill(value);
            require(DrawPresenceOverlay(c,a.position,{a},false,false,0,{}, {},{},depth.data())==baseline,
                    "ground or background changes pose/visibility");
        }
    });
    test("idle and walking retain whole-image foot anchor",[] {
        const auto c=camera();auto a=follower();std::array<float,256*192> depth;depth.fill(1);
        for(bool moving:{false,true}) for(double motion:{0.0,1.0}) {
            a.moving=moving;a.companionMotionScale=motion;
            const auto baseline=DrawPresenceOverlay(c,a.position,{a},false,false,0,{}, {},{},depth.data());
            for(int ms:{70,140,280,700})
                require(DrawPresenceOverlay(c,a.position,{a},false,false,ms,{}, {},{},depth.data())==baseline,
                        "depth handling introduces time-based bobbing or warping");
        }
    });
    test("depth surfaces stay associated with display buffer",[] {
        const auto c=camera();const auto a=follower();std::array<float,256*192> hidden,clear;hidden.fill(0);clear.fill(1);
        PresenceSurface surface;
        surface.publishRenderer(PresenceSurface::ProjectedRenderer([&](const QVariantMap&,qint64,const float* depth) {
            return DrawPresenceOverlay(c,a.position,{a},false,false,0,{}, {},{},depth);
        }),true,true);
        surface.publishFrameProjection({},0,nullptr,hidden.data());
        surface.publishFrameProjection({},1,nullptr,clear.data());
        require(pixels(surface.snapshot(0))==0,"wrong depth buffer used for front display");
        require(pixels(surface.snapshot(1))>100,"wrong depth buffer used for back display");
    });
    std::cout<<passed<<" passed, "<<failed<<" failed\n";
    return failed?1:0;
}
