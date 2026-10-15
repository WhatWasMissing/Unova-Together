"""Build the launcher's small, plain-text feed from patchnotes/*.md."""
from __future__ import annotations

import json
import re
from pathlib import Path

NOTE_NAME = re.compile(r"RELEASE_NOTES_(\d{1,4}\.\d{1,4}\.\d{1,4})\.md\Z")
HEADING = re.compile(
    r"#\s*Unova Together(?:\s+beta)?\s+(\d{1,4}\.\d{1,4}\.\d{1,4})"
    r"(?:\s*[—–-]\s*(.*))?\s*\Z"
)


def build_index(root: Path) -> dict:
    folder = Path(root) / "patchnotes"
    notes = []
    for path in folder.glob("RELEASE_NOTES_*.md"):
        match = NOTE_NAME.fullmatch(path.name)
        if not match:
            continue
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        if not lines:
            raise ValueError(f"Empty patch note: {path.name}")
        heading = HEADING.fullmatch(lines[0].strip())
        if not heading or heading.group(1) != match.group(1):
            raise ValueError(f"Patch note heading does not match its filename: {path.name}")
        body = "\n".join(lines[1:]).strip()
        if not body or len(body) > 12000 or "\x00" in body:
            raise ValueError(f"Invalid patch note text: {path.name}")
        notes.append({
            "version": match.group(1),
            "title": (heading.group(2) or "What changed").strip(),
            "file": path.name,
            "body": body,
        })
    notes.sort(key=lambda note: tuple(map(int, note["version"].split("."))), reverse=True)
    if not notes:
        raise ValueError("No versioned patch notes found")
    return {"schema": 1, "notes": notes}


def write_index(root: Path) -> Path:
    root = Path(root)
    target = root / "patchnotes" / "index.json"
    index = build_index(root)
    target.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    lines = ["# Unova Together patch notes", "",
             "Pick a version to read what changed. The newest release is first.", ""]
    lines.extend(f"- [Unova Together {note['version']} — {note['title']}]({note['file']})"
                 for note in index["notes"])
    lines.extend(["", "The launcher reads these same notes from `index.json` on GitHub."])
    (root / "patchnotes" / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    target = write_index(args.root)
    print(f"Wrote {target}")
