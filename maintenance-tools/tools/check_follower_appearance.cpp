#include "FollowerAppearance.h"
#include <QFile>
#include <cassert>
#include <iostream>
int main(int argc,char** argv) {
    auto code=QByteArray::fromHex("00041b0c000c090c5840120c48405040082801d20120704700207047");
    assert(FollowerShinyThreshold(code)==8);
    code[16]=char(128);
    assert(FollowerShinyThreshold(code)==128);
    for(unsigned value:{7u,8u,15u,127u,128u})
        assert((value<FollowerShinyThreshold(code))==(value<128));
    auto corrupt=code;corrupt[18]=0;assert(FollowerShinyThreshold(corrupt)==8);
    auto stock=code;stock[16]=8;assert(FollowerShinyThreshold(code+stock)==8);
    assert(FollowerShinyThreshold(QByteArray())==8);
    if(argc>1) {QFile file(argv[1]);assert(file.open(QIODevice::ReadOnly));assert(FollowerShinyThreshold(file.readAll())==128);}
    std::cout<<"Native shiny threshold checks passed.\n";
}
