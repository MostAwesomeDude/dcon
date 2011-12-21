import unittest

from newrem.util import split_camel_case

class TestSplitCamelCase(unittest.TestCase):

    def test_single(self):
        s = "Single"
        self.assertEqual([s], split_camel_case(s))

    def test_double(self):
        s = "DoubleDecker"
        e = ["Double", "Decker"]
        self.assertEqual(e, split_camel_case(s))

    def test_single_lower(self):
        s = "lower"
        self.assertEqual([s], split_camel_case(s))

    def test_double_lower(self):
        s = "lowerLevel"
        e = ["lower", "Level"]
        self.assertEqual(e, split_camel_case(s))
