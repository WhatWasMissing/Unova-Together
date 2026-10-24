#pragma once

// The battle hook may reuse only a field position that the tracker verified
// immediately before entering a battle. Zone 0 is valid in Black 2/White 2.
constexpr bool hasBattleSceneryFieldContext(bool verifiedFieldSample,
                                            int matrixZone,
                                            int fieldZone) noexcept
{
    return verifiedFieldSample &&
        matrixZone >= 0 && matrixZone <= 65535 &&
        fieldZone >= 0 && fieldZone <= 65535;
}

// A live field sample can select its area's scene. During battles, accept only
// a known battle state paired with a retained, verified field context.
constexpr bool canUseBattleScenerySample(bool catalogLoaded,
                                         bool verifiedFieldSample,
                                         bool inBattle,
                                         bool battleStateKnown,
                                         bool retainedFieldContext) noexcept
{
    return catalogLoaded &&
        (verifiedFieldSample ||
         (inBattle && battleStateKnown && retainedFieldContext));
}
