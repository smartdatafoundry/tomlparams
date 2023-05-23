"""
Parameters
==========
"""
import os


import tomli
import tomli_w

from pprint import pformat
from typing import Optional

from xparams.paramsgroup import create_params_groups
from xparams.parsemismatch import ParseMismatchType
from xparams.utils import (
    DEFAULT_PARAMS_NAME,
    DEFAULT_PARAMS_TYPE_CHECKING_NAME,
    error,
    to_saveable_object,
    is_user_reserved_path,
    nvl,
    overwrite_defaults_with_toml,
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
        type_check_env_var: str = None,
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

        self._type_check_env_var = nvl(
            type_check_env_var, DEFAULT_PARAMS_TYPE_CHECKING_NAME
        )
        env_var_value = os.environ.get(self._type_check_env_var)
        self._check_types = self.check_type_env_var_to_typechecking(
            env_var_value, check_types
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
        return to_saveable_object(self.__dict__)

    def write_consolidated_toml(
        self, path: str, verbose: Optional[bool] = None
    ):
        verbose = nvl(verbose, self._verbose)
        d = to_saveable_object(self.__dict__)
        with open(path, "wb") as f:
            tomli_w.dump(d, f)
        if verbose:
            print(f'Consolidated TOML file written to {path}.')

    def check_type_env_var_to_typechecking(
        self, env_var, default_value
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
                f"Not a valid {type(self).__name__}.TypeChecking value. Change"
                f" {self._type_check_env_var} to one of: 'warn', 'error', or"
                " 'ignore'."
            )
