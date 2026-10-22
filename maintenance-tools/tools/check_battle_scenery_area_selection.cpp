#include "battle_scenery_area_selection.h"
#include <cassert>

int main()
{
    constexpr auto areaFor = [](int zone) constexpr {
        return zone == 107 || zone == 337 ? 38 : zone == 201 ? 12 : -1;
    };

    constexpr auto routeSeven = selectBattleSceneryArea(337, 107, areaFor);
    static_assert(routeSeven.battleZone == 107);
    static_assert(routeSeven.battleArea == 38);
    static_assert(routeSeven.matrixZone == 337);
    static_assert(routeSeven.useNearbyGeometry);

    constexpr auto mismatchedArea = selectBattleSceneryArea(201, 107, areaFor);
    static_assert(mismatchedArea.battleArea == 38);
    static_assert(!mismatchedArea.useNearbyGeometry);

    constexpr auto invalidBattleZone = selectBattleSceneryArea(337, 400, areaFor);
    static_assert(!static_cast<bool>(invalidBattleZone));
    return 0;
}
