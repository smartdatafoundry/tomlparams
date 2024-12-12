"""
Utils
=====
"""

from __future__ import annotations

import warnings
from typing import Any, Generator, NoReturn, TypeVar

import tomli


class TOMLParamsError(Exception):
    pass


def error(*msg: str) -> NoReturn:
    raise TOMLParamsError(msg)


def warn(*msg: str) -> None:
    warnings.warn(" ".join(msg))


U = TypeVar("U")
V = TypeVar("V")


def nvl(value: U | None, default: V) -> U | V:
    """Returns value if value is not None, otherwise default.

    Args:
        value: a value
        default: a default value

    Returns:
        value if value is not None, otherwise default
    """
    return default if value is None else value


def load_toml(path: str) -> dict[str, Any]:
    """Protected TOML load using tomli that reports what the file was if
    parsing fails (and then re-raises the exception)."""
    with open(path, 'rb') as f:
        return tomli.load(f)


def concatenate_keys(
    d: dict[str, Any], sep: str = '.'
) -> Generator[tuple[str, Any], None, None]:
    """Concatenate keys in a nested dict, e.g.:

    >>> d = {'a': {'b': 1, 'c': 2}, 'd': 3}
            >>> dict(concat_keys(d))
            {'a.b': 1, 'a.c': 2, 'd': 3}
    Args:
        d: dict
        sep: separator between keys
    Returns:
        generator of (key, value) pairs
    """
    for key1, value1 in d.items():
        if isinstance(value1, dict):
            for key2, value2 in dict(
                concatenate_keys(value1, sep=sep)
            ).items():
                yield key1 + sep + key2, value2
        else:
            yield key1, value1


def concatenate_keys_with_list(
    d: dict[str, Any], sep: str = '.'
) -> Generator[tuple[str, Any], None, None]:
    """Concatenate keys in a nested dict, e.g.:

    >>> d = {'a': {'b': 1, 'c': 2}, 'd': 3}
            >>> dict(concat_keys(d))
            {'a.b': 1, 'a.c': 2, 'd': 3}
    Special when values is a list:
            >>> d = {'a': {'b': 1, 'c': 2}, 'd': [3, {'e': 4}]}
            >>> dict(concat_keys(d))
            {'a.b': 1, 'a.c': 2, 'd.0': 3, 'd.1.e': 4}
    Args:
        d: dict
        sep: separator between keys
    Returns:
        generator of (key, value) pairs
    """
    for key1, value1 in d.items():
        if isinstance(value1, dict):
            for key2, value2 in dict(
                concatenate_keys_with_list(value1, sep=sep)
            ).items():
                yield key1 + sep + key2, value2
        elif isinstance(value1, list):
            for list_index, list_item in enumerate(value1):
                if isinstance(list_item, dict):
                    for key3, value3 in concatenate_keys_with_list(
                        list_item, sep=sep
                    ):
                        yield f'{key1}{sep}{list_index}{sep}{key3}', value3
                else:
                    yield f'{key1}{sep}{list_index}', list_item
        else:
            yield key1, value1
