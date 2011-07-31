#!/usr/bin/env python

import os
import sys

interpreter = os.path.expanduser("~/local/bin/python")
if sys.executable != interpreter:
    os.execl(interpreter, interpreter, *sys.argv)

sys.path.append(os.path.dirname(__file__))

from newrem.main import app
from newrem import views

application = app

import logging
handler = logging.FileHandler("error.log")
handler.setLevel(logging.WARNING)
application.logger.addHandler(handler)

if __name__ == "__main__":
    raise SystemExit(app.run(debug=True, host="0.0.0.0"))
