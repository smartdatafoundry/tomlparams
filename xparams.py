"""
Parameters
==========
"""
import datetime
import os
import random
import re
import sys
import tomli
import tomli_w

from dataclasses import dataclass
from datetime import date
from pprint import pformat
from typing import Optional, Any, Dict

USER_RESERVED_NAMES_RE = re.compile(r'^(u|user)[-_].*$')

DEFAULT_PARAMS_NAME = 'xparams'


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


def selectively_update_dict(
    d: Dict[str, Any], new_d: Dict[str, Any], show_warnings: bool = True
) -> int:
    """
    Selectively update dictionary d with any values that are in new_d,
    but being careful only to update keys in dictionaries that are present
    in new_d.

    Args:
        d: dictionary with string keys
        new_d: dictionary with string keys
        show_warnings: chattier if true
    """
    warnings = []
    for k, v in new_d.items():
        if isinstance(v, dict) and k in d:
            if isinstance(d[k], dict):
                selectively_update_dict(d[k], v)
            else:
                msg = (
                    f'Replacing value for {k}, of type {type(d[k])} '
                    f'with dictionary {v}.'
                )
                warn(msg, show=show_warnings)
                warnings.append(msg)
                d[k] = v
        else:
            d[k] = v
    return warnings


def nvl(v: Any, default: Any) -> Any:
    return default if v is None else v


def error(*msg, exit_code=1):
    print('*** ERROR:', *msg, file=sys.stderr)
    sys.exit(exit_code)


def warn(*msg, exit_code=1):
    print('*** WARNING ', *msg, file=sys.stderr)


def is_user_reserved_path(path):
    name = os.path.basename(path)
    return bool(re.match(USER_RESERVED_NAMES_RE, name))


class XParams:
    """
    Collection of Simulation Parameters

    The keys for the toml file are the same as those in defaults,
    and the values in defaults are used where nothing is specified
    in the toml file.
    """

    verbose = False
    json_indent = 0
    json_test_indent = 4

    def __init__(
        self,
        defaults,
        name=None,
        paramsname=DEFAULT_PARAMS_NAME,
        env_var=None,
        base_params_stem='base',
        standard_params_dir=None,
        user_params_dir=None,
        verbose=True,
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
        self.set_params(name, report_load=self._verbose)

    @classmethod
    def indent(cls, is_test):
        """
        Returns amount to indent JSON, which depends on whether
        this is a test run or not.
        """
        return cls.json_test_indent if is_test else cls.json_indent

    def set_params(self, name: str, report_load: bool = False):
        """
        Sets the name for the run, which is used as
          - the subdirectory of glenresults for results
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

        _ = self.load(report=report_load)

        # directories organization for results dir
        self.compute_internals()

    def compute_internals(self):
        return

    def read_toml_file(self, report: bool = False, name=None):
        """
        Reads parameters from toml file

        Args:
            report: print loading status

        Returns:
            dictionary of parameters from toml file.
        """
        params = {}
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
                    f'No readable file {pfile} exists at'
                    f' {std_path} or {custom_path}; abandoning all hope.'
                )
            path = os.path.realpath(path)
            if path in self.toml_files_used:
                return params

            with open(path, 'rb') as f:
                params = tomli.load(f)
                self.toml_files_used = [path] + self.toml_files_used

                if include := params.get('include', None):
                    if isinstance(include, list):
                        new_params = {}
                        for name in include:
                            new_params |= self.read_toml_file(report, name)
                    else:
                        new_params = self.read_toml_file(report, include)
                    selectively_update_dict(new_params, params)
                    params = new_params
            if report:
                print(f'Parameters set from: {path}')

        return params

    def load(self, report: bool = False):
        """
        Loads parameters from .toml file.

        The TOML file's name is the stem in self.name + '.toml'
        It is located either in ./standardparams or ../glenparams.
        If both exist, the one in glenparams "wins".

        Args:
            report: print loading status
        """
        p = self.read_toml_file(report)
        for k, v in self._defaults.items():
            if isinstance(v, dict):
                self.__dict__[k] = d = ParamsGroup()
                pp = p.get(k)
                if pp is not None and type(pp) is not dict:
                    error(
                        f'*** ERROR: {k} should be a section '
                        f'of the toml file {self.toml_files_str()}'
                    )
                for key, value in v.items():
                    d.__dict__[key] = pp.get(key, value) if pp else value
            else:
                self.__dict__[k] = p.get(k, v)
        if (
            bad_keys := set(p.keys())
            - set(self._defaults.keys())
            - {'include'}
        ):
            error(
                f'Unknown parameters in {self.toml_files_str()}: ',
                ' '.join(sorted(bad_keys)),
            )

    def toml_files_str(self):
        return ', '.join(self.toml_files_used) or ''

    def __str__(self):
        return pformat(self.__dict__, indent=4)

    def as_saveable_object(self):
        return flatten(self.__dict__)

    def write_consolidated_toml(self, path: str, verbose=None):
        verbose = nvl(verbose, self._verbose)
        d = flatten(self.__dict__, self._defaults)
        with open(path, 'wb') as f:
            tomli_w.dump(d, f)
        if self._verbose:
            print(f'Consolidated TOML file written to {path}.')


class ParamsGroup:
    def __str__(self):
        return f'ParamsGroup(**{pformat(self.__dict__, indent=4)})'

    def as_saveable_object(self):
        return flatten(self.__dict__)

    __repr__ = __str__
