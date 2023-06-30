"""
Utils
=====
"""
import sys
from typing import NoReturn

import tomli


def error(*msg, exit_code=1) -> NoReturn:
    print("*** ERROR:", *msg, file=sys.stderr)
    sys.exit(exit_code)


def warn(*msg):
    print("*** WARNING:", *msg, file=sys.stderr)


def nvl(v, default):
    return default if v is None else v


def load_toml(path):
    """
    Protected TOML load using tomli that reports what the file
    was if parsing fails (and then re-raises the exception).
    """
    with open(path, 'rb') as f:
        try:
            return tomli.load(f)
        except Exception:
            print(
                f'\n***\n*** Problem parsing {path}:\n***\n', file=sys.stderr
            )
            raise
