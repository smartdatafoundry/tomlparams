# XParams
## TOML-based parameter files made better


[![XParams tests](https://github.com/gofcoe/xparams/actions/workflows/tests.yml/badge.svg)](https://github.com/gofcoe/xparams/actions/workflows/tests.yml)

# Usage
```python
XParams(
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
)
```

# Defaults


# Hierarchy
TOMLs handled by `XParams` differ from standard TOMLs via the addition of an `include` keyword with
special meaning: 

# Type checking

# Key checking