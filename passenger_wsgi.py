#!/usr/bin/env python

import os
import sys

sys.path.append(os.path.dirname(__file__))

from newrem.main import app
from newrem import views

import logging
handler = logging.FileHandler("error.log")
handler.setLevel(logging.WARNING)
app.logger.addHandler(handler)

if __name__ == "__main__":
    raise SystemExit(app.run(debug=True, host="0.0.0.0"))
