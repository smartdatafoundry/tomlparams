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

## The Simplest Case (Defaults Only)

A TOMLParams object is initialized with a set of default values for all parameters.
The defaults can be supplied as a Python dictionary from a TOML file, and all
values should be TOML-serializable (so no `None` values).

```python
from datetime import date, datetime
from tomlparams import TOMLParams

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
lookup or dictionary-style lookup with `[]`:

```python
>>> params.run_days
366
>>> params['start_date']
datetime.date(2024, 1, 1)
>>> params.logging.format
'.csv'
>>> params['logging']['events']
['financial', 'telecoms']
```

## Using a TOML file to override some parameter values

If the `name` is set to anything other than `'defaults'`, that will be
used as the stem name of TOML file in which to look for override parameters.
This defaults to `base` (for `base.toml`). The directory in which the system
looks for this TOML file can be set with `standard_params_dir`, and if not specified
will default to `~/tomlparams` (i.e. `tomlparams` in the user's home directory).

So if `base.toml` exists in the current working directory, and contains

```toml
start_date = 2024-03-03

[logging]
format = '.json'
```

Then we will have the following (using the same `defaults` dict as before)
```python
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

Notice how the two values in `base.toml` have overridden the defaults (`start_date`
and `logging.format`), but that other parameters, including `logging.events`, retained
their values.

## Parameter (Key) Checking

Only parameters in `defaults` are allowed;
an exception is raised if any unexpected values are found in the TOML file.

## Setting a custom TOML file name

# Hierarchical Inclusion

A special key, `include` may be used as the first line of a TOML file,
and may be set to either single string name
(the stem name of a TOML file to include),
or a list of such names.

```toml
include = ['one', 'two']
```

Inclusions are processed left-to-right, before the rest of the values in the
file with the `include` statement, but each include is only processed once,
the first time it is encountered, with newer values always overriding old ones.

So if `base.toml` (or other named TOML file used)
starts with this `include` line, and neither of `one` and `two`
has any further inclusions, the order of parameter setting will be:

  1. values from `defaults`
  2. values from `one.toml`
  3. values from `two.toml`
  4. any other values

If `one` and `two` both start with

```toml
include = 'three'
```

then the order of processing will be:

  1. values from `defaults`
  2. values from `three.toml` (from its inclusion by `one.toml`)
  3. values from `one.toml`
  4. values from `two.toml` (`three.toml` will is *not* included a second time)
  5. any other values

Circular inclusion does not cause a problem, because each file is only ever included once,
but is potentially confusing for the reader, so is not recommended.

Unless `verbose` is set to `False` when initializing `TOMLParams`, any TOML files processed
are reported, in order of inclusion, listing full paths.

## Writing out the consolidated TOML file

Hierarchical file inclusion is powerful, and allows different sets of parameters
to be combined easily, but it can be hard for the reader to know what the final
set of parameters used is without thinking through the inclusion hierarchy.
TOMParams can write out a consolidated parameter values finally used as a single
TOML file containing them all, without inclusions.




# Environment Variables


# Type Checking

Type checking is performed against the types of any values present in
the passed-in `defaults`. Three levels of action are configurable:

* `WARN` (default) — a warning is sent to `stderr` but processing continues)
* `ERROR` — processing stops. All type-checking and key-checking errors are collected
   and reported before exit
* `OFF` — no type checking. (Useful when using polymorphic parameters.)

Type checking of any collections (e.g. `list`, `set` and `tuple`)
present in `defaults` is also performed and the selected action taken
if a type appears in a TOML array that is not present in the
corresponding collection in the defaults.

Action on a type checking mismatch can be configure in two ways:

* Via the environment variable specified by the
`type_check_env_var` setting (defaults to `XPARAMSCHECKING`) with allowed levels:
`warn`, `error`, and `off`.
* Via the `check_types` setting

The environment variable takes precedence over the setting where set.


# Setting defaults from a TOML File

