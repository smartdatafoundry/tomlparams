import os
import shutil
import sys

from tomlparams import __version__



DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(DIR)
EXAMPLES_DIR = os.path.join(PARENT_DIR, 'examples')
TEST_DIR = os.path.join(PARENT_DIR, 'tests')
print(f'DIR: {DIR}')
print(f'PARENT_DIR: {PARENT_DIR}')
print(f'TEST_DIR: {TEST_DIR}')

sys.path.append(TEST_DIR)
from test_tomlparams import TestTOMLParams


HELP = '''TOMLParams

USAGE:
    tomlparams help      --- show this message
    tomlparams version   --- report version number
    tomlparams examples  --- copy the examples to ./tomlparams_examples
    tomlparams test      --- run the tomlparams tests

Source: https://github.com/smartdatafoundry.com/tomlparams
Documentation: https://tomlparams.readthedocs.io/

Installation:

    python -m pip install -U tomlparams
'''



def main(args):
    if len(args) < 1:
        print(HELP)
        sys.argv(0)
    cmd = args[1].lower()
    if cmd in ('help', '--help', '-h'):
        print(HELP)
    elif cmd in ('version', '--version', '-v'):
        print(__version__)
    elif cmd == 'examples':
        dest_dir = os.path.abspath('.')
        dest_path = os.path.join(dest_dir, 'tomlparams_examples')
        shutil.copytree(EXAMPLES_DIR, dest_path)
        print(f'Examples copied to {dest_path}.')
    elif cmd == 'test':
        from tdda.referencetest import ReferenceTestCase
        ReferenceTestCase.main()


if __name__ == '__main__':
    main(sys.srgv)
