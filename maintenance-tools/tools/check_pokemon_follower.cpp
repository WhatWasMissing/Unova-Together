#include "PokemonFollower.h"
#include "PresenceOverlay.h"
#include "PokemonFollowerEntries.h"
#include <QFile>
#include <cassert>
#include <iostream>
#include <QPainter>
#include <QDir>
#include <QGuiApplication>
int main(int argc,char** argv) {
    QGuiApplication app(argc,argv);
    PokemonFollowerTrail t;
    t.update(1,1,{0,0},0,true);assert(!t.visible);
    t.update(1,1,{1,0},0,true);assert(t.visible && t.position==QPointF(0,0));
    t.update(1,1,{1,1},0,true);assert(t.position==QPointF(1,0) && t.facing=="South");
    t.update(1,1,{1,1.5},0,true);assert(t.position==QPointF(1,0.5));
    t.update(1,1,{1,1.5},0,true);assert(!t.moving);
    t.update(1,1,{100,100},0,true);assert(!t.visible);
    t.update(2,1,{100,101},0,true);assert(!t.visible);
    t.update(2,2,{100,102},0,true);assert(!t.visible);
    t.update(2,2,{100,103},0,true);assert(t.visible);
    t.update(2,2,{100,103},0,false);assert(!t.visible);
    assert(argc==2 || argc==3);QFile file(QString::fromLocal8Bit(argv[1]));assert(file.open(QIODevice::ReadOnly));
    const auto rom=file.readAll();unsigned walkers=0,icons=0;
    QImage sheet(1120,40*72,QImage::Format_ARGB32);sheet.fill(QColor(210,223,201));
    unsigned gen5Walkers=0,gen5Icons=0;
    for(unsigned species=1;species<=649;++species) {
        const auto result=LoadLocalPokemonSprites(reinterpret_cast<const unsigned char*>(rom.constData()),rom.size(),species);
        const auto frames=result.value("frames").toList();
        if(frames.size()!=12) {std::cerr<<species<<": "<<result.value("status").toString().toStdString()<<"\n";return 1;}
        for(const auto& frame:frames) {const auto image=frame.value<QImage>();assert(image.width()==32 || image.width()==64);assert(image.height()==image.width()+2);
            bool visible=false;for(int y=0;y<image.height();++y) for(int x=0;x<image.width();++x) visible|=qAlpha(image.pixel(x,y))!=0;
            assert(visible);}
        result.value("walking").toBool()?++walkers:++icons;
        for(int direction=0;direction<4;++direction)
            assert(frames[direction*3].value<QImage>()!=frames[direction*3+1].value<QImage>());
        if(species>=494) {
            if(result.value("walking").toBool()) {
                // A decoded sprite is not enough: the walking pose must animate.
                bool animated=false;
                for(int i=0;i<12;++i) animated|=frames[i].value<QImage>()!=frames[(i/3)*3].value<QImage>();
                assert(animated);
                for(int direction=0;direction<4;++direction)
                    assert(frames[direction*3].value<QImage>()!=frames[direction*3+1].value<QImage>());
            }
            result.value("walking").toBool()?++gen5Walkers:++gen5Icons;
            const unsigned index=species-494,page=index/40,row=(index%40)/2,column=index%2;
            if(index%40==0) sheet.fill(QColor(210,223,201));
            QPainter p(&sheet);p.setPen(Qt::black);
            p.drawText(column*560+6,row*144+16,QString("%1 · %2").arg(species).arg(result.value("walking").toBool()?"Walking":"Party icon"));
            for(unsigned direction=0;direction<4;++direction) for(unsigned pose=0;pose<2;++pose)
                p.drawImage(QRect(column*560+direction*128+pose*64,row*144+28,64,64),frames[direction*3+pose].value<QImage>().scaled(64,64,Qt::IgnoreAspectRatio,Qt::FastTransformation));
            p.end();
            if(argc==3 && (index%40==39 || species==649)) {QDir().mkpath(QString::fromLocal8Bit(argv[2]));sheet.save(QString::fromLocal8Bit(argv[2])+QString("/gen5-%1.png").arg(page));}
        }
    }
    assert(walkers==649 && icons==0 && gen5Walkers==156 && gen5Icons==0);
    unsigned variants=0;
    for(const auto& asset:QDir(":/followers/variants").entryList({"*.btx"},QDir::Files)) {
        const auto identity=asset.chopped(4).split('-');assert(identity.size()==3);
        const auto normal=LoadLocalPokemonSprites(reinterpret_cast<const unsigned char*>(rom.constData()),rom.size(),identity[0].toUInt(),identity[1].toUInt(),identity[2].toUInt(),false);
        const auto shiny=LoadLocalPokemonSprites(reinterpret_cast<const unsigned char*>(rom.constData()),rom.size(),identity[0].toUInt(),identity[1].toUInt(),identity[2].toUInt(),true);
        assert(normal.value("frames").toList().size()==12 && shiny.value("frames").toList().size()==12);
        assert(shiny.value("shiny").toBool());
        bool recoloured=false;
        const auto normalFrames=normal.value("frames").toList(),shinyFrames=shiny.value("frames").toList();
        for(int i=0;i<12;++i) {
            const auto a=normalFrames[i].value<QImage>(),b=shinyFrames[i].value<QImage>();
            assert(a.size()==b.size());recoloured=recoloured || a!=b;
            for(int y=0;y<a.height();++y) for(int x=0;x<a.width();++x) assert(qAlpha(a.pixel(x,y))==qAlpha(b.pixel(x,y)));
        }
        if(!recoloured) {std::cerr<<"Shiny palette unchanged: "<<asset.toStdString()<<"\n";return 1;}
        for(const auto& image:shiny.value("frames").toList()) {
            const auto frame=image.value<QImage>();assert(frame.width()==32 || frame.width()==64);
            assert(frame.height()==frame.width()+2);
        }
        ++variants;
    }
    assert(variants==743);
    // Audino regression: a shiny flag must change rendered pixels, not merely
    // the returned metadata. Both variants must retain identical geometry.
    const auto audinoNormal=LoadLocalPokemonSprites(reinterpret_cast<const unsigned char*>(rom.constData()),rom.size(),531,0,2,false).value("frames").toList();
    const auto audinoShiny=LoadLocalPokemonSprites(reinterpret_cast<const unsigned char*>(rom.constData()),rom.size(),531,0,2,true).value("frames").toList();
    assert(audinoNormal.size()==12 && audinoShiny.size()==12);
    for(int i=0;i<12;++i) {
        const auto normal=audinoNormal[i].value<QImage>(),shiny=audinoShiny[i].value<QImage>();
        assert(normal.size()==shiny.size() && normal!=shiny);
    }
    // Identity regressions found by contact-sheet review. These assets depict
    // evolved species, and must never be attached to the earlier evolution.
    assert(PokemonFollowerEntries[507]==922 && PokemonFollowerEntries[506]==0);
    assert(PokemonFollowerEntries[523]==928 && PokemonFollowerEntries[522]==0);
    assert(PokemonFollowerEntries[525]==929 && PokemonFollowerEntries[524]==0);
    assert(PokemonFollowerEntries[533]==933 && PokemonFollowerEntries[532]==0);
    assert(PokemonFollowerEntries[580]==953 && PokemonFollowerEntries[583]==954);
    assert(PokemonFollowerEntries[600]==959 && PokemonFollowerEntries[599]==0);
    assert(LoadLocalPokemonSprites(nullptr,0,1).value("frames").toList().isEmpty());
    assert(LoadLocalPokemonSprites(reinterpret_cast<const unsigned char*>(rom.constData()),rom.size(),650).value("frames").toList().isEmpty());
    std::cout<<"Follower trails passed; all 649 species decoded ("<<walkers<<" walking, "<<icons<<" icon fallback).\n";
    std::cout<<"Gen 5: "<<gen5Walkers<<" walking, "<<gen5Icons<<" party-icon fallback.\n";
}
