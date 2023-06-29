import os
import shutil
import sys
import unittest
from importlib.metadata import version


DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(DIR, 'examples')


USAGE = '''TOMLParams

USAGE:
    tomlparams help      --- show this message
    tomlparams version   --- report version number
    tomlparams examples  --- copy the examples to ./tomlparams_examples
    tomlparams test      --- run the tomlparams tests

Documentation: https://tomlparams.readthedocs.io/
Source code:   https://github.com/smartdatafoundry.com/tomlparams
Website:       https://tomlparams.com

Installation:

    python -m pip install -U tomlparams
'''



def main():
    args = sys.argv
    if len(args) < 2:
        print(USAGE)
    else:
        cmd = args[1].lower()
        if cmd in ('help', '--help', '-h'):
            print(USAGE)
        elif cmd in ('version', '--version', '-v'):
            print(version('tomlparams'))
        elif cmd == 'examples':
            dest_dir = os.path.abspath('.')
            dest_path = os.path.join(dest_dir, 'tomlparams_examples')
            shutil.copytree(EXAMPLES_DIR, dest_path, ignore=shutil.ignore_patterns('__pycache__'))
            print(f'Examples copied to {dest_path}.')
        elif cmd == 'test':
            from tomlparams.tests.test_tomlparams import TestTOMLParams
            suite = unittest.TestSuite()
            test_loader = unittest.TestLoader()
            s = test_loader.loadTestsFromTestCase(TestTOMLParams)
            suite.addTest(s)
            tester = unittest.TextTestRunner(verbosity=2)
            tester.run(suite)

        else:
            print(f'*** Unknown command: {" ".join(args)}\n')
            print(USAGE, file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
