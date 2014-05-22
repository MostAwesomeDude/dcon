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
from datetime import datetime
from unittest import TestCase

from flask import Flask

from newrem.converters import make_model_converter
from newrem.models import db, Newspost

class TestNewspostConverter(TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        self.converter_cls = make_model_converter(self.app, Newspost, "time")
        self.converter = self.converter_cls(None)

        db.init_app(self.app)
        with self.app.test_request_context():
            db.create_all()

    def test_trivial(self):
        pass

    def test_apocalypse_to_url(self):
        dt = datetime(2012, 12, 21)
        news = Newspost("Test")
        news.time = dt
        expected = "1356048000"
        self.assertEqual(self.converter.to_url(news), expected)

    def test_apocalypse_to_python(self):
        dt = datetime(2012, 12, 21)
        news = Newspost(u"Test")
        news.time = dt
        # Hax: PID is needed by DB.
        news.portrait_id = 0

        fragment = "1356048000"

        with self.app.test_request_context():
            db.session.add(news)
            db.session.commit()

            result = self.converter.to_python(fragment)
            db.session.add(result)

            # No direct equality check, but this is close enough.
            self.assertEqual(result.title, news.title)
            self.assertEqual(result.time, news.time)
