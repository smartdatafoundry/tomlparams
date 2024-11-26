import unittest

from tomlparams.utils import warn
from parameterized import parameterized


class TestUtils(unittest.TestCase):

    @parameterized.expand(
        [
            ("This is a warning",),
            ("This", "is", "a", "warning"),
            ("This is a warning", "and this is another warning"),
        ]
    )
    def test_warn(self, *msg):
        with self.assertWarns(UserWarning):
            warn(*msg)
