#!/usr/bin/env python3
"""Validate and render a data-driven Gen 5-style dialogue demo as a local HTML preview."""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
import tempfile
import unicodedata
from urllib.parse import urlparse


SCREEN_WIDTH = 256
SCREEN_HEIGHT = 192
TILE = 8
DIALOGUE_HEIGHT_TILES = 4  # field talk bars are 32 tiles wide by four tiles high in BW2
TEXT_LINES = 2
TEXT_CELLS_PER_LINE = 28  # conservative 8px-per-cell budget, including a margin allowance
COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
FLAG = re.compile(r"^[A-Z][A-Z0-9_]{0,31}$")
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_PORTRAIT_BYTES = 4 * 1024 * 1024


class DialogueError(ValueError):
    pass


def _line_cells(line: str) -> int:
    cells = 0
    for char in line:
        if unicodedata.combining(char):
            continue
        cells += 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
    return cells


def validate_scene(scene: object) -> list[str]:
    issues: list[str] = []
    if not isinstance(scene, dict):
        return ["scene must be a JSON object"]
    if scene.get("schemaVersion") != 1:
        issues.append("schemaVersion must be 1")
    if not isinstance(scene.get("id"), str) or not re.fullmatch(r"[a-z0-9_-]{1,48}", scene["id"]):
        issues.append("id must use 1-48 lowercase letters, digits, underscores, or hyphens")
    speakers = scene.get("speakers")
    if not isinstance(speakers, dict) or not speakers:
        issues.append("speakers must be a non-empty object")
        speakers = {}
    else:
        for speaker_id, speaker in speakers.items():
            if not isinstance(speaker_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", speaker_id):
                issues.append(f"invalid speaker id: {speaker_id!r}")
            if not isinstance(speaker, dict) or not isinstance(speaker.get("name"), str) or not speaker["name"].strip():
                issues.append(f"speaker {speaker_id!r} needs a display name")
                continue
            expressions = speaker.get("expressions")
            if not isinstance(expressions, dict) or not expressions:
                issues.append(f"speaker {speaker_id!r} needs at least one expression")
                continue
            for expression, art in expressions.items():
                if not isinstance(expression, str) or not re.fullmatch(r"[a-z0-9_-]{1,24}", expression):
                    issues.append(f"invalid expression id for speaker {speaker_id!r}")
                if not isinstance(art, dict):
                    issues.append(f"expression {speaker_id}.{expression} must be an object")
                    continue
                if art.get("portrait") is not None and not isinstance(art.get("portrait"), str):
                    issues.append(f"portrait for {speaker_id}.{expression} must be a relative path or null")
                if art.get("portrait") is not None:
                    for credit_field in ("credit", "license"):
                        if not isinstance(art.get(credit_field), str) or not art[credit_field].strip():
                            issues.append(f"portrait for {speaker_id}.{expression} needs {credit_field} metadata")
                    source_url = art.get("sourceUrl")
                    try:
                        parsed_url = urlparse(source_url) if isinstance(source_url, str) else None
                    except ValueError:
                        parsed_url = None
                    if parsed_url is None or parsed_url.scheme != "https" or not parsed_url.netloc:
                        issues.append(f"portrait for {speaker_id}.{expression} needs an https sourceUrl")
                if art.get("color") is not None and (not isinstance(art["color"], str) or not COLOR.fullmatch(art["color"])):
                    issues.append(f"color for {speaker_id}.{expression} must be a #RRGGBB color")

    flags = scene.get("flags", {})
    if not isinstance(flags, dict):
        issues.append("flags must be an object of boolean event flags")
        flags = {}
    for name, value in flags.items():
        if not isinstance(name, str) or not FLAG.fullmatch(name) or not isinstance(value, bool):
            issues.append(f"invalid initial event flag {name!r}")

    nodes = scene.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        issues.append("nodes must be a non-empty array")
        return issues
    node_by_id: dict[str, dict] = {}
    for index, node in enumerate(nodes):
        where = f"nodes[{index}]"
        if not isinstance(node, dict):
            issues.append(f"{where} must be an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not re.fullmatch(r"[a-z0-9_-]{1,48}", node_id):
            issues.append(f"{where}.id is invalid")
        elif node_id in node_by_id:
            issues.append(f"duplicate node id {node_id!r}")
        else:
            node_by_id[node_id] = node
        speaker_id = node.get("speaker")
        if not isinstance(speaker_id, str) or speaker_id not in speakers:
            issues.append(f"{where}.speaker does not name a speaker")
        elif isinstance(speakers.get(speaker_id), dict):
            expression = node.get("expression")
            expressions = speakers[speaker_id].get("expressions", {})
            if not isinstance(expression, str) or not isinstance(expressions, dict) or expression not in expressions:
                issues.append(f"{where}.expression is not defined for speaker {speaker_id!r}")
        text = node.get("text")
        if not isinstance(text, str) or not text.strip():
            issues.append(f"{where}.text must be non-empty text")
        else:
            lines = text.split("\n")
            if len(lines) > TEXT_LINES:
                issues.append(f"{where}.text exceeds the {TEXT_LINES}-line dialogue limit")
            if any(_line_cells(line) > TEXT_CELLS_PER_LINE for line in lines):
                issues.append(f"{where}.text exceeds {TEXT_CELLS_PER_LINE} display cells on a line")
            if any(any(unicodedata.category(char).startswith("C") or ord(char) > 0xFFFF
                       for char in line) for line in lines):
                issues.append(f"{where}.text contains a control character or unsupported glyph")
            if any("\r" in line or "\t" in line for line in lines):
                issues.append(f"{where}.text cannot contain tabs or carriage returns")
        next_id = node.get("next")
        if next_id is not None and not isinstance(next_id, str):
            issues.append(f"{where}.next must be a node id")
        choices = node.get("choices", [])
        if not isinstance(choices, list) or len(choices) > 4:
            issues.append(f"{where}.choices must contain at most four options")
            choices = []
        for choice_index, choice in enumerate(choices):
            choice_where = f"{where}.choices[{choice_index}]"
            if not isinstance(choice, dict) or not isinstance(choice.get("label"), str) or not choice["label"].strip():
                issues.append(f"{choice_where} needs a label")
                continue
            if _line_cells(choice["label"]) > TEXT_CELLS_PER_LINE:
                issues.append(f"{choice_where}.label exceeds {TEXT_CELLS_PER_LINE} display cells")
            if any(unicodedata.category(char).startswith("C") or ord(char) > 0xFFFF for char in choice["label"]):
                issues.append(f"{choice_where}.label contains a control character or unsupported glyph")
            if not isinstance(choice.get("next"), str):
                issues.append(f"{choice_where}.next must be a node id")
            condition = choice.get("when")
            if condition is not None:
                if (not isinstance(condition, dict) or not isinstance(condition.get("flag"), str)
                        or not FLAG.fullmatch(condition["flag"]) or not isinstance(condition.get("equals"), bool)):
                    issues.append(f"{choice_where}.when must compare a boolean event flag")
    if not isinstance(scene.get("start"), str) or scene.get("start") not in node_by_id:
        issues.append("start must name an existing node")
    for node_id, node in node_by_id.items():
        targets = [node.get("next")] if node.get("next") is not None else []
        choices = node.get("choices", [])
        if isinstance(choices, list):
            targets.extend(choice.get("next") for choice in choices if isinstance(choice, dict))
        for target in targets:
            if not isinstance(target, str) or target not in node_by_id:
                issues.append(f"node {node_id!r} points to missing node {target!r}")
        for choice in choices if isinstance(choices, list) else []:
            condition = choice.get("when") if isinstance(choice, dict) else None
            condition_flag = condition.get("flag") if isinstance(condition, dict) else None
            if isinstance(condition_flag, str) and condition_flag not in flags:
                issues.append(f"node {node_id!r} tests unknown event flag {condition.get('flag')!r}")
    return issues


def _portrait_data(scene: dict, assets_root: Path | None) -> dict[str, str]:
    encoded: dict[str, str] = {}
    if assets_root is None:
        return encoded
    if assets_root.expanduser().is_symlink():
        raise DialogueError("assets path must not be a symbolic link")
    root = assets_root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise DialogueError("assets path must be a directory")
    for speaker_id, speaker in scene["speakers"].items():
        for expression, art in speaker["expressions"].items():
            relative = art.get("portrait")
            if relative is None:
                continue
            candidate = Path(relative)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise DialogueError(f"portrait path must stay inside the assets folder: {relative}")
            unresolved = root / candidate
            if any((root.joinpath(*candidate.parts[:index])).is_symlink()
                   for index in range(1, len(candidate.parts) + 1)):
                raise DialogueError(f"portrait path must not contain a symbolic link: {relative}")
            try:
                portrait = unresolved.resolve(strict=True)
            except FileNotFoundError:
                # An art path can be prepared before the image is present; show
                # the expression-aware fallback until the credited asset exists.
                continue
            if root not in portrait.parents or not portrait.is_file():
                raise DialogueError(f"portrait is outside the assets folder or is not a regular file: {relative}")
            mime = mimetypes.guess_type(portrait.name)[0]
            if mime not in ALLOWED_IMAGE_TYPES:
                raise DialogueError(f"unsupported portrait file type: {relative}")
            raw = portrait.read_bytes()
            if len(raw) > MAX_PORTRAIT_BYTES:
                raise DialogueError(f"portrait exceeds the 4 MiB limit: {relative}")
            valid_signatures = {
                "image/png": raw.startswith(b"\x89PNG\r\n\x1a\n"),
                "image/jpeg": raw.startswith(b"\xff\xd8\xff"),
                "image/webp": len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP",
                "image/gif": raw.startswith((b"GIF87a", b"GIF89a")),
            }
            if not valid_signatures.get(mime, False):
                raise DialogueError(f"portrait file signature does not match its type: {relative}")
            key = f"{speaker_id}:{expression}"
            encoded[key] = f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"
    return encoded


def build_preview(scene: dict, assets_root: Path | None = None) -> str:
    issues = validate_scene(scene)
    if issues:
        raise DialogueError("; ".join(issues))
    images = _portrait_data(scene, assets_root)
    embedded = json.dumps({"scene": scene, "portraits": images}, ensure_ascii=False).replace("<", "\\u003c")
    return _HTML.replace("__SCENE_DATA__", embedded)


_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Unova Together dialogue preview</title>
<style>
:root{color-scheme:dark;--ink:#eef7fa;--muted:#a8c6ce;--blue:#143c59;--cyan:#58cde0;--gold:#f0c56a;--paper:#102b40}
*{box-sizing:border-box}body{margin:0;background:#0c1823;color:var(--ink);font:15px/1.45 system-ui,sans-serif}
main{max-width:1040px;margin:24px auto;padding:0 18px;display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:20px;align-items:start}
h1{font-size:20px;margin:0 0 4px;font-weight:650}header p{margin:0 0 14px;color:var(--muted);font-size:13px}
#screen{position:relative;width:100%;aspect-ratio:4/3;overflow:hidden;border:3px solid #577183;background:linear-gradient(#a8d5dc 0 64%,#57795a 64% 100%);image-rendering:pixelated;box-shadow:0 12px 36px #0008}
.sky{position:absolute;inset:0 0 36% 0;background:linear-gradient(#284b67 0 20%,#507989 20% 100%);}
.stars{position:absolute;inset:0;background-image:radial-gradient(#d2eef0 1px,transparent 1.3px);background-size:31px 27px;opacity:.25}
.horizon{position:absolute;left:0;right:0;bottom:36%;height:18%;background:linear-gradient(180deg,#536c53,#445845);clip-path:polygon(0 60%,22% 44%,44% 63%,64% 30%,100% 48%,100% 100%,0 100%)}
.ground{position:absolute;left:0;right:0;bottom:36%;height:20%;background:linear-gradient(180deg,#6a925f,#526d4f);border-top:4px solid #9bc078}
.portrait-frame{position:absolute;width:40%;height:65%;left:30%;top:2%;display:grid;place-items:center}
.speaker-tag{position:absolute;z-index:3;left:7%;top:58%;padding:4px 9px;background:#102b40dd;border:1px solid #9dbdc5;color:#fff;font:bold 12px monospace;letter-spacing:.04em;max-width:86%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.portrait{width:100%;height:100%;object-fit:contain;image-rendering:pixelated;filter:drop-shadow(0 5px 2px #10192199)}
.fallback{position:relative;width:48%;height:80%;max-height:148px;min-width:88px;background:transparent;--accent:#5b9db0;}
.fallback .body{position:absolute;left:19%;bottom:0;width:62%;height:43%;background:var(--accent);border:3px solid #172b35;clip-path:polygon(15% 0,85% 0,100% 100%,0 100%);}
.fallback .neck{position:absolute;left:42%;top:42%;width:16%;height:13%;background:#c8946d;border:2px solid #172b35;z-index:1}
.fallback .head{position:absolute;left:23%;top:8%;width:54%;height:44%;background:#d4a177;border:3px solid #172b35;border-radius:42% 42% 35% 35%;z-index:2}
.fallback .hair{position:absolute;left:20%;top:3%;width:60%;height:22%;background:#39404a;clip-path:polygon(10% 45%,30% 0,66% 12%,92% 0,100% 100%,78% 67%,57% 92%,35% 70%,0 100%);z-index:3}
.fallback .eyes{position:absolute;left:31%;top:29%;width:40%;height:5px;display:flex;justify-content:space-between;z-index:4}
.fallback .eyes:before,.fallback .eyes:after{content:"";width:5px;height:5px;background:#14232a}
.fallback .mouth{position:absolute;left:42%;top:40%;width:17%;height:5px;border-bottom:2px solid #723f3c;z-index:4}
.fallback.thoughtful .mouth{width:4px;height:4px;left:49%;border:2px solid #723f3c;border-radius:50%}
.fallback.worried .mouth{top:41%;height:4px;border-top:2px solid #723f3c;border-bottom:0}
.fallback.happy .mouth{height:7px;border-bottom:2px solid #723f3c;border-radius:0 0 10px 10px}
.choices{position:absolute;right:4%;bottom:19%;width:52%;display:grid;gap:3px;z-index:4}
.choice{border:1px solid #c6d5d7;background:#152c3dec;color:#fff;padding:4px 7px;text-align:left;font:11px monospace;min-height:25px;cursor:pointer}
.choice:hover,.choice:focus-visible{background:#286079;outline:2px solid var(--gold);outline-offset:1px}
.choice.locked{opacity:.48;cursor:not-allowed}
.dialogue{position:absolute;left:0;right:0;bottom:0;height:16.6667%;border:2px solid #dde9e8;background:#102b40;color:#fff;padding:2px 5px;font:clamp(8px,1.4vw,14px)/1.1 monospace;display:flex;align-items:center;white-space:pre-line}
.next{position:absolute;right:8px;bottom:6px;color:var(--gold);font:10px monospace;animation:pulse 1s infinite alternate}
@keyframes pulse{to{opacity:.45}}
aside{background:#122638;border:1px solid #314d60;padding:14px;border-radius:8px}aside h2{font-size:13px;margin:0 0 10px}aside p{font-size:12px;color:var(--muted);margin:0 0 12px}
.flag{display:flex;gap:8px;align-items:center;padding:8px 0;border-top:1px solid #294252;font:12px monospace}.flag input{accent-color:var(--cyan)}
.actions{display:flex;gap:8px;margin-top:14px}.actions button{background:#1b4059;border:1px solid #5d7d90;color:#fff;border-radius:4px;padding:7px 10px;cursor:pointer}
.foot{grid-column:1/-1;color:#91aeb7;font-size:11px;margin-top:2px}
@media(max-width:760px){main{grid-template-columns:1fr;margin:12px auto}.portrait-frame{width:48%;left:26%}aside{display:grid;grid-template-columns:1fr 1fr;gap:4px 14px}.foot{grid-column:1}}
</style></head><body>
<main><section><header><h1>Field dialogue preview</h1><p>Gen 5 screen layout · portrait expression · choices and event-flag conditions</p></header>
<div id="screen" role="application" aria-label="Interactive dialogue preview"><div class="sky"></div><div class="stars"></div><div class="horizon"></div><div class="ground"></div>
<div class="portrait-frame" id="portrait-frame"></div><div class="speaker-tag" id="speaker-tag" aria-live="polite"></div><div class="choices" id="choices"></div>
<div class="dialogue" id="dialogue" aria-live="polite"></div><div class="next" id="next"></div></div>
<div class="actions"><button id="advance" type="button">Continue</button><button id="restart" type="button">Restart</button></div></section>
<aside><h2>Demo event flags</h2><p>Toggle a flag to see the corresponding conditional choice appear or lock.</p><div id="flags"></div><h2>Portrait credits</h2><div id="credits"><p>No external portraits in this demo.</p></div></aside>
<div class="foot">No game assets are bundled. Missing portraits use a simple expression-aware silhouette. Supplied artwork must include a credit and license in the scene data.</div></main>
<script id="scene-data" type="application/json">__SCENE_DATA__</script>
<script>
"use strict";
const payload=JSON.parse(document.getElementById("scene-data").textContent),scene=payload.scene;
const nodes=new Map(scene.nodes.map(n=>[n.id,n]));let current=scene.start,flags={...scene.flags};
const el=id=>document.getElementById(id);
function makeFallback(expression,color){const root=document.createElement("div");root.className="fallback "+expression;root.style.setProperty("--accent",color||"#5b9db0");for(const part of ["body","neck","head","hair","eyes","mouth"]){const node=document.createElement("span");node.className=part;root.appendChild(node)}return root}
function drawFlags(){const box=el("flags");box.replaceChildren();for(const [name,value] of Object.entries(flags)){const label=document.createElement("label");label.className="flag";const input=document.createElement("input");input.type="checkbox";input.checked=value;input.addEventListener("change",()=>{flags[name]=input.checked;render()});const text=document.createElement("span");text.textContent=name;label.append(input,text);box.appendChild(label)}}
function render(){const node=nodes.get(current),speaker=scene.speakers[node.speaker],art=speaker.expressions[node.expression]||{};const image=payload.portraits[node.speaker+":"+node.expression];const frame=el("portrait-frame");frame.replaceChildren();if(image){const img=document.createElement("img");img.className="portrait";img.alt=speaker.name+" — "+node.expression;img.src=image;frame.appendChild(img)}else frame.appendChild(makeFallback(node.expression,art.color));el("speaker-tag").textContent=speaker.name+" · "+node.expression;el("dialogue").textContent=node.text;const list=el("choices");list.replaceChildren();for(const choice of node.choices||[]){const allowed=!choice.when||flags[choice.when.flag]===choice.when.equals;const button=document.createElement("button");button.type="button";button.className="choice"+(allowed?"":" locked");button.textContent=choice.label+(choice.when&&!allowed?" · locked":"");button.disabled=!allowed;button.addEventListener("click",()=>{current=choice.next;render()});list.appendChild(button)}el("next").textContent=(node.choices&&node.choices.length)?"":"A · continue";el("advance").disabled=!!(node.choices&&node.choices.some(c=>!c.when||flags[c.when.flag]===c.when.equals));const credits=el("credits");credits.replaceChildren();let hasCredits=false;for(const [speakerId,s] of Object.entries(scene.speakers)){for(const [expression,entry] of Object.entries(s.expressions)){if(entry.portrait){hasCredits=true;const p=document.createElement("p");p.textContent=s.name+" · "+expression+": "+entry.credit+" ("+entry.license+") · "+entry.sourceUrl;credits.appendChild(p)}}}if(!hasCredits){const p=document.createElement("p");p.textContent="No external portraits in this demo.";credits.appendChild(p)}drawFlags()}
function advance(){const node=nodes.get(current);if(node.choices&&node.choices.length)return;if(node.next){current=node.next;render()}}
el("advance").addEventListener("click",advance);el("restart").addEventListener("click",()=>{current=scene.start;flags={...scene.flags};render()});
document.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){if(document.activeElement.tagName!=="BUTTON"){event.preventDefault();advance()}}});render();
</script></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate_parser = sub.add_parser("validate", help="validate dialogue data and screen bounds")
    validate_parser.add_argument("scene", type=Path)
    render_parser = sub.add_parser("render", help="write a self-contained HTML preview")
    render_parser.add_argument("scene", type=Path)
    render_parser.add_argument("output", type=Path)
    render_parser.add_argument("--assets", type=Path, help="optional portrait asset directory")
    render_parser.add_argument("--backup", action="store_true", help="preserve output.bak before replacing an existing preview")
    args = parser.parse_args()
    try:
        scene_path = args.scene.expanduser().resolve(strict=True)
        scene = json.loads(scene_path.read_text(encoding="utf-8"))
        issues = validate_scene(scene)
        if issues:
            result = {"ok": False, "errors": issues, "scene": str(scene_path)}
            print(json.dumps(result, ensure_ascii=False))
            return 2
        if args.command == "validate":
            print(json.dumps({"ok": True, "scene": str(scene_path), "nodes": len(scene["nodes"]),
                              "speakers": len(scene["speakers"]), "screen": [SCREEN_WIDTH, SCREEN_HEIGHT],
                              "dialogueWindowTiles": [SCREEN_WIDTH // TILE, DIALOGUE_HEIGHT_TILES],
                              "lineLimitCells": TEXT_CELLS_PER_LINE, "lineCountLimit": TEXT_LINES}, ensure_ascii=False))
            return 0
        raw_output = args.output.expanduser()
        output = raw_output.resolve(strict=False)
        if output == scene_path or raw_output.is_symlink() or not output.parent.is_dir():
            raise DialogueError("output must be a new regular file in an existing directory")
        backup_path = output.with_name(output.name + ".bak")
        if output.exists() and not args.backup:
            raise DialogueError("output exists; pass --backup to preserve it before replacement")
        if args.backup and not output.exists():
            raise DialogueError("--backup is only valid when output already exists")
        if backup_path.exists() or backup_path.is_symlink():
            raise DialogueError("output backup already exists")
        html = build_preview(scene, args.assets)
        if output.exists():
            backup_created = False
            try:
                with output.open("rb") as original:
                    with backup_path.open("xb") as saved:
                        backup_created = True
                        shutil.copyfileobj(original, saved)
            except OSError:
                if backup_created:
                    backup_path.unlink(missing_ok=True)
                raise
            if backup_path.read_bytes() != output.read_bytes():
                backup_path.unlink(missing_ok=True)
                raise DialogueError("could not verify output backup")
        fd, temp_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(html)
            temp_path.replace(output)
        finally:
            temp_path.unlink(missing_ok=True)
        print(json.dumps({"ok": True, "output": str(output), "scene": str(scene_path),
                          "bytes": output.stat().st_size, "portraitAssetsEmbedded": bool(args.assets)}, ensure_ascii=False))
        return 0
    except (OSError, json.JSONDecodeError, DialogueError) as error:
        print(json.dumps({"ok": False, "error": str(error), "command": args.command}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
