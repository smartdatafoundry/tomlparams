"""
Parameters
==========
"""
import os


import tomli
import tomli_w

from pprint import pformat
from typing import Any, Dict, Optional

from pyxparams.paramsgroup import create_params_groups, ParamsGroup
from pyxparams.utils import (
    check_type_env_var_to_typechecking,
    DEFAULT_PARAMS_NAME,
    error,
    flatten,
    is_user_reserved_path,
    nvl,
    overwrite_defaults_with_toml,
    ParseMismatchType,
    selectively_update_dict,
    TypeChecking,
    warn,
)


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
        base_params_stem: str = "base",
        standard_params_dir: str = None,
        user_params_dir: str = None,
        verbose: Optional[bool] = True,
        check_types: TypeChecking = WARN,
        type_check_env_var: str = 'XPARAMSCHECKING',
    ):
        self._defaults = defaults
        self._env_var = nvl(env_var, paramsname.upper())  # XPARAMS
        self._base_params_stem = base_params_stem

        self._standard_params_dir = nvl(
            standard_params_dir, os.path.expanduser(f"~/{paramsname}")
        )
        self._user_params_dir = nvl(
            user_params_dir, os.path.expanduser(f"~/user{paramsname}")
        )
        self._verbose = verbose

        self._type_check_env_var = os.environ.get(type_check_env_var)
        self._check_types = check_type_env_var_to_typechecking(
            self._type_check_env_var, check_types
        )

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
            if ext == ".toml":
                pfile = name
            elif ext == "":
                pfile = f"{name}.toml"
            else:
                error(
                    "configuration files must use .toml extension\n"
                    f"(unlike {name})."
                )

            std_path = os.path.join(self._standard_params_dir, pfile)
            custom_path = os.path.join(self._user_params_dir, pfile)
            path = std_path
            if os.path.exists(std_path):
                if is_user_reserved_path(path):
                    error(
                        f"path {path} is reserved for user "
                        "TOML files, but exists in standardparams."
                    )
                if os.path.exists(custom_path):
                    warn(
                        f"{pfile} exists as {std_path} "
                        f"and {custom_path}; using {custom_path}"
                    )
            elif os.path.exists(custom_path):
                path = custom_path
            else:
                error(
                    f"*** ERROR: No readable file {pfile} exists at"
                    f" {std_path} or {custom_path}; abandoning all hope."
                )
            path = os.path.realpath(path)
            if path in self.toml_files_used:
                return outer_params

            with open(path, "rb") as f:
                outer_params = tomli.load(f)
                self.toml_files_used = [path] + self.toml_files_used

                if include := outer_params.get("include", None):
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
                print(f"Parameters set from: {path}")

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
        return ", ".join(self.toml_files_used) or ""

    def __str__(self):
        return pformat(self.__dict__, indent=4)

    def as_saveable_object(self):
        return flatten(self.__dict__)

    def write_consolidated_toml(
        self, path: str, verbose: Optional[bool] = None
    ):
        verbose = nvl(verbose, self._verbose)
        d = flatten(self.__dict__, self._defaults)
        with open(path, "wb") as f:
            tomli_w.dump(d, f)
        if verbose:
            print(f'Consolidated TOML file written to {path}.')


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
                return (
                    f'Type mismatch {hierarchy} - key: {self.key},'
                    f' default_type: {self.default_type}, toml_type:'
                    f' {self.toml_type}\n'
                )
            case ParseMismatchType.BADKEY:
                return f'Bad key {hierarchy} - key: {self.key}\n'

    def __repr__(self):
        return (
            f'ParseMismatch({self.pm_type} at'
            f' {self.position if self.position else "root"}, {self.key}, '
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
