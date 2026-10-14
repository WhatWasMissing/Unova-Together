# Soaring design

Soaring is an optional, local flight scene for Black 2. Enable **Settings → Experimental features → Soaring flight**, then open **Unova → Pokémon → Take flight** and choose a healthy Flying-type Pokémon or a Pokémon with Fly. D-pad steers; hold A while moving forward to boost; L/R changes altitude; X lands near verified clear ground; B returns to take-off. The Town Map is never used as the flight display, and flight positions are not sent to other players.

## Regional atlas preview

Black 2 stores outdoor scenery in discrete map matrices. The main Unova matrix is a 29×27 layout with 277 real terrain cells referencing 52 outdoor zones. The flight worker keeps the take-off matrix as its regional coordinate system and streams nearby chunks as the player crosses the region. Each request stays on the launcher worker, outside the game and render loops. The scene window now reaches 4,096 world units; dense areas fall back through 3,072, 2,560, 2,048, 1,536 and 1,024 until the native face and memory limits are met. The renderer draws visible terrain out to 1,750 units and fades it into fog before the camera far clip.

The renderer shows real ROM terrain and supported buildings, fades distant geometry into fog, and uses an authored sky/sea gradient wherever the matrix has gaps or no more data. This keeps flight visually continuous over open water while avoiding synthetic landing points. Landings come only from verified walkable ground; B always provides a safe return to the original take-off spot.

## Current limits and next checks

Each take-off uses one outdoor matrix. Separate matrices have not been placed into a shared regional atlas, and malformed or unsupported chunks are covered by the cloud sea. The preview does not add walking bridges between maps, encounters in flight, multiplayer mounts or new story destinations. The flight scene remains experimental and off by default.

The two large outdoor matrices in this ROM share the same 277 chunk IDs and grid positions. Other outdoor matrices are small standalone maps without a verified regional transform, so they are not placed at guessed coordinates. The ROM-backed worker tests cover ordinary route terrain, a neighboring zone, budget fallback and the empty area beyond the matrix. The native renderer check covers streamed landings and a neighboring-map landing. At a sampled 3,072-unit window, the scene contained 16,076 faces and the 256×192 renderer check measured 7.75 ms p95; the 2,048-unit sample measured 7.22 ms p95. These focused scene microbenchmarks are not full-game frame-time guarantees. Live playtesting should verify travel across several routes and towns, fog transitions, landing and save/reload before the feature is treated as stable.
