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
    d: dict, sep='.'
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
    for k, v in d.items():
        if isinstance(v, dict):
            for k2, v2 in dict(concatenate_keys(v, sep=sep)).items():
                yield k + sep + k2, v2
        else:
            yield k, v
