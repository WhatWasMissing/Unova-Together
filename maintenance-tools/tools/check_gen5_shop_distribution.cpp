// Unova Together: Copyright (C) 2026 mvq1303. GPL-3.0-or-later.
// Exercise the packaged shop policy without Qt or an emulator process.
#include "Gen5ShopPolicy.h"
#include "Gen5MegaItemIds.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>

using namespace Gen5ShopPolicy;

static std::array<uint16_t, 49> stones()
{
    std::array<uint16_t, 49> result{113, 126};
    std::copy(RepurposedMegaStoneIds.begin(), RepurposedMegaStoneIds.end(), result.begin() + 2);
    result.back() = 123;
    return result;
}

static void checkStock(const Narc& shops, const Narc& counts)
{
    const auto roster = stones();
    std::array<unsigned, 49> occurrences{};
    for (unsigned member = 0; member < AllPokeMartListCount; ++member)
    {
        const auto count = counts.files.at(0).at(member);
        assert(count <= 45 && count * 2 <= shops.files.at(member).size());
        const Bytes stock{shops.files[member].data(), shops.files[member].size()};
        std::array<bool, 49> seen{};
        unsigned found = 0;
        for (unsigned row = 0; row < count; ++row)
            for (unsigned stone = 0; stone < roster.size(); ++stone)
                if (stock.half(row * 2) == roster[stone])
                {
                    assert(!seen[stone]);
                    seen[stone] = true;
                    ++occurrences[stone];
                    ++found;
                }
        const bool center = member >= 6 && member < 26;
        assert(found == (center ? 3 : 0));
    }
    unsigned repeated = 0;
    for (const auto count : occurrences)
    {
        assert(count == 1 || count == 2);
        repeated += count == 2;
    }
    assert(repeated == 11);
}

static void unitChecks()
{
    Narc shops{}, counts{};
    shops.files.resize(80, {1, 0, 2, 0});
    counts.files = {std::vector<uint8_t>(80, 2)};
    const auto roster = stones();
    // Legacy stock in a center and a special mart must be normalized.
    for (const unsigned member : {7, 73})
    {
        shops.files[member].insert(shops.files[member].end(), {113, 0, 113, 0});
        counts.files[0][member] += 2;
    }
    shops.files[8] = {0x48, 1, 0x4D, 1}; // TM stock remains first and in order.
    const auto unrelated = shops.files[79];
    unsigned added = 0;
    assert(distributeMegaStonesAcrossPokemonCenterMarts(shops, counts, roster, &added));
    assert(added == 60);
    checkStock(shops, counts);
    assert(shops.files[8][0] == 0x48 && shops.files[8][2] == 0x4D);
    assert(shops.files[79] == unrelated && counts.files[0][79] == 2);
    const auto once = shops.files;
    const auto onceCounts = counts.files;
    assert(distributeMegaStonesAcrossPokemonCenterMarts(shops, counts, roster));
    assert(shops.files == once && counts.files == onceCounts);

    // A center with 43 ordinary rows cannot accept three more in native storage.
    shops.files[6].assign(86, 0);
    for (unsigned row = 0; row < 43; ++row) shops.files[6][row * 2] = 1;
    counts.files[0][6] = 43;
    const auto full = shops.files;
    const auto fullCounts = counts.files;
    assert(!distributeMegaStonesAcrossPokemonCenterMarts(shops, counts, roster));
    assert(shops.files == full && counts.files == fullCounts);
    auto invalid = roster;
    invalid[1] = invalid[0];
    assert(!distributeMegaStonesAcrossPokemonCenterMarts(shops, counts, invalid));
    assert(shops.files == full && counts.files == fullCounts);
    counts.files[0].pop_back();
    assert(!distributeMegaStonesAcrossPokemonCenterMarts(shops, counts, roster));
    std::cout << "PASS: balanced stock, roster coverage, native capacity, idempotency, negative cases\n";
}

