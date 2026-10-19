"""Safe Redux field-character model selection for the launcher.

The game resolves the walking avatar through overlay 36's PLAYER_SPRITE_MAP.
We replace only the two gender-specific normal-walking object codes; cycling,
surfing and other special movement forms keep their native models.
"""
from pathlib import Path
import hashlib
import json
import os
import struct

import ndspy.code
import ndspy.narc
import ndspy.rom

import unova_storage as storage
from . import preferences as prefs


PLAYER_MAP = (
    (0xE7, 0), (0xE8, 1), (0xE9, 2), (0xE9, 3), (0xEA, 4),
    (0xEB, 4), (0xEC, 4), (0xEE, 4), (0xEF, 4), (0xED, 4),
    (0xF0, 0), (0xF1, 1), (0xF2, 2), (0xF2, 3), (0xF3, 4),
    (0xF4, 4), (0xF5, 4), (0xF7, 4), (0xF8, 4), (0xF6, 4),
)
PLAYER_MAP_SIGNATURE = b''.join(struct.pack('<HH', *entry) for entry in PLAYER_MAP)
OVERLAY_ID = 36
CONFIG_ARCHIVE = 'a/0/4/7'
RESOURCE_ARCHIVE = 'a/0/4/8'
CONFIG_RECORD_SIZE = 28
CONFIG_COUNT = 1008
HUMANOID_SCENE_NODES = frozenset((10, 11))
WALK_ANIMATION_CONTROLLERS = frozenset((13, 14))
KNOWN_LABELS = {0x126B: 'Cynthia'}


def display_name(model_id):
    model_id = int(model_id)
    known = KNOWN_LABELS.get(model_id)
    return f'{known} (model {model_id})' if known else f'NPC model {model_id}'


def _player_map_offset(data):
    offsets = []
    # Ignore only the two object-code words that we intentionally replace.
    # All movement-form codes and exState words remain part of the signature,
    # so a previously generated player-model ROM can be validated too.
    anchor = PLAYER_MAP_SIGNATURE[2:40]
    suffix = PLAYER_MAP_SIGNATURE[42:]
    start = 0
    while True:
        found = data.find(anchor, start)
        if found < 0:
            break
        offset = found - 2
        if offset >= 0 and data[offset + 42:offset + 80] == suffix:
            offsets.append(offset)
        start = found + 1
    if len(offsets) != 1:
        raise ValueError('This game does not have the reviewed Redux player-model table.')
    return offsets[0]


def _patch_player_map(data, model_id):
    if type(model_id) is not int or not 0 <= model_id <= 0xFFFF:
        raise ValueError('Choose a valid NPC model.')
    offset = _player_map_offset(data)
    patched = bytearray(data)
    # Each PLAYER_SPRITE_MAP entry is {u16 objCode, u16 exState}; the first
    # entry in each sex's ten-form block is the normal walking avatar.
    struct.pack_into('<H', patched, offset, model_id)
    struct.pack_into('<H', patched, offset + 10 * 4, model_id)
    return bytes(patched)


def _actor_models(config_data, resources):
    if len(config_data) != 4 + CONFIG_COUNT * CONFIG_RECORD_SIZE:
        raise ValueError('The field actor table has an unexpected size; no ROM changes were made.')
    count = struct.unpack_from('<I', config_data)[0]
    if count != CONFIG_COUNT:
        raise ValueError('The field character table is not the reviewed Redux layout.')
    eligible = []
    seen = set()
    for index in range(count):
        offset = 4 + index * CONFIG_RECORD_SIZE
        row = config_data[offset:offset + CONFIG_RECORD_SIZE]
        model_id = struct.unpack_from('<H', row, 0)[0]
        entity_type, scene_node = struct.unpack_from('<BB', row, 2)
        sprite_controller = row[9]
        texture_resource, model_resource = struct.unpack_from('<HH', row, 16)
        if (entity_type != 1 or scene_node not in HUMANOID_SCENE_NODES
                or sprite_controller not in WALK_ANIMATION_CONTROLLERS
                or model_id in seen or texture_resource >= len(resources)
                or model_resource >= len(resources)):
            continue
        # Gen 5 stores the animated model in res2 and its matching texture in
        # res1. Reject props, incomplete actors and entries with missing art.
        if resources[texture_resource][:4] != b'BTX0' or resources[model_resource][:4] != b'BMD0':
            continue
        seen.add(model_id)
        eligible.append(model_id)
    if not eligible:
        raise ValueError('No compatible animated NPC models were found in this ROM.')
    return sorted(eligible)


def _load_rom(path):
    rom = ndspy.rom.NintendoDSRom.fromFile(str(path))
    if rom.idCode != b'IREO':
        raise ValueError('Player models are supported for the reviewed English Blaze Black 2 Redux game.')
    return rom


