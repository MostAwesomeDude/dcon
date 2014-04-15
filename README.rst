====
DCoN
====

DCoN, the Doubly-linked Comic ORM for Newrem, is a simple, straightforward
webcomic management system. It differentiates itself from other comic
management systems by its architecture of Python, Flask, and SQLAlchemy, as
well as its ability to manage comics anachronistically.

DCoN incorporates code from Ben Kero's osuchan library.

DCoN is made available under the GNU Public License, version 2.

Deployment
----------

The files secret.key, temp.db, and passwords.dcon must exist in order to run
the app. Secret.key must contain at least one byte of data for the app to run
correctly.

To enable admin panel access, add each account's username and password to
passwords.dcon in the format

.. code-block:: 
    username:password

One way to make the app go, after running shell.py to create the necessary
database tables, is 

.. code-block:: 

    $ pip install twisted
    $ twistd -n web --wsgi newrem.main.app 
