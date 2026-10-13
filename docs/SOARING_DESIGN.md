# Soaring design

The launcher now provides **Settings → Experimental features → Soaring flight**, off by default. When enabled, the game menu has **Unova → Pokémon → Take flight**, a one-step shortcut to Black 2's native party menu. Selecting a Pokémon and choosing Fly still uses the ROM's own destination list, map loading, story gates and landing position. This keeps travel compatible with the game while the aerial mode is designed.

## Target experience

Build an optional, ORAS-inspired flight sequence for Black 2 / Blaze Black 2 Redux. The player should choose a flying partner, steer over a recognizable Unova overview, discover or select valid places, and land through the game's field transition. It should feel like flying, rather than relabeling the existing Fly command.

## Technical shape

Black 2's field is a collection of discrete tile maps, not a continuous 3D region. A faithful free-flight camera cannot be made by moving the ordinary field camera above the current map. The practical route is a separate flight scene and region atlas, derived from map/location data in the player's loaded ROM and rendered with project-authored graphics.

1. Read the ROM's map/location tables and native Fly destination data. Keep a verified destination's zone and landing coordinates together; never synthesize a landing point from a map name or warp to (0, 0).
2. Draw a new, clearly stylized Unova atlas and flight layer. Use original graphics or properly credited assets; do not bundle Nintendo game art.
3. Let the player steer a mounted flying Pokémon, change pace, and choose a discovered native Fly destination. Flight controls must not send ordinary movement inputs into the live field.
4. Transition to the chosen landing using the validated native field-map event path, then restore normal controls and camera state.
5. Keep the native Fly route available as a fallback, and gate the new scene behind supported ROM/profile checks until route and save behavior are confirmed.

## Current limit

Only the native Fly shortcut is implemented. There is no free-flight scene, atlas, discovery system, or new landing behavior in this build. Before calling the feature Soaring, verify the ROM tables and field-transition ownership, then exercise takeoff, cancel, landing and recovery on a copied save with JIT both enabled and disabled.
