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
from jinja2 import ChoiceLoader, FileSystemLoader
from werkzeug.exceptions import NotFound
from flask import Flask
from flask.helpers import locked_cached_property, send_from_directory


class DCoN(Flask):
    """
    A Flask application that permits multiple static and template search
    paths.
    """

    def __init__(self, *args, **kwargs):
        super(DCoN, self).__init__(*args, **kwargs)

        self.static_paths = []
        self.template_paths = []

    def send_static_file(self, filename):
        cache_timeout = self.get_send_file_max_age(filename)

        l = self.static_paths[:]
        if self.has_static_folder:
            l.append(self.static_folder)

        for path in l:
            try:
                return send_from_directory(path, filename,
                        cache_timeout=cache_timeout)
            except NotFound:
                continue

        raise NotFound()

    @locked_cached_property
    def jinja_loader(self):
        parent_loader = super(DCoN, self).jinja_loader
        loaders = [FileSystemLoader(path) for path in self.template_paths]
        loaders.append(parent_loader)

        return ChoiceLoader(loaders)
