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
