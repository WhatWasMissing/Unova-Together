"""Bounded validation and filtering for profile-local player appearance choices."""



MAX_FAVORITES = 128
MAX_PRESETS = 20
MAX_PRESET_NAME = 32
FILTER_ALL = 'All characters'
FILTER_NPCS = 'People'
FILTER_POKEMON = 'Pokémon'
FILTER_FAVORITES = 'Favorites'
FILTERS = (FILTER_ALL, FILTER_NPCS, FILTER_POKEMON, FILTER_FAVORITES)


def normalize_favorites(value):
    if not isinstance(value, list):
        return []
    result = []
    seen = set()
    for model_id in value:
        if type(model_id) is int and 0 < model_id <= 0xFFFF and model_id not in seen:
            result.append(model_id)
            seen.add(model_id)
            if len(result) >= MAX_FAVORITES:
                break
    return result


def normalize_presets(value):
    if not isinstance(value, list):
        return []
    result = []
    seen = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        name = item.get('name')
        model_id = item.get('model_id')
        if (not isinstance(name, str) or type(model_id) is not int
                or not 0 <= model_id <= 0xFFFF):
            continue
        name = ''.join(char for char in name.strip() if char.isprintable())[:MAX_PRESET_NAME]
        key = name.casefold()
        if not name or key in seen:
            continue
        result.append({'name': name, 'model_id': model_id})
        seen.add(key)
        if len(result) >= MAX_PRESETS:
            break
    return result


def normalize_settings(values):
    """Return only validated appearance preferences from a profile setting map."""
    if not isinstance(values, dict):
        return {}
    result = {}
    if 'player_model_favorites' in values:
        result['player_model_favorites'] = normalize_favorites(values['player_model_favorites'])
    if 'player_model_presets' in values:
        result['player_model_presets'] = normalize_presets(values['player_model_presets'])
    return result


def filter_models(models, query='', category=FILTER_ALL, favorites=(), sort='name'):
    """Filter supported ROM actor IDs without changing the catalog or stored choice."""
    from . import player_models
    category = category if category in FILTERS else FILTER_ALL
    favorite_ids = set(normalize_favorites(list(favorites)))
    term = str(query).strip().casefold()
    result = []
    for model_id in models:
        is_pokemon = model_id in player_models.POKEMON_MODEL_LABELS
        is_npc = model_id in player_models.NPC_MODEL_LABELS or model_id in player_models.SPECIAL_NPC_MODEL_LABELS
        if category == FILTER_NPCS and not is_npc:
            continue
        if category == FILTER_POKEMON and not is_pokemon:
            continue
        if category == FILTER_FAVORITES and model_id not in favorite_ids:
            continue
        label = player_models.display_name(model_id)
        if term and term not in label.casefold() and term not in str(model_id):
            continue
        result.append(model_id)
    if sort == 'number':
        result.sort()
    else:
        result.sort(key=lambda model_id: (player_models.display_name(model_id).casefold(), model_id))
    return result
