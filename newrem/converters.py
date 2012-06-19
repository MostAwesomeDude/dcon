from __future__ import with_statement

from datetime import datetime
from time import mktime

from werkzeug.routing import BaseConverter, ValidationError

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.types import DateTime

freezers = {
    DateTime: lambda dt: str(int(mktime(dt.timetuple()))),
}

thawers = {
    DateTime: lambda s: datetime.fromtimestamp(float(s)),
}

class ModelConverter(BaseConverter):
    """
    Converts a URL segment to and from a SQLAlchemy model.

    Rather than use an initializer, this class should be subclassed and have
    the `model` and `field` class attributes filled in. `model` is the
    Flask-SQLAlchemy model to use for queries, and `field` is the field on the
    model to use for lookups.
    """

    def to_python(self, value):
        value = self.thawer(value)

        try:
            with self.app.test_request_context():
                obj = self.model.query.filter_by(**{self.field: value}).one()
        except (MultipleResultsFound, NoResultFound):
            raise ValidationError()

        return obj

    def to_url(self, value):
        return self.freezer(getattr(value, self.field))

def make_model_converter(a, m, f):
    """
    Create a ModelConverter for the given app, model, and field.
    """

    column_type = type(m.__table__.columns[f].type)

    class Subclass(ModelConverter):
        app = a
        field = f
        model = m
        freezer = staticmethod(freezers.get(column_type, str))
        thawer = staticmethod(thawers.get(column_type, unicode))

    return Subclass
