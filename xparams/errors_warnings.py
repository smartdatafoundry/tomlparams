import sys
from typing import NoReturn


def error(*msg, exit_code=1) -> NoReturn:
    print("*** ERROR:", *msg, file=sys.stderr)
    sys.exit(exit_code)


def warn(*msg):
    print("*** WARNING:", *msg, file=sys.stderr)
