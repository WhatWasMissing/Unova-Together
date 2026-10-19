#include "Gen5Menu.h"
#include "RivalAgreement.h"
#include "NpcStoryHold.h"
#include <QCoreApplication>
#include <QFile>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <cassert>
#include <iostream>
int main(int argc,char**argv) {
 QCoreApplication app(argc,argv);assert(argc>=2);
 unsigned cases=0;
 for(int arg=1;arg<argc;++arg) {
  QFile f(argv[arg]);assert(f.open(QIODevice::ReadOnly));auto b=f.readAll();QString reason;
  auto catalog=Gen5Menu::npcTrainers(reinterpret_cast<const unsigned char*>(b.constData()),b.size(),reason);
  if(!reason.isEmpty()) { std::cerr<<reason.toStdString()<<"\n"; }
  assert(reason.isEmpty() && !catalog.isEmpty());QMap<unsigned,QList<unsigned>> groups;
  for(auto item:catalog) {auto row=item.toMap();auto family=row.value("rivalFamily").toUInt();if(family)groups[family].append(row.value("id").toUInt());}
  assert(groups.size()>=6);
  for(auto ids:groups) {assert(ids.size()==3);
   for(auto host:ids)for(auto guest:ids) {
    auto h=NpcStoryHold::identity(0x85,host),g=NpcStoryHold::identity(0x85,guest);
    assert(CompatibleNpcAgreement(g,h,catalog));++cases;
    assert(!CompatibleNpcAgreement(g,NpcStoryHold::identity(0x86,host),catalog));++cases;
   }
   std::cout<<ids[0]<<","<<ids[1]<<","<<ids[2]<<" verified starter arms\n";
  }
  for(auto a:groups.keys())for(auto b:groups.keys())if(a!=b)assert(!CompatibleNpcAgreement(NpcStoryHold::identity(0x85,a),NpcStoryHold::identity(0x85,b),catalog));
  assert(!CompatibleNpcAgreement(0,NpcStoryHold::identity(0x85,156),catalog));
  std::cout<<argv[arg]<<": "<<groups.size()<<" rival encounter families\n";
 }
 std::cout<<cases<<" same/different starter and wrong event-kind cases passed\n";
}
