"""
Utils
=====
"""

import sys
from typing import Any, Generator, NoReturn

import tomli


def error(*msg, exit_code=1) -> NoReturn:
    print("*** ERROR:", *msg, file=sys.stderr)
    sys.exit(exit_code)
    # raise Exception


def warn(*msg):
    print("*** WARNING:", *msg, file=sys.stderr)


def nvl(v, default):
    return default if v is None else v


def load_toml(path):
    """
    Protected TOML load using tomli that reports what the file
    was if parsing fails (and then re-raises the exception).
    """
    with open(path, 'rb') as f:
        try:
            return tomli.load(f)
        except Exception:
            print(
                f'\n***\n*** Problem parsing {path}:\n***\n', file=sys.stderr
            )
            raise


def concatenate_keys(
    dict_to_flatten: dict[Any, Any], sep: str = '.'
) -> Generator[tuple[str, Any], None, None]:
    """
    Concatenate keys in a nested dict, e.g.:
            >>> d = {'a': {'b': 1, 'c': 2}, 'd': 3}
            >>> dict(concat_keys(d))
            {'a.b': 1, 'a.c': 2, 'd': 3}
    Args:
        d: dict
        sep: separator between keys
    Returns:
        generator of (key, value) pairs
    """
    for key1, value1 in dict_to_flatten.items():
        if isinstance(value1, dict):
            for key2, value2 in dict(
                concatenate_keys(value1, sep=sep)
            ).items():
                yield key1 + sep + key2, value2
        else:
            yield key1, value1
