// Unova Together: Copyright (C) 2026 mvq1303. GPL-3.0-or-later.
#include "PresenceOverlay.h"
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QGuiApplication>
#include <QJsonDocument>
#include <QJsonObject>
#include <iostream>
#include <stdexcept>

static QByteArray hashFrames(const QVariantMap& result, bool shiny)
{
    if (result.value("shiny").toBool()!=shiny || !result.value("walking").toBool())
        throw std::runtime_error("Appearance metadata mismatch");
    const auto frames=result.value("frames").toList();
    if(frames.size()!=12) throw std::runtime_error("Missing directional frames");
    QCryptographicHash hash(QCryptographicHash::Sha256);
    for(const auto& value:frames) {
        const auto image=value.value<QImage>();
        if((image.width()!=32 && image.width()!=64) || image.height()!=image.width()+2)
            throw std::runtime_error("Unexpected frame dimensions");
        bool visible=false;
        for(int y=0;y<image.height();++y) for(int x=0;x<image.width();++x)
            visible|=qAlpha(image.pixel(x,y))!=0;
        if(!visible) throw std::runtime_error("Invisible frame");
        hash.addData(QByteArrayView(reinterpret_cast<const char*>(image.constBits()),image.sizeInBytes()));
    }
    return hash.result().toHex();
}

int main(int argc,char** argv)
{
    QGuiApplication app(argc,argv);
    try {
        // All authored variants load from resources before any ROM read.
        unsigned char rom[512]{};
        QJsonObject snapshot;
        const auto assets=QDir(":/followers/variants").entryList({"*.btx"},QDir::Files);
        if(assets.size()!=743) throw std::runtime_error("Original variants missing");
        for(const auto& asset:assets) {
            const auto identity=asset.chopped(4).split('-');
            const unsigned species=identity[0].toUInt(), form=identity[1].toUInt(),gender=identity[2].toUInt();
            const auto normal=LoadLocalPokemonSprites(rom,sizeof(rom),species,form,gender,false);
            const auto shiny=LoadLocalPokemonSprites(rom,sizeof(rom),species,form,gender,true);
            QJsonObject entry{{"normal",QString::fromLatin1(hashFrames(normal,false))},
                              {"shiny",QString::fromLatin1(hashFrames(shiny,true))}};
            if(QFile::exists(QString(":/followers/official-hgss/%1.png").arg(asset.chopped(4)))) {
                if(normal.value("status").toString()!="HGSS directional follower")
                    throw std::runtime_error("Normal override was not selected");
                if(shiny.value("status").toString()=="HGSS directional follower")
                    throw std::runtime_error("Shiny incorrectly used normal artwork");
            }
            snapshot.insert(asset.chopped(4),entry);
        }
        for(unsigned species=1;species<=649;++species) {
            const auto normal=LoadLocalPokemonSprites(rom,sizeof(rom),species,0,0,false);
            const auto shiny=LoadLocalPokemonSprites(rom,sizeof(rom),species,0,0,true);
            hashFrames(normal,false);hashFrames(shiny,true);
        }
        std::cout<<QJsonDocument(snapshot).toJson(QJsonDocument::Compact).toStdString()<<'\n';
    } catch(const std::exception& error) {
        std::cerr<<error.what()<<'\n';return 1;
    }
}
