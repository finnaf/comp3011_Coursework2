import unittest
from src.main import parse_flags, calculate_verbosity_level

# not testing the main loop, just the utility functions within main.py

class TestCalculateVerbosityLevel(unittest.TestCase):
    def test_default_verbosity(self):
        self.assertEqual(calculate_verbosity_level(False, False), 1)

    def test_verbose_flag(self):
        self.assertEqual(calculate_verbosity_level(True, False), 2)

    def test_silent_flag(self):
        self.assertEqual(calculate_verbosity_level(False, True), 0)

    def test_silent_overrides_verbose(self):
        """Both flags set — silent wins"""
        self.assertEqual(calculate_verbosity_level(True, True), 0)


class TestParseFlags(unittest.TestCase):

    # bool flags

    def test_bool_flag_defaults_to_false(self):
        _, flags = parse_flags([], set(), {"--ascending"})
        self.assertFalse(flags["--ascending"])

    def test_bool_flag_set_to_true_when_present(self):
        _, flags = parse_flags(["--ascending"], set(), {"--ascending"})
        self.assertTrue(flags["--ascending"])

    def test_multiple_bool_flags(self):
        _, flags = parse_flags(
            ["--ascending", "--connected"],
            set(),
            {"--ascending", "--connected"}
        )
        self.assertTrue(flags["--ascending"])
        self.assertTrue(flags["--connected"])

    # value flags

    def test_value_flag_parsed_as_int(self):
        _, flags = parse_flags(["--top", "5"], {"--top"}, set())
        self.assertEqual(flags["--top"], 5)
        self.assertIsInstance(flags["--top"], int)

    def test_value_flag_stays_as_string_when_not_numeric(self):
        _, flags = parse_flags(["--from", "my_index.json"], {"--from"}, set())
        self.assertEqual(flags["--from"], "my_index.json")

    def test_value_flag_missing_value_returns_none(self):
        positional, flags = parse_flags(["--top"], {"--top"}, set())
        self.assertIsNone(positional)
        self.assertIsNone(flags)

    # positional args

    def test_positional_args_separated_correctly(self):
        positional, _ = parse_flags(
            ["hello", "world", "--ascending"],
            set(),
            {"--ascending"}
        )
        self.assertEqual(positional, ["hello", "world"])

    def test_empty_args(self):
        positional, flags = parse_flags([], set(), set())
        self.assertEqual(positional, [])
        self.assertEqual(flags, {})

    # combination

    def test_mixed_positional_and_flags(self):
        positional, flags = parse_flags(
            ["python", "--top", "3", "--ascending"],
            {"--top"},
            {"--ascending"}
        )
        self.assertEqual(positional, ["python"])
        self.assertEqual(flags["--top"], 3)
        self.assertTrue(flags["--ascending"])

    def test_flags_can_appear_before_positional(self):
        positional, flags = parse_flags(
            ["--top", "10", "someword"],
            {"--top"},
            set()
        )
        self.assertEqual(positional, ["someword"])
        self.assertEqual(flags["--top"], 10)