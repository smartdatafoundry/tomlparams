"""
Parameters
==========
"""
import datetime
import os
import re
import sys
from dataclasses import dataclass

import tomli
import tomli_w


from enum import Enum
from pprint import pformat
from typing import Optional, Any, Dict, NoReturn

USER_RESERVED_NAMES_RE = re.compile(r'^(u|user)[-_].*$')

DEFAULT_PARAMS_NAME = 'xparams'


TypeChecking = Enum('TypeChecking', ['IGNORE', 'WARN', 'ERROR'])
ParseMismatchType = Enum('ParseMismatch', ['BADKEY', 'TYPING'])


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
    elif hasattr(o, 'as_saveable_object'):
        return o.as_saveable_object()
    else:
        if key is None:
            print(
                f'Cannot flatten object type {type(o)}:\n{str(o)}\nSkipping!!',
                file=sys.stderr,
            )
        else:
            print(
                (
                    f'Cannot flatten object type {type(o)} for'
                    f' {key}\n\nSkipping!!'
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
    print('*** ERROR:', *msg, file=sys.stderr)
    sys.exit(exit_code)


def warn(*msg) -> None:
    print('*** WARNING:', *msg, file=sys.stderr)


def is_user_reserved_path(path: str) -> bool:
    name = os.path.basename(path)
    return bool(re.match(USER_RESERVED_NAMES_RE, name))


class XParams:
    """
    Collection of Simulation Parameters

    The keys for the toml file are the same as those in defaults,
    and the values in defaults are used where nothing is specified
    in the toml file.
    """

    ERROR = TypeChecking.ERROR
    WARN = TypeChecking.WARN
    IGNORE = TypeChecking.IGNORE

    json_indent = 0
    json_test_indent = 4

    def __init__(
        self,
        defaults: dict,
        name: str = None,
        paramsname: str = DEFAULT_PARAMS_NAME,
        env_var: str = None,
        base_params_stem: str = 'base',
        standard_params_dir: str = None,
        user_params_dir: str = None,
        verbose: Optional[bool] = True,
        check_types: TypeChecking = WARN,
    ):
        self._defaults = defaults
        self._env_var = nvl(env_var, paramsname.upper())  # XPARAMS
        self._base_params_stem = base_params_stem

        self._standard_params_dir = nvl(
            standard_params_dir, os.path.expanduser(f'~/{paramsname}')
        )
        self._user_params_dir = nvl(
            user_params_dir, os.path.expanduser(f'~/user{paramsname}')
        )
        self._verbose = verbose
        self._check_types = check_types
        self.set_params(name, report_load=self._verbose)

    @classmethod
    def indent(cls, is_test: bool) -> int:
        """
        Returns amount to indent JSON, which depends on whether
        this is a test run or not.
        """
        return cls.json_test_indent if is_test else cls.json_indent

    def set_params(self, name: str, report_load: bool = False):
        """
        Sets the name for the run, which is used as
          - the subdirectory for results
          - the parameter file for setting other run parameters

        Args:
            name: the name of the run, which is also the name for the
                  parameter file, the results subdirectory etc.

                  If None, the system will try to use
                  the environment variable specified.
                  and if that is not set, it will use 'default'.
            report_load: print loading status
        """
        self.toml_files_used = []
        envparams = os.environ.get(self._env_var, self._base_params_stem)
        if name is None:
            name = envparams
        self.name = name  # of the run/params/results subdir etc.

        self.load(report=report_load)

    def read_toml_file(self, report: bool = False, name=None):
        """
        Reads parameters from toml file

        Args:
            report: print loading status

        Returns:
            dictionary of parameters from toml file.
        """
        outer_params = {}
        if name := name or self.name:
            base, ext = os.path.splitext(name)
            if ext == '.toml':
                pfile = name
            elif ext == '':
                pfile = f'{name}.toml'
            else:
                error(
                    'configuration files must use .toml extension\n'
                    f'(unlike {name}).'
                )

            std_path = os.path.join(self._standard_params_dir, pfile)
            custom_path = os.path.join(self._user_params_dir, pfile)
            path = std_path
            if os.path.exists(std_path):
                if is_user_reserved_path(path):
                    error(
                        f'path {path} is reserved for user '
                        'TOML files, but exists in standardparams.'
                    )
                if os.path.exists(custom_path):
                    warn(
                        f'{pfile} exists as {std_path} '
                        f'and {custom_path}; using {custom_path}'
                    )
            elif os.path.exists(custom_path):
                path = custom_path
            else:
                error(
                    f'*** ERROR: No readable file {pfile} exists at'
                    f' {std_path} or {custom_path}; abandoning all hope.'
                )
            path = os.path.realpath(path)
            if path in self.toml_files_used:
                return outer_params

            with open(path, 'rb') as f:
                outer_params = tomli.load(f)
                self.toml_files_used = [path] + self.toml_files_used

                if include := outer_params.get('include', None):
                    if isinstance(include, list):
                        included_params = {}
                        for name in include:
                            included_params |= self.read_toml_file(
                                report, name
                            )
                    else:
                        included_params = self.read_toml_file(report, include)
                    selectively_update_dict(included_params, outer_params)
                    outer_params = included_params
            if report:
                print(f'Parameters set from: {path}')

        return outer_params

    def load(self, report: bool = False):
        """
        Loads parameters from .toml file.

        The TOML file's name is the stem in self.name + '.toml'
        It is located either in ./standardparams or ../userparams.
        If both exist, the one in usernparams "wins".

        Args:
            report: print loading status
        """
        toml = self.read_toml_file(report)
        consolidated_dict, mismatches = overwrite_defaults_with_toml(
            hierarchy=[],
            defaults=self._defaults,
            overwrite=toml,
        )

        if mismatches:
            error_messages = []
            type_mismatch_strings = [
                str(m)
                for m in mismatches
                if m.pm_type is ParseMismatchType.TYPING
            ]
            bad_key_strings = [
                str(m)
                for m in mismatches
                if m.pm_type is ParseMismatchType.BADKEY
            ]

            if type_mismatch_strings and self._check_types is XParams.WARN:
                warning_messages = ["The following issues were found:\n"]
                warning_messages.extend(type_mismatch_strings)
                warn(*warning_messages)
            elif type_mismatch_strings and self._check_types is XParams.ERROR:
                error_messages.append("The following issues were found:\n")
                error_messages.extend(type_mismatch_strings)
            if bad_key_strings:
                if not error_messages:
                    error_messages.append("The following issues were found:\n")
                error_messages.extend(bad_key_strings)

            if error_messages:
                error(*error_messages)

        self.__dict__.update(
            create_params_groups(consolidated_dict).get_params()
        )

    def toml_files_str(self):
        return ', '.join(self.toml_files_used) or ''

    def __str__(self):
        return pformat(self.__dict__, indent=4)

    def as_saveable_object(self):
        return flatten(self.__dict__)

    def write_consolidated_toml(
        self, path: str, verbose: Optional[bool] = None
    ):
        verbose = nvl(verbose, self._verbose)
        d = flatten(self.__dict__, self._defaults)
        with open(path, 'wb') as f:
            tomli_w.dump(d, f)
        if verbose:
            print(f'Consolidated TOML file written to {path}.')


class ParamsGroup:
    def __init__(self, depth: int = 0):
        self._depth = depth

    def __str__(self) -> str:
        indent = "\t" * self._depth
        desc = 'ParamsGroup(\n'
        for k, v in self.__dict__.items():
            if k != "_depth":
                desc += f"{indent}\t{k}: {str(v)},\n"
        return f"{desc[:-2]}\n{indent})"

    def as_saveable_object(self):
        return flatten(self.__dict__)

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


class ParseMismatch:
    def __init__(
        self,
        pm_type: ParseMismatchType,
        position: list[str],
        key: str,
        default_type: Optional[type] = None,
        toml_type: Optional[type] = None,
    ):
        self.pm_type = pm_type
        self.position = position
        self.key = key
        self.default_type = default_type.__name__ if default_type else None
        self.toml_type = toml_type.__name__ if toml_type else None

    def __str__(self):
        hierarchy = (
            f'at level: {".".join(self.position)}'
            if self.position
            else "at root level"
        )
        match self.pm_type:
            case ParseMismatchType.TYPING:
                return f'Type mismatch {hierarchy} - key: {self.key}, default_type: {self.default_type}, toml_type: {self.toml_type}\n'
            case ParseMismatchType.BADKEY:
                return f'Bad key {hierarchy} - key: {self.key}\n'

    def __repr__(self):
        return (
            f'ParseMismatch({self.pm_type} at {self.position if self.position else "root"}, {self.key}, '
            + f'types: {self.default_type}, {self.toml_type})'
        )


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
