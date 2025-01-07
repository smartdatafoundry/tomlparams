from __future__ import annotations

import datetime
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any

import tomli
from parameterized import parameterized

from tomlparams import TOMLParams
from tomlparams.params_group import ParamsGroup
from tomlparams.tests.captureoutput import CaptureOutput
from tomlparams.utils import TOMLParamsError, concatenate_keys

THISDIR = os.path.dirname(os.path.abspath(__file__))
XDIR = os.path.join(THISDIR, 'testdata')
EXPECTEDDIR = os.path.join(THISDIR, 'testdata', 'expected')


class TestTOMLParams(unittest.TestCase):
    def setUp(self) -> None:
        self.co = CaptureOutput(stream='stderr')

    def tearDown(self) -> None:
        self.co.restore()

    def assertFileCorrect(self, path: str | Path, refpath: str | Path) -> None:
        with open(path) as f:
            orig = f.read()
        with open(refpath) as f:
            ref = f.read()
        self.assertEqual(orig, ref)

    def test_write_consolidated_toml_unchanged_from_defaults(self) -> None:
        # Tests writing of consolidated TOML file when
        # uk_retirees.toml exists but is empty, so what's written
        # is in fact the defaults.
        defaults = {
            'n': 1,
            'f': 1.5,
            's': 'tomlparams',
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
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'in_params.toml')

        params = TOMLParams(
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

    def test_write_consolidated_toml_with_hierarchy(self) -> None:
        # Tests writing of consolidated TOML file when
        # one.toml and two.toml both exist.
        # two.toml includes one.toml and they have some conflicts
        defaults: dict[str, Any] = {
            'n': 1,
            'f': 1.5,
            's': 'tomlparams',
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
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'in_params.toml')

        params = TOMLParams(
            defaults=defaults,
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

    def test_write_consolidated_toml_list_hierarchy(self) -> None:
        # Tests writing of consolidated TOML file when
        # three.toml, four.toml and five.toml all exist.
        # three.toml includes four.toml and five.toml in order
        # with some conflicts
        defaults: dict[str, Any] = {
            'n': 1,
            'f': 1.5,
            's': 'tomlparams',
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
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'in_params.toml')

        params = TOMLParams(
            defaults,
            name='three',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )
        params.write_consolidated_toml(consolidated_path, verbose=False)
        self.assertFileCorrect(
            consolidated_path, os.path.join(EXPECTEDDIR, 'three.toml')
        )

        expected = defaults  # Same object, but being updated
        expected['s'] = 'three'
        expected['subsection']['n'] = 5
        expected['section2']['n'] = 4
        with open(consolidated_path, 'rb') as f:
            loaded_params = tomli.load(f)
        self.assertEqual(loaded_params, expected)

    def test_self_inclusion(self) -> None:
        defaults: dict[str, Any] = {
            'n': 1,
            'f': 1.5,
            's': 'tomlparams',
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
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'in_params.toml')

        params = TOMLParams(
            defaults,
            name='self',
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )
        params.write_consolidated_toml(consolidated_path, verbose=False)
        self.assertFileCorrect(
            consolidated_path, os.path.join(EXPECTEDDIR, 'self.toml')
        )

        expected = defaults  # Same object, but being updated
        expected['s'] = 'self'
        expected['subsection']['n'] = 1
        expected['section2']['n'] = 1
        with open(consolidated_path, 'rb') as f:
            loaded_params = tomli.load(f)
        self.assertEqual(loaded_params, expected)

    def test_write_consolidated_toml_deep_equals(self) -> None:
        defaults: dict[str, Any] = {
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
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        outdir = tempfile.mkdtemp()
        consolidated_path = os.path.join(outdir, 'in_params.toml')

        params = TOMLParams(
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

    def test_userparams_not_in_stdparams(self) -> None:
        defaults: dict[str, Any] = {'x': 10}
        stddir: str = os.path.join(XDIR, 'tomlparams')
        userdir: str = os.path.join(XDIR, 'usertomlparams')
        outdir: str = tempfile.mkdtemp()
        consolidated_path: str = os.path.join(outdir, 'in_params.toml')

        params = TOMLParams(
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

    def test_reserved_user_raises(self) -> None:
        defaults: dict[str, Any] = {'x': 10}
        stddir: str = os.path.join(XDIR, 'tomlparams')
        userdir: str = os.path.join(XDIR, 'usertomlparams')
        naughty_toml: str = os.path.join(XDIR, 'tomlparams', 'user_only.toml')
        open(naughty_toml, "wt").close()

        def create_params() -> None:
            TOMLParams(
                defaults,
                name='user_only',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
            )

        try:
            self.assertRaises(ValueError, create_params)
            with self.assertRaises(ValueError) as cm:
                create_params()
                expected_error = (
                    '*** ERROR: path'
                    f' {THISDIR}/testdata/tomlparams/user_only.toml is'
                    ' reserved for user TOML files, but exists in'
                    ' standardparams.\n'
                )
                self.assertEqual(str(cm.exception), expected_error)
        finally:
            os.remove(naughty_toml)

    def test_reserved_u_raises(self) -> None:
        defaults = {'x': 10}
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        naughty_toml = os.path.join(XDIR, 'tomlparams', 'u_only.toml')
        open(naughty_toml, "wt").close()

        def create_params() -> None:
            TOMLParams(
                defaults,
                name='u_only',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
            )

        try:
            self.assertRaises(ValueError, create_params)
            with self.assertRaises(ValueError) as cm:
                create_params()
                expected_error = (
                    '*** ERROR: path'
                    f' {THISDIR}/testdata/tomlparams/u_only.toml is reserved'
                    ' for user TOML files, but exists in standardparams.\n'
                )
                self.assertEqual(str(cm.exception), expected_error)
        finally:
            os.remove(naughty_toml)

    def test_default_env_param_used_no_name(self) -> None:
        stddir: str = os.path.join(XDIR, 'tomlparams')
        userdir: str = os.path.join(XDIR, 'usertomlparams')
        outdir: str = tempfile.mkdtemp()
        consolidated_path: str = os.path.join(outdir, 'in_params.toml')
        defaults: dict[str, Any] = {
            's': 'none',
            'subsection': {'n': 0},
            'section2': {'n': 0},
        }

        self.assertIsNone(os.environ.get('TOMLPARAMS'))
        os.environ['TOMLPARAMS'] = 'one'

        params = TOMLParams(
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

        os.environ.pop('TOMLPARAMS', None)

    def test_defined_env_param_used_no_name(self) -> None:
        stddir: str = os.path.join(XDIR, 'tomlparams')
        userdir: str = os.path.join(XDIR, 'usertomlparams')
        outdir: str = tempfile.mkdtemp()
        consolidated_path: str = os.path.join(outdir, 'in_params.toml')
        defaults: dict[str, Any] = {
            's': 'none',
            'subsection': {'n': 0},
            'section2': {'n': 0},
        }

        self.assertIsNone(os.environ.get('MYTOMLPARAMS'))
        os.environ['MYTOMLPARAMS'] = 'one'

        params = TOMLParams(
            defaults,
            standard_params_dir=stddir,
            user_params_dir=userdir,
            env_var='MYTOMLPARAMS',
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

        os.environ.pop('MYTOMLPARAMS', None)

    def test_type_checking_root_level_warning(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        defaults = {"not_there_1": 2, "z": 4}
        with self.assertWarns(Warning):
            TOMLParams(
                defaults,
                name='type_check_root_level',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
                check_types=TOMLParams.WARN,
            )

    def test_type_checking_shallow_warning(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        defaults = {"s": "one", "section": {"subsection": {"n": "one"}}}
        with self.assertWarns(Warning):
            TOMLParams(
                defaults,
                name='type_check_shallow',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
                check_types=TOMLParams.WARN,
            )

    def test_type_checking_list(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        defaults = {"s": ["one", 2]}
        with self.assertWarns(Warning):
            TOMLParams(
                defaults,
                name='type_check_list',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
                check_types=TOMLParams.WARN,
            )

    def test_type_checking_deep_level_warning(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
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
        with self.assertWarns(Warning):
            TOMLParams(
                defaults,
                name='type_check_deeper_level',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
                check_types=TOMLParams.WARN,
            )

    def test_date_type_checking_warning(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        defaults = {
            "not_there_1": 2,
            "date": '1970-01-01',
        }
        with self.assertWarns(Warning):
            TOMLParams(
                defaults,
                name='type_check_dates',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
                check_types=TOMLParams.WARN,
            )

    def test_type_checking_root_level_error(self) -> None:
        stddir: str = os.path.join(XDIR, 'tomlparams')
        userdir: str = os.path.join(XDIR, 'usertomlparams')
        defaults: dict[str, Any] = {"not_there_1": 2, "z": 4}

        def create_params() -> None:
            TOMLParams(
                defaults,
                name='type_check_root_level',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
                check_types=TOMLParams.ERROR,
            )

        self.assertRaises(
            TOMLParamsError,
            create_params,
        )

    def test_type_checking_shallow_error(self) -> None:
        stddir: str = os.path.join(XDIR, 'tomlparams')
        userdir: str = os.path.join(XDIR, 'usertomlparams')
        defaults: dict[str, Any] = {
            "s": "one",
            "section": {"subsection": {"n": "one"}},
        }

        def create_params() -> None:
            TOMLParams(
                defaults,
                name='type_check_shallow',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
                check_types=TOMLParams.ERROR,
            )

        self.assertRaises(
            TOMLParamsError,
            create_params,
        )

    def test_bad_key_shallow_error(self) -> None:
        stddir: str = os.path.join(XDIR, 'tomlparams')
        userdir: str = os.path.join(XDIR, 'usertomlparams')
        defaults: dict[str, Any] = {
            "s": 1,
            "section": {"subsection": {"m": "two"}},
        }

        def create_params() -> None:
            TOMLParams(
                defaults,
                name='type_check_shallow',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
                check_types=TOMLParams.ERROR,
            )

        self.assertRaises(
            TOMLParamsError,
            create_params,
        )

    def test_type_checking_bad_key_shallow_error(self) -> None:
        stddir: str = os.path.join(XDIR, 'tomlparams')
        userdir: str = os.path.join(XDIR, 'usertomlparams')
        defaults: dict[str, Any] = {
            "s": "one",
            "section": {"subsection": {"m": "two"}},
        }

        def create_params() -> None:
            TOMLParams(
                defaults,
                name='type_check_shallow',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
                check_types=TOMLParams.ERROR,
            )

        self.assertRaises(
            TOMLParamsError,
            create_params,
        )

    def test_type_checking_warn_bad_key_shallow_error(self) -> None:
        stddir: str = os.path.join(XDIR, 'tomlparams')
        userdir: str = os.path.join(XDIR, 'usertomlparams')
        defaults: dict[str, Any] = {
            "s": "one",
            "section": {"subsection": {"m": "two"}},
        }

        def create_params() -> None:
            TOMLParams(
                defaults,
                name='type_check_shallow',
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
                check_types=TOMLParams.WARN,
            )

        self.assertRaises(
            TOMLParamsError,
            create_params,
        )

    def test_type_check_env_var_fail(self) -> None:
        stddir: str = os.path.join(XDIR, 'tomlparams')
        userdir: str = os.path.join(XDIR, 'usertomlparams')
        defaults: dict[str, Any] = {
            's': 'none',
            'subsection': {'n': 0},
            'section2': {'n': 0},
        }

        self.assertIsNone(os.environ.get('TOMLPARAMSCHECKING'))
        os.environ['TOMLPARAMSCHECKING'] = 'pp'

        def create_params() -> None:
            TOMLParams(
                defaults,
                standard_params_dir=stddir,
                user_params_dir=userdir,
                env_var='MYTOMLPARAMS',
                verbose=False,
            )

        self.assertRaises(
            TOMLParamsError,
            create_params,
        )
        os.environ.pop('TOMLPARAMSCHECKING', None)

    def test_concatenate_keys(self) -> None:
        d = {'a': {'b': 1, 'c': 2}, 'd': 3}
        expected = (('a.b', 1), ('a.c', 2), ('d', 3))
        self.assertEqual(tuple(concatenate_keys(d)), expected)

    def test_read_defaults_as_directory(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        defaults_as_dir = os.path.join(stddir, 'defaults_as_dir')
        defaults_as_file = os.path.join(stddir, 'defaults_as_file')
        params_default_as_dir = TOMLParams(
            defaults_as_dir,
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )
        params_default_as_file = TOMLParams(
            defaults_as_file,
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )
        self.assertEqual(params_default_as_dir, params_default_as_file)

    @parameterized.expand(['human', 'animals', 'fungi'])  # type: ignore [misc]
    def test_content_defaults_as_directory(
        self, default_primary_key: str
    ) -> None:
        # primary keys of default as file
        # primary_keys = ['human', 'animals', 'fungi']
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        defaults_as_dir = os.path.join(stddir, 'defaults_as_dir')
        defaults_as_file = os.path.join(stddir, 'defaults_as_file')
        params_default_as_dir = TOMLParams(
            defaults_as_dir,
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )
        params_default_as_file = TOMLParams(
            defaults_as_file,
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )
        d_as_dir = set(
            concatenate_keys(
                params_default_as_dir[default_primary_key].as_dict()
            )
        )
        d_as_file = set(
            concatenate_keys(
                params_default_as_file[default_primary_key].as_dict()
            )
        )
        self.assertEqual(d_as_dir, d_as_file)

    def test_read_defaults_as_directory_repeated_keys(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')
        defaults_as_dir_repeated_keys = os.path.join(
            stddir, 'defaults_as_dir_repeated_keys'
        )
        self.assertRaises(
            KeyError,
            lambda: TOMLParams(
                defaults_as_dir_repeated_keys,
                standard_params_dir=stddir,
                user_params_dir=userdir,
                verbose=False,
            ),
        )

    def test_table_array(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')

        params = TOMLParams(
            "table_array_defaults",
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )

        for array in params['array']:
            self.assertIsInstance(array, ParamsGroup)

    def test_table_array_overwriting_same_length(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')

        params = TOMLParams(
            defaults="table_array_defaults",
            name="table_array_same_length",
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )

        self.assertEqual(len(params['array']), 2)

    def test_table_array_overwriting_longer(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')

        params = TOMLParams(
            defaults="table_array_defaults",
            name="table_array_longer",
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )

        self.assertEqual(len(params['array']), 3)

    def test_table_array_overwriting_shorter(self) -> None:
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')

        params = TOMLParams(
            defaults="table_array_defaults",
            name="table_array_shorter",
            standard_params_dir=stddir,
            user_params_dir=userdir,
            verbose=False,
        )

        self.assertEqual(len(params['array']), 1)

    @parameterized.expand(  # type: ignore [misc]
        [
            ["a", 2],  # present in defaults
            [
                "b",
                3,  # not present, but top level key currently works (should it?)
            ],
            ["nested.a", 4],  # nested key
        ]
    )
    def test_set_item(self, key: str, value: Any) -> None:
        defaults: dict[str, Any] = {
            'a': 1,
            "nested": {
                "a": 1,
                "b": 2,
            },
        }
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')

        params = TOMLParams(
            defaults=defaults,
            name='base',
            standard_params_dir=stddir,
            user_params_dir=userdir,
        )
        params[key] = value
        assert params[key] == value

    def test_set_item_raises(self) -> None:
        """Trying to set a nested key that doesn't exist should raise a
        KeyError."""
        defaults: dict[str, Any] = {
            'a': 1,
        }
        stddir = os.path.join(XDIR, 'tomlparams')
        userdir = os.path.join(XDIR, 'usertomlparams')

        params = TOMLParams(
            defaults=defaults,
            name='base',
            standard_params_dir=stddir,
            user_params_dir=userdir,
        )

        with self.assertRaises(KeyError):
            params['b.c'] = 2


if __name__ == '__main__':
    unittest.main()
