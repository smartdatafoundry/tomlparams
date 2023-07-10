"""
Parse Helpers
=============
"""
from __future__ import annotations

import datetime
import os
import re
from enum import Enum
from typing import Any, Dict, Optional
from tomlparams.utils import error
from tomlparams import params_group

USER_RESERVED_NAMES_RE = re.compile(r'^(u|user)[-_].*$')
DEFAULT_PARAMS_NAME = 'tomlparams'
DEFAULT_PARAMS_TYPE_CHECKING_NAME = 'TOMLPARAMSCHECKING'
DEFAULTS_ONLY_NAMES = ['default', 'defaults']

TypeChecking = Enum('TypeChecking', ['OFF', 'WARN', 'ERROR'])
ParseMismatchType = Enum('ParseMismatch', ['BADKEY', 'TYPING'])


class ParseMismatch:
    def __init__(
        self,
        pm_type: ParseMismatchType,
        position: list[str],
        key: str,
        default_type: Optional[type | list[type]] = None,
        toml_type: Optional[type | list[type]] = None,
    ):
        self.pm_type = pm_type
        self.position = position
        self.key = key
        if default_type:
            if isinstance(default_type, list):
                self.default_type = (
                    '['
                    + ','.join(sorted([d.__name__ for d in default_type]))
                    + ']'
                )
            else:
                self.default_type = default_type.__name__
        if toml_type:
            if isinstance(toml_type, list):
                self.toml_type = (
                    '['
                    + ','.join(sorted([t.__name__ for t in toml_type]))
                    + ']'
                )
            else:
                self.toml_type = toml_type.__name__

    def __str__(self):
        hierarchy = (
            f'at level: {".".join(self.position)}'
            if self.position
            else 'at root level'
        )
        if self.pm_type is ParseMismatchType.TYPING:
            return (
                f'Type mismatch {hierarchy} - key: {self.key},'
                f' default_type: {self.default_type}, toml_type:'
                f' {self.toml_type}\n'
            )
        elif self.pm_type is ParseMismatchType.BADKEY:
            return f'Bad key {hierarchy} - key: {self.key}\n'
        else:
            error(f'Unknown parse_mismatch type: {self.pm_type}')

    def __repr__(self):
        return (
            f'ParseMismatch({self.pm_type} at'
            f' {self.position if self.position else "root"}, {self.key}, '
            + f'types: {self.default_type}, {self.toml_type})'
        )


def to_saveable_object(o: Any, ref: Optional[Any] = None):
    """
    Convert a TOMLParams Object, a ParamsGroup object, or a collection
    type (dict, list, tuple) recursively to a TOML-dumpable object.
    Typically called on either a TOMLParams or ParamsGroup object as
    top-level invocation.

    Also accepts other objects with as_saveable_object methods,
    which it will use to make TOML-compatible version of those.

    Raises an exception using error if non-TOML-compatible data
    is found.

    Args:
        o: object to be flattened
        ref: object to compare keys of o against

    Returns:
        TOML-dumpable object

    """
    if isinstance(o, dict):
        return {
            k: to_saveable_object(v, ref[k])
            for k, v in o.items()
            if ref and k in ref
        }
    elif isinstance(o, params_group.ParamsGroup):
        return {
            k: to_saveable_object(v, ref[k])
            for k, v in o.__dict__.items()
            if ref and k in ref
        }
    elif isinstance(o, (list, tuple)):
        if ref:
            return [to_saveable_object(v, w) for (v, w) in zip(o, ref)]
        return [to_saveable_object(v) for v in o]
    elif o is None or type(o) in (
        bool,
        str,
        int,
        float,
        datetime.date,
        datetime.time,
        datetime.datetime,
    ):
        return o
    elif hasattr(o, 'as_saveable_object'):
        return o.as_saveable_object()
    else:
        error(f'Cannot flatten object type {type(o)}:\n{str(o)}')


def selectively_update_dict(d: Dict[str, Any], new_d: Dict[str, Any]) -> None:
    """
    Selectively update dictionary d with any values that are in new_d,
    but being careful only to update keys in dictionaries that are present
    in new_d.

    Args:
        d: dictionary with string keys
        new_d: dictionary with string keys
    """
    for k, v in new_d.items():
        if isinstance(v, dict) and k in d:
            if isinstance(d[k], dict):
                selectively_update_dict(d[k], v)
            else:
                d[k] = v
        else:
            d[k] = v


def is_user_reserved_path(path: str) -> bool:
    name = os.path.basename(path)
    return bool(re.match(USER_RESERVED_NAMES_RE, name))


def get_collection_types(coll: list[Any] | set[Any] | tuple[Any]) -> set[type]:
    types = set()
    for item in coll:
        types.add(type(item))
    return types


def overwrite_defaults_with_toml(
    hierarchy: list[str],
    defaults: dict[str, Any],
    overwrite: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Any], list[ParseMismatch]]:
    ret_d = {}
    parse_mismatches = []

    for dk, dv in defaults.items():
        if isinstance(dv, dict):
            ov = overwrite.get(dk) if overwrite is not None else None
            if ov is not None and type(ov) is not dict:
                error(f'*** ERROR: {dk} should be a section of the toml file')
            new_dict, new_type_mismatches = overwrite_defaults_with_toml(
                hierarchy + [dk],
                defaults=dv,
                overwrite=ov,
            )
            ret_d[dk] = new_dict
            parse_mismatches.extend(new_type_mismatches)
        else:
            ov = overwrite.get(dk, dv) if overwrite is not None else dv
            if (
                isinstance(dv, list)
                or isinstance(dv, set)
                or isinstance(dv, tuple)
            ):
                default_types = get_collection_types(dv)
                toml_types = get_collection_types(ov)
                if default_types - toml_types:
                    parse_mismatches.append(
                        ParseMismatch(
                            ParseMismatchType.TYPING,
                            hierarchy,
                            dk,
                            list(default_types),
                            list(toml_types),
                        )
                    )
            if type(ov) != type(dv):
                parse_mismatches.append(
                    ParseMismatch(
                        ParseMismatchType.TYPING,
                        hierarchy,
                        dk,
                        type(dv),
                        type(ov),
                    )
                )
            ret_d[dk] = ov

    if overwrite is not None and (
        bad_keys := set(overwrite.keys()) - set(defaults.keys()) - {'include'}
    ):
        parse_mismatches.extend(
            [
                ParseMismatch(ParseMismatchType.BADKEY, hierarchy, key)
                for key in bad_keys
            ]
        )

    return ret_d, parse_mismatches
