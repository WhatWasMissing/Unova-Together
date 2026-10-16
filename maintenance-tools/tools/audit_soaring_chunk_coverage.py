"""Audit the static outdoor field-chunk decoder against a Black 2 ROM."""
import argparse
from collections import Counter
from pathlib import Path
import json
import struct

import ndspy.narc
import ndspy.rom

from extract_battle_surroundings import field_chunk_model, matrix_cells
from field_scene_geometry import decode
from build_battle_surroundings import FieldSource
from soaring_scene_worker import (flight_atlas_coverage,
                                  flight_matrix_offsets,merged_flight_grid)


def decomp_matrix_audit(decomp_path, matrices, canonical_outdoor):
    """Cross-check ROM matrix dimensions against the Black 2 decomp data."""
    root=Path(decomp_path)
    constants=root/'data'/'constants'/'map_matrices.txt'
    matrix_dir=root/'data'/'map_matrices'
    if not constants.is_file() or not matrix_dir.is_dir():
        raise ValueError(f'Not a Black 2 decomp data tree: {root}')
    names=[line.split(' = ',1)[0].strip() for line in
           constants.read_text(encoding='utf-8').splitlines()
           if line.startswith('MAP_MATRIX_')]
    checked=[];missing=[];mismatches=[]
    for matrix_id in sorted(canonical_outdoor):
        if matrix_id>=len(names):
            missing.append({'matrix':matrix_id,'name':None})
            continue
        name=names[matrix_id]
        suffix=name.removeprefix('MAP_MATRIX_').lower()
        path=matrix_dir/f'{suffix}.json'
        if not path.is_file():
            missing.append({'matrix':matrix_id,'name':name})
            continue
        rows=json.loads(path.read_text(encoding='utf-8'))['maps']
        rom_width,rom_depth,_ids,_zones=matrix_cells(matrices[matrix_id])
        decomp_depth=len(rows);decomp_width=max((len(row) for row in rows),default=0)
        checked.append(matrix_id)
        if (decomp_width,decomp_depth)!=(rom_width,rom_depth) or any(
                len(row)!=rom_width for row in rows):
            mismatches.append({'matrix':matrix_id,'name':name,
                'romDimensions':[rom_width,rom_depth],
                'decompDimensions':[decomp_width,decomp_depth]})
    # Redux adds matrix 416; the public Black 2 decomp stops at 415.
    expected_redux_only=[416]
    passed=(not mismatches and
            [entry['matrix'] for entry in missing]==expected_redux_only)
    return {
        'source':str(root),'decompMatrixCount':len(names),
        'matchedOutdoorMatrices':len(checked),'missingOutdoorMatrices':missing,
        'dimensionMismatches':mismatches,'passed':passed,
    }


def matrix_root_audit(source, canonical_outdoor):
    """Ensure every outdoor takeoff root resolves the same absolute atlas."""
    reference_root=min(canonical_outdoor)
    reference=flight_matrix_offsets(source,reference_root)
    unresolved=[];disagreements=[]
    for root in sorted(canonical_outdoor):
        offsets=flight_matrix_offsets(source,root)
        if root not in reference:
            unresolved.append({'root':root,'reason':'missing from reference atlas'})
            continue
        missing=sorted(set(canonical_outdoor)-set(offsets))
        extra=sorted(set(offsets)-set(canonical_outdoor))
        if missing or extra:
            unresolved.append({'root':root,'missing':missing,'extra':extra})
        expected={matrix:(position[0]-reference[root][0],
                          position[1]-reference[root][1])
                  for matrix,position in reference.items()}
        mismatches=[matrix for matrix,position in expected.items()
                    if offsets.get(matrix)!=position]
        if mismatches:
            disagreements.append({'root':root,'matrices':mismatches})
    return {
        'referenceMatrix':reference_root,'outdoorRoots':len(canonical_outdoor),
        'rootsResolvingAllMatrices':len(canonical_outdoor)-len(unresolved),
        'unresolvedRoots':unresolved,'placementDisagreements':disagreements,
        'passed':not unresolved and not disagreements,
    }


