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
import os.path

import yaml


def load_config(app):
    config = {
        "slogan": "Slogan goes here",
        "upload_time_now": False,
    }

    with app.open_resource("../dcon.yaml") as handle:
        d = yaml.safe_load(handle)
        config.update(d)

    app.config["DCON_CONFIG"] = config
    app.config["SQLALCHEMY_DATABASE_URI"] = config["database"]
    app.config["SQLALCHEMY_ECHO"] = app.debug

    app.config["RECAPTCHA_PUBLIC_KEY"] = config["recaptcha_public"]
    app.config["RECAPTCHA_PRIVATE_KEY"] = config["recaptcha_private"]

    assets = config.get("assets", "")
    if assets:
        app.static_paths = [os.path.join(assets, "static")]


def write_config(app):
    config = app.config["DCON_CONFIG"]
    # open_resource() sucks. Hard. This is just a transplant.
    with open(os.path.join(app.root_path, "../dcon.yaml"), "wb") as handle:
        yaml.dump(config, handle)
