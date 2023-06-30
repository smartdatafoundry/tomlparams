"""
ParamsGroup
===========

Container for parameters.
"""
from typing import Any, Dict
from tomlparams.parse_helpers import to_saveable_object


class ParamsGroup:
    """
    Container for parameters.
    """

    def __init__(self, depth: int = 0, indent=4):
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

    def __getitem__(self, item):
        return self.__dict__[item]

    def as_saveable_object(self):
        return to_saveable_object(self.get_params())

    def get_params(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items() if not k.startswith('_')
        }

    def values(self):
        return self.get_params().values()

    def keys(self):
        return self.get_params().keys()

    def items(self):
        return self.get_params().items()


def create_params_groups(d: Dict[str, Any], depth: int = 0) -> ParamsGroup:
    pg = ParamsGroup(depth)
    for k, v in d.items():
        if isinstance(v, dict):
            pg.__dict__[k] = create_params_groups(v, depth + 1)
        else:
            pg.__dict__[k] = v
    return pg
