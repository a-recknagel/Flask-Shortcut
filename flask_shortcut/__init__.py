from importlib_metadata import version

from flask_shortcut.logic import Shortcut

__version__ = version("flask_shortcut")
__all__ = ["__version__", "Shortcut"]
