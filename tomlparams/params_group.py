"""
ParamsGroup
===========

Container for parameters.
"""

from __future__ import annotations

from typing import Any
from tomlparams.parse_helpers import to_saveable_object
from tomlparams.utils import concatenate_keys


class ParamsGroup:
    """
    Container for parameters.
    """

    def __init__(self, depth: int = 0, indent: int = 4):
        self._depth = depth
        self._param_indent = ' ' * indent * (depth + 1)
        self._group_indent = ' ' * indent * depth

    def __str__(self) -> str:
        body = f',\n{self._param_indent}'.join(
            f'{k}: {str(v)}'
            for (k, v) in self.__dict__.items()
            if not k.startswith('_')
        )
        return (
            f'ParamsGroup(\n{self._param_indent}{body}\n{self._group_indent})'
        )

    def __repr__(self) -> str:
        body = f',\n{self._param_indent}'.join(
            f'{k}={repr(v)}'
            for (k, v) in self.__dict__.items()
            if not k.startswith('_')
        )
        return (
            f'ParamsGroup(\n{self._param_indent}{body}\n{self._group_indent})'
        )

    def __eq__(self, other: Any) -> bool | type[NotImplemented]:
        if not isinstance(other, ParamsGroup):
            return NotImplemented
        return set(concatenate_keys(self.as_saveable_object())) == set(
            concatenate_keys(other.as_saveable_object())
        )

    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def as_saveable_object(self):
        return to_saveable_object(self, self.as_dict())

    def get_params(self) -> dict:
        """Return a dictionary of parameters, excluding private attributes."""
        return {
            k: v for k, v in self.__dict__.items() if not k.startswith('_')
        }

    def as_dict(self) -> dict:
        """Return a dictionary of parameters, including nested ParamsGroups.
        Exclude private attributes."""
        return {
            k: v.as_dict() if isinstance(v, ParamsGroup) else v
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        }

    def values(self):
        return self.get_params().values()

    def keys(self):
        return self.get_params().keys()

    def items(self):
        return self.get_params().items()


def create_params_groups(
    input_dict: dict[str, Any], depth: int = 0
) -> ParamsGroup:
    params_group = ParamsGroup(depth)
    for k, v in input_dict.items():
        if isinstance(v, dict):
            params_group.__dict__[k] = create_params_groups(v, depth + 1)
        elif is_iterable_of_dicts(v):
            params_group.__dict__[k] = [
                create_params_groups(x, depth + 1) for x in v
            ]
        else:
            params_group.__dict__[k] = v
    return params_group


def is_iterable_of_dicts(item: Any):
    if isinstance(item, (set, list, tuple)):
        return all(isinstance(x, dict) for x in item)
    return False
