"""Export, load, render, and exercise landing on every Redux outdoor matrix.

All ROM exports, native executables, and preview captures live in a temporary
directory and are removed automatically when the sweep finishes.
"""
from pathlib import Path
import os
import re
import shlex
import struct
import subprocess
import tempfile
import time
import json

import ndspy.rom

from build_battle_surroundings import FieldSource
from extract_battle_surroundings import matrix_cells
from soaring_scene_worker import (SoaringWorker, export_with_budget, flight_matrix_aliases,
                                  flight_matrix_layout, flight_matrix_offsets,
                                  _MATRIX_SCALE)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'melonDS-source-1.1'
FRONTEND = SOURCE / 'src' / 'frontend' / 'qt_sdl'
ROM_DEFAULT = ROOT / 'game-files' / 'unova-together' / (
    'Pokemon Black 2 Redux Complete (v1.4.1) - Unova Together.nds')
MSYS_BIN = Path('C:/msys64/ucrt64/bin')
QTDIR = Path('C:/msys64/ucrt64/share/qt6')
NO_LANDING_MATRICES = {273}  # Marine Tube is exterior, but has no safe ground.


def valid_flight_zone(source, zone):
    """A landing label must resolve to a real, exterior area in this ROM."""
    if zone < 0 or zone >= len(source.headers) // 48:
        return False
    area, _matrix = struct.unpack_from('<HH', source.headers, zone * 48 + 2)
    return area * 10 + 7 <= len(source.areas) and bool(source.areas[area * 10 + 6])


