from logging import getLogger
from typing import Union, Tuple, Dict, Any
from functools import wraps
import json

from click import secho
from flask import request, Flask

from flask_shortcut.util import diff, get_request_data

PRODUCTION = "production"
logger = getLogger(__name__)


class Shortcut:
    def __init__(self, app: Flask):
        self.app = None
        if app.env != PRODUCTION:
            logger.info(f"Setting up flask shortcuts in environment '{app.env}'.")
            secho("   Route shortcuts enabled. Do not do this in any kind of production environment.", fg="red")
            self.app = app

    def __call__(self, mapping: Union[Tuple[Any, int], Dict[str, Tuple[Any, int]]]):
        logger.debug(f"Registering shortcut with mapping of type '{type(mapping)}'.")

        # wrapper for simple tuple mappings
        def simple_map(f):
            f_name = f"{f.__module__}.{f.__name__}"
            logger.debug(f"Adding simple_map shortcut for routing function '{f_name}'.")

            @wraps(f)
            def decorated(*args, **kwargs):
                assert isinstance(mapping, tuple), "Messed up shortcut wiring, abort."  # nosec
                if self.app.env != PRODUCTION:
                    # 'condition' is assumed to be always True in this shortcut
                    response, status = mapping
                    return self.app.make_response(response), status
                return f(*args, **kwargs)

            return decorated

        # wrapper for dict-based mappings
        def dict_map(f):
            f_name = f"{f.__module__}.{f.__name__}"
            logger.debug(f"Adding dict_map shortcut for routing function '{f_name}'.")

            @wraps(f)
            def decorated(*args, **kwargs):
                assert isinstance(mapping, dict), "Messed up shortcut wiring, abort."  # nosec
                logger.debug(f"Running shortcut for '{f_name}'.")

                if self.app.env != PRODUCTION:
                    for condition, (response, status) in mapping.items():
                        try:
                            sub_resolves = diff(get_request_data(request), json.loads(condition))
                        except TypeError as e:
                            logger.debug(
                                f"Couldn't walk '{condition}' in the target request, got error message '{str(e)}'. "
                                f"This could mean that the shortcut for this function is not well-defined."
                            )
                            continue
                        if not sub_resolves:
                            continue
                        return self.app.make_response(response), status
                    else:
                        logger.debug(f"Shortcut conditions couldn't be satisfied, defaulting to actual implementation.")
                return f(*args, **kwargs)

            return decorated

        # auto-wiring the right decorator depending on mapping types
        if isinstance(mapping, tuple):
            return simple_map
        elif isinstance(mapping, dict):
            return dict_map
        else:
            raise TypeError(f"'{type(mapping)}' is not a supported mapping type for shortcuts yet.")

    def wire(self, shortcuts=Dict[str, Union[Tuple, Dict]]):
        route_map = {str(r): r.endpoint for r in self.app.url_map.iter_rules()}

        for route in shortcuts:
            if route in route_map:
                wrap = self(shortcuts[route])(self.app.view_functions[route_map[route]])
                self.app.view_functions[route_map[route]] = wrap
            else:
                logger.warning(f"Can't resolve route '{route}' in the registered route '{[*route_map]}'")
