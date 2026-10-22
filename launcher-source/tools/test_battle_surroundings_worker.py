"""Production-path checks for damaged nearby-scene requests and reports."""
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from battle_surroundings_worker import REVISION, SurroundingsWorker, scene_key
from field_scene_geometry import polygon_overlaps_square


class OnePassStop:
    def __init__(self):
        self.calls = 0

    def wait(self, _seconds):
        self.calls += 1
        return self.calls > 1


class BattleSurroundingsWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name) / 'nearby'
        self.directory.mkdir()
        self.zone, self.x, self.z, self.y = 37, 512, 1024, 0
        self.key = scene_key(self.zone, self.x, self.z, self.y)
        self.request = self.directory / 'request-test.json'

    def tearDown(self):
        self.temp.cleanup()

    def worker(self):
        worker = object.__new__(SurroundingsWorker)
        worker.directory = self.directory
        worker.rom = self.directory / 'unused.nds'
        worker.stop = OnePassStop()
        worker.started = time.time() - 10
        worker.budget = 16384
        return worker

    def run_worker(self):
        self.worker().run()

    def write_request(self, value):
        self.request.write_text(json.dumps(value), encoding='utf-8')

    def test_non_object_request_does_not_terminate_worker(self):
        self.write_request([])
        self.run_worker()

    def test_non_object_scene_report_returns_fallback_without_terminating_worker(self):
        self.write_request({
            'zone': self.zone, 'worldX': self.x, 'worldZ': self.z,
            'worldY': self.y, 'key': self.key,
        })
        destination = self.directory / f'scene-v{REVISION}-{self.key}'
        destination.mkdir()
        (destination / 'scene.json').write_text('[]', encoding='utf-8')

        self.run_worker()

        ready = self.directory / 'ready-test.json'
        result = json.loads(ready.read_text(encoding='utf-8'))
        self.assertEqual(result['key'], self.key)
        self.assertIn('fallback', result)

    def test_scene_report_cannot_read_model_outside_its_generated_filename(self):
        self.write_request({
            'zone': self.zone, 'worldX': self.x, 'worldZ': self.z,
            'worldY': self.y, 'key': self.key,
        })
        destination = self.directory / f'scene-v{REVISION}-{self.key}'
        destination.mkdir()
        outside = Path(self.temp.name) / 'private-sentinel.bin'
        outside.write_bytes(b'private')
        (destination / 'scene.json').write_text(json.dumps({
            'model': str(outside), 'bytes': outside.stat().st_size,
            'sha256': hashlib.sha256(outside.read_bytes()).hexdigest(),
            'omittedProps': [],
        }), encoding='utf-8')

        original_read_bytes = Path.read_bytes
        reads = []

        def track_read(path, *args, **kwargs):
            reads.append(Path(path))
            return original_read_bytes(path, *args, **kwargs)

        with patch.object(Path, 'read_bytes', track_read):
            self.run_worker()

        ready = self.directory / 'ready-test.json'
        result = json.loads(ready.read_text(encoding='utf-8'))
        self.assertEqual(result['key'], self.key)
        self.assertIn('fallback', result)
        self.assertNotIn(outside, reads)

    def test_valid_scene_report_is_delivered(self):
        self.write_request({
            'zone': self.zone, 'worldX': self.x, 'worldZ': self.z,
            'worldY': self.y, 'key': self.key,
        })
        destination = self.directory / f'scene-v{REVISION}-{self.key}'
        destination.mkdir()
        model = destination / 'surroundings.nsbmd'
        model.write_bytes(b'validated scene')
        digest = hashlib.sha256(model.read_bytes()).hexdigest()
        (destination / 'scene.json').write_text(json.dumps({
            'model': model.name, 'bytes': model.stat().st_size,
            'sha256': digest, 'area': 38, 'omittedProps': ['prop'],
        }), encoding='utf-8')

        self.run_worker()

        result = json.loads((self.directory / 'ready-test.json').read_text(encoding='utf-8'))
        self.assertEqual(result['key'], self.key)
        self.assertEqual(result['sha256'], digest)
        self.assertEqual(result['area'], 38)
        self.assertEqual(result['omittedProps'], 1)

    def test_scene_report_without_area_returns_fallback(self):
        self.write_request({
            'zone': self.zone, 'worldX': self.x, 'worldZ': self.z,
            'worldY': self.y, 'key': self.key,
        })
        destination = self.directory / f'scene-v{REVISION}-{self.key}'
        destination.mkdir()
        model = destination / 'surroundings.nsbmd'
        model.write_bytes(b'validated scene')
        (destination / 'scene.json').write_text(json.dumps({
            'model': model.name, 'bytes': model.stat().st_size,
            'sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
            'omittedProps': [],
        }), encoding='utf-8')

        self.run_worker()

        result = json.loads((self.directory / 'ready-test.json').read_text(encoding='utf-8'))
        self.assertIn('fallback', result)


class BattleCentreClearanceTests(unittest.TestCase):
    def test_crossing_prop_is_rejected_even_when_all_vertices_are_outside(self):
        crossing = [(-100, 0, -12), (100, 0, -12),
                    (100, 0, 12), (-100, 0, 12)]
        self.assertTrue(polygon_overlaps_square(crossing, 64))

    def test_prop_wholly_outside_centre_remains_available(self):
        outside = [(70, 0, 70), (100, 0, 70), (100, 0, 100), (70, 0, 100)]
        self.assertFalse(polygon_overlaps_square(outside, 64))

    def test_touching_protected_boundary_counts_as_overlap(self):
        touching = [(64, 0, -10), (80, 0, -10), (80, 0, 10), (64, 0, 10)]
        self.assertTrue(polygon_overlaps_square(touching, 64))

    def test_invalid_clearance_is_rejected(self):
        with self.assertRaises(ValueError):
            polygon_overlaps_square([(0, 0, 0)], -1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
