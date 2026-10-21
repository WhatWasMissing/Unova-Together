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
import ndspy.texture
from PIL import Image

import unova_storage as storage
from . import preferences as prefs
from .player_model_names import NPC_MODEL_LABELS, POKEMON_MODEL_LABELS, SPECIAL_NPC_MODEL_LABELS


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
HUMAN_SCENE_NODES = frozenset((2,))
HUMAN_WALK_ANIMATION_CONTROLLERS = frozenset((2, 3))
POKEMON_SCENE_NODES = frozenset((10, 11))
POKEMON_WALK_ANIMATION_CONTROLLERS = frozenset((13, 14))


def display_name(model_id):
    model_id = int(model_id)
    if model_id in SPECIAL_NPC_MODEL_LABELS:
        return f'{SPECIAL_NPC_MODEL_LABELS[model_id]} (model {model_id})'
    if model_id in NPC_MODEL_LABELS:
        return f'NPC · {NPC_MODEL_LABELS[model_id]} (model {model_id})'
    if model_id in POKEMON_MODEL_LABELS:
        return f'Pokémon · {POKEMON_MODEL_LABELS[model_id]} (model {model_id})'
    return f'Field character model {model_id}'


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
        is_animated_human = (
            scene_node in HUMAN_SCENE_NODES
            and sprite_controller in HUMAN_WALK_ANIMATION_CONTROLLERS
        )
        is_animated_pokemon = (
            scene_node in POKEMON_SCENE_NODES
            and sprite_controller in POKEMON_WALK_ANIMATION_CONTROLLERS
        )
        if (entity_type != 1 or not (is_animated_human or is_animated_pokemon)
                or model_id in seen or texture_resource >= len(resources)
                or model_resource >= len(resources)):
            continue
        # Field characters and Pokémon use billboard actors backed by BTX0
        # textures plus the shared BMD0 model. Restrict both categories to the
        # reviewed walking-animation sets; props and partial records are out.
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
    """Return compatible animated human and Pokémon field actor codes from a ROM."""
    return _catalog_from_rom(_load_rom(Path(path)))


def _render_i4(texture, palette):
    if texture.format != ndspy.texture.TextureFormat.I4:
        raise ValueError('This field character uses an unsupported preview texture format.')
    width, height = texture.width, texture.height
    if not (0 < width <= 128 and 0 < height <= 128):
        raise ValueError('This field character has an unsupported preview image size.')
    packed = texture.data1
    pixel_count = width * height
    if len(packed) * 2 < pixel_count or len(palette.colors) < 16:
        raise ValueError('This field character has incomplete preview graphics.')
    image = Image.new('RGBA', (width, height))
    pixels = []
    for byte in packed[:(pixel_count + 1) // 2]:
        pixels.append(byte & 0x0F)
        if len(pixels) < pixel_count:
            pixels.append(byte >> 4)
    colors = [(color.r * 255 // 31, color.g * 255 // 31, color.b * 255 // 31, 0 if index == 0 else 255)
              for index, color in enumerate(palette.colors[:16])]
    image.putdata([colors[index] for index in pixels])
    return image


def _preview_steps(controller):
    # The face sequence and durations follow the pinned B2W2 field billboard
    # animation tables. NPC controllers 2 and 3 expose the north-facing walk
    # cycle; Pokémon controllers 13 and 14 use their native two-frame field loop.
    if controller == 2:
        return ((1, False, 4), (0, False, 4), (1, True, 4), (0, False, 4)), 'Walk cycle'
    if controller == 3:
        return ((1, False, 4), (0, False, 4), (2, False, 4), (0, False, 4)), 'Walk cycle'
    if controller in POKEMON_WALK_ANIMATION_CONTROLLERS:
        return ((0, False, 10), (1, False, 10)), 'Field animation'
    raise ValueError('This field character does not have a supported animated preview.')


def _decode_preview_frames(textures, palette, controller):
    steps, _label = _preview_steps(controller)
    frames = []
    for face, flip_s, ticks in steps:
        if face >= len(textures):
            raise ValueError('This field character is missing an animation frame.')
        image = _render_i4(textures[face], palette)
        if flip_s:
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        frames.append((image, max(1, round(ticks * 1000 / 60))))
    return frames


def load_preview(path, model_id):
    """Decode a small, native field-animation preview from the selected ROM."""
    if type(model_id) is not int or not 0 <= model_id <= 0xFFFF:
        raise ValueError('Choose a valid field character.')
    rom = _load_rom(Path(path))
    config = ndspy.narc.NARC(rom.getFileByName(CONFIG_ARCHIVE))
    resources = ndspy.narc.NARC(rom.getFileByName(RESOURCE_ARCHIVE))
    for index in range(CONFIG_COUNT):
        offset = 4 + index * CONFIG_RECORD_SIZE
        row = config.files[0][offset:offset + CONFIG_RECORD_SIZE]
        if struct.unpack_from('<H', row, 0)[0] != model_id:
            continue
        entity_type, scene_node = struct.unpack_from('<BB', row, 2)
        controller = row[9]
        texture_resource, model_resource = struct.unpack_from('<HH', row, 16)
        is_human = scene_node in HUMAN_SCENE_NODES and controller in HUMAN_WALK_ANIMATION_CONTROLLERS
        is_pokemon = scene_node in POKEMON_SCENE_NODES and controller in POKEMON_WALK_ANIMATION_CONTROLLERS
        if entity_type != 1 or not (is_human or is_pokemon):
            break
        if (texture_resource >= len(resources.files) or model_resource >= len(resources.files)
                or resources.files[texture_resource][:4] != b'BTX0'
                or resources.files[model_resource][:4] != b'BMD0'):
            raise ValueError('This field character is missing its preview graphics.')
        btx = ndspy.texture.NSBTX(resources.files[texture_resource])
        if not btx.textures or not btx.palettes:
            raise ValueError('This field character is missing its preview graphics.')
        frames = _decode_preview_frames([texture for _name, texture in btx.textures], btx.palettes[0][1], controller)
        _preview_label = _preview_steps(controller)[1]
        return frames, _preview_label
    raise ValueError('This field character is not available in the selected game.')


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
