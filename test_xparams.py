import datetime
import os
import tempfile
import tomli
from tdda.referencetest import ReferenceTestCase
from pyxparams.captureoutput import CaptureOutput
from pyxparams.xparams import XParams, TypeChecking

UGDIR = os.path.dirname(__file__)
XDIR = os.path.join('testdata')
EXPECTEDDIR = os.path.join('testdata', 'expected')


class TestXParams(ReferenceTestCase):

    def setUp(self):
        self.co = CaptureOutput(stream='stderr')

    def tearDown(self):
        self.co.restore()

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

    def test_write_consolidated_toml_with_hierarchies(self):
        # Tests writing of consolidated TOML file when
        # one.toml and two.toml both exist.
        # two.toml includes one.toml and they have some conflicts
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
        defaults = {
            "not_there_1": 2,
            "z": 4,
            "this": {
                "was": {
                    "pretty": {
                        "deep": {"folks": {"x": 1, "y": 3, "not_there_2": 9}}
                    }
                }
            },
        }
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'params.toml')

        params = XParams(
            defaults,
            name='deep',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )

        params.write_consolidated_toml(consolidated_path, verbose=False)
        self.assertFileCorrect(
            consolidated_path, os.path.join(EXPECTEDDIR, 'deep.toml')
        )

        expected = defaults  # Same object, but being updated
        expected['z'] = 3
        expected['this']['was']['pretty']['deep']['folks']['x'] = 2
        expected['this']['was']['pretty']['deep']['folks']['y'] = 5
        with open(consolidated_path, 'rb') as f:
            loaded_params = tomli.load(f)
        self.assertEqual(loaded_params, expected)


    def test_userparams_not_in_stdparams(self):
        defaults = {
            'x': 10
        }
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'params.toml')

        params = XParams(
            defaults,
            name='user_only',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )

        params.write_consolidated_toml(consolidated_path, verbose=False)
        self.assertFileCorrect(
            consolidated_path, os.path.join(EXPECTEDDIR, 'user_only.toml')
        )

        expected = defaults  # Same object, but being updated
        expected['x'] = 4
        with open(consolidated_path, 'rb') as f:
            loaded_params = tomli.load(f)
        self.assertEqual(loaded_params, expected)


    def test_reserved_user_raises(self):
        defaults = {
            'x': 10
        }
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        naughty_toml = os.path.join(XDIR, 'xparams', 'user_only.toml')
        open(naughty_toml, "wt").close()

        create_params = lambda: XParams(
            defaults,
            name='user_only',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )
        try:
            self.assertRaises(
                SystemExit,
                create_params
            )

            expected_error = (
                '*** ERROR: path testdata/xparams/user_only.toml is reserved for user TOML files, but exists '
                'in standardparams.\n'
            )
            self.assertEqual(str(self.co), expected_error)
        finally:
            os.remove(naughty_toml)

    def test_reserved_u_raises(self):
        defaults = {
            'x': 10
        }
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        naughty_toml = os.path.join(XDIR, 'xparams', 'u_only.toml')
        open(naughty_toml, "wt").close()

        create_params = lambda: XParams(
            defaults,
            name='u_only',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )
        try:
            self.assertRaises(
                SystemExit,
                create_params
            )

            expected_error = (
                '*** ERROR: path testdata/xparams/u_only.toml is reserved for user TOML files, but exists '
                'in standardparams.\n'
            )
            self.assertEqual(str(self.co), expected_error)
        finally:
            os.remove(naughty_toml)

    def test_default_env_param_used_no_name(self):
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'params.toml')
        defaults = {
            's': 'none',
            'subsection': {
                'n': 0
            },
            'section2': {
                'n': 0
            }
        }
        os.environ['XPARAMS'] = 'one'

        params = XParams(
            defaults,
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )

        params.write_consolidated_toml(consolidated_path, verbose=False)
        self.assertFileCorrect(
            consolidated_path, os.path.join(EXPECTEDDIR, 'one.toml')
        )

        expected = defaults
        expected['s'] = 'one'
        expected['subsection']['n'] = 1
        expected['section2']['n'] = 1
        with open(consolidated_path, 'rb') as f:
            loaded_params = tomli.load(f)
        self.assertEqual(loaded_params, expected)

        os.environ.pop('XPARAMS', None)

    def test_defined_env_param_used_no_name(self):
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'params.toml')
        defaults = {
            's': 'none',
            'subsection': {
                'n': 0
            },
            'section2': {
                'n': 0
            }
        }
        os.environ['MYXPARAMS'] = 'one'

        params = XParams(
            defaults,
            standard_params_dir=stddir,
            user_params_dir=userdir,
            env_var='MYXPARAMS',
            verbose=False,
        )

        params.write_consolidated_toml(consolidated_path, verbose=False)
        self.assertFileCorrect(
            consolidated_path, os.path.join(EXPECTEDDIR, 'one.toml')
        )

        expected = defaults
        expected['s'] = 'one'
        expected['subsection']['n'] = 1
        expected['section2']['n'] = 1
        with open(consolidated_path, 'rb') as f:
            loaded_params = tomli.load(f)
        self.assertEqual(loaded_params, expected)

        os.environ.pop('MYXPARAMS', None)

    def test_type_checking_root_level_warning(self):
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        defaults = {"not_there_1": 2, "z": 4}
        params = XParams(
            defaults,
            name='type_check_root_level',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
            check_types=TypeChecking.WARN,
        )
        expected_warning = (
            '*** WARNING  Types mismatch in default and toml '
            'at root level key: z, default_type: <class \'int\'>, '
            'toml_type: <class \'str\'>\n'
        )

        self.assertEqual(str(self.co), expected_warning)


    def test_type_checking_deep_level_warning(self):
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        defaults = {
            "not_there_1": 2,
            "z": 4,
            "this": {
                "was": {
                    "pretty": {
                        "deep": {"folks": {"x": 1, "y": 3, "not_there_2": 9}}
                    }
                }
            },
        }
        params = XParams(
            defaults,
            name='type_check_deeper_level',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
            check_types=TypeChecking.WARN,
        )
        expected_warning = (
            '*** WARNING  Types mismatch in default and toml '
            'at level: this.was.pretty.deep.folks key: x, '
            'default_type: <class \'int\'>, toml_type: <class \'str\'>\n'
        )
        self.assertEqual(str(self.co), expected_warning)


    def test_date_type_checking_warning(self):
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        defaults = {
            "not_there_1": 2,
            "date": '1970-01-01',
        }
        params = XParams(
            defaults,
            name='type_check_dates',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
            check_types=TypeChecking.WARN,
        )
        expected_warning = (
            '*** WARNING  Types mismatch in default and toml '
            'at root level key: date, default_type: <class \'str\'>, '
            'toml_type: <class \'datetime.date\'>\n'
        )
        self.assertEqual(str(self.co), expected_warning)


    def test_type_checking_root_level_error(self):
        stddir = os.path.join(XDIR, 'xparams')
        userdir = os.path.join(XDIR, 'userxparams')
        defaults = {"not_there_1": 2, "z": 4}
        expected_error = (
            '*** ERROR: Types mismatch in default and toml '
            'at root level key: z, default_type: <class \'int\'>, '
            'toml_type: <class \'str\'>\n'
        )
        create_params = lambda: XParams(
            defaults,
            name='type_check_root_level',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
            check_types=TypeChecking.ERROR,
        )
        self.assertRaises(
            SystemExit,
            create_params,
        )
        self.assertEqual(str(self.co), expected_error)


if __name__ == '__main__':
    ReferenceTestCase.main()
