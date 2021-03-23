|Logo|

|CI_CD| |Docs| |pyPI| |py_versions| |License| |Style|


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

In a test-engineering context, it would be considered a "fake".

What is a Shortcut?
-------------------

In the context of this package, a shortcut is a condition-and-response pair.
The response is `anything that a view function can return`_, and the
condition depends on one of the three possible mapping contexts.

In the first context, only the response is passed as the shortcut, and the
condition is assumed to always be true, effectively replacing the route to
always just return the given response. Showcased with the view ``foo``
in the usage section.

In the second context, a dictionary that maps strings to responses is passed
as the shortcut. The strings need to be deserializeable as json, and the
first one that can be fully matched as a substructure into the request body
will see its condition as fulfilled, returning its associated response.
If none of them are valid sub-matches, the original view function will run.
Showcased with the view ``bar`` in the usage section.

In the third context, either a single function or a list of functions is
passed as the shortcut. The functions can run any code whatsoever and will
be executed one after the other as long as they return ``None``, which means
that their condition is not fulfilled. As soon as one of them returns
something different, it is passed on as the response. If all of them return
``None``, the original view function is executed. Showcased with the view
``baz`` in the usage section.


Usage
-----

You can add shortcuts to your view functions either individually with
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

    @app.route('/foo', methods=['GET'])
    @short.cut(('short_foo', 200))
    def foo():
        return 'foo'

    @app.route('/bar', methods=['POST'])
    @short.cut({
        '{"name": "TestUser"}': ('short_bar', 200),
        '{"name": "UserTest"}': ('longer_bar', 200),
    })
    def bar():
        return 'bar'

    @app.route('/baz', methods=['POST'])
    @short.cut(lambda: ("json_baz", 200) if "json" in request.mimetype else None)
    def baz():
        return 'baz'


**With a wire call**

.. code-block:: python

    from flask import Flask
    from flask_shortcut import Shortcut

    app = Flask(__name__)

    @app.route('/foo', methods=['GET'])
    def foo():
        return 'foo'

    @app.route('/bar', methods=['POST'])
    def bar():
        return 'bar'

    @app.route('/baz', methods=['POST'])
    def baz():
        return 'baz'

    Shortcut(app).wire(
        {
             '/foo': ('short_foo', 200),
             '/bar': {
                 '{"name": "TestUser"}': ('short_bar', 200),
                 '{"name": "UserTest"}': ('longer_bar', 200),
             }
             '/baz': lambda: ("json_baz", 200) if "json" in request.mimetype else None
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
  >>> post('http://127.0.0.1:5000/baz').text
  'baz'  # no shortcut match -> the function returned None
  >>> post('http://127.0.0.1:5000/baz', json={"name": "me"}).text
  'json_baz'  # shortcut matched -> the function returned a valid response

One focus of this package is that a production deployment would remain
as ignorant as possible about the existence of shortcuts. While the
shortcut object is still created, it only delegates the view functions
and no shortcut code has any chance of being executed, or showing up in
stack traces.


Configuration
-------------

Shortcuts will only be applied when ``FLASK_ENV`` is set to something
different from its default setting, ``production``. You can extend that list
through the ``SHORTCUT_EXCLUSIONS`` config setting, either by adding it to
your app's config before creating any Shortcut objects, or preferably by
setting up the whole config `with a file`_.

Possible values for it are all environments that you want to block other
than ``production`` separated by commas. For example ``staging,master`` will
block the envs ``production``, ``staging``, and ``master`` from receiving
shortcuts.


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

.. _with a file: https://flask.palletsprojects.com/en/1.1.x/config/#configuring-from-files

.. _anything that a view function can return: https://flask.palletsprojects.com/en/1.1.x/quickstart/#about-responses