import os.path

import yaml


def load_config(app):
    config = {
        "slogan": "Slogan goes here",
    }
    with app.open_resource("../dcon.yaml") as handle:
        d = yaml.safe_load(handle)
        print d
        config.update(d)
        print config

    app.config["DCON_CONFIG"] = config
    app.config["SQLALCHEMY_DATABASE_URI"] = config["database"]
    app.config["SQLALCHEMY_ECHO"] = app.debug

    app.config["RECAPTCHA_PUBLIC_KEY"] = config["recaptcha_public"]
    app.config["RECAPTCHA_PRIVATE_KEY"] = config["recaptcha_private"]

    assets = config.get("assets", "")
    if assets:
        app.static_paths = [os.path.join(assets, "static")]
        app.template_paths = [os.path.join(assets, "template")]


def write_config(app):
    config = app.config["DCON_CONFIG"]
    # open_resource() sucks. Hard. This is just a transplant.
    with open(os.path.join(app.root_path, "../dcon.yaml"), "wb") as handle:
        yaml.dump(config, handle)
