from __future__ import annotations

import unittest
from typing import Any

from parameterized import parameterized

from tomlparams.utils import convert_dicts_to_lists, nest_dict, warn


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


class TestConvertDictsToLists(unittest.TestCase):
    @parameterized.expand(  # type: ignore [misc]
        [
            (
                {0: {"a": 1}, 1: {"b": 2}, 2: {"c": 3}},
                [{"a": 1}, {"b": 2}, {"c": 3}],
            ),
            ({}, {}),
            ({"a": 1, "b": 2}, {"a": 1, "b": 2}),
            (
                {"a": {"b": {"c": 1}}, "d": {"e": {"f": 2}}},
                {"a": {"b": {"c": 1}}, "d": {"e": {"f": 2}}},
            ),
            (
                [{"a": {"b": {"c": 1}}, "d": {"e": {"f": 2}}}],
                [{"a": {"b": {"c": 1}}, "d": {"e": {"f": 2}}}],
            ),
            (
                {
                    0: {0: {"weight": 1}},
                    1: {1: {"weight": 2}},
                    2: {0: {"weight": 3}},
                    3: {1: {"weight": 4}},
                },
                [
                    [{"weight": 1}],
                    [{"weight": 2}],
                    [{"weight": 3}],
                    [{"weight": 4}],
                ],
            ),
        ]
    )
    def test_convert_dicts_to_lists(
        self,
        input_dict: dict[str, Any] | list[Any],
        expected_output: dict[str, Any] | list[Any],
    ) -> None:
        self.assertEqual(
            convert_dicts_to_lists(d=input_dict), second=expected_output
        )


class TestNestDict(unittest.TestCase):
    @parameterized.expand(  # type: ignore [misc]
        [
            (
                {
                    "a.matter.0.0.weight": 1,
                    "a.matter.0.1.weight": 2,
                    "a.matter.1.0.weight": 3,
                    "a.matter.1.1.weight": 4,
                },
                {
                    "a": {
                        "matter": [
                            [{"weight": 1}, {"weight": 2}],
                            [{"weight": 3}, {"weight": 4}],
                        ]
                    }
                },
            ),
        ]
    )
    def test_nest_dict(
        self,
        input_dict: dict[str, Any],
        expected_output: dict[str, Any],
    ) -> None:
        self.assertEqual(nest_dict(input_dict), second=expected_output)
