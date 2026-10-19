import tomllib
import unittest

from lan_harness_config import make_instance_parent_tables_explicit


class LanHarnessConfigTests(unittest.TestCase):
    def test_promotes_implicit_instance_parents_before_nested_tables(self):
        source = (
            "LimitFPS = true\n"
            "[MP]\nRecvTimeout = 100\n"
            "[Instance0.Keyboard]\nA = 88\n"
            "[Instance1.Audio]\nVolume = 0\n"
        )

        result = make_instance_parent_tables_explicit(source)
        parsed = tomllib.loads(result)

        self.assertLess(result.index("[Instance0]"), result.index("[Instance0.Keyboard]"))
        self.assertLess(result.index("[Instance1]"), result.index("[Instance1.Audio]"))
        self.assertEqual(parsed["Instance0"]["Keyboard"]["A"], 88)
        self.assertEqual(parsed["Instance1"]["Audio"]["Volume"], 0)
        self.assertEqual(make_instance_parent_tables_explicit(result), result)

    def test_keeps_existing_explicit_parent_and_values(self):
        source = (
            "[Instance0]\nSaveFilePath = \"test.sav\"\n"
            "[Instance0.Keyboard]\nA = 88\n"
        )

        result = make_instance_parent_tables_explicit(source)

        self.assertEqual(result, source)
        self.assertEqual(tomllib.loads(result)["Instance0"]["SaveFilePath"], "test.sav")


if __name__ == "__main__":
    unittest.main()
