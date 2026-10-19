#include "CoopExperienceGuard.h"
#include "CoopRewardPolicy.h"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <vector>

static_assert(!CoopRewardPolicy::suppressionActive(false, true, false, false, true));
static_assert(CoopRewardPolicy::suppressionActive(true, true, false, false, true));
static_assert(!CoopRewardPolicy::suppressionActive(true, false, false, false, true));
static_assert(!CoopRewardPolicy::suppressionActive(true, true, true, false, true));
static_assert(!CoopRewardPolicy::suppressionActive(true, true, false, true, true));
static_assert(!CoopRewardPolicy::suppressionActive(true, true, false, false, false));
static_assert(CoopRewardPolicy::nativeExperienceAllowed(false, true, false, false, true));
static_assert(!CoopRewardPolicy::nativeExperienceAllowed(true, true, false, false, true));

int main() {
    constexpr std::array<unsigned char, 16> entry{
        0xf0, 0xb5, 0x8d, 0xb0, 0x00, 0x90, 0x40, 0x68,
        0x01, 0x91, 0x02, 0x92, 0x1d, 0x1c, 0xef, 0xf7};
    constexpr std::array<unsigned char, 14> caller{
        0x14, 0x4b, 0x28, 0x1c, 0x39, 0x1c, 0x22, 0x1c,
        0xeb, 0x18, 0x05, 0xf0, 0xf7, 0xff};
    constexpr unsigned output = 0x02001000;
    std::vector<unsigned char> ram(0x400000, 0);
    std::memcpy(ram.data() + 0x1aee0c, entry.data(), entry.size());
    std::memcpy(ram.data() + 0x1a8e10, caller.data(), caller.size());

    auto* rewards = ram.data() + output - 0x02000000;
    for (unsigned i = 0; i < 6; ++i) {
        auto* record = rewards + i * 12;
        record[0] = 0x12;
        record[1] = 0x34;
        record[2] = 0x56;
        record[3] = 0x78;
        record[4] = static_cast<unsigned char>(0xa0 + i);
        record[5] = static_cast<unsigned char>(0xb0 + i);
        record[6] = static_cast<unsigned char>(0xc0 + i);
        record[7] = static_cast<unsigned char>(0xd0 + i);
        record[8] = static_cast<unsigned char>(0xe0 + i);
        record[9] = static_cast<unsigned char>(0xf0 + i);
        record[10] = static_cast<unsigned char>(0x20 + i);
        record[11] = static_cast<unsigned char>(0x30 + i);
    }

    assert(CoopExperienceGuard::suppress(ram.data(), 0x021aee0c, 0x021a8e1f, output));
    for (unsigned i = 0; i < 6; ++i) {
        const auto* record = rewards + i * 12;
        assert(record[0] == 0 && record[1] == 0 && record[2] == 0 && record[3] == 0);
        assert(record[4] == 0xa0 + i && record[5] == 0xb0 + i);
        assert(record[6] == 0xc0 + i && record[7] == 0xd0 + i);
        assert(record[8] == 0xe0 + i && record[9] == 0xf0 + i);
        assert(record[10] == 0x20 + i && record[11] == 0x30 + i);
    }

    const auto beforeWrongPc = rewards[12];
    assert(!CoopExperienceGuard::suppress(ram.data(), 0x021aee08, 0x021a8e1f, output));
    assert(rewards[12] == beforeWrongPc);
    assert(!CoopExperienceGuard::suppress(ram.data(), 0x021aee0c, 0x021a8e1d, output));
    assert(!CoopExperienceGuard::suppress(ram.data(), 0x021aee0c, 0x021a8e1f, output + 1));

    ram[0x1aee0c] ^= 0xff;
    assert(!CoopExperienceGuard::suppress(ram.data(), 0x021aee0c, 0x021a8e1f, output));

    std::cout << "Co-op EXP suppression policy and reward guard passed.\n";
    return 0;
}
