from flask_shortcut import __version__


# -- Project information -----------------------------------------------------
project = "Flask-Shortcut"
copyright = "2020, Arne"
author = "Arne Caratti"
release = __version__


# -- General configuration ---------------------------------------------------
templates_path = ["_templates"]
extensions = [
    # builtin
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    # external
    "pallets_sphinx_themes",
]


# -- Options for HTML output -------------------------------------------------
html_theme = "flask"
html_static_path = ["_static"]
html_logo = "_static/shortcut-logo-narrow.png"
