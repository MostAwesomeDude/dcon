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
from flask import url_for

from newrem.util import slugify


def url_for_comic(comic, **kwargs):
    return url_for("comics", u=comic.universe, cid=comic.id,
                   name=slugify(comic.title), **kwargs)


def load_filters(app):

    @app.template_filter()
    def ten_or_fewer(i):
        return min(len(list(i)), 10)

    app.template_global()(url_for_comic)
