// Unova Together: mvq1303 / WhatWasMissing, GPL-3.0-or-later.
// Test actual ROM data and production overlay/price policy; never write a ROM.
#include "Gen5ShopPolicy.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc,char** argv) {
    assert(argc==3);std::ifstream stream(argv[1],std::ios::binary);
    std::vector<uint8_t> rom((std::istreambuf_iterator<char>(stream)),{});assert(!rom.empty());
    const auto original=rom;const auto policy=Gen5ShopPolicy::patches(rom.data(),rom.size());
    assert(policy.size()==4);melonDS::ROMAssetOverlay overlay;assert(overlay.set(policy,uint32_t(rom.size())));
    // Materialise only the tiny patched reads, for independent stock checks.
    auto fat=Gen5ShopPolicy::file({rom.data(),rom.size()},{"a","2","8","2"});
    std::array<uint8_t,8> range{};std::memcpy(range.data(),rom.data()+fat.fat,8);overlay.apply(fat.fat,8,range.data());
    Gen5ShopPolicy::Bytes pointer{range.data(),range.size()};const auto start=pointer.word(0),end=pointer.word(4);
    std::vector<uint8_t> relocated(rom.begin()+start,rom.begin()+end);overlay.apply(start,end-start,relocated.data());
    const auto shops=Gen5ShopPolicy::parse({relocated.data(),relocated.size()});
    const auto countsFile=Gen5ShopPolicy::file({rom.data(),rom.size()},{"a","2","8","3"});
    auto countBytes=countsFile.bytes.copy();overlay.apply(countsFile.start,uint32_t(countBytes.size()),countBytes.data());
    const auto counts=Gen5ShopPolicy::parse({countBytes.data(),countBytes.size()});
    const auto oldShops=Gen5ShopPolicy::parse(fat.bytes),oldCounts=Gen5ShopPolicy::parse(countsFile.bytes);
    unsigned active=0,added=0;
    for(unsigned i=0;i<shops.files.size();++i) {
        const auto before=oldCounts.files[0][i],after=counts.files[0][i];
        if(!before) {assert(!after && shops.files[i]==oldShops.files[i]);continue;}
        ++active;unsigned copies=0;std::vector<unsigned> originalItems,newItems;
        for(unsigned j=0;j<before;++j) originalItems.push_back(Gen5ShopPolicy::Bytes{oldShops.files[i].data(),oldShops.files[i].size()}.half(j*2));
        for(unsigned j=0;j<after;++j) {const auto id=Gen5ShopPolicy::Bytes{shops.files[i].data(),shops.files[i].size()}.half(j*2);newItems.push_back(id);copies+=id==76;}
        assert(copies==1 && after==before+(std::find(originalItems.begin(),originalItems.end(),76)==originalItems.end()));
        for(const auto item:originalItems) assert(std::find(newItems.begin(),newItems.end(),item)!=newItems.end());
        added+=after!=before;
    }
    const auto itemsFile=Gen5ShopPolicy::file({rom.data(),rom.size()},{"a","0","2","4"});
    auto itemsBytes=itemsFile.bytes.copy();overlay.apply(itemsFile.start,uint32_t(itemsBytes.size()),itemsBytes.data());
    const auto oldItems=Gen5ShopPolicy::parse(itemsFile.bytes),newItems=Gen5ShopPolicy::parse({itemsBytes.data(),itemsBytes.size()});
    assert(oldItems.files.size()==newItems.files.size());
    for(unsigned i=0;i<oldItems.files.size();++i) {
        if(i==76) {assert(newItems.files[i][0]==1 && newItems.files[i][1]==0);assert(std::equal(oldItems.files[i].begin()+2,oldItems.files[i].end(),newItems.files[i].begin()+2));}
        else assert(oldItems.files[i]==newItems.files[i]);
    }
    std::ofstream output(argv[2],std::ios::binary);output.write(reinterpret_cast<const char*>(newItems.files[76].data()),newItems.files[76].size());output.close();
    assert(rom==original);
    std::cout<<active<<" active money-shop catalogs, "<<added<<" additions; all other stock/item data preserved; native encoded price 1 (10 money) passed.\n";
}
