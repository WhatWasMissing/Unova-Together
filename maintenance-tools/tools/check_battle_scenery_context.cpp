#include "battle_scenery_context.h"

#include <iostream>

int main()
{
    auto check = [](bool actual, bool expected, const char* name) {
        if (actual == expected) return true;
        std::cerr << "FAIL: " << name << "\n";
        return false;
    };

    bool ok = true;
    ok &= check(hasBattleSceneryFieldContext(true, 337, 107), true,
                "verified Route 7 field context");
    ok &= check(hasBattleSceneryFieldContext(true, 0, 65535), true,
                "valid boundary zones");
    ok &= check(hasBattleSceneryFieldContext(false, 337, 107), false,
                "unverified field context");
    ok &= check(hasBattleSceneryFieldContext(true, -1, 107), false,
                "invalid matrix zone");
    ok &= check(hasBattleSceneryFieldContext(true, 337, 65536), false,
                "invalid field zone");

    ok &= check(canUseBattleScenerySample(true, true, false, false, false),
                true, "verified live field sample");
    ok &= check(canUseBattleScenerySample(true, false, true, true, true),
                true, "battle with retained verified field context");
    ok &= check(canUseBattleScenerySample(true, false, true, false, true),
                false, "unknown battle state");
    ok &= check(canUseBattleScenerySample(true, false, true, true, false),
                false, "battle without retained field context");
    ok &= check(canUseBattleScenerySample(false, true, false, false, false),
                false, "catalog not loaded");
    return ok ? 0 : 1;
}
