#!/usr/bin/env python

from newrem.main import app
from newrem import views

if __name__ == "__main__":
    raise SystemExit(app.run(debug=True, host="0.0.0.0"))
