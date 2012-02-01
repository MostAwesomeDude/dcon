import unittest

from newrem.util import slugify, split_camel_case

class TestSlugify(unittest.TestCase):

    def test_noop(self):
        s = "noop"
        self.assertEqual(s, slugify(s))

    def test_lower(self):
        s = "Lower"
        e = "lower"
        self.assertEqual(e, slugify(s))

    def test_space(self):
        s = "spheres in space"
        e = "spheres-in-space"
        self.assertEqual(e, slugify(s))

    def test_flavor_text(self):
        s = "Flavor Text"
        e = "flavor-text"
        self.assertEqual(e, slugify(s))

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
