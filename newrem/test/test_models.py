# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.
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
        self.m = Universe(u"Testing")

    def test_trivial(self):
        pass

class TestNewspostModel(unittest.TestCase):

    def setUp(self):
        self.m = Newspost("Title", u"Content")

    def test_trivial(self):
        pass
