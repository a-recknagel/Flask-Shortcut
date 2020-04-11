from functools import singledispatchmethod, wraps
from typing import Callable, Tuple, Dict, Optional

import flask


class Shortcut:
    def __init__(self, app):
        print(app.env)
        self.app = app

    def dev_only_wrap(self, map_applier: Callable[[dict], Optional[Tuple[str, int]]]) -> Callable:
        def outer(func):
            @wraps(func)
            def inner(*args, **kwargs) -> Tuple[flask.Response, int]:
                if self.app.env != "production":
                    if response := map_applier(flask.request.json):
                        return self.app.make_response(response[0]), response[1]
                return func(*args, **kwargs)
            return inner
        return outer

    @singledispatchmethod
    def __call__(self, mapper) -> Callable:
        raise NotImplementedError(f"Mapper of type '{type(mapper)}' is not accepted.")

    @__call__.register(tuple)
    def simple_map(self, mapper: Tuple[str, int]) -> Callable:
        return self.dev_only_wrap(lambda r: mapper)

    @__call__.register(dict)
    def dict_map(self, mapper: Dict[str, int]) -> Callable:
        return self.dev_only_wrap(lambda r: next([mapper[k] for k in mapper if k in r], None))
