#!/usr/bin/env python

if __name__ == "__main__":
    from newrem.main import app
    from newrem import views
    raise SystemExit(app.run(debug=True, host="0.0.0.0"))
