"""Import Black 2's native terrain sampler tables from its decomp source.

Usage: py -3 tools/import_soaring_height_tables.py <field_map_chunk_height.c>

The generated module is bundled with the launcher, so players do not need the
decomp checkout to build flight scenery.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re


TABLES = ("MAP_HEIGHT_SLOPE_TABLE", "MAP_HEIGHT_OFFSET_TABLE")


def parse_table(source: str, name: str) -> list[int]:
    match = re.search(rf"\b{name}\[\]\s*=\s*\{{(.*?)\}}\s*;", source, re.S)
    if match is None:
        raise ValueError(f"Could not find {name}")
    values = [int(value.replace(" ", ""), 0) for value in
              re.findall(r"[-+]?\s*(?:0x[0-9a-fA-F]+|\d+)", match.group(1))]
    if not values:
        raise ValueError(f"{name} is empty")
    return values


def render_module(source_path: Path) -> str:
    source = source_path.read_text(encoding="utf-8")
    slopes = parse_table(source, TABLES[0])
    offsets = parse_table(source, TABLES[1])
    if len(slopes) % 3 or len(slopes) < 900 or len(offsets) < 1000:
        raise ValueError("Decomp terrain tables have unexpected dimensions")

    def tuple_lines(values: list[int], width: int = 12) -> str:
        rows = []
        for start in range(0, len(values), width):
            rows.append("    " + ", ".join(str(value) for value in values[start:start + width]) + ",")
        return "\n".join(rows)

    return (
        '"""Generated from pokebw2 src/ov036/field_map_chunk_height.c.\n'
        'Black 2 terrain sampler tables; see that decomp for GPL attribution.\n'
        'Do not edit by hand; regenerate with import_soaring_height_tables.py.\n'
        '"""\n\n'
        f"MAP_HEIGHT_SLOPE_TABLE = (\n{tuple_lines(slopes)}\n)\n\n"
        f"MAP_HEIGHT_OFFSET_TABLE = (\n{tuple_lines(offsets)}\n)\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="decomp field_map_chunk_height.c")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name("soaring_height_tables.py"))
    args = parser.parse_args()
    args.output.write_text(render_module(args.source), encoding="utf-8", newline="\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
