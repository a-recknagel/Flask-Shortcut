|Logo|

|CI_CD| |pyPI| |Docs| |License| |py_versions| |Style|


.. header-end

Project Description
-------------------

This extension provides an easy and safe way to add dev-only shortcuts to
routes in your flask application.

The main beneficiaries are microservices that need to be tested regularly in
conjunction with their clients. If you need to assert working communication and
basic integration in a sufficiently complex ecosystem, clients that can not
freely chose how their requests are formed gain a lot from being able to
receive predictable responses. By skipping over the details of how the
microservice is implemented, which bugs and minor changes it experiences over
time, testing basic API compatibility gets a lot more manageable.



Usage
-----

You can add shortcuts to your route functions either individually with
decorators, or in a single swoop once all routes have been defined. Both ways
are functionally equivalent.

Applying Shortcuts
==================

**With decorators:**

.. code-block:: python

    from flask import Flask
    from flask_shortcut import Shortcut

    app = Flask(__name__)
    short = Shortcut(app)

    app.route('/foo', methods=['GET'])
    short.cut(('short_foo', 200))
    def foo():
        return 'foo'

    app.route('/bar', methods=['POST'])
    short.cut({
        '{"name": "TestUser"}': ('short_bar', 200)},
        '{"name": "UserTest"}': ('longer_bar', 200),
    )
    def bar():
        return 'bar'

**With a wire call**

.. code-block:: python

    from flask import Flask
    from flask_shortcut import Shortcut

    app = Flask(__name__)

    app.route('/foo', methods=['GET'])
    def foo():
        return 'foo'

    app.route('/bar', methods=['POST'])
    def bar():
        return 'bar'

    Shortcut(app).wire(
        {
             '/foo': ('short_foo', 200),
             '/bar': {
                 '{"name": "TestUser"}': ('short_bar', 200),
                 '{"name": "UserTest"}': ('longer_bar', 200),
             }
        }
    )


What it looks like
==================

To showcase how the shortcuts are supposed to work, here is the result
of a couple of requests sent against the server from the example above
if it were run with ``FLASK_ENV=test flask run``:

.. code-block:: python

  >>> from request import get, post
  >>> get('http://127.0.0.1:5000/foo').text
  'short_foo'  # the only response this route will give
  >>> post('http://127.0.0.1:5000/bar', json={"name": "me"}).text
  'bar'  # no shortcut match -> the original logic was executed
  >>> post('http://127.0.0.1:5000/bar', json={"name": "TestUser"}).text
  'short_bar'  # shortcut match
  >>> post('http://127.0.0.1:5000/bar', json={"name": "UserTest", "job": None}).text
  'longer_bar'  # shortcut only needs to be contained for a match

One focus of this package was, that a production deployment would remain
as ignorant as possible about the existence of shortcuts. While the
shortcut object is still created, it only delegates the route functions
and no shortcut code has any chance of being run.


Configuration
-------------

By default, shortcuts will only be applied when ``FLASK_ENV`` is set to
something different than the default setting ``production``. You can
extend that list through the ``SHORTCUT_EXCLUSIONS`` config setting,
either by adding it to your app's config before creating any Shortcut
objects, or preferably by setting up the whole config `through a file`_.

Possible values for it are all environments other than ``production`` that
you want to block separated by commas, for example ``staging,master``.

----

Project home is `on github`_.

.. |Logo| image:: https://user-images.githubusercontent.com/2063412/79631833-c1b39400-815b-11ea-90da-d9264420ef68.png
   :alt: Logo
   :width: 1200
   :target: https://github.com/a-recknagel/Flask-Shortcut

.. |CI_CD| image:: https://github.com/a-recknagel/Flask-Shortcut/workflows/CI-CD/badge.svg
   :alt: Main workflow status
   :target: https://github.com/a-recknagel/Flask-Shortcut/actions

.. |pyPI| image:: https://img.shields.io/pypi/v/flask-shortcut
   :alt: Current pyPI version
   :target: https://pypi.org/project/flask-shortcut/

.. |Docs| image:: https://img.shields.io/badge/docs-github--pages-blue
   :alt: Documentation home
   :target: https://a-recknagel.github.io/Flask-Shortcut/

.. |License| image:: https://img.shields.io/pypi/l/flask-shortcut
   :alt: Package license
   :target: https://pypi.org/project/flask-shortcut/

.. |py_versions| image:: https://img.shields.io/pypi/pyversions/flask-shortcut
   :alt: Supported on python versions
   :target: https://pypi.org/project/flask-shortcut/

.. |Style| image:: https://img.shields.io/badge/codestyle-black-black
   :alt: Any color you want
   :target: https://black.readthedocs.io/en/stable/

.. _on github: https://github.com/a-recknagel/Flask-Shortcut

.. _through a file: https://flask.palletsprojects.com/en/1.1.x/config/#configuring-from-files