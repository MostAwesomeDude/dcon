import unittest

from newrem.util import abbreviate, slugify, split_camel_case

class TestAbbreviate(unittest.TestCase):

    def test_single(self):
        s = "Anime"
        e = "a"
        self.assertEqual(e, abbreviate(s))

    def test_double(self):
        s = "Papercraft & Origami"
        e = "po"
        self.assertEqual(e, abbreviate(s))

class TestSlugify(unittest.TestCase):

    def test_noop(self):
        s = u"noop"
        e = "noop"
        self.assertEqual(e, slugify(s))

    def test_lower(self):
        s = u"Lower"
        e = "lower"
        self.assertEqual(e, slugify(s))

    def test_space(self):
        s = u"spheres in space"
        e = "spheres-in-space"
        self.assertEqual(e, slugify(s))

    def test_flavor_text(self):
        s = u"Flavor Text"
        e = "flavor-text"
        self.assertEqual(e, slugify(s))

    def test_patch_notes(self):
        s = u"6/17/12 Patch Notes"
        e = "6-17-12-patch-notes"
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
