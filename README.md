# TOMLParams

[![TOMLParams tests](https://github.com/itsbigspark/tomlparams/actions/workflows/push_main.yml/badge.svg)](https://github.com/itsbigspark/tomlparams/actions/workflows/push_main.yml)

TOML-based parameter files made better

## Key features

- Simple externalization of parameters in one or more TOML files.
- Supports loading, saving, default values, parameter name checking and
  optional parameter type checking.
- Parameters available through attribute lookup or dictionary lookup.
- Supports hierarchical file inclusion with overriding.
- Support for using environment variables to select parameter set (as well as
  API).
- Default values can be specified in code (as Python dictionaries) or in a TOML
  file.
- Full support for parameter hierarchy (using TOML Tables), still with
  attribute and dictionary lookup.
- Support for writing consolidated parameters as TOML after hierarchical
  inclusion and resolution.
- Can be subclassed and other attributes can be used without affecting TOML
  file writing.

## Installation

From PyPI:

```sh
python -m pip install -U tomlparams
```

Source installation from Github:

```sh
python -m pip install -U git+ssh://git@github.com/itsbigspark/tomlparams.git
```

## Sample Usage

### The Simplest Case (Defaults Only)

A TOMLParams object is initialized with a set of default values for all
parameters. The defaults can be supplied as a Python dictionary from a TOML
file, and all values should be TOML-serializable (so no `None` values).

```python
from datetime import date, datetime
from tomlparams import TOMLParams

defaults = {
    'start_date': datetime.date(2024, 1, 2),
    'run_days': 366,
    'tolerance': 0.0002,
    'log': True,
    'locale': 'en_GB',
    'critical_event_time': datetime.datetime(2024, 7, 31, 3, 22, 23),
    'logging': {
        'format': '.csv',
        'events': ['financial', 'telecoms']
    }
}

params = TOMLParams(defaults=defaults, name='defaults')
```

The special value for `'defaults'` for name specifies that the default values
should be used and nothing should be read from a custom TOML parameters file.

Parameters are stored as attributes and can be accessed using `.` style
attribute lookup or dictionary-style lookup with `[]`:

```python
>>> params.run_days
366
>>> params['start_date']
datetime.date(2024, 1, 2)
>>> params.logging.format
'.csv'
>>> params['logging']['events']
['financial', 'telecoms']
```

### Using a TOML file to override some parameter values

If the `name` is set to anything other than `'defaults'`, that will be used as
the stem name of TOML file in which to look for override parameters. This
defaults to `base` (for `base.toml`). The directory in which the system looks
for this TOML file can be set with `standard_params_dir`, and if not specified
will default to `~/tomlparams` (i.e. `tomlparams` in the user's home
directory).

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

Notice how the two values in `base.toml` have overridden the defaults
(`start_date` and `logging.format`), but that other parameters, including
`logging.events`, retained their values.

## Setting defaults from a TOML File

We can set the defaults from a TOML file instead of a Python dictionary by
simply giving the path to the TOML file as the value for `defaults` when
initializing `TOMLParams`. If it's an absolute path, it will be read, but if
it's a relative path, the system will look in the `standard_params_dir`.

This TOML file:

```toml
start_date = 2024-01-01
run_days = 366
tolerance = 0.0001
locale = "en_GB"
critical_event_time = 2024-07-31 03:22:22

[logging]
format = ".csv"
events = [
    "financial",
    "telecoms",
]
```

is equivalent to the dict used above.

and if stored in `./defaults.toml` can be used with

```python
>>> params = TOMLParams(
     defaults='defaults',
     standard_params_dir='.'
)

```

### Setting a custom TOML file name and Parameter (Key) Checking

Only parameters in `defaults` are allowed to exist in other TOML parameter
files. an exception is raised if any unexpected values are found in the TOML
file.

For example, if `newparams.toml` is:

```toml
new_param = 'this will go badly'
```

and we repeated the use the same defaults, passing `newparams` as the `name` we
get the following error:

```python
>>> params = TOMLParams(
     defaults='defaults',
     name='newparam',
     standard_params_dir='.'
)
*** ERROR: The following issues were found:
 Bad key at root level - key: new_param
```

## Hierarchical Inclusion

A special key, `include` may be used as the first line of a TOML file, and may
be set to either single string name (the stem name of a TOML file to include),
or a list of such names.

```toml
include = ['one', 'two']
```

Inclusions are processed left-to-right, before the rest of the values in the
file with the `include` statement, but each include is only processed once, the
first time it is encountered, with newer values always overriding old ones.

So if `base.toml` (or other named TOML file used) starts with this `include`
line, and neither of `one` and `two` has any further inclusions, the order of
parameter setting will be:

1. values from defaults
1. values from `one.toml`
1. values from `two.toml`
1. any other values

If `one` and `two` both start with

```toml
include = 'three'
```

then the order of processing will be:

1. values from defaults
1. values from `three.toml` (from its inclusion by `one.toml`)
1. values from `one.toml`
1. values from `two.toml` (`three.toml` will is *not* included a second time)
1. any other values

Circular inclusion does not cause a problem, because each file is only ever
included once, but is potentially confusing for the reader, so is not
recommended.

Unless `verbose` is set to `False` when initializing `TOMLParams`, any TOML
files processed are reported, in order of inclusion, listing full paths.

So running this code (available in the source repo as
`examples/readme/readme4.py`):

```python
from tomlparams import TOMLParams

params = TOMLParams(
     defaults='defaults2',
     name='hier',
     standard_params_dir='.'
)

print(repr(params))
```

we see the following output:

```none
$ python readme4.py
Parameters set from: /home/itsbigspark/tomlparams/examples/readme/three.toml
Parameters set from: /home/itsbigspark/tomlparams/examples/readme/one.toml
Parameters set from: /home/itsbigspark/tomlparams/examples/readme/two.toml
Parameters set from: /home/itsbigspark/tomlparams/examples/readme/hier.toml
TOMLParams(
    a='hier',
    b='two',
    c='one',
    d='three',
    e='default',
    group=ParamsGroup(
        a='group hier',
        b='group two',
        c='group one',
        d='group three',
        e='group default',
        subgroup=ParamsGroup(
            a='subgroup hier',
            b='subgroup two',
            c='subgroup one',
            d='subgroup three',
            e='subgroup default'
        )
    )
)
```

where (in order of parameter setting): `defaults2.toml` (used to specify
defaults) is:

```toml
# defaults2.toml

a = 'default'
b = 'default'
c = 'default'
d = 'default'
e = 'default'

[group]

a = 'group default'
b = 'group default'
c = 'group default'
d = 'group default'
e = 'group default'

[group.subgroup]

a = 'subgroup default'
b = 'subgroup default'
c = 'subgroup default'
d = 'subgroup default'
e = 'subgroup default'
```

These settings are overridden first by `three.toml`:

```toml
# three.toml

a = 'three'
b = 'three'
c = 'three'
d = 'three'

[group]

a = 'group three'
b = 'group three'
c = 'group three'
d = 'group three'

[group.subgroup]

a = 'subgroup three'
b = 'subgroup three'
c = 'subgroup three'
d = 'subgroup three'
```

These are next overridden by `one.toml`:

```toml
# one.toml

include = 'three'
a = 'one'
b = 'one'
c = 'one'


[group]

a = 'group one'
b = 'group one'
c = 'group one'

[group.subgroup]

a = 'subgroup one'
b = 'subgroup one'
c = 'subgroup one'
```

In turn, these are overridden by `two.toml`:

```toml
# two.toml

include = 'three'
a = 'two'
b = 'two'

[group]

a = 'group two'
b = 'group two'

[group.subgroup]

a = 'subgroup two'
b = 'subgroup two'
```

Finally, the parameters set in `hier.toml` over-ride all others:

```toml
# hier.toml

include = ['one', 'two']

a = 'hier'

[group]

a = 'group hier'

[group.subgroup]

a = 'subgroup hier'
```

### Writing out the consolidated TOML file

Hierarchical file inclusion is powerful, and allows different sets of
parameters to be combined easily, but it can be hard for the reader to know
what the final set of parameters used is without thinking through the inclusion
hierarchy. TOMLParams can write out a consolidated parameter values finally
used as a single TOML file containing them all, without inclusions. The method
`write_consolidated_toml` on a `TOMLParams` object will do this:

```python
param.write_consolidated_toml('consolidated_params.toml')
```

## Determination of Name of TOML Parameters File

When a `TOMLParams` object is instantiated, the second
argument---`name`---determines which set of parameters is used. Many options
for setting this are supported. In determining which parameters file to use,
there are two relevant directories:

- the *standard parameters directory* can be set by passing in a path as
  `standard_params_dir`. If this is not specified, explicitly,
  `~/{params_name}` will be used if the `params_name` argument has been set on
  instantiating TOMLParams, or `~/tomlparams` otherwise.
- the *user parameters directory* can be set by passing in a path as
  `user_params_dir`. If this is not specified, explicitly,
  `~/user{params_name}` will be used if the `params_name` argument has been set
  on instantiating TOMLParams, or `~/usertomlparams` otherwise.

1. If `name` is set to `foo`, TOMLParams will search for `foo.toml` in both the
   standard parameters directory and the user parameters directory. If it is
   found in either it will be used. If it is not found at all, an exception
   will be raised. If it is found in both places, an exception will also be
   raised.

   (This behaviour is designed to allow code to supply standard parameters,
   possibly in a read-only directory and for users also to have their own
   parameters in another directory, while not allowing either to take priority
   over the other, so that which parameters are used is unambiguous.)

1. If `name` is set to either of the special values `default` or `defaults`,
   the default values will be used for all parameters, whether those were
   supplied as a Python dictionary or in a TOML file (specified by the
   `defaults` argument).

1. If `name` is not supplied, or is passed as `None`, TOMLParams will look the
   value in an environment variable. That variable defaults to `TOMLPARAMS`,
   but can be set by setting the argument `env_var` when instantiating a
   `TOMLParams` object. If this environment variable is set to `foo`,
   `foo.toml` will be searched for in both parameters directories exactly as if
   it had been provided as the value of `name`.

   THe environment variable is particularly convenient when several programs
   need to share a set of parameters. Most commonly, the environment variable
   will be specified on the command line before the Python command, e.g.

   ```sh
   TOMLPARAMS=bar python simulate.py
   ```

   if the Python program using `TOMLParams` is `simulate.py`. Alternatively, a
   value may be export a shell start-up file, or in a script, using
   `export TOMLPARAMS=bar`.

1. If `name` is not supplied, and the relevant environment variable is not set,
   the value of the argument `base_params_dir` will be used; this defaults to
   `base`.

### Idiomatic command-line use

If you want to use `base.toml` as the standard parameters, but allow people to
list the parameters file (stem) on the command line for a program
`simulate.py`, with `~/simparams` as the standard parameters directory, and
defaults being read from `defaults.toml` in that directory, the usual procedure
would be to use code like this:

```python
import sys
from tomlparams import TOMLParams

class Simulate:
    def __init__(params, ...)


if __name__ == '__main__:
    name = sys.argv[1] if len(sys.argv) > 1 else 'base'
    params = TOMLParams('defaults.toml', name, params_name='simparams')
    sim = Simulate(params, ...)

```

## Environment Variables

As noted above, there are two environment variables that can affect the
behaviour of TOMLParams.

- If the `name` argument is not passed to`TOMLParams` (or is passed as `None`)
  the environment variable `TOMLPARAMS` will be consulted (by default). The
  name of the environment variable to consult can be changed by passing a
  different value for `env_var`.

- Any value for the variable `check_types` can be overridden by setting the
  environment variable `TOMLPARAMSCHECKING` to `warn`, `error` or `off`. A
  variable other than `TOMLPARAMSCHECKING` can be specified using the argument
  `type_check_env_var` when initializing `TOMLParams`.

## Type Checking

Type checking is performed against the types of any values present in the
passed-in `defaults`. Three levels of action are configurable:

- `WARN` (default) — a warning is sent to `stderr` but processing continues)
- `ERROR` — processing stops. All type-checking and key-checking errors are
  collected and reported before exit
- `OFF` — no type checking. (Useful when using polymorphic parameters.)

Type checking of any collections (e.g. `list`, `set` and `tuple`) present in
`defaults` is also performed and the selected action taken if a type appears in
a TOML array that is not present in the corresponding collection in the
defaults.

Action on a type checking mismatch can be configured in two ways:

- Via the environment variable specified by the `type_check_env_var` setting
  (defaults to `TOMLPARAMSCHECKING`) with allowed levels `warn`, `error`, and
  `off`.
- Via the `check_types` setting.

The environment variable takes precedence over the setting where set.

## Command line tool tomlparams

As part of installing the TOMLParams library, a command line tool called
tomlparams is made available. This provides a few functions, the most important
of which is the ability to copy usage examples to your current working
directory.

Running the command by itself prints usage information:

```bash
$ tomlparams
TOMLParams

USAGE:
    tomlparams help      --- show this message
    tomlparams version   --- report version number
    tomlparams examples  --- copy the examples to ./tomlparams_examples

Documentation: https://tomlparams.readthedocs.io/
Source code:   https://github.com/itsbigspark.com/tomlparams
Website:       https://tomlparams.com

Installation:

    python -m pip install -U tomlparams

```

The examples can be copied as follows:

```sh
$ pwd
/home/itsbigspark/tomlparams

$ tomlparams examples
Examples copied to /home/itsbigspark/tomlparams/tomlparams_examples.
```

The `readme` subdirectory of the resulting `tomlparams_examples` contains all
the examples from this `README.md` file.

## Documentation and API Help

The documentation for `tomlparams` is available at
[tomlparams.readthedocs.io](https://tomlparams.readthedocs.io). More detailed
help on all the arguments available when initializing `TOMLParams` is available
from the documentation, and also from the help system within Python using:

```python
>>> import tomlparams
>>> help(tomlparams.TOMLParams)
```
