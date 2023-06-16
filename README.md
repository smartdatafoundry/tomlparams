# TOMLParams

[![TOMLParams tests](https://github.com/gofcoe/xparams/actions/workflows/tests.yml/badge.svg)](https://github.com/gofcoe/xparams/actions/workflows/tests.yml)

TOML-based parameter files made better

## Key features

 * Simple externalization of parameters in one or more TOML files.
 * Supports loading, saving, default values, parameter name checking
   and optional parameter type checking.
 * Parameters available through attribute lookup or dictionary lookup.
 * Supports hierarchical file inclusion with overriding.
 * Support for using environment variables to select parameter set (as well as API).
 * Default values can be specified in code (as Python dictionaries) or in a TOML file.
 * Full support for parameter hierarchy (using TOML Tables),
   still with attribute and dictionary lookup.
 * Support for writing consolidated parameters as TOML after hierarchical inclusion
   and resolution.
 * Can be subclassed and other attributes can be used without affecting TOML file writing.



## Installation

From PyPI:
```
python -m pip install -U tomlparams
```

Source installation from Github:
```
python -m pip install -U git+ssh://git@github.com/gofcoe/tomlparams.git
```

# Sample Usage

A TOMLParams object is initialized with a set of default values for all parameters.
The defaults can be supplied as a Python dictionary from a TOML file.

```python
from datetime import date, datetime
from tomlparams import TOMLParams
from pprint import pprint

defaults = {
    'start_date': datetime.date(2024, 1, 1),
    'run_days': 366,
    'tolerance': 0.0001,
    'logging': True,
    'locale': 'en_GB',
    'critical_event_time': datetime.datetime(2024, 7, 31, 3, 22, 22),
    'logging': {
        'format': '.csv',
        'events': ['financial', 'telecoms']
    }
}

params = TOMLParams(defaults=defaults, name='defaults')
```

The special value for `'defaults'` for name specifies that the default values
should be used and nothing should be read from a custom TOML parameters file.

Parameters are stored as attributes and can be accessed using `.` style attribute
lookup or dictionary-style lookup:

```
>>> params.run_days
366
>>> params['start_date']
datetime.date(2024, 1, 1)
>>> params.logging.format
'.csv'
>>> params['logging']['events']
['financial', 'telecoms']
```

If the `name` is set to anything other than `defaults` or `default`, that will be
used as the stem name of TOML file in which to look for override parameters.
This defaults to `base` (for `base.toml`). The directory in which the system
looks for this TOML file can be set with `standard_params_dir`, and if not specified
will default to `~/tomlparams` (i.e. `tomlparams` in the user's home directory).

So if `base.toml` exists in the current working directory, and contains

```
start_date = 2024-03-03

[logging]

format = '.json'
```

Then we will have the following (using the same `defaults` dict as before)
```
>>> params = TOMLParams(defaults=defaults, name='defaults')
>>> params.run_days
366
>>> params['start_date']
datetime.date(2024, 3, 3)
>>> params.logging.format
'.json'
>>> params['logging']['events']
['financial', 'telecoms']

>>> params
TOMLParams(
    start_date: datetime.date(2024, 3, 3),
    run_days: 366,
    tolerance: 0.0001,
    logging: ParamsGroup(
    	format: '.json',
    	events: ['financial', 'telecoms']
    ),
    locale: 'en_GB',
    critical_event_time: datetime.datetime(2024, 7, 31, 3, 22, 22)
)
```

## Additional Options

```python
TOMLParams(
    defaults: dict,
    name: str = None, # name of the run,
    params_name: str, # defaults to 'tomlparams'
    env_var: str = None, # if none, defaults to 'TOMLPARAMS'
    base_params_stem: str = "base",
    standard_params_dir: str = None,
    user_params_dir: str = None,
    verbose: Optional[bool] = True,
    check_types: TypeChecking = WARN,
    type_check_env_var: str = None,
)
```

[TODO] - fill out table. To be honest, I'm not sure I get the logic of
precedence of env variable, then user directories, then instantiation
variable for config of TOMLParams, I think this is quite specific for
use in the Glen, and I'm not sure how useful the majority of users
will find this. I don't really like the idea of an app config file
looking at my home directory for further config files. The complexity
level of where `TOMLParams` looks for TOMLs should perhaps be tunable
somehow, perhaps with a `local_only` flag on instantiation which would
lock down where it searches?

| param     | description           | default  |
|-----------|-----------------------|----------|
| defaults  | see description below | required |
| env_var   |                       | XPARAMS  |
| name      | name of the run,      |


# Defaults

The defaults provided on instantiation of an `TOMLParams` object are a
standard `Python` `dict` (containing any further structure of nested
`dicts`). The keys set in defaults define the keys accepted in the
final `TOMLParams` config: no key can be created by TOML file(s) that
is not present in defaults. Any excess keys found in the TOML file(s)
will raise an error on `TOMLParams` creation, showing the position of
keys in the

Type checking will be performed against the `types` of values present in the defaults.


# Hierarchy

TOMLs handled by `TOMLParams` differ from standard TOMLs via the
addition of an `include` keyword with special meaning:

```toml
include = ['one', 'two', 'three']
```

In this case, settings will be processed in the following order: all
in `base.toml` (depending on `base_params_stem` setting), which are in
turn overwritten (in case of overlap) by those in `one.toml`,
processed depth first, and then selectively those in `two.toml` and
`three.toml`, each processed depth first.  Each TOML file is used only
once at the earliest point of its inclusion in the hierarchy.

# Type checking

Type checking is performed against the types of any values present in
the passed-in `defaults`. Three levels of action are configurable:

* `WARN` (default) — a warning is sent to `stderr` but processing continues)
* `ERROR` — processing stops. All type-checking and key-checking errors are collected
   and reported before exit
* `OFF` — no type checking. (Useful when using polymorphic parameters.)

Type checking of any collections (e.g. `list`, `set` and `tuple`)
present in `defaults` is also performed and the selected action taken
if a type appears in a TOML array that is not present in the
corresponding collection in defaults.

Action on a type checking mismatch can be configure in two ways:

* Via the environment variable specified by the
`type_check_env_var` setting (defaults to `XPARAMSCHECKING`) with allowed levels:
`warn`, `error`, and `off`.
* Via the `check_types` setting

The environment variable takes precedence over the setting where set.

# Key checking

Key checking as described above is also performed - any key present at
any point in the final consolidated input TOML that is not present in
`defaults` raises an error. Key checking errors are collected together
with type checking errors and warnings and show before exit.
