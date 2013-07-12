from collections import namedtuple
from unittest import TestCase

from newrem.forms import (label_for_comic, select_option_for_comics,
                          select_list_for_comics)


FauxComic = namedtuple("FauxComic", "id, title, position")


class TestLabelForComic(TestCase):

    def test_label_for_comic(self):
        comic = FauxComic(1, "Test", 0)
        expected = u'"Test" (0)'
        self.assertEqual(label_for_comic(comic), expected)


class TestSelectOptionForComics(TestCase):

    def test_select_option_for_comics(self):
        first = FauxComic(1, "First", 0)
        second = FauxComic(2, "Second", 1)
        expected = 1, u'"First" (0) to "Second" (1)'
        self.assertEqual(select_option_for_comics(first, second), expected)


class TestSelectListForComics(TestCase):

    def test_select_list_for_comics_one(self):
        comics = [
            FauxComic(1, "First", 0),
        ]
        expected = [
            (-1, u'Before "First" (0)'),
            (1, u'After "First" (0)'),
        ]
        self.assertEqual(select_list_for_comics(comics), expected)

    def test_select_list_for_comics_one_id(self):
        comics = [
            FauxComic(42, "First", 0),
        ]
        expected = [
            (-1, u'Before "First" (0)'),
            (42, u'After "First" (0)'),
        ]
        self.assertEqual(select_list_for_comics(comics), expected)

    def test_select_list_for_comics_two(self):
        comics = [
            FauxComic(1, "First", 0),
            FauxComic(2, "Second", 1),
        ]
        expected = [
            (-1, u'Before "First" (0)'),
            (1, u'"First" (0) to "Second" (1)'),
            (2, u'After "Second" (1)'),
        ]
        self.assertEqual(select_list_for_comics(comics), expected)
