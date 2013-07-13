from ConfigParser import SafeConfigParser


def load_config(app):
    cp = SafeConfigParser()
    handle = app.open_resource("../dcon.ini")
    cp.readfp(handle)
    handle.close()
    app.config["DCON_CONFIG"] = cp
    app.config["SQLALCHEMY_DATABASE_URI"] = cp.get("dcon", "database")
    app.config["SQLALCHEMY_ECHO"] = app.debug


def write_config(app):
    cp = app.config["DCON_CONFIG"]
    # Ugh, annoying race condition here, but not much that can be done about
    # it while using open_resource().
    handle = app.open_resource("../dcon.ini", mode="wb")
    cp.write(handle)
    handle.close()
