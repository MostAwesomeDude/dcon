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


def extend_fp(fp, segments):
    """
    Extend a ``FilePath`` given a list of segments.
    """

    for segment in segments:
        fp = fp.child(segment)
    return fp


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
