import logging
import os
import shutil
import sys

from tomlparams import __version__
from tomlparams.utils import error

DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(DIR, "examples")


USAGE = """TOMLParams

USAGE:
    tomlparams help      --- show this message
    tomlparams version   --- report version number
    tomlparams examples  --- copy the examples to ./tomlparams_examples

Documentation: https://tomlparams.readthedocs.io/
Source code:   https://github.com/itsbigspark.com/tomlparams
Website:       https://tomlparams.com

Installation:

    python -m pip install -U tomlparams
"""


def main() -> None:
    args: list[str] = sys.argv
    if len(args) < 2:
        print(USAGE)
    else:
        cmd = args[1].lower()
        if cmd in ("help", "--help", "-h"):
            print(USAGE)
        elif cmd in ("version", "--version", "-v"):
            print(__version__)
        elif cmd == "examples":
            dest_dir: str = os.path.abspath(".")
            dest_path: str = os.path.join(dest_dir, "tomlparams_examples")
            shutil.copytree(
                EXAMPLES_DIR,
                dest_path,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            print(f"Examples copied to {dest_path}.")
        else:
            print(f"*** Unknown command: {' '.join(args)}\n")
            print(USAGE, file=sys.stderr)
            error(f"Unknown command: {cmd}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
