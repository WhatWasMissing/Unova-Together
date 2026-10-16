#include "SoaringScene.h"
#include <QGuiApplication>
#include <QElapsedTimer>
#include <QTemporaryDir>
#include <cassert>
#include <iostream>
int main(int argc,char** argv) {
    QGuiApplication app(argc,argv);SoaringScene scene;scene.phase=SoaringScene::Takeoff;
    for(int i=0;i<30;++i) scene.step(0,.05);
    assert(scene.phase==SoaringScene::Flying && scene.altitude==96);
    for(int i=0;i<200;++i) scene.step((1<<6)|1,.05);
    assert(std::abs(scene.z)<=600 && scene.speed>170);
    for(int i=0;i<100;++i) scene.step(1<<9,.05);
    assert(scene.altitude==256);
    for(int i=0;i<100;++i) scene.step(1<<8,.05);
    assert(scene.altitude==64);
    scene.phase=SoaringScene::Landing;for(int i=0;i<100;++i) scene.step(0,.05);assert(!scene.active());
    assert(scene.render({},0).size()==QSize(256,192));
    {
        QTemporaryDir directory;assert(directory.isValid());
        QImage red(2,2,QImage::Format_ARGB32);red.fill(Qt::red);assert(red.save(directory.filePath("red.png")));
        QImage blue=red;blue.fill(Qt::blue);assert(blue.save(directory.filePath("blue.png")));
        auto vertex=[](double x,double y,double z,double u,double v) {return QJsonArray{x,y,z,u,v};};
        QJsonArray lower{0,QJsonArray{vertex(-160,0,-400,0,0),vertex(160,0,-400,2,0),vertex(160,0,100,2,2),vertex(-160,0,100,0,2)}};
        QJsonArray upper{1,QJsonArray{vertex(-100,40,-250,0,0),vertex(100,40,-250,2,0),vertex(100,40,80,2,2),vertex(-100,40,80,0,2)}};
        auto load=[&](QJsonArray faces) {
            QFile file(directory.filePath("scene.json"));assert(file.open(QIODevice::WriteOnly));
            file.write(QJsonDocument(QJsonObject{{"format",1},{"zone",191},{"world",QJsonArray{0,0,0}},{"textures",QJsonArray{"red.png","blue.png"}},{"faces",faces}}).toJson());file.close();
            scene.reset();scene.map=191;assert(scene.load(file.fileName()));scene.altitude=96;
            return scene.render({},0);
        };
        const auto first=load({lower,upper}),second=load({upper,lower});assert(first==second);
        int redPixels=0,bluePixels=0;
        for(int y=0;y<192;++y) for(int x=0;x<256;++x) {const auto colour=first.pixelColor(x,y);redPixels+=colour==Qt::red;bluePixels+=colour==Qt::blue;}
        assert(redPixels>100 && bluePixels>100);
        // A polygon crossing the near plane still renders its visible part.
        const auto clipped=load({QJsonArray{0,QJsonArray{vertex(-50,120,300,0,0),vertex(120,0,-300,2,0),vertex(-120,0,-300,0,2)}}});
        int visible=0;for(int y=0;y<192;++y) for(int x=0;x<256;++x) visible+=clipped.pixelColor(x,y)==Qt::red;
        assert(visible>100);
        // Redux's full regional atlas may use more than 512 small ROM textures.
        // Keep a fixture referencing index 512 while the decoded pixel budget
        // remains the actual limit on memory use.
        QJsonArray manyTextureNames;for(int i=0;i<513;++i) manyTextureNames.append("red.png");
        QFile manyTexturesFile(directory.filePath("many-textures-scene.json"));assert(manyTexturesFile.open(QIODevice::WriteOnly));
        manyTexturesFile.write(QJsonDocument(QJsonObject{{"format",1},{"zone",191},{"world",QJsonArray{0,0,0}},
            {"textures",manyTextureNames},{"faces",QJsonArray{QJsonArray{512,lower[1]}}}}).toJson());manyTexturesFile.close();
        scene.reset();scene.map=191;assert(scene.load(manyTexturesFile.fileName()));
        QJsonArray bridgeVertices{QJsonArray{-80,-26,-220},QJsonArray{80,-26,-220},QJsonArray{0,-25,-80}};
        QJsonArray forestVertices{QJsonArray{-140,-30,-220},QJsonArray{-80,-30,-220},QJsonArray{-110,-10,-170}};
        QJsonArray debugRoute{QJsonArray{.5,.5},QJsonArray{1.5,.5},QJsonArray{2.5,1.5}};
        QFile debugFile(directory.filePath("debug-scene.json"));assert(debugFile.open(QIODevice::WriteOnly));
        debugFile.write(QJsonDocument(QJsonObject{{"format",2},{"zone",191},{"sourceZone",191},{"world",QJsonArray{0,0,0}},
            {"textures",QJsonArray{"red.png","blue.png"}},{"faces",QJsonArray{lower,upper}},
            {"atlasSize",QJsonArray{3,2}},{"atlasGrid",QJsonArray{1,0,1,1,1,1}},
            {"atlasBiome",QJsonArray{2,0,1,2,2,2}},
            {"flywayRoutes",QJsonArray{debugRoute}},{"flywayFaces",QJsonArray{QJsonArray{0,bridgeVertices}}},
            {"regionFaces",QJsonArray{QJsonArray{2,forestVertices}}},
            {"collisionDebug",true},{"collisionTiles",QJsonArray{QJsonArray{6,6,0,0},QJsonArray{7,6,0,1},QJsonArray{8,6,0,2}}}}).toJson());debugFile.close();
        scene.reset();scene.map=191;assert(scene.load(debugFile.fileName()));
        const auto debugFrame=scene.render({},0);assert(debugFrame.size()==QSize(256,192) && debugFrame!=first);
        QFile regionalFile(directory.filePath("regional-scene.json"));assert(regionalFile.open(QIODevice::WriteOnly));
        regionalFile.write(QJsonDocument(QJsonObject{{"format",3},{"zone",191},{"sourceZone",191},{"world",QJsonArray{0,0,0}},
            {"textures",QJsonArray{"red.png","blue.png"}},{"faces",QJsonArray{lower,upper}},
            {"landings",QJsonArray{QJsonArray{191,10,20,0,520,1000}}},
            {"atlasSize",QJsonArray{3,2}},{"atlasOriginCell",QJsonArray{-1,2}},
            {"atlasGrid",QJsonArray{1,0,1,1,1,1}},
            {"collisionDebug",true},{"collisionTiles",QJsonArray{QJsonArray{-4,70,0,0}}}}).toJson());regionalFile.close();
        scene.reset();scene.map=191;assert(scene.load(regionalFile.fileName()));
        scene.anchor={{"worldX",0.},{"worldY",0.},{"worldZ",0.}};scene.x=520;scene.z=1000;scene.altitude=96;
        const auto destination=scene.nearestLanding(1);
        assert(destination.value("map").toInt()==191 && destination.value("tileX").toInt()==10 &&
               destination.value("tileZ").toInt()==20 && destination.value("worldX").toDouble()==520 &&
               destination.value("worldZ").toDouble()==1000);
        assert(scene.render({},1).size()==QSize(256,192));
    }
    if(argc>1) {
        scene.reset();
        const QString scenePath=QString::fromLocal8Bit(argv[1]);
        QFile sceneFile(scenePath);assert(sceneFile.open(QIODevice::ReadOnly));
        const auto sceneData=QJsonDocument::fromJson(sceneFile.readAll()).object();
        scene.map=sceneData.value("sourceZone").toInt(sceneData.value("zone").toInt(-1));
        const bool loaded=scene.map>=0 && scene.load(scenePath);
        if(!loaded) std::cerr<<"Flight scene rejected: "<<scene.error.toStdString()<<"\n";
        assert(loaded);
        for(int i=0;i<30;++i) scene.step(0,.05);
        QElapsedTimer clock;clock.start();QList<double> timings;
        for(int i=0;i<120;++i) {
            scene.heading=i*6.283185/120;scene.altitude=64+(i%3)*80;
            QElapsedTimer sample;sample.start();const auto frame=scene.render({},i*17);timings.append(sample.nsecsElapsed()/1e6);
            if(i==0) frame.save("test-fixtures/soaring-preview.png");
        }
        std::sort(timings.begin(),timings.end());
        std::cerr<<"Actual ROM map render average: "<<clock.elapsed()/120.<<" ms; p95: "<<timings[114]<<" ms; maximum: "<<timings.last()<<" ms.\n";
        assert(timings[114]<33.3);
        // Paint callbacks must use a fresh copy, rather than integrating the
        // elapsed time again on an already-advanced snapshot.
        const auto snapshot=scene;
        auto paint=[snapshot]() {auto frame=snapshot;frame.step(1<<6,.05);return frame.render({},100);};
        assert(paint()==paint());assert(scene.x==snapshot.x && scene.z==snapshot.z);
        if(argc>2) {
            const int expectedVisibleMap=argc>3?QString::fromLocal8Bit(argv[3]).toInt():96;
            scene.anchor={{"worldX",3368.},{"worldZ",7432.}};
            const QString nextPath=QString::fromLocal8Bit(argv[2]);QFile nextFile(nextPath);assert(nextFile.open(QIODevice::ReadOnly));
            const auto nextWorld=QJsonDocument::fromJson(nextFile.readAll()).object().value("world").toArray();
            assert(nextWorld.size()==3);
            scene.x=nextWorld[0].toDouble()-scene.anchor.value("worldX").toDouble();
            scene.z=nextWorld[2].toDouble()-scene.anchor.value("worldZ").toDouble();
            scene.altitude=144;scene.heading=.4;scene.speed=72;
            const double streamedX=scene.x,streamedZ=scene.z;
            assert(scene.load(nextPath));
            assert(scene.visibleMap==expectedVisibleMap && scene.map==191);
            assert(scene.phase==SoaringScene::Flying && scene.altitude==144 && scene.x==streamedX && scene.z==streamedZ && scene.speed==72);
            assert(scene.sceneX==streamedX && scene.sceneZ==streamedZ);
            assert(!scene.landingSites.isEmpty());
            const auto site=scene.landingSites.first();
            scene.x=site.value("worldX").toDouble()-3368;scene.z=site.value("worldZ").toDouble()-7432;
            scene.altitude=site.value("worldY").toDouble()+96;
            const auto destination=scene.nearestLanding(1);assert(!destination.isEmpty());
            assert(destination.value("map").toInt()!=scene.map || destination.value("tileZ").toInt()!=464);
            scene.landingX=scene.x;scene.landingZ=scene.z;scene.landingHeight=site.value("worldY").toDouble();
            scene.phase=SoaringScene::Landing;
            for(int i=0;i<120;++i) scene.step(0,.05);
            assert(scene.phase==SoaringScene::Off && scene.altitude==scene.landingHeight);
            scene.phase=SoaringScene::Flying;scene.altitude=144;scene.z=-532;
            for(int i=0;i<100;++i) scene.step(1<<6,.05);
            assert(scene.z<-600); // No longer clamped to take-off's old window.
            scene.render({},200).save("test-fixtures/soaring-neighbor-preview.png");
        }
    }
    std::cout<<"Takeoff, flight controls, altitude limits, map bounds, landing and rendering passed.\n";
}