static void cartridgeCheck(const char* path)
{
    std::ifstream input(path, std::ios::binary);
    assert(input);
    std::vector<uint8_t> rom((std::istreambuf_iterator<char>(input)), {});
    assert(rom.size() >= 0x200);
    // NDSCart::ParseROM rounds trimmed dumps up to a power of two and fills
    // the in-memory padding with 0xFF before constructing asset overlays.
    std::size_t paddedSize = 1;
    while (paddedSize < rom.size()) paddedSize *= 2;
    rom.resize(paddedSize, 0xFF);
    const Bytes original{rom.data(), rom.size()};
    const auto stock = file(original, {"a", "2", "8", "2"});
    const auto numbers = file(original, {"a", "2", "8", "3"});
    const auto items = file(original, {"a", "0", "2", "4"});
    const auto originalShops = parse(stock.bytes);
    const auto originalCounts = parse(numbers.bytes);
    const auto itemData = parse(items.bytes);
    const auto patchesToApply = patches(rom.data(), rom.size(), stones());
    assert(patchesToApply.size() == 4);
    for (const auto& patch : patchesToApply)
        assert(patch.offset == stock.fat || patch.offset == numbers.start ||
               patch.offset == items.start + itemData.offsets[SuperRepel] ||
               patch.offset >= original.word(0x80));
    // Independently apply the returned byte ranges; no emulator or card-read
    // implementation is exercised by this data-level cartridge check.
    const auto readPatched = [&](uint32_t offset, uint32_t size) {
        assert(uint64_t(offset) + size <= rom.size());
        std::vector<uint8_t> result(rom.begin() + offset, rom.begin() + offset + size);
        for (const auto& patch : patchesToApply)
        {
            const auto first = std::max(uint64_t(offset), uint64_t(patch.offset));
            const auto last = std::min(uint64_t(offset) + size, uint64_t(patch.offset) + patch.bytes.size());
            if (first < last)
                std::copy_n(patch.bytes.data() + first - patch.offset, last - first,
                            result.data() + first - offset);
        }
        return result;
    };
    const auto relocated = readPatched(stock.fat, 8);
    const Bytes pointer{relocated.data(), relocated.size()};
    const auto begin = pointer.word(0), end = pointer.word(4);
    assert(begin < end && end <= rom.size());
    const auto shopBytes = readPatched(begin, end - begin);
    const auto numberBytes = readPatched(numbers.start, uint32_t(numbers.bytes.length));
    const auto patchedShops = parse({shopBytes.data(), shopBytes.size()});
    const auto patchedCounts = parse({numberBytes.data(), numberBytes.size()});
    checkStock(patchedShops, patchedCounts);
    unsigned maximum = 0;
    const auto roster = stones();
    for (unsigned member = 0; member < AllPokeMartListCount; ++member)
    {
        std::vector<uint16_t> expected;
        const Bytes old{originalShops.files[member].data(), originalShops.files[member].size()};
        for (unsigned row = 0; row < originalCounts.files[0][member]; ++row)
            expected.push_back(uint16_t(old.half(row * 2)));
        if (!expected.empty() && std::find(expected.begin(), expected.end(), SuperRepel) == expected.end())
            expected.push_back(SuperRepel);
        expected.erase(std::remove_if(expected.begin(), expected.end(), [&](uint16_t id) {
            return std::find(roster.begin(), roster.end(), id) != roster.end();
        }), expected.end());
        const Bytes now{patchedShops.files[member].data(), patchedShops.files[member].size()};
        for (unsigned row = 0; row < expected.size(); ++row)
            assert(now.half(row * 2) == expected[row]);
        assert(patchedCounts.files[0][member] == expected.size() + ((member >= 6 && member < 26) ? 3 : 0));
        maximum = std::max(maximum, unsigned(patchedCounts.files[0][member]));
    }
    std::cout << "PASS: cartridge stock and ordinary inventory; maximum mart rows=" << maximum << "\n";
}

int main(int argc, char** argv)
{
    std::cout << std::unitbuf;
    static_assert(MaxShopUIEntries == 45, "Keep the merchant crash fix's native storage limit");
    unitChecks();
    for (int i = 1; i < argc; ++i) cartridgeCheck(argv[i]);
}
