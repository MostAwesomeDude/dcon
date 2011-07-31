import readline, rlcompleter
readline.parse_and_bind("tab:complete")

from newrem.main import app
from newrem.models import *

db.init_app(app)
app.test_request_context().push()

db.create_all()
