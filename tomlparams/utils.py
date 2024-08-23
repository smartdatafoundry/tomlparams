"""
Utils
=====
"""

from typing import Any, Generator, NoReturn
import warnings

import tomli


class TOMLParamsError(Exception):
    pass


def error(*msg) -> NoReturn:
    raise TOMLParamsError(msg)


def warn(*msg: str):
    warnings.warn(msg)


def nvl(v, default):
    return default if v is None else v


def load_toml(path):
    """
    Protected TOML load using tomli that reports what the file
    was if parsing fails (and then re-raises the exception).
    """
    with open(path, 'rb') as f:
        return tomli.load(f)


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
    for key1, value1 in d.items():
        if isinstance(value1, dict):
            for key2, value2 in dict(
                concatenate_keys(value1, sep=sep)
            ).items():
                yield key1 + sep + key2, value2
        else:
            yield key1, value1


def concatenate_keys_with_list(
    d: dict, sep='.'
) -> Generator[tuple[str, Any], None, None]:
    """
    Concatenate keys in a nested dict, e.g.:
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
