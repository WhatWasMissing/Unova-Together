// Unova Together by mvq1303 / WhatWasMissing. GPL-3.0-or-later.
#pragma once

struct BattleSceneryAreaSelection {
    int battleZone = -1;
    int battleArea = -1;
    int matrixZone = -1;
    bool useNearbyGeometry = false;

    explicit constexpr operator bool() const { return battleArea >= 0; }
};

// The field's loaded zone selects its battle area. The outdoor matrix cell is
// only suitable for nearby geometry when both zone records resolve to the same
// area; callers should otherwise use the battle area's safe fallback arena.
template <typename AreaForZone>
constexpr BattleSceneryAreaSelection selectBattleSceneryArea(
    int matrixZone, int battleZone, AreaForZone areaForZone)
{
    const int battleArea = areaForZone(battleZone);
    if (battleZone < 0 || battleArea < 0)
        return {};

    const int matrixArea = areaForZone(matrixZone);
    return {battleZone, battleArea, matrixZone,
            matrixZone >= 0 && matrixArea == battleArea};
}
