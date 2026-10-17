"""Build Soaring's named regional anchors and route graph from the BW2 decomp.

The generated runtime data is a small, derived catalog. Field scenery and
landing surfaces still come from the player's ROM at runtime.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


def read_constants(path: Path, prefix: str) -> dict[str, int]:
    """Read the decomp's implicit/explicit C-style constant lists."""
    result: dict[str, int] = {}
    next_value = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("//", 1)[0].strip()
        match = re.match(rf"^({prefix}[A-Z0-9_]*)(?:\s*=\s*(0x[0-9a-fA-F]+|\d+))?\s*,?$", line)
        if not match:
            continue
        name, explicit = match.groups()
        value = int(explicit, 0) if explicit else next_value
        result[name] = value
        next_value = value + 1
    return result


def _solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Solve a small square linear system with pivoted Gaussian elimination."""
    n = len(vector)
    rows = [list(matrix[i]) + [vector[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(rows[row][col]))
        if abs(rows[pivot][col]) < 1e-10:
            raise ValueError("Town Map anchor fit is singular")
        rows[col], rows[pivot] = rows[pivot], rows[col]
        divisor = rows[col][col]
        rows[col] = [value / divisor for value in rows[col]]
        for row in range(n):
            if row == col:
                continue
            factor = rows[row][col]
            rows[row] = [a - factor * b for a, b in zip(rows[row], rows[col])]
    return [rows[i][-1] for i in range(n)]


def fit_affine(points: list[tuple[float, float, float]]) -> list[float]:
    """Fit ``world = c0 + c1 * map_x + c2 * map_y`` by least squares."""
    if len(points) < 3:
        raise ValueError("At least three main-map anchors are required")
    normal = [[0.0] * 3 for _ in range(3)]
    rhs = [0.0] * 3
    for map_x, map_y, world in points:
        row = (1.0, map_x, map_y)
        for i in range(3):
            rhs[i] += row[i] * world
            for j in range(3):
                normal[i][j] += row[i] * row[j]
    return _solve(normal, rhs)


def _slug(zone: str) -> str:
    return zone.removeprefix("ZONE_").lower()


def _biome(name: str, place_type: int) -> str:
    key = name.lower().replace("é", "e")
    if any(word in key for word in ("desert", "resort", "sand")):
        return "desert"
    if any(word in key for word in ("mountain", "chasm", "cave", "peak", "tower", "victory road")):
        return "mountain"
    if any(word in key for word in ("forest", "wood", "dreamyard", "shrine", "grove")):
        return "forest"
    if any(word in key for word in ("bay", "tube", "abyssal", "garden", "island")):
        return "coast"
    if place_type == 0:
        return "settlement"
    if place_type == 1:
        return "route"
    return "grassland"


def build_region_data(decomp: Path) -> dict:
    data = decomp / "data"
    zones = read_constants(data / "constants" / "zones.txt", "ZONE_")
    matrices = read_constants(data / "constants" / "map_matrices.txt", "MAP_MATRIX_")
    town_order = json.loads((data / "town_map" / "order.json").read_text(encoding="utf-8"))
    place_by_zone = {}
    matrix_by_zone = {}
    cell_by_zone = {}
    matrix0_name = matrices.get("MAP_MATRIX_OVERWORLD")

    for zone_name, zone_id in zones.items():
        zone_path = data / "zones" / f"{_slug(zone_name)}.json"
        if not zone_path.is_file():
            continue
        zone_data = json.loads(zone_path.read_text(encoding="utf-8"))
        matrix_name = zone_data.get("matrix")
        if matrix_name in matrices:
            matrix_by_zone[zone_name] = matrices[matrix_name]
        place_name = zone_data.get("place")
        if place_name:
            place_slug = place_name.removeprefix("PLACE_").lower()
            place_path = data / "places" / f"{place_slug}.json"
            if place_path.is_file():
                place_by_zone[zone_name] = json.loads(place_path.read_text(encoding="utf-8"))

    main_map_path = data / "map_matrices" / "overworld.json"
    main_zone_grid = json.loads(main_map_path.read_text(encoding="utf-8"))["zones"]
    for zone_name in zones:
        coords = [(x, y) for y, row in enumerate(main_zone_grid)
                  for x, value in enumerate(row) if value == zone_name]
        if coords:
            cell_by_zone[zone_name] = [
                sum(x + 0.5 for x, _ in coords) / len(coords),
                sum(y + 0.5 for _, y in coords) / len(coords),
            ]

    town_places = {}
    for path in (data / "town_map").glob("*.json"):
        if path.name in {"order.json", "place.schema.json"}:
            continue
        try:
            place = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if isinstance(place, dict) and place.get("zone") in zones:
            town_places[place["zone"]] = place

    anchors = []
    for zone_name in town_order:
        place = town_places.get(zone_name)
        if not place:
            continue
        place_name = place_by_zone.get(zone_name, {}).get("name", _slug(zone_name).replace("_", " ").title())
        town = place["position"]
        zone_file = data / "zones" / f"{_slug(zone_name)}.json"
        zone_data = json.loads(zone_file.read_text(encoding="utf-8")) if zone_file.is_file() else {}
        anchor = {
            "zone": zone_name,
            "zoneId": zones[zone_name],
            "name": place_name,
            "type": int(place.get("type", 2)),
            "map": [int(town["x"]), int(town["y"])],
            "fly": bool(place.get("fly", False)),
            "arrivalFlag": place.get("arrival_flag"),
            "description": place.get("description"),
            "landmarks": place.get("landmarks", []),
            "matrix": matrix_by_zone.get(zone_name, -1),
            "biome": _biome(place_name, int(place.get("type", 2))),
        }
        if zone_name in cell_by_zone:
            anchor["mainCell"] = [round(v, 4) for v in cell_by_zone[zone_name]]
        fly = zone_data.get("fly")
        if isinstance(fly, dict):
            anchor["flyPosition"] = [int(fly.get("x", 0)), int(fly.get("y", 0)), int(fly.get("z", 0))]
        anchors.append(anchor)

    # Fit town-map pixels to real 512-unit chunk cells from shared outdoor
    # landmarks. This locates detached named areas in the same regional frame.
    calibration_points = []
    for anchor in anchors:
        if anchor.get("matrix") != matrix0_name or "mainCell" not in anchor:
            continue
        calibration_points.append((anchor["map"][0], anchor["map"][1], anchor["mainCell"][0] * 512))
    town_x_to_world_x = fit_affine(calibration_points)
    calibration_points = []
    for anchor in anchors:
        if anchor.get("matrix") != matrix0_name or "mainCell" not in anchor:
            continue
        calibration_points.append((anchor["map"][0], anchor["map"][1], anchor["mainCell"][1] * 512))
    town_map_to_world_z = fit_affine(calibration_points)

    # Adjacent named zones in the decomp's overworld grid define the authored
    # regional route graph. It is bundled for corridor design and map labels.
    known = set(town_places)
    edges = set()
    for y, row in enumerate(main_zone_grid):
        for x, zone_name in enumerate(row):
            if zone_name not in known:
                continue
            for nx, ny in ((x + 1, y), (x, y + 1)):
                if ny >= len(main_zone_grid) or nx >= len(main_zone_grid[ny]):
                    continue
                other = main_zone_grid[ny][nx]
                if other in known and other != zone_name:
                    edges.add(tuple(sorted((zone_name, other))))

    return {
        "schema": 1,
        "source": "pokebw2 decomp: data/town_map, data/zones, data/map_matrices",
        "mainMatrix": matrix0_name,
        "worldUnitsPerCell": 512,
        "townMapToWorldX": [round(v, 8) for v in town_x_to_world_x],
        "townMapToWorldZ": [round(v, 8) for v in town_map_to_world_z],
        "places": anchors,
        "connections": [list(edge) for edge in sorted(edges)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decomp", type=Path, help="Black 2 decomp checkout")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name("soaring_region_data.json"))
    args = parser.parse_args()
    result = build_region_data(args.decomp)
    if len(result["places"]) < 40 or len(result["connections"]) < 30:
        raise ValueError("Decomp regional catalog is unexpectedly incomplete")
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(result['places'])} named places and {len(result['connections'])} decomp route links to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
