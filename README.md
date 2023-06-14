# TOMLParams

[![TOMLParams tests](https://github.com/gofcoe/xparams/actions/workflows/tests.yml/badge.svg)](https://github.com/gofcoe/xparams/actions/workflows/tests.yml)

TOML-based parameter files made better

## Key features

 * Designed to make it easy to externalize parameters one or more TOML files,
   load them into Python, with defaulting, parameter name checking and optional
   type checking.
 * Parameters available through attribute lookup or dictionary lookup
 * Supports hierarchical file inclusion and default values
 * Support for choosing parameter files using environment variables or setting
   from API
 * Default values can be specified in code (as Python dictionaries) or in a TOML file
 * Full support for hierarchical values, still with attribute and dictionary lookup
 * Support for writing consolidated parameters as TOML after hierarchical inclusion
 * Can be subclassed and other attributes can be used without affecting TOML file writing.



## Installation

```
pip install -U git+ssh://git@github.com/gofcoe/tomlparams.git
```

# Sample Usage

TOMLParams requires a toml file and a dictionary with defaults values.
If we have a file called `myrun.toml` with the following content:

```
[section.subsection1]
param1 = 1234
param4 = [1, 3, 4]
```

```python
from datetime import date
from tomlparams import TOMLParams
from pprint import pprint

defaults = {
    'param': 'myparam',
    'section':{
        'subsection1': {
            'param1': 500,
            'param2': True,
            'param3': 'foo'
            'param4': [1, 2, 3]
        },
        'subsection2': {
            'param1': False,
            'param2': 2.0,
            'param3': date(2023, 6, 3)
            'param4': -1
            'param5': {
                'var1': 1,
                'var2': '2'
                }
        }
    }
}


params = TOMLParams(defaults=defaults, name='myrun', user_params_dir='.')

print(params.param)
>> myparam
print(params.section.subsection1.param1)
>>1234
print(params.section.subsection1.param4)
>>[1, 3, 4]
print(params.section.subsection2.param5.var1)
>>1
```
```
pprint(params.section.subsection2)
>>ParamsGroup(
			param1: False,
			param2: 2.0,
			param3: 2023-06-03,
			param4: -1,
			param5: ParamsGroup(
				var1: 1,
				var2: 2
			)
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

* `IGNORE` - not recommended
* `WARN` (default) - a warning is sent to `stderr` but processing
continues)
* `ERROR` - processing stops, but all type checking and key checking error are collected
   and shown before exit

Type checking of any collections (e.g. `list`, `set` and `tuple`)
present in `defaults` is also performed and the selected action taken
if a type appears in a TOML array that is not present in the
corresponding collection in defaults.

Action on a type checking mismatch can be configure in two ways:

* Via the environment variable specified by the
`type_check_env_var` setting (defaults to `XPARAMSCHECKING`) with allowed levels: `ignore`,
`warn` and `error`
* Via the `check_types` setting

The environment variable takes precedence over the setting where set.

# Key checking

Key checking as described above is also performed - any key present at
any point in the final consolidated input TOML that is not present in
`defaults` raises an error. Key checking errors are collected together
with type checking errors and warnings and show before exit.