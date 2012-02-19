from flask import flash

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
