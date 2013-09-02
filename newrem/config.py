from ConfigParser import SafeConfigParser
import os.path


def load_config(app):
    d = {
        "slogan": "Slogan goes here",
    }
    cp = SafeConfigParser(d)
    with app.open_resource("../dcon.ini") as handle:
        cp.readfp(handle)

    app.config["DCON_CONFIG"] = cp
    app.config["SQLALCHEMY_DATABASE_URI"] = cp.get("dcon", "database")
    app.config["SQLALCHEMY_ECHO"] = app.debug

    app.config["RECAPTCHA_PUBLIC_KEY"] = cp.get("dcon", "recaptcha_public")
    app.config["RECAPTCHA_PRIVATE_KEY"] = cp.get("dcon", "recaptcha_private")

    assets = cp.get("dcon", "assets", "")
    if assets:
        app.static_paths = [os.path.join(assets, "static")]
        app.template_paths = [os.path.join(assets, "template")]


def write_config(app):
    cp = app.config["DCON_CONFIG"]
    # open_resource() sucks. Hard. This is just a transplant.
    with open(os.path.join(app.root_path, "../dcon.ini"), "wb") as handle:
        cp.write(handle)
