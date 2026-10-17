import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC=importlib.util.spec_from_file_location('package_unova_release',Path(__file__).with_name('package_unova_release.py'))
PACKAGE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)

class PackageRuntimeTests(unittest.TestCase):
    def test_rejects_runtime_without_soaring(self):
        with tempfile.TemporaryDirectory() as directory:
            executable=Path(directory)/'melonDS.exe'
            executable.write_bytes(b'old runtime without flight menu')
            with self.assertRaisesRegex(ValueError,'missing Soaring support'):
                PACKAGE.verify_soaring_runtime(executable)

    def test_accepts_runtime_with_soaring_controls_and_menu(self):
        with tempfile.TemporaryDirectory() as directory:
            executable=Path(directory)/'melonDS.exe'
            executable.write_bytes(b'UNOVA_EXPERIMENTAL_SOARING Take flight (experimental)')
            PACKAGE.verify_soaring_runtime(executable)

if __name__=='__main__':
    unittest.main()
