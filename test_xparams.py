import datetime
import os
import tempfile
import tomli
from tdda.referencetest import ReferenceTestCase, tag

UGDIR = os.path.dirname(__file__)
XDIR = os.path.join('testdata')
EXPECTEDDIR = os.path.join('testdata', 'expected')

from pyxparams.xparams import XParams


class TestXParams(ReferenceTestCase):
    def test_write_consolidated_toml_unchanged_from_defaults(self):
        # Tests writing of consolidated TOML file when
        # base.toml exists but is empty, so what's written
        # is in fact the defaults.
        defaults = {
            'n': 1,
            'f': 1.5,
            's': 'xparams',
            'd': datetime.datetime(2000, 1, 1, 12, 34, 56),
            'b': True,
            'subsection': {
                'n': 0,
                'pi': 3.14159265,
            },
            'section2': {
                'is_subsec': True,
                'n': 2,
            },
        }
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'params.toml')

        params = XParams(
            defaults,
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )
        params.write_consolidated_toml(consolidated_path, verbose=False)
        self.assertFileCorrect(
            consolidated_path, os.path.join(EXPECTEDDIR, 'unchanged.toml')
        )
        with open(consolidated_path, 'rb') as f:
            loaded_params = tomli.load(f)
        self.assertEqual(loaded_params, defaults)

    def test_write_consolidated_toml(self):
        # Tests writing of consolidated TOML file when
        # one.toml and two.toml both exist.
        # two includes 1 and they have some conflicts
        defaults = {
            'n': 1,
            'f': 1.5,
            's': 'xparams',
            'd': datetime.datetime(2000, 1, 1, 12, 34, 56),
            'b': True,
            'subsection': {
                'n': 0,
                'pi': 3.14159265,
            },
            'section2': {
                'is_subsec': True,
                'n': 2,
            },
        }
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'params.toml')

        params = XParams(
            defaults,
            name='two',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )
        params.write_consolidated_toml(consolidated_path, verbose=False)
        self.assertFileCorrect(
            consolidated_path, os.path.join(EXPECTEDDIR, 'two.toml')
        )
        expected = defaults  # Same object, but being updated
        expected['s'] = 'two'
        expected['subsection']['n'] = 2
        expected['section2']['n'] = 1
        with open(consolidated_path, 'rb') as f:
            loaded_params = tomli.load(f)
        self.assertEqual(loaded_params, expected)

    def test_write_consolidated_toml_deep_equals(self):
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'params.toml')

        defaults = {
            "not_there_1": 2,
            "z": 4,
            "this": {
                "was": {
                    "pretty": {
                        "deep": {
                            "folks": {
                                "x": 1,
                                "y": 3,
                                "not_there_2": 9
                            }
                        }
                    }
                }
            }
        }

        params = XParams(
            defaults,
            name='deep',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )

        params
        # params.write_consolidated_toml(consolidated_path, verbose=False)
        # self.assertFileCorrect(
        #     consolidated_path, os.path.join(EXPECTEDDIR, 'deep.toml')
        # )


if __name__ == '__main__':
    ReferenceTestCase.main()
