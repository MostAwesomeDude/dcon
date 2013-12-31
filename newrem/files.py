from bp.filepath import FilePath

from flask import flash


def fp_root(app):
    """
    Figure out where file storage is in the filesystem.
    """

    return app.config["DCON_UPLOAD_PATH"]


def url_root(app):
    """
    Figure out where file storage is in the URL.
    """

    url = app.config["DCON_STATIC_URL"]
    if not url.endswith("/"):
        url = url + "/"
    return url


def extend_url(url, segments):
    """
    Extend a URL given a list of segments.
    """

    return url + "/".join(segments)


def save_file(fp, fs):
    """
    Save a ``FileStorage`` to a ``FilePath``.
    """

    parent = fp.parent()
    try:
        if not parent.exists():
            parent.makedirs()
    except IOError:
        flash("Couldn't create path %r" % parent.path)
        return False
    else:
        fs.save(fp.path)
        return True


def assets_in_paths(app, segments):
    """
    Select some assets from all of the static paths in the app which match the
    given segments, and return the available basenames.

    Useful for getting a list of options for random selections of banners or
    other images.
    """

    names = []

    for path in app.static_paths:
        root = FilePath(path)
        fp = root.descendant(segments)

        # Get some banners, if they exist.
        if fp.exists():
            names.extend([p.basename() for p in fp.children()])

    return names