def _catalog_from_rom(rom):
    overlays = ndspy.code.loadOverlayTable(
        rom.arm9OverlayTable, lambda overlay_id, file_id: rom.files[file_id])
    if OVERLAY_ID not in overlays:
        raise ValueError('This game is missing the Redux player-model table.')
    _player_map_offset(overlays[OVERLAY_ID].data)
    config = ndspy.narc.NARC(rom.getFileByName(CONFIG_ARCHIVE))
    resources = ndspy.narc.NARC(rom.getFileByName(RESOURCE_ARCHIVE))
    return _actor_models(config.files[0], resources.files)


def list_models(path):
    """Return compatible animated humanoid NPC object codes from a ROM."""
    return _catalog_from_rom(_load_rom(Path(path)))


def _verify_model_in_rom(rom, model_id):
    models = _catalog_from_rom(rom)
    if model_id not in models:
        raise ValueError(f'NPC model {model_id} is not a compatible animated character in this ROM.')
    return models


def _patch_rom(rom, model_id):
    _verify_model_in_rom(rom, model_id)
    overlays = ndspy.code.loadOverlayTable(
        rom.arm9OverlayTable, lambda overlay_id, file_id: rom.files[file_id])
    overlay = overlays[OVERLAY_ID]
    overlay.data = _patch_player_map(overlay.data, model_id)
    rom.files[overlay.fileID] = overlay.save(compress=overlay.compressed)
    rom.arm9OverlayTable = ndspy.code.saveOverlayTable(overlays)


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def prepare_variant(source, home, model_id):
    """Create or reuse one launcher-owned ROM variant; never edit the source."""
    if model_id == 0:
        return Path(source).resolve()
    if type(model_id) is not int or not 0 <= model_id <= 0xFFFF:
        raise ValueError('Choose a valid NPC model.')
    source = Path(source).resolve()
    if source.suffix.lower() != '.nds' or not source.is_file():
        raise ValueError('Choose an existing Nintendo DS ROM first.')
    source_stat = source.stat()
    source_signature = (source_stat.st_size, source_stat.st_mtime_ns)
    source_digest = _sha256(source)
    root = Path(home).resolve()
    cache = root / '.launcher-player-models'
    if not storage.safe_managed_path(cache, root):
        raise ValueError('The player-model cache folder is unsafe; remove linked or externally linked paths before continuing.')
    cache.mkdir(parents=True, exist_ok=True)
    if not storage.safe_managed_path(cache, root):
        raise ValueError('The player-model cache folder is unsafe; remove linked or externally linked paths before continuing.')
    cache = cache.resolve()
    target = cache / source.name
    manifest = cache / (source.name + '.player-model.json')
    if not storage.safe_managed_path(target, root) or not storage.safe_managed_path(manifest, root):
        raise ValueError('A player-model cache file is unsafe; remove linked or externally linked paths before continuing.')
    if target.exists() and manifest.is_file():
        try:
            saved = json.loads(manifest.read_text(encoding='utf-8'))
            expected = {
                'source_sha256': source_digest,
                'model_id': model_id,
                'output_size': target.stat().st_size,
                'output_sha256': _sha256(target),
            }
            if saved == expected:
                return target
            if (source == target and isinstance(saved, dict)
                    and saved.get('model_id') == model_id
                    and saved.get('output_size') == expected['output_size']
                    and saved.get('output_sha256') == expected['output_sha256']):
                return target
        except (OSError, ValueError, TypeError):
            pass
    if source == target:
        raise ValueError('Choose the original game ROM instead of a cached player-model copy.')

    with prefs.staged_path(target) as pending:
        rom = _load_rom(source)
        _patch_rom(rom, model_id)
        rom.saveToFile(str(pending))
        current_stat = source.stat()
        if (current_stat.st_size, current_stat.st_mtime_ns) != source_signature:
            raise ValueError('The source ROM changed while the character model was being prepared.')
        check = _load_rom(pending)
        overlay = ndspy.code.loadOverlayTable(
            check.arm9OverlayTable, lambda overlay_id, file_id: check.files[file_id])[OVERLAY_ID]
        offset = _player_map_offset(overlay.data)
        if (struct.unpack_from('<H', overlay.data, offset)[0] != model_id
                or struct.unpack_from('<H', overlay.data, offset + 40)[0] != model_id):
            raise ValueError('The generated player-model ROM did not pass its reload check.')
        current_stat = source.stat()
        if (current_stat.st_size, current_stat.st_mtime_ns) != source_signature:
            raise ValueError('The source ROM changed while the character model was being prepared.')
        os.replace(pending, target)
        prefs.atomic(manifest, json.dumps({
            'source_sha256': source_digest,
            'model_id': model_id,
            'output_size': target.stat().st_size,
            'output_sha256': _sha256(target),
        }))
    return target
