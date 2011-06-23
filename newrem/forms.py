from flaskext.uploads import configure_uploads, IMAGES, UploadSet
from flaskext.wtf import (Form, FileAllowed, FileRequired,
    Required, FileField, QuerySelectField, IntegerField,
    SubmitField, TextField)
from wtforms.fields import Field
from wtforms.widgets import TextInput

from newrem.main import app
from newrem.models import Character

images = UploadSet("images", IMAGES)

configure_uploads(app, (images,))

class TagListField(Field):
    widget = TextInput()

    def _value(self):
        if self.data:
            return u", ".join(self.data)
        else:
            return u""

    def process_formdata(self, data):
        if data:
            self.data = [word.strip() for word in data[0].split(",")]
            self.data.sort()
        else:
            self.data = []

class CharacterCreateForm(Form):
    name = TextField(u"New name", validators=(Required(),))
    submit = SubmitField("Create!")

class CharacterModifyForm(Form):
    characters = QuerySelectField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    name = TextField(u"New name", validators=(Required(),))
    submit = SubmitField("Modify!")

class CharacterDeleteForm(Form):
    characters = QuerySelectField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    submit = SubmitField("Delete!")

class UploadForm(Form):
    file = FileField("Select a file to upload",
        validators=(FileRequired("Must upload a comic!"),
            FileAllowed(images, "Images only!")))
    characters = TagListField("Characters")
    index = IntegerField("Where to insert this comic?",
        validators=(Required(),))
    submit = SubmitField("Upload!")
