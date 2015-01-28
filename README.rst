====
DCoN
====

DCoN, the Doubly-linked Comic ORM for Newrem, is a simple, straightforward
webcomic management system. It differentiates itself from other comic
management systems by its architecture of Python, Flask, and SQLAlchemy, as
well as its ability to manage comics anachronistically.

For licensing information, see the ``LICENSE`` file.

Deployment
==========

Virtual Environments
--------------------

If you don't have other preferences for your DCON deployment, you probably
want to install its dependencies in a `virtual environment`_. 

.. _virtual environment: https://virtualenv.pypa.io/en/latest/

::
    # only create the virtual environment ONCE
    $ virtualenv venv
    
    # activate the virtualenv every time you want to use it
    $ source venv/bin/activate

    # run this command again if the requirements change
    (venv)$ pip install -r requirements.txt

    # leave the virtualenv when you're done working with dcon
    (venv)$ deactivate

Create required files
---------------------

::
    # secret.key must contain at least 1 byte of data for dcon to function
    # put 50 random characters in it
    $ pwgen 50 1 > secret.key

    $ touch passwords.dcon
    
    # customize dcon.yaml with your site's name, database URL, etc.
    $ cp dcon.yaml.example dcon.yaml

    # only if you're using db settings from dcon.yaml.example
    $ touch temp.db

Enable admin access
-------------------

Edit the file ``passwords.dcon`` to contain the usernames and passwords of
everyone who gets administrative access in your dcon instance, one per line,
in the form::

    username:password

Create database tables
----------------------

Once you've got your database URL set correctly in ``dcon.yaml``, just run
``shell.py``::

    (venv)$ python shell.py
    
Start the app
-------------

One way to make the app go is:: 

    (venv)$ pip install twisted
    (venv)$ twistd -n web --wsgi newrem.main.app 

Yes, that's ``newrem.main.app``, not the name of your comic, since all the
files relevant to twisted are in the ``newrem`` directory.

Add Content
-----------

If you're running dcon with twisted as shown above, your site will now be
online at `http://localhost:8080/ <http://localhost:8080/>`_. If you haven't
created any universes yet, the site will show only a footer. Start adding
content by going to `/admin <http://localhost:8080/admin>`_ and logging in
with the credentials you set in ``passwords.dcon``.  