def outdoor_roots(source):
    aliases = flight_matrix_aliases(source)
    roots = {}
    outdoor_zones = set()
    for zone in range(len(source.headers) // 48):
        area, raw_matrix = struct.unpack_from('<HH', source.headers, zone * 48 + 2)
        if area * 10 + 7 > len(source.areas) or not source.areas[area * 10 + 6]:
            continue
        matrix = aliases.get(raw_matrix, raw_matrix)
        roots.setdefault(matrix, zone)
        outdoor_zones.add(zone)
    return aliases, roots, outdoor_zones


def launch_point(source, matrix, zone, outdoor_zones, aliases, offsets):
    width, depth, ids, zones = flight_matrix_layout(source, matrix, aliases)
    ox, oz = offsets[matrix]
    candidates = []
    for cell, chunk in enumerate(ids):
        if chunk < 0:
            continue
        cell_zone = zones[cell] if zones is not None else -1
        selected_zone = cell_zone if cell_zone in outdoor_zones else zone
        row, column = divmod(cell, width)
        # Prefer a labelled cell near the matrix centre to avoid selecting a
        # stray transition tile when the matrix has an explicit zone table.
        score = (cell_zone not in outdoor_zones,
                 (column - (width - 1) / 2) ** 2 +
                 (row - (depth - 1) / 2) ** 2, row, column)
        candidates.append((score, selected_zone,
                          ox + (column + .5) * _MATRIX_SCALE,
                          oz + (row + .5) * _MATRIX_SCALE))
    if not candidates:
        raise AssertionError(f'Matrix {matrix} has no occupied launch cell')
    _score, selected_zone, x, z = min(candidates)
    return selected_zone, x, z


def build_renderer(directory, env):
    flags = shlex.split(subprocess.check_output(
        [str(MSYS_BIN / 'pkg-config.exe'), '--cflags', '--libs', 'Qt6Gui'],
        env=env, text=True))
    executable = directory / 'check-soaring-scene.exe'
    subprocess.run([
        str(MSYS_BIN / 'g++.exe'), '-std=c++17', '-O2',
        '-I' + str(FRONTEND), str(ROOT / 'tools' / 'check_soaring_scene.cpp'),
        '-o', str(executable), *flags,
    ], env=env, check=True)
    return executable


def check_background_worker(source, renderer, work, env, rom_path,
                            aliases, roots, outdoor_zones, matrix=225):
    """Exercise the launcher-facing request/ready worker with the real ROM."""
    if matrix not in roots or roots[matrix] < 0:
        raise AssertionError(f'Matrix {matrix} is unavailable as a worker request fixture')
    zone, x, z = launch_point(source, matrix, roots[matrix], outdoor_zones,
                              aliases, flight_matrix_offsets(source, matrix))
    if zone < 0:
        raise AssertionError(f'Worker request selected invalid take-off map {zone}')
    cache = work / f'worker-request-{matrix}'
    cache.mkdir()
    worker = SoaringWorker(rom_path, cache)
    try:
        # The disposable request is the fixture itself; ignore its rounded
        # filesystem timestamp so it cannot race the worker's start time.
        worker.started = 0
        request = cache / 'request-native-check.json'
        request.write_text(json.dumps({'zone': zone, 'worldX': x,
                                       'worldZ': z, 'worldY': 0}),
                           encoding='utf-8')
        ready = cache / 'ready-native-check.json'
        deadline = time.monotonic() + 60
        while not ready.is_file() and time.monotonic() < deadline:
            time.sleep(.05)
        if not ready.is_file():
            raise AssertionError('Background Soaring worker did not answer within 60 seconds')
        response = json.loads(ready.read_text(encoding='utf-8'))
        if response.get('error'):
            raise AssertionError(f'Background Soaring worker rejected request: {response["error"]}')
        scene_path = (cache / response.get('scene', '')).resolve()
        if not scene_path.is_relative_to(cache.resolve()) or not scene_path.is_file():
            raise AssertionError('Background Soaring worker returned a scene outside its cache')
        scene = json.loads(scene_path.read_text(encoding='utf-8'))
        if not scene.get('faces') or not scene.get('landings'):
            raise AssertionError('Background worker scene lacks scenery or safe landing targets')
        invalid = [site for site in scene['landings']
                   if not valid_flight_zone(source,site[0])]
        if invalid:
            raise AssertionError(f'Background worker returned invalid landings: {invalid[:3]}')
        checked = subprocess.run([str(renderer), str(scene_path), '--check-landing'],
                                  cwd=work, env=env, capture_output=True, text=True)
        if checked.returncode:
            raise AssertionError('Background worker scene failed native load/landing check:\n'
                                 f'{checked.stdout}\n{checked.stderr}')
        print('Background ROM request/ready worker passed native load and landing checks.',
              flush=True)
    finally:
        worker.stop.set()
        worker.thread.join(timeout=3)
        if worker.thread.is_alive():
            raise AssertionError('Background Soaring worker did not stop cleanly')


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROM_DEFAULT)
    parser.add_argument('--matrices', type=int, nargs='*',
                        help='Limit the sweep to these matrix IDs (default: all outdoor roots)')
    parser.add_argument('--check-streams', action='store_true',
                        help='Also test loading scenery 450 world units into flight for each selected root')
    args = parser.parse_args()
    if not args.rom.is_file():
        raise SystemExit(f'Black 2 Redux ROM not found: {args.rom}')

    env = dict(os.environ)
    env['PATH'] = str(MSYS_BIN) + os.pathsep + env.get('PATH', '')
    env['QT_QPA_PLATFORM'] = 'offscreen'
    env['QT_PLUGIN_PATH'] = str(QTDIR / 'plugins')
    env['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(QTDIR / 'plugins' / 'platforms')

    rom = ndspy.rom.NintendoDSRom.fromFile(str(args.rom))
    source = FieldSource(rom)
    aliases, roots, outdoor_zones = outdoor_roots(source)
    offsets = flight_matrix_offsets(source, 0)
    if set(roots) != set(offsets):
        raise AssertionError(f'Outdoor root/atlas mismatch: roots={sorted(roots)} offsets={sorted(offsets)}')
    if not NO_LANDING_MATRICES <= set(roots):
        raise AssertionError('Marine Tube matrix is missing from the Redux outdoor root set')

    with tempfile.TemporaryDirectory(prefix='unova-soaring-matrix-sweep-') as temp:
        work = Path(temp)
        (work / 'test-fixtures').mkdir()
        renderer = build_renderer(work, env)
        successes = []
        no_landing = []
        slowest = (0.0, None, None)
        largest_frame = (0.0, None)
        selected = sorted(roots) if args.matrices is None else args.matrices
        missing = sorted(set(selected) - set(roots))
        if missing:
            raise SystemExit(f'Not outdoor matrix roots: {missing}')
        for matrix in selected:
            root_offsets = flight_matrix_offsets(source, matrix)
            if root_offsets.get(matrix) != (0, 0):
                raise AssertionError(f'Matrix {matrix} was not normalized as its own launch origin')
            zone, x, z = launch_point(source, matrix, roots[matrix],
                                      outdoor_zones, aliases, root_offsets)
            scene_dir = work / f'matrix-{matrix}'
            result = export_with_budget(source, zone, x, z, 0.0, scene_dir)
            atlas_width,atlas_height=result['atlasSize']
            if len(result.get('atlasLandmarks',()))<50:
                raise AssertionError(f'Matrix {matrix} did not map the decomp named places')
            if result.get('regionConnectorCount')!=len(result.get('decompRoutes',())):
                raise AssertionError(f'Matrix {matrix} has inconsistent decomp route metadata')
            if result.get('regionConnectorCount',0)<40:
                raise AssertionError(f'Matrix {matrix} is missing authored regional connectors')
            if len(result.get('decompRouteNames',()))!=len(result['decompRoutes']):
                raise AssertionError(f'Matrix {matrix} route names do not match route geometry')
            for marker in result['atlasLandmarks']:
                if (len(marker)!=7 or not 0<=marker[0]<=atlas_width or
                        not 0<=marker[1]<=atlas_height or not marker[2]):
                    raise AssertionError(f'Matrix {matrix} exported an invalid place marker: {marker}')
            for route in result['decompRoutes']:
                if len(route)<2 or any(not (0<=point[0]<=atlas_width and
                                             0<=point[1]<=atlas_height)
                                       for point in route):
                    raise AssertionError(f'Matrix {matrix} exported a route outside the atlas')
            if len(result.get('regionFaces',()))>6000:
                raise AssertionError(f'Matrix {matrix} exceeds the native regional terrain limit')
            if any(value not in (0,1,2,3,4) for value in result['atlasBiome']):
                raise AssertionError(f'Matrix {matrix} has an invalid regional biome')
            invalid_landings = [site for site in result['landings']
                                if not valid_flight_zone(source,site[0])]
            if invalid_landings:
                raise AssertionError(
                    f'Matrix {matrix} exported invalid landing destinations: '
                    f'{invalid_landings[:3]}')
            if not result['faces'] and not result['regionFaces'] and not result['flywayFaces']:
                raise AssertionError(f'Matrix {matrix} exported no visible scene geometry')
            landing_count = len(result['landings'])
            if matrix in NO_LANDING_MATRICES:
                if landing_count:
                    raise AssertionError(f'Matrix {matrix} unexpectedly gained unsafe landing sites')
                mode = '--expect-no-landing'
                no_landing.append(matrix)
            else:
                if not landing_count:
                    raise AssertionError(f'Matrix {matrix} exported no clear nearby landing target')
                mode = '--check-landing'
            completed = subprocess.run(
                [str(renderer), str(scene_dir / 'scene.json'), mode],
                cwd=work, env=env, capture_output=True, text=True)
            if completed.returncode:
                raise AssertionError(
                    f'Matrix {matrix} native scene/flight/landing check failed:\n'
                    f'{completed.stdout}\n{completed.stderr}')
            timing = re.search(r'p95: ([0-9.]+) ms; maximum: ([0-9.]+) ms',
                               completed.stderr)
            if not timing:
                raise AssertionError(f'Matrix {matrix} renderer did not report timings')
            p95, maximum = map(float, timing.groups())
            if p95 >= 33.3:
                raise AssertionError(f'Matrix {matrix} exceeds 30 FPS frame budget: {p95:.2f} ms p95')
            if p95 > slowest[0]:
                slowest = (p95, matrix, maximum)
            if maximum > largest_frame[0]:
                largest_frame = (maximum, matrix)
            successes.append((matrix, len(result['faces']),
                              len(result['textures']), landing_count, p95))
            print(f'Matrix {matrix}: loaded/rendered, {len(result["faces"])} faces, '
                  f'{len(result["textures"])} textures, {landing_count} landings, '
                  f'p95 {p95:.2f} ms', flush=True)
            if args.check_streams:
                stream_dir=work/f'matrix-{matrix}-stream'
                streamed=export_with_budget(source,zone,x+450,z,0.0,stream_dir)
                if not streamed['faces'] and not streamed['regionFaces'] and not streamed['flywayFaces']:
                    raise AssertionError(f'Matrix {matrix} streamed scene has no visible geometry')
                continuity=subprocess.run(
                    [str(renderer),str(scene_dir/'scene.json'),'--check-stream',
                     str(stream_dir/'scene.json'),str(streamed['zone'])],
                    cwd=work,env=env,capture_output=True,text=True)
                if continuity.returncode:
                    raise AssertionError(
                        f'Matrix {matrix} streamed-scene continuity check failed:\n'
                        f'{continuity.stdout}\n{continuity.stderr}')
                print(f'Matrix {matrix}: streamed scenery kept the flight state and position.',
                      flush=True)
        check_background_worker(source, renderer, work, env, args.rom,
                                aliases, roots, outdoor_zones,225)
        check_background_worker(source, renderer, work, env, args.rom,
                                aliases, roots, outdoor_zones,357)

    if args.matrices is None and (len(successes) != 69 or no_landing != [273]):
        raise AssertionError(f'Unexpected sweep coverage: {len(successes)} matrices; no landing={no_landing}')
    if 273 in no_landing and (args.matrices is None or 273 in selected):
        print(f'Passed {len(successes)} outdoor matrices; only Marine Tube {no_landing[0]} '
              f'has no safe landing. Slowest p95: {slowest[0]:.2f} ms on matrix '
              f'{slowest[1]}; largest frame: {largest_frame[0]:.2f} ms on matrix '
              f'{largest_frame[1]}.')
    else:
        print(f'Passed {len(successes)} selected outdoor matrices. Slowest p95: '
              f'{slowest[0]:.2f} ms on matrix {slowest[1]}; largest frame: '
              f'{largest_frame[0]:.2f} ms on matrix {largest_frame[1]}.')


if __name__ == '__main__':
    main()
