import unittest

from newrem.models import (Board, Newspost, Post, Universe)

class TestPostModel(unittest.TestCase):

    def setUp(self):
        self.m = Post("Anonymous", "A comment.", "anon@example.org", [None])

    def test_trivial(self):
        pass

class TestBoardModel(unittest.TestCase):

    def setUp(self):
        self.m = Board("t", "Testing")

    def test_trivial(self):
        pass

class TestUniverseModel(unittest.TestCase):

    def setUp(self):
        self.m = Universe("Testing")

    def test_trivial(self):
        pass

class TestNewspostModel(unittest.TestCase):

    def setUp(self):
        self.m = Newspost("Title", u"Content")

    def test_trivial(self):
        pass
