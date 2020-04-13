from importlib import metadata

from flask_shortcut.logic import Shortcut

__version__ = metadata.version("flask_shortcut")
__all__ = ["__version__", "Shortcut"]
