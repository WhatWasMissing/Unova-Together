# Refinements in development

These changes are in a local development build after stable 1.0.10. They are not
yet a new GitHub release.

- Hosting: LAN discovery announcements run outside the emulator frame loop with
  a nonblocking socket and one pending announcement. Protocol and timing are
  unchanged. Local co-op checkpoint buffers are reused without changing capture
  cadence or recovery contents. Native ping and checkpoint timing are visible.
- Teammates: overlay sprites project using the camera matched to each displayed
  framebuffer, and remote motion is sampled at render time. This targets shaking
  when walking around a teammate; native NPC rendering is unchanged.
- Followers: dedicated normal and shiny variants share directional artwork,
  geometry and transparent silhouettes. All 649 species and 743 supported
  appearance variants pass the expanded sprite audit.
- Companions: longer rotation of implicit-nature observations, friendship/type/
  area/season context and varied reactions. Low-HP companions use gentle motion.
  Longer replies paginate instead of cutting off their final sentences.
- Connection feedback: explains stale presence, menus, battles, map mismatch,
  ROM mismatch, camera availability and known version differences. Legacy
  development-version advertisements are identified as inconclusive.
- Trainer browsing: every valid ROM opponent remains available; practice teams
  can be filtered to near-party, easier or harder levels and show team counts.
  This improves catalog access without changing story eligibility or networking.

## Experimental Soaring

Enable **Settings → Experimental → Soaring flight** in the matching launcher;
it remains off by default. In game use **Unova → Pokémon → Take flight**, then
choose a healthy Flying-type partner or a Pokémon with Fly.

The flight scene reads the player's actual outdoor map meshes and textures,
including supported static buildings. It does not open or draw over the Town
Map. Extraction runs in a launcher worker, outside the game/render thread.

D-pad steers and moves; hold A while moving forward to boost. L/R lowers/raises
altitude. X or the touch-screen Land control descends near a position where the
player previously stood in the current field. B returns to the take-off point.
Landing elsewhere uses the existing verified native field-transition event,
never a guessed actor-coordinate write. Reset, field loss or a battle cancels
the local scene. No synthetic flight positions are sent to other players.

The main Black 2 outdoor matrix acts as a regional flight atlas: its 29×27
layout references 277 real terrain cells across 52 outdoor zones. The scene
now streams up to 4,096 world units around the flight position. Dense scenes
step down through 3,072, 2,560, 2,048, 1,536 and 1,024 units to stay within the
32,000-face and 16 MB scene limits. At one sampled town position, a 3,072-unit
scene contained 16,076 faces across 21 chunks and serialized to 2.4 MB. Visible
terrain fades into fog before the 1,750-unit render cutoff. Map extraction
stays on the launcher worker, and camera-space culling keeps hidden geometry
out of the native render pass. The 256×192 renderer check measured 7.75 ms p95
for the wider scene and 7.22 ms for a 2,048-unit sample; this microbenchmark
does not guarantee full-game performance. Cruise speed is 100 units/s;
holding A while moving forward boosts to 180 units/s.
Landing choices come from flat, ordinary walkable collision tiles under the
actual outdoor mesh; blocked tiles, water, special behaviors, slopes, props and
ambiguous stacked surfaces are excluded. Visited clear ground remains available
across neighbouring zones. A green marker identifies nearby ground, and the
landing camera interpolates the rider to the selected tile before the existing
native map-change event moves the player. The flight renderer closes a small
number of missing outer building walls at exposed roof edges; other unsupported
model gaps may remain. Travel between separate map
matrices, seamless travel across the whole region, roaming encounters,
fully rigged 3D mounts and shared multiplayer flight are not implemented.
Unsupported animated props may be omitted; indoor/scripted fields can refuse
flight. Keep the feature experimental pending live take-off/landing/save tests.

## Validation

Three-player ENet pairing/radio/result/cleanup/disconnect regression passes on
isolated ports, including a deliberately stalled discovery sender. Checkpoint
bytes match the original serializer and retained snapshots survive repeated
captures, errors and storage lifetime. Camera-buffer, renderer, follower,
dialogue and companion regressions pass. Actual town geometry extraction
produced 5,442 faces and 139 textures; neighbouring zone 96 loaded from zone
191. The renderer uses perspective-correct textures, per-pixel depth,
near-plane clipping and camera-space bounds culling. On the same local 120-view
renderer check, the expanded 1,024-unit scene (6,628 faces) measured 3.8 ms
average and 6.1 ms median-of-three p95, compared with 4.7 ms average and 6.5 ms
p95 for the older 768-unit scene before bounds culling. This is only the scene
renderer microbenchmark, not a full-game or multiplayer performance guarantee.
Other maps and systems may differ. The two large outdoor matrices in this ROM
use the same 277 chunks at the same positions; smaller standalone matrices
still lack a verified transform and are not stitched into the regional scene.
Flight over empty gaps has no synthetic landing ground.
Draw-order, clipping, repeated-redraw and streamed-position tests pass. Hosted hitching and teammate shaking still
need confirmation in the installed development build.
