import os
import shutil
import sys
import unittest

from tomlparams import __version__


DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(DIR)
EXAMPLES_DIR = os.path.join(PARENT_DIR, 'examples')


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
            print(__version__)
        elif cmd == 'examples':
            dest_dir = os.path.abspath('.')
            dest_path = os.path.join(dest_dir, 'tomlparams_examples')
            shutil.copytree(EXAMPLES_DIR, dest_path)
            print(f'Examples copied to {dest_path}.')
        elif cmd == 'test':
            try:
                from tomlparams.tests.test_tomlparams import TestTOMLParams
            except:
                print('To run the tests, please pip install tdda',
                      file=sys.stderr)
                sys.exit(1)
            suite = unittest.TestSuite()
            testloader = unittest.TestLoader()
            s = testloader.loadTestsFromTestCase(TestTOMLParams)
            suite.addTest(s)
            tester = unittest.TextTestRunner()
            tester.run(suite)

        else:
            print(f'*** Unknown command: {" ".join(args)}\n')
            print(USAGE, file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
