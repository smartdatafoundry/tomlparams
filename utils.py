"""
Utils
=====
"""
import datetime
import os
import re
import sys

from enum import Enum
from typing import Any, Dict, NoReturn, Optional

from pyxparams.paramsgroup import ParamsGroup

USER_RESERVED_NAMES_RE = re.compile(r"^(u|user)[-_].*$")

DEFAULT_PARAMS_NAME = "xparams"


TypeChecking = Enum("TypeChecking", ["IGNORE", "WARN", "ERROR"])


def flatten(
    o: Any, ref: Any, key: Optional[str] = None, exclude_none: bool = False
):
    if isinstance(o, dict):
        return {
            k: flatten(v, ref[k], key=k)
            for k, v in o.items()
            if k in ref and (v is not None or not exclude_none)
        }
    elif isinstance(o, ParamsGroup):
        return {
            k: flatten(v, ref[k], key=k)
            for k, v in o.__dict__.items()
            if k in ref and (v is not None or not exclude_none)
        }
    elif isinstance(o, (list, tuple)):
        return [
            flatten(v, w, key=str(i)) for i, (v, w) in enumerate(zip(o, ref))
        ]
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
    elif hasattr(o, "as_saveable_object"):
        return o.as_saveable_object()
    else:
        if key is None:
            print(
                f"Cannot flatten object type {type(o)}:\n{str(o)}\nSkipping!!",
                file=sys.stderr,
            )
        else:
            print(
                (
                    f"Cannot flatten object type {type(o)} for"
                    f" {key}\n\nSkipping!!"
                ),
                file=sys.stderr,
            )


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


def error(*msg, exit_code=1) -> NoReturn:
    print("*** ERROR:", *msg, file=sys.stderr)
    sys.exit(exit_code)


def warn(*msg):
    print("*** WARNING ", *msg, file=sys.stderr)


def is_user_reserved_path(path: str) -> bool:
    name = os.path.basename(path)
    return bool(re.match(USER_RESERVED_NAMES_RE, name))


def overwrite_defaults_with_toml(
    hierarchy: list[str],
    defaults: dict[str, Any],
    check_types: TypeChecking,
    overwrite: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    ret_d = {}
    hierarchy_level = (
        f'at level: {".".join(hierarchy)} ' if hierarchy else "at root level "
    )

    for dk, dv in defaults.items():
        if isinstance(dv, dict):
            ov = overwrite.get(dk) if overwrite is not None else None
            if ov is not None and type(ov) is not dict:
                error(f"*** ERROR: {dk} should be a section of the toml file")
            ret_d[dk] = overwrite_defaults_with_toml(
                hierarchy + [dk],
                check_types=check_types,
                defaults=dv,
                overwrite=ov,
            )
        else:
            overwrite_v = (
                overwrite.get(dk, dv) if overwrite is not None else dv
            )
            if check_types != TypeChecking.IGNORE and type(
                overwrite_v
            ) != type(dv):
                if check_types == TypeChecking.WARN:
                    warn(
                        (
                            "Types mismatch in default and toml"
                            f" {hierarchy_level}key: {dk}, default_type:"
                            f" {type(dv).__name__}, toml_type:"
                            f" {type(overwrite_v).__name__}"
                        ),
                    )
                elif check_types == TypeChecking.ERROR:
                    error(
                        (
                            "Types mismatch in default and toml"
                            f" {hierarchy_level}key: {dk}, default_type:"
                            f" {type(dv).__name__}, toml_type:"
                            f" {type(overwrite_v).__name__}"
                        ),
                    )
            ret_d[dk] = overwrite_v

    if overwrite is not None and (
        bad_keys := set(overwrite.keys()) - set(defaults.keys()) - {"include"}
    ):
        error(
            f"Unknown parameters in toml {hierarchy_level}",
            " ".join(sorted(bad_keys)),
        )

    return ret_d


def check_type_env_var_to_typechecking(
    env_var: str, default_value: TypeChecking
) -> TypeChecking:
    if env_var is None:
        return default_value
    elif env_var == 'warn':
        return TypeChecking.WARN
    elif env_var == 'ignore':
        return TypeChecking.IGNORE
    elif env_var == 'error':
        return TypeChecking.ERROR
    else:
        error(
            "Not a valid TypeChecking value. Values: 'warn',"
            " 'error', or 'ignore'"
        )
