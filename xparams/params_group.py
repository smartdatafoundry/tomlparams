"""
Parameters Groups
=================

Container for parameters.
"""
from typing import Any, Dict, TYPE_CHECKING
from tomlparams.parse_helpers import to_saveable_object


class ParamsGroup:
    def __init__(self, depth: int = 0, indent=4):
        self._depth = depth
        self._indent = ' ' * indent * depth

    def __str__(self) -> str:
        desc = 'ParamsGroup(\n'
        for k, v in ((k, v) for (k, v) in self.__dict__.items() if not k.startswith('_')):
            if k != "_depth":
                desc += f"{self._indent}\t{k}: {repr(v)},\n"
        return f"{desc[:-2]}\n{self._indent})"

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

    __repr__ = __str__


def create_params_groups(d: Dict[str, Any], depth: int = 0) -> ParamsGroup:
    pg = ParamsGroup(depth)
    for k, v in d.items():
        if isinstance(v, dict):
            pg.__dict__[k] = create_params_groups(v, depth + 1)
        else:
            pg.__dict__[k] = v
    return pg
