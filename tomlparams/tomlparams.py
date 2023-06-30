"""
TOML-based parameter files made better (main class)
"""

import os
import tomli_w
from typing import Optional, Union

from tomlparams.params_group import create_params_groups
from tomlparams.utils import error, warn, nvl, load_toml
from tomlparams.parse_helpers import (
    DEFAULT_PARAMS_NAME,
    DEFAULT_PARAMS_TYPE_CHECKING_NAME,
    DEFAULTS_ONLY_NAMES,
    ParseMismatchType,
    to_saveable_object,
    is_user_reserved_path,
    overwrite_defaults_with_toml,
    selectively_update_dict,
    TypeChecking,
)


class TOMLParams:
    """
    TOML-based parameter files made better

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
        defaults: Union[dict, str],
        name: str = None,
        params_name: str = DEFAULT_PARAMS_NAME,
        env_var: str = None,
        base_params_stem: str = 'base',
        standard_params_dir: str = None,
        user_params_dir: str = None,
        verbose: Optional[bool] = True,
        check_types: TypeChecking = WARN,
        type_check_env_var: str = None,
    ):
        self._env_var = nvl(env_var, params_name.upper())  # TOMLPARAMS
        self._base_params_stem = base_params_stem

        self._standard_params_dir = nvl(
            standard_params_dir, os.path.expanduser(f'~/{params_name}')
        )
        self._user_params_dir = nvl(
            user_params_dir, os.path.expanduser(f'~/user{params_name}')
        )
        self._verbose = verbose

        if type(defaults) == str:
            self._defaults = self.load_defaults_toml_file(defaults)
        else:
            self._defaults = defaults

        self._type_check_env_var = nvl(
            type_check_env_var, DEFAULT_PARAMS_TYPE_CHECKING_NAME
        )

        env_var_checking_value = os.environ.get(self._type_check_env_var)
        self._check_types = self.check_type_env_var_to_typechecking(
            env_var_checking_value, check_types
        )

        self.set_params(name, report_load=self._verbose)

    def __getitem__(self, item):
        return self.__dict__[item]

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

                  If name is `'default'` or `'defaults'`, only the
                  default values will be used.

                  If None, the system will try to use
                  the environment variable specified.
                  and if that is not set, it will use `self._base_params_stem`,
                  which is set from `base_params_stem`,
                  which defaults to `'base'`

            report_load: print loading status
        """
        self._toml_files_used = []
        env_params = os.environ.get(self._env_var, self._base_params_stem)
        if name is None:
            name = env_params
        self._name = name  # of the run/in_params/results subdir etc.

        self.load(report=report_load)

    def read_toml_file(self, report: bool = False, name: Optional[str] = None):
        """
        Reads parameters from toml file

        Args:
            report: print loading status
            name: name of the toml file;

        Returns:
            dictionary of parameters from toml file.
        """
        outer_params = {}
        if name := name or self._name:
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
            if path in self._toml_files_used:
                return outer_params

            outer_params = load_toml(path)
            self._toml_files_used = [path] + self._toml_files_used

            if include := outer_params.get('include', None):
                if isinstance(include, list):
                    included_params = {}
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
                print(f'Parameters set from: {path}')
        else:
            if report:
                print('Using default parameters.')
        return outer_params

    def load_defaults_toml_file(self, path):
        """
        Loads defaults from TOML file at path provided.
        """
        fullpath = (
            path
            if os.path.isabs(path)
            else os.path.join(self._standard_params_dir, path)
        )
        if not os.path.splitext(path)[1]:
            fullpath += '.toml'
        if os.path.exists(fullpath):
            defaults = load_toml(fullpath)
            if 'include' in defaults:
                error(
                    f'Defaults TOML file {fullpath} includes key "include",\n'
                    'which is not allow in defaults TOML files.'
                )
            return defaults
        else:
            error(f'Defaults cannot be read from {fullpath}.')

    def load(self, report: bool = False):
        """
        Loads parameters from TOML file.

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

    def toml_files_str(self):
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

    def as_saveable_object(self):
        return to_saveable_object(self.__dict__, self._defaults)

    def write_consolidated_toml(
        self, path: str, verbose: Optional[bool] = None
    ):
        verbose = nvl(verbose, self._verbose)
        d = to_saveable_object(self.__dict__, self._defaults)
        with open(path, 'wb') as f:
            tomli_w.dump(d, f)
        if verbose:
            print(f'Consolidated TOML file written to {path}.')

    def check_type_env_var_to_typechecking(
        self, env_var, default_value
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
