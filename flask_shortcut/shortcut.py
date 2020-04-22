from logging import getLogger
from typing import Union, Tuple, Dict, Any, Callable, Optional
from types import MethodType, FunctionType
from functools import wraps
import inspect
import json

from click import secho
from flask import Flask

from flask_shortcut.util import diff, get_request_data

logger = getLogger(__name__)

#: Shorthand for the return type of something pretending to be a route function.
RESPONSE_ARGS = Tuple[Any, int]


class Shortcut:
    """Object that handles the shortcut rerouting.

    Calling an instance of this class on a view function gives the view an
    option to behave differently in non-production environments. The way in
    which the behavior may differ is constrained in three possible ways.

    In the first one, only the arguments for a response are passed to the
    shortcut definition, meaning that the original view is effectively
    disabled and the route will instead just return the shortcut's arguments
    as its only response.

    In the second one, any number of shortcut response arguments are mapped
    to condition-keys. The condition is a json-like string that is used to
    assert a substructure in request bodies that reach that route, and will
    only apply its respective shortcut-response iff that substructure can
    be matched.

    In the third one, a function represents the shortcut and can run
    arbitrary code to ensure whatever the user deems necessary on the
    request body, header, etc. Such a shortcut function may not accept
    arguments and needs to either return None, to signal that the shortcut
    condition failed and the original logic should be run, or valid
    response arguments in the form of a tuple.

    If none of the condition can be satisfied, the route will run its
    original view.

    There are two different ways to register shortcuts, one using decorators
    on the target functions before the are decorated as routes, and the
    other by running the a single wire call after all routes were added.

    Example:

        - Basic app setup:

        >>> app = Flask(__name__)
        >>> short = Shortcut(app)

        - With shortcut decorator:

        >>> @app.route('/my_route', methods=['GET'])
        ... @short.cut(('short_ok', 200))
        ... def my_func():
        ...     return 'ok', 200

        - Equivalent post route-definition wiring:

        >>> @app.route('/my_route', methods=['GET'])
        ... def my_func():
        ...     return 'ok', 200
        >>> short.wire({'/my_route': ('short_ok', 200)})
    """

    def __init__(self, app: Flask):
        self.app = app
        self.exclude = ["production"]
        if app.config.get("SHORTCUT_EXCLUSIONS"):
            exclusions = [x.strip() for x in app.config["SHORTCUT_EXCLUSIONS"].split(",") if x]
            self.exclude.extend(exclusions)
        if app.env not in self.exclude:
            logger.info(f"Setting up flask shortcuts in environment '{app.env}'.")
            secho("   Route shortcuts enabled. Do not do this in any kind of production environment.", fg="red")
        else:
            # make .cut(...) return a wrapper that does nothing
            self.cut = MethodType(lambda _self, mapping: lambda f: f, self)  # type: ignore

    def cut(self, mapping: Union[RESPONSE_ARGS, Dict[str, RESPONSE_ARGS], Callable[[], Optional[RESPONSE_ARGS]]]):
        """Returns view function wrappers.

        Depending on the input argument, a different wrapper will be returned.
        This function can only run in applications that are not listed in the
        `_EXCLUDE` list.

        Args:
            mapping: The mapping that decides which types of shortcuts can be
                offered under which type of condition.
        """
        # wrapper in case only the response is given, assumes that the 'condition' is always True
        def simple_map(f):
            f_name = f"{f.__module__}.{f.__name__}"
            logger.info(f"Adding simple_map shortcut for routing function '{f_name}'.")
            assert isinstance(mapping, tuple), "Messed up shortcut wiring, abort."  # nosec

            @wraps(f)
            def decorated(*_, **__):
                logger.debug(f"Running shortcut for '{f_name}'.")

                response, status = mapping
                return self.app.make_response(response), status

            return decorated

        # wrapper for dict-based mappings
        def dict_map(f):
            f_name = f"{f.__module__}.{f.__name__}"
            logger.info(f"Adding dict_map shortcut for routing function '{f_name}'.")
            assert isinstance(mapping, dict), "Messed up shortcut wiring, abort."  # nosec
            for s in mapping:
                try:
                    json.loads(s)
                except Exception as e:
                    raise TypeError(f"'{s}' can't be deserialized into valid json, raises '{str(e)}'.")

            @wraps(f)
            def decorated(*args, **kwargs):
                logger.debug(f"Running shortcut for '{f_name}'.")

                for condition, (response, status) in mapping.items():
                    request_data = get_request_data()
                    try:
                        sub_resolves = diff(request_data, json.loads(condition))
                    except TypeError as e_:
                        logger.debug(
                            f"Couldn't walk '{condition}' in the target request, got error message '{str(e_)}'. "
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

        # wrapper for function mappings
        def func_map(f):
            f_name = f"{f.__module__}.{f.__name__}"
            logger.info(f"Adding func_map shortcut for routing function '{f_name}'.")
            assert isinstance(mapping, (FunctionType, list)), "Messed up shortcut wiring, abort."  # nosec
            func_list = mapping if isinstance(mapping, list) else [mapping]
            for func in func_list:
                assert isinstance(func, FunctionType), "All mappings in a shortcut lists need to be functions."  # nosec
                assert not inspect.signature(func).parameters, "Mapping functions can't take arguments."  # nosec

            @wraps(f)
            def decorated(*args, **kwargs):
                logger.debug(f"Running shortcut for '{f_name}'.")

                for function in func_list:
                    response = function()
                    if response is not None:
                        return response
                else:
                    logger.debug(f"Shortcut conditions couldn't be satisfied, defaulting to actual implementation.")
                    return f(*args, **kwargs)

            return decorated

        # assigning the right decorator given the mapping types
        if isinstance(mapping, tuple):
            return simple_map
        elif isinstance(mapping, dict):
            return dict_map
        elif isinstance(mapping, (FunctionType, list)):
            return func_map
        else:
            raise TypeError(f"'{type(mapping)}' is not a supported mapping type for shortcuts yet.")

    def wire(
        self,
        shortcuts: Dict[str, Union[RESPONSE_ARGS, Dict[str, RESPONSE_ARGS], Callable[[], Optional[RESPONSE_ARGS]]]],
    ):
        """Manual wiring function.

        If you don't want to have the shortcut definitions in your routing
        file for some reason (e.g. there are lots of shortcuts and it would
        make the whole thing hard to read), you can use this function at
        some point after all view functions were registered and before the
        server is started.

        Args:
            shortcuts: A dictionary that maps routes to the mappings that
                would have been used as arguments in the shortcut decorator.
        """
        route_map = {str(r): r.endpoint for r in self.app.url_map.iter_rules()}

        for route, mapping in shortcuts.items():
            if route in route_map:
                wrap = self.cut(mapping)(self.app.view_functions[route_map[route]])
                self.app.view_functions[route_map[route]] = wrap
            else:
                logger.warning(f"Can't resolve route '{route}' in the registered routes '{[*route_map]}'")
