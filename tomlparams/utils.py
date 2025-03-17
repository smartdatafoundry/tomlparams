"""
Utils
=====
"""

from __future__ import annotations

import re
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


def nest_dict(
    flat_dict: dict[str, Any], key_separator: str = "."
) -> (
    list[list[Any] | dict[str, list[Any] | dict[str, Any]]]
    | dict[str, list[Any] | dict[str, Any]]
):
    """Convert a flat dictionary to a nested dictionary. Convert a flat
    dictionary to a nested dictionary. The keys in the flat dictionary are
    separated by `key_separator`. If a key is a number, it indicates a list
    index. The nested dictionary is returned as a list if all keys are numbers,
    otherwise as a dictionary.

    For example, the following flat dictionary:

    ```python
    flat_dict = {
        "a.b": 1,
        "a.c": 2,
        "d.0": 3,
        "d.1.e": 4,
    }
    nested_dict = nest_dict(flat_dict)
    ```

    will be converted to the following nested dictionary:

    ```python
    nested_dict = {
        "a": {"b": 1, "c": 2},
        "d": [3, {"e": 4}],
    }
    ```

    Args:
        flat_dict: a flat dictionary
        key_separator: separator between keys

    Returns:
        a nested dictionary
    """
    nested: dict[str, Any] = {}
    for key, value in flat_dict.items():
        parts = key.split(key_separator)
        current = nested
        for i, part in enumerate(parts):
            # Check if the part is a number (indicating a list index)
            if re.match(r"^\d+$", part):
                part = int(part)  # type: ignore
                if isinstance(current, dict):
                    if part not in current:  # type: ignore [unused-ignore]
                        current[part]: dict[str, Any] = {}  # type: ignore
                    current = current[part]  # type: ignore [unused-ignore]
                elif isinstance(current, list):
                    while len(current) <= part:
                        current.append({})
                    current = current[part]

            elif i == len(parts) - 1:  # Last part, assign value
                if isinstance(current, list):
                    current.append({part: value})
                else:
                    current[part] = value

            else:  # Intermediate keys
                if part.isdigit():
                    part = int(x=part)  # type: ignore
                if part not in current:  # type: ignore [unused-ignore]
                    current[part] = {} if not parts[i + 1].isdigit() else []  # type: ignore [unused-ignore]
                current: dict[str, Any] = current[part]  # type: ignore

    return convert_dicts_to_lists(d=nested)


def convert_dicts_to_lists(
    d: dict[str, Any] | list[Any],
) -> (
    list[list[Any] | dict[str, list[Any] | dict[str, Any]]]
    | dict[str, list[Any] | dict[str, Any]]
):
    """Recursively convert dictionaries with numeric keys to lists. For
    example, the following dictionary:

    ```python
    d = {
    0: {"a": 1},
    1: {"b": 2},
    2: {"c": 3},
    }
    new_d = convert_dicts_to_lists(d)
    ```
    will be converted to the following list:

    ```python
    new_d = [{"a": 1}, {"b": 2}, {"c": 3}]
    ```
    Another example:

    ```python
    d = {
        0:{0: {"weight": 1}},
        1:{1: {"weight": 2}},
        2:{0: {"weight": 3}},
        3:{1: {"weight": 4}},
    }
    new_d = convert_dicts_to_lists(d)
    ```
    will be converted to the following dictionary:

    ```python
    new_d =   [
        [{"weight": 1}],
        [{"weight": 2}],
        [{"weight": 3}],
        [{"weight": 4}],
    ]
    ```

    Args:
        d: a dictionary

    Returns:
        a list or a dictionary
    """
    if not d:
        return d
    if isinstance(d, dict):
        if all(isinstance(k, int) for k in d.keys()):
            return [convert_dicts_to_lists(d[k]) for k in sorted(d.keys())]
        else:
            return {k: convert_dicts_to_lists(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_dicts_to_lists(v) for v in d]
    else:
        return d
