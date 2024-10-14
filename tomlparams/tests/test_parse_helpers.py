import os
import unittest

from tomlparams.parse_helpers import to_saveable_object
from tomlparams.tomlparams import TOMLParams

THISDIR = os.path.dirname(os.path.abspath(__file__))
XDIR = os.path.join(THISDIR, 'testdata')
EXPECTEDDIR = os.path.join(THISDIR, 'testdata', 'expected')


class TestParseHelpers:
    def test_to_saveable_object(self) -> None:
        defaults = {
            'a': 1,
            'b': 'two',
            'c': [1, 2, 3],
            'd': [{'e': 4, 'f': ['five', 5]}],
        }
        params = TOMLParams(
            defaults=defaults,
            name='saveable',
            standard_params_dir=EXPECTEDDIR,
        )
        params_dict = {
            k: v for k, v in params.__dict__.items() if k in defaults
        }
        # as stated in saveable.tom;
        expected_saveable_object = {
            'a': 1,
            'b': 'two',
            'c': [1, 2, 3],
            'd': [{'e': 4, 'f': ['five', 6]}, {'e': 4, 'f': [7]}],
        }
        assert (
            to_saveable_object(params_dict, defaults)
            == expected_saveable_object
        )


if __name__ == '__main__':
    unittest.main()
