"""
Utils
=====
"""
import datetime
import os
import re
from enum import Enum
from typing import Any, Dict, Optional
from xparams.errors_warnings import error
import xparams.paramsgroup as paramsgroup
import xparams.parsemismatch as parsemismatch

USER_RESERVED_NAMES_RE = re.compile(r"^(u|user)[-_].*$")

DEFAULT_PARAMS_NAME = "xparams"

DEFAULT_PARAMS_TYPE_CHECKING_NAME = "XPARAMSCHECKING"


TypeChecking = Enum("TypeChecking", ["IGNORE", "WARN", "ERROR"])


def to_saveable_object(o: Any, ref: Optional[Any] = None):
    """
    Convert an XParams Object, a ParamsGroup object, or a collection
    type (dict, list, tuple) recursively to a TOML-dumpable object.
    Typically called on either a XParams or ParamsGroup object as
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
    elif isinstance(o, paramsgroup.ParamsGroup):
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


def nvl(v, default):
    return default if v is None else v


def is_user_reserved_path(path: str) -> bool:
    name = os.path.basename(path)
    return bool(re.match(USER_RESERVED_NAMES_RE, name))


def overwrite_defaults_with_toml(
    hierarchy: list[str],
    defaults: dict[str, Any],
    overwrite: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Any], list[parsemismatch.ParseMismatch]]:
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
            if type(ov) != type(dv):
                parse_mismatches.append(
                    parsemismatch.ParseMismatch(
                        parsemismatch.ParseMismatchType.TYPING,
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
                parsemismatch.ParseMismatch(parsemismatch.ParseMismatchType.BADKEY, hierarchy, key)
                for key in bad_keys
            ]
        )

    return ret_d, parse_mismatches
