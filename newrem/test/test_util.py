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
