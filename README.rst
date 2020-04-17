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
    short.cut({'{"name": "TestUser"}': ('short_bar', 200)})
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
             '/bar': {'{"name": "TestUser"}': ('short_bar', 200)
        }
    )


----

Project home `on github`_.

.. |Logo| image:: https://user-images.githubusercontent.com/2063412/79608525-76ff3100-80f5-11ea-9421-a7e0b7a20ac2.png
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