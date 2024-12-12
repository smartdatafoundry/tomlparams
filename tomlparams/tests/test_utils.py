import unittest

from parameterized import parameterized

from tomlparams.utils import warn


class TestUtils(unittest.TestCase):

    @parameterized.expand(
        [
            ("This is a warning",),
            ("This", "is", "a", "warning"),
            ("This is a warning", "and this is another warning"),
        ]
    )  # type: ignore [misc]
    def test_warn(self, *msg: str) -> None:
        with self.assertWarns(UserWarning):
            warn(*msg)
