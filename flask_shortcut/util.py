from flask import Request
import xmltodict


def get_request_data(r: Request):
    """Request data fetcher.

    This function inspects the mimetype in order to figure out how the data
    can be represented in a standard python-dictionary form.

    Returns:
        The data in a form that sticks as close a parsed json object as possible, since
            that is the format in which the mappings expect to be passed by.

    Raises:
        ValueError: In case of unexpected request data formats.
        Exception: In case of junk data, hard to list what each parser
            decides is best to raise.
    """
    if "json" in r.mimetype:
        return r.json
    if "xml" in r.mimetype:
        return xmltodict.parse(r.data, dict_constructor=dict)
    raise ValueError(f"Mimetype '{r.mimetype}' not parsable.")


def diff(target, sub, path_=None) -> bool:
    """Simple recursive asymmetric diff function on json-like data structures.

    Args:
        target: The data container in which we want to find a subtree.
        sub: The subtree that needs to be matched.
        path_: A private object used to produce meaningful error messages.

    Returns:
        True if the subtree could be cleanly matched, else False.

    Raises:
        TypeError: If the parse paths don't match, e.g. the target is a list
            at a level where the subtree expected it to be a dictionary.
    """
    if path_ is None:
        path_ = ["root"]

    if type(target) != type(sub):
        raise TypeError(f"Types of target '{type(target)}' and sub '{type(sub)}' are incompatible at junction {path_}.")

    if isinstance(sub, list):
        for n, s_elem in enumerate(sub):
            for t_elem in target:
                if diff(t_elem, s_elem, [*path_, n]):
                    break
            else:
                return False
        return True
    elif isinstance(sub, dict):
        for s_key in sub:
            if s_key in target and diff(target[s_key], sub[s_key], [*path_, s_key]):
                continue
            return False
        return True
    else:  # some kind of leaf, i.e. string, int, bool, float, or None
        return bool(target == sub)