def audit(rom_path, decomp_path=None):
    rom = ndspy.rom.NintendoDSRom.fromFile(str(Path(rom_path)))
    headers = ndspy.narc.NARC(rom.getFileByName('a/0/1/2')).files[0]
    matrices = ndspy.narc.NARC(rom.getFileByName('a/0/0/9')).files
    chunks = ndspy.narc.NARC(rom.getFileByName('a/0/0/8')).files
    areas = rom.getFileByName('a/0/1/3')
    zones = 0
    outdoor_matrix_ids = set()
    matrix_signatures = {}
    for matrix_id, matrix_data in enumerate(matrices):
        try:
            width, height, cell_ids, _cell_zones = matrix_cells(matrix_data)
        except ValueError:
            continue
        matrix_signatures[matrix_id] = (width, height, cell_ids)
    canonical_by_signature = {}
    for matrix_id, signature in matrix_signatures.items():
        canonical_by_signature.setdefault(signature, matrix_id)
    canonical_matrix = {matrix_id: canonical_by_signature[signature]
                        for matrix_id, signature in matrix_signatures.items()}
    chunk_owners = {}
    for zone in range(len(headers) // 48):
        area, matrix = struct.unpack_from('<HH', headers, zone * 48 + 2)
        if area * 10 + 7 > len(areas) or not areas[area * 10 + 6]:
            continue
        if matrix >= len(matrices):
            raise ValueError(f'Outdoor zone {zone} references missing matrix {matrix}')
        zones += 1
        outdoor_matrix_ids.add(matrix)
        _width, _height, cell_ids, _cell_zones = matrix_cells(matrices[matrix])
        for chunk_id in cell_ids:
            if chunk_id >= 0:
                chunk_owners.setdefault(chunk_id, set()).add((zone, matrix))

    formats = Counter()
    decoded = Counter()
    failures = []
    for chunk_id in sorted(chunk_owners):
        if chunk_id >= len(chunks):
            failures.append({'chunk': chunk_id, 'error': 'outside field chunk archive'})
            continue
        source = chunks[chunk_id]
        formats[source[:2].decode('ascii', errors='replace')] += 1
        try:
            model, _props, has_terrain = field_chunk_model(source)
            geometry = decode(bytes(model))
            decoded['ground' if has_terrain else 'sceneryOnly'] += 1
            decoded['faces'] += len(geometry)
        except (ValueError, IndexError, KeyError, struct.error) as error:
            failures.append({'chunk': chunk_id, 'error': str(error),
                             'owners': sorted([list(item) for item in chunk_owners[chunk_id]])})

    source=FieldSource(rom)
    offsets=flight_matrix_offsets(source,0)
    canonical_outdoor={canonical_matrix[matrix] for matrix in outdoor_matrix_ids}
    root_audit=matrix_root_audit(source,canonical_outdoor)
    unresolved=sorted(canonical_outdoor-set(offsets))
    atlas_origin_x,atlas_origin_z,atlas_width,atlas_depth,atlas_cells,_layouts=merged_flight_grid(source,offsets)
    world_coverage=flight_atlas_coverage(atlas_width,atlas_depth,atlas_cells)
    world_coverage.update({
        'resolvedOutdoorMatrices':len(canonical_outdoor)-len(unresolved),
        'totalOutdoorMatrices':len(canonical_outdoor),
        'unresolvedOutdoorMatrices':unresolved,
        'originCell':[atlas_origin_x,atlas_origin_z],
        'rootPlacementAudit':root_audit,
    })
    world_coverage['passed']=(not unresolved and
        world_coverage['enclosedVoidCells']==0 and
        world_coverage['unfilledCellsTouchingMap']==0 and
        world_coverage['coveredComponents']==1 and root_audit['passed'])
    decomp_coverage=(decomp_matrix_audit(decomp_path,matrices,canonical_outdoor)
                     if decomp_path else None)

    return {
        'romCode': rom.idCode.decode('ascii', errors='replace'),
        'outdoorZones': zones,
        'outdoorMatrixIds': len(outdoor_matrix_ids),
        'canonicalOutdoorMatrices': len({canonical_matrix[matrix] for matrix in outdoor_matrix_ids}),
        'uniqueOutdoorChunks': len(chunk_owners),
        'chunkFormats': dict(sorted(formats.items())),
        'decoded': dict(sorted(decoded.items())),
        'worldCoverage':world_coverage,
        'decompCrosscheck':decomp_coverage,
        'failures': failures,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, help='Path to the English Black 2 ROM')
    parser.add_argument('--decomp', help='Optional path to the Black 2 decomp checkout')
    args = parser.parse_args()
    result = audit(args.rom,args.decomp)
    print(json.dumps(result, indent=2))
    return 1 if (result['failures'] or not result['worldCoverage']['passed'] or
                 result['decompCrosscheck'] is not None and
                 not result['decompCrosscheck']['passed']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
