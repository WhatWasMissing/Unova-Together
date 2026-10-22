"""Verify the packaged battle-area selection and source-patch metadata."""
import hashlib
import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / 'maintenance-tools/patches/development-polish.patch'
METADATA = ROOT / 'maintenance-tools/patches/development-polish.json'
HEADER = ROOT / 'maintenance-tools/tools/battle_scenery_area_selection.h'
SOURCE_HEADER = 'source/melonDS/src/frontend/qt_sdl/BattleSceneryAreaSelection.h'
SOURCE_CLASS = 'source/melonDS/src/frontend/qt_sdl/AreaBattleScenes.h'


def patch_section(patch_text, source_path):
    start = patch_text.find(f'--- a/{source_path}\n')
    if start < 0:
        return ''
    end = patch_text.find('\n--- ', start + 1)
    return patch_text[start:] if end < 0 else patch_text[start:end]


def added_source(patch_text, source_path):
    path = re.escape(source_path)
    match = re.search(
        rf'(?ms)^--- /dev/null\n\+\+\+ b/{path}\n@@ -0,0 \+1,\d+ @@\n(.*?)(?=^--- |\Z)',
        patch_text,
    )
    if not match:
        return None
    return ''.join(line[1:] + '\n' for line in match.group(1).splitlines() if line.startswith('+'))


class BattleSceneryAreaSelectionTests(unittest.TestCase):
    def test_area_selection_uses_loaded_field_zone_and_gates_nearby_scene(self):
        delta = patch_section(PATCH.read_text(encoding='utf-8'), SOURCE_CLASS)
        self.assertIn('sample.value("fieldZone",-1)', delta)
        self.assertIn('sample.value("map",-1)', delta)
        self.assertIn('selectBattleSceneryArea(matrixZone,battleZone,areaForZone)', delta)
        self.assertIn('if(areaSelection.useNearbyGeometry', delta)
        self.assertIn('candidate.value("area").toInt(-1)==area', delta)
        self.assertIn('candidate.value("zone").toInt(-1)==matrixZone', delta)
        self.assertIn('if(!areaSelection)', delta)
        self.assertIn('currentSelection.clear()', delta)
        self.assertIn('Area scenery unavailable; original background', delta)
        self.assertIn('++frames%6==0', delta)

    def test_distributed_selection_header_matches_tested_source(self):
        patch_text = PATCH.read_text(encoding='utf-8')
        self.assertEqual(added_source(patch_text, SOURCE_HEADER), HEADER.read_text(encoding='utf-8'))

    def test_patch_metadata_hash_and_native_file_list_match(self):
        metadata = json.loads(METADATA.read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256(PATCH.read_bytes()).hexdigest(), metadata['patchSha256'])
        self.assertIn('src/frontend/qt_sdl/AreaBattleScenes.h', metadata['changedNativeFiles'])
        self.assertIn('src/frontend/qt_sdl/BattleSceneryAreaSelection.h', metadata['changedNativeFiles'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
