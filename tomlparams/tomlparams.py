"""TOML-based parameter files made better (main class)"""

from __future__ import annotations

import logging
import os
from glob import glob
from typing import Any

import tomli_w

from tomlparams.params_group import ParamsGroup, create_params_groups
from tomlparams.parse_helpers import (
    DEFAULT_PARAMS_NAME,
    DEFAULT_PARAMS_TYPE_CHECKING_NAME,
    DEFAULTS_ONLY_NAMES,
    ParseMismatchType,
    TypeChecking,
    is_user_reserved_path,
    overwrite_defaults_with_toml,
    selectively_update_dict,
    to_saveable_object,
)
from tomlparams.utils import (
    concatenate_keys,
    concatenate_keys_with_list,
    error,
    load_toml,
    warn,
)

SPECIAL_KEYS = ['include', 'exclude_keys']
LOGGER = logging.getLogger(__name__)


class TOMLParams:
    """TOML-based parameter files made better.

    Args:

        defaults: Specifies the default values, and types of all parameters
                  to be allowed when reading TOML files.
                  Can be a string-keyed Python dictionary (potentially
                  nested) or a string, specifying the name of the TOML file
                  containing the default values. Such a default TOML file
                  may not include inclusions. If using a TOML file,
                  absolute paths can be anywhere; relative paths will
                  be taken to refer to the standard parameters directory.

        name: The (stem) name of the TOML file to use.

              If `None` (the default), `'base'` (or any other base name
              provided as `base_params_stem`, see below) will be used.

              If `'default'` or `'defaults'`, the default values will
              be used,
              i.e. no TOML files will be read other than (if using a file)
              the defaults file.

              If anything else, the name will be searched for in the
              standard_params_dir and the user_params_dir; it should
              only exist in one of those places.

        params_name: If standard params or user params directories are
                     not provided, explicitly, they are based on this
                     value, which defaults to `'tomlparams'`, meaning that
                     if not specified the standard
                     parameters directory will be `~/tomlparams`,
                     and the user parameters directory will be
                     `~/usertomlparams`.

        env_var: The name of an environment variable to look up if
                 name is not set (i.e. is passed in as None). This
                 defaults to TOMLPARAMS.  If TOMLPARAMS is set,
                 for example, 'foo', that will be used as the TOML
                 file stem name for parameter loading.

        base_params_stem: value to use for name (the TOML file stem)
                          if name is passed as None. Defaults to 'base'.

        standard_params_dir: Absolute or relative path for the standard
                             parameters directory. If not set,
                             `~/tomlparams` will be used, or
                             `'~/{params_name}'` if params_name has
                             been set. This path will often be
                             under source control as part of the
                             project using TOMLParams.

        user_params_dir: Absolute or relative path for the user
                         parameters directory. If not set,
                         `~/usertomlparams` will be used, or
                         `'~/user{params_name}'` if params_name has
                         been set. This path will usually *not* be
                         under source control.

        verbose: Set to False to disable output to standard out

        check_types: Controls whether to do type checking of values from
                     TOML files. When type checking is used, the
                     expected type is determined by defaults (the
                     default Python dictionary or TOML file), not
                     by type hinting.  By default
                     (`WARN = tomlparams.WARN`),
                     types not consistent those
                     in defaults generate a warning.  Set to `ERROR`
                     (`tomlparams.ERROR`) to cause an exception to
                     be raised.  Set to `OFF` (`tomlparams.OFF`) to
                     disable type checking.

        type_check_env_var: The name of an environment variable to
                            use to override check_types. Defaults
                            to `'TOMLPARAMSCHECKING'`.  If this
                            environment variable exists, it should
                            be set to one of `'warn'`, `'error'`, or
                            `'off'`, and that value will override
                            the value of check_types passed in.
    """

    ERROR = TypeChecking.ERROR
    WARN = TypeChecking.WARN
    OFF = TypeChecking.OFF

    json_indent = 0
    json_test_indent = 4

    def __init__(
        self,
        defaults: dict[str, Any] | str,
        name: str | None = None,
        params_name: str = DEFAULT_PARAMS_NAME,
        env_var: str | None = None,
        base_params_stem: str = 'base',
        standard_params_dir: str | None = None,
        user_params_dir: str | None = None,
        verbose: bool = True,
        check_types: TypeChecking = WARN,
        type_check_env_var: str | None = None,
    ):
        self._env_var = env_var or params_name.upper()  # TOMLPARAMS
        self._base_params_stem = base_params_stem

        self._standard_params_dir = standard_params_dir or os.path.expanduser(
            f'~/{params_name}'
        )
        self._user_params_dir = user_params_dir or os.path.expanduser(
            f'~/user{params_name}'
        )
        self._verbose = verbose

        if isinstance(defaults, str):
            self._defaults = self.load_defaults_toml_file(defaults)
        else:
            self._defaults = defaults

        self._type_check_env_var = (
            type_check_env_var or DEFAULT_PARAMS_TYPE_CHECKING_NAME
        )

        env_var_checking_value = os.environ.get(self._type_check_env_var)
        self._check_types = self.check_type_env_var_to_typechecking(
            env_var_checking_value, check_types
        )

        self.set_params(name, report_load=self._verbose)

    @property
    def _concatenated_keys(self) -> dict[str, Any]:
        return dict(concatenate_keys(self.as_dict()))

    @property
    def _concatenated_keys_with_list(self) -> dict[str, Any]:
        return dict(concatenate_keys_with_list(self.as_saveable_object()))

    def __getitem__(self, item: str) -> Any:
        try:
            return self.__dict__[item]
        except KeyError:
            try:
                return self.get_concatenated_key(item)
            except KeyError:
                try:
                    return self.get_concatenated_key_with_list(item)
                except KeyError:
                    raise KeyError(f"Key {item} not found in {self}")

    def get_concatenated_key(self, key: str) -> Any:
        if key not in self._concatenated_keys:
            raise KeyError(f"Key {key} not found in {self}")
        return self._concatenated_keys[key]

    def get_concatenated_key_with_list(self, key: str) -> Any:
        if key not in self._concatenated_keys_with_list:
            raise KeyError(f"Key {key} not found in {self}")
        return self._concatenated_keys_with_list[key]

    def __setitem__(self, key: str, value: Any) -> None:
        splitted_key: list[int | str] = [
            int(k) if k.isdigit() else k for k in key.split(".")
        ]
        # first key is always a string
        _initial_key = splitted_key.pop(0)
        assert isinstance(_initial_key, str)
        initial_key: str = _initial_key
        if len(splitted_key) == 0 and isinstance(initial_key, str):
            self.__dict__[initial_key] = value
            return
        param_value = self[initial_key]
        while splitted_key:
            if len(splitted_key) == 1:
                break
            next_key = splitted_key.pop(0)
            if isinstance(param_value, list) and isinstance(next_key, int):
                param_value = param_value[next_key]
            elif isinstance(param_value, ParamsGroup) and isinstance(
                next_key, str
            ):
                param_value = param_value.get(next_key)
        if param_value is None:
            raise KeyError(f"Key {key} not found in {self}")
        else:
            param_value[splitted_key[0]] = value

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TOMLParams):
            return NotImplemented
        return set(concatenate_keys(self.as_saveable_object())) == set(
            concatenate_keys(other.as_saveable_object())
        )

    @classmethod
    def indent(cls, is_test: bool) -> int:
        """Returns amount to indent JSON, which depends on whether this is a
        test run or not."""
        return cls.json_test_indent if is_test else cls.json_indent

    def set_params(self, name: str | None, report_load: bool = False) -> None:
        """Sets the name for the run, which is used as.

          - the subdirectory for results
          - the parameter file for setting other run parameters

        Args:
            name: the name of the run, which is also the name for the
                  parameter file, the results subdirectory etc.

                  If name is `'default'` or `'defaults'`, only the
                  default values will be used.

                  If None, the system will try to use
                  the environment variable specified.
                  and if that is not set, it will use `self._base_params_stem`,
                  which is set from `base_params_stem`,
                  which defaults to `'base'`

            report_load: print loading status
        """
        self._toml_files_used: list[str] = []
        env_params = os.environ.get(self._env_var, self._base_params_stem)
        if name is None:
            name = env_params
        self._name = name  # of the run/in_params/results subdir etc.

        self.load(report=report_load)

    def read_toml_file(
        self, report: bool = False, name: str | None = None
    ) -> dict[str, Any]:
        """Reads parameters from toml file.

        Args:
            report: print loading status
            name: name of the toml file;

        Returns:
            dictionary of parameters from toml file.
        """
        outer_params: dict[str, Any] = {}
        if name := name or self._name:
            base, ext = os.path.splitext(name)
            if ext == '.toml':
                pfile = name
            elif ext == '':
                pfile = f'{name}.toml'
            else:
                raise ValueError(
                    'configuration files must use .toml extension\n'
                    f'(unlike {name}).'
                )

            std_path = os.path.join(self._standard_params_dir, pfile)
            custom_path = os.path.join(self._user_params_dir, pfile)
            path = std_path
            if os.path.exists(std_path):
                if is_user_reserved_path(path):
                    raise ValueError(
                        f'path {path} is reserved for user '
                        'TOML files, but exists in standardparams.'
                    )
                if os.path.exists(custom_path):
                    warn(
                        f'{pfile} exists as {std_path} '
                        f'and {custom_path}; using {custom_path}'
                    )
                    path = custom_path
            elif os.path.exists(custom_path):
                path = custom_path
            else:
                error(
                    f'*** ERROR: No readable file {pfile} exists at'
                    f' {std_path} or {custom_path}; abandoning all hope.'
                )
            path = os.path.realpath(path)
            if path in self._toml_files_used:
                return outer_params

            outer_params = load_toml(path)
            self._toml_files_used = [path] + self._toml_files_used

            if include := outer_params.get('include', None):
                if isinstance(include, list):
                    included_params: dict[str, Any] = {}
                    for name in include:
                        this_inclusion = self.read_toml_file(report, name)
                        selectively_update_dict(
                            included_params, this_inclusion
                        )
                else:
                    included_params = self.read_toml_file(report, include)
                selectively_update_dict(included_params, outer_params)
                outer_params = included_params
            if report:
                LOGGER.info(f'Parameters set from: {path}')
        else:
            if report:
                LOGGER.info('Using default parameters.')
        return outer_params

    def read_defaults_as_directory(self, fullpath: str) -> dict[str, Any]:
        """Reads defaults from a directory of TOML files.

        Args:
            fullpath: path to directory containing TOML files

        Returns:
            dictionary of defaults
        """
        defaults: dict[str, Any] = {}
        toml_dict: dict[str, Any] = {}
        all_tomls = sorted(glob(f'{fullpath}/**/*.toml', recursive=True))
        for i, toml in enumerate(all_tomls):
            toml_dict = load_toml(toml)
            for special_key in SPECIAL_KEYS:
                # Check for special keys in the TOML file, which are not
                # allowed in the consolidated defaults. These are:
                # 'include', 'exclude_keys'
                if special_key in toml_dict:
                    raise KeyError(
                        f'TOML file {toml} includes key'
                        f' "{special_key}",\nwhich is not allow in the'
                        ' consolidated defaults.'
                    )
            if defaults:
                defaults_concatenated_keys = {
                    key for key, _ in concatenate_keys(defaults)
                }
                toml_dict_concatenated_keys = {
                    key for key, _ in concatenate_keys(toml_dict)
                }

                if keys_in_common := defaults_concatenated_keys.intersection(
                    toml_dict_concatenated_keys
                ):
                    raise KeyError(
                        f"Duplicated key(s) '{keys_in_common}' in {toml}."
                        f" Check any of the files in {all_tomls[:i]}"
                    )
            selectively_update_dict(defaults, toml_dict)

        return defaults

    def load_defaults_toml_file(self, path: str) -> dict[str, Any]:
        """Loads defaults from TOML file at path provided."""
        fullpath = (
            path
            if os.path.isabs(path)
            else os.path.join(self._standard_params_dir, path)
        )
        if not os.path.splitext(path)[1]:
            toml_path = f'{fullpath}.toml'
        else:
            toml_path = fullpath
        if os.path.exists(toml_path):
            defaults: dict[str, Any] = load_toml(toml_path)
            for special_key in SPECIAL_KEYS:
                # Check for special keys in the TOML file, which are not
                # allowed in the defaults. These are:
                # 'include', 'exclude_keys'
                if special_key in defaults:
                    raise KeyError(
                        f'Defaults TOML file {toml_path} includes key'
                        f' "{special_key}",\nwhich is not allow in defaults'
                        ' TOML files.'
                    )
            return defaults
        elif os.path.isdir(fullpath):
            return self.read_defaults_as_directory(fullpath)
        else:
            error(f'Defaults cannot be read from {fullpath}.')

    def load(self, report: bool = False) -> None:
        """Loads parameters from TOML file.

        The TOML file's name is the stem in `self._name + '.toml'`.

        It is located either in the standard parameters directory
        or the user parameters directory.

        If both exist, this is an error.

        Args:
            report: print loading status
        """
        if self._name in DEFAULTS_ONLY_NAMES:
            toml = {}
        else:
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

            if type_mismatch_strings and self._check_types is TOMLParams.WARN:
                warning_messages = ['The following issues were found:\n']
                warning_messages.extend(type_mismatch_strings)
                warn(*warning_messages)
            elif (
                type_mismatch_strings and self._check_types is TOMLParams.ERROR
            ):
                error_messages.append('The following issues were found:\n')
                error_messages.extend(type_mismatch_strings)
            if bad_key_strings:
                if not error_messages:
                    error_messages.append('The following issues were found:\n')
                error_messages.extend(bad_key_strings)

            if error_messages:
                error(*error_messages)

        self.__dict__.update(
            create_params_groups(consolidated_dict).get_params()
        )

    def toml_files_str(self) -> str:
        return ', '.join(self._toml_files_used) or ''

    def __str__(self) -> str:
        body = ',\n    '.join(
            f'{k}: {str(v)}'
            for (k, v) in self.__dict__.items()
            if not k.startswith('_')
        )
        return f'TOMLParams(\n    {body}\n)'

    def __repr__(self) -> str:
        body = ',\n    '.join(
            f'{k}={repr(v)}'
            for (k, v) in self.__dict__.items()
            if not k.startswith('_')
        )
        return f'TOMLParams(\n    {body}\n)'

    def as_saveable_object(
        self,
    ) -> Any:
        return to_saveable_object(self.__dict__, self._defaults)

    def as_dict(self) -> Any:
        return to_saveable_object(self.__dict__, self._defaults, False)

    def write_consolidated_toml(
        self, path: str, verbose: bool | None = None
    ) -> None:
        verbose = verbose or self._verbose
        d = to_saveable_object(self.__dict__, self._defaults)
        with open(path, 'wb') as f:
            tomli_w.dump(d, f)
        if verbose:
            LOGGER.info(f'Consolidated TOML file written to {path}.')

    def check_type_env_var_to_typechecking(
        self, env_var: str | None, default_value: TypeChecking
    ) -> TypeChecking:
        if env_var is None:
            return default_value
        elif env_var.lower() == 'warn':
            return TypeChecking.WARN
        elif env_var.lower() == 'off':
            return TypeChecking.OFF
        elif env_var.lower() == 'error':
            return TypeChecking.ERROR
        else:
            error(
                f"Not a valid {type(self).__name__}.TypeChecking value. Change"
                f" {self._type_check_env_var} to one of: 'warn', 'error', or"
                " 'off'."
            )
