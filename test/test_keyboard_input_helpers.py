"""
Tests for keyboard_input_helpers.py
"""
# ruff: noqa: S101
# pylint: disable=missing-function-docstring

from ndo.keyboard_input_helpers import get_executable_args


def test_get_executable_args() -> None:
    assert get_executable_args(
        "a, b",
        {"a": 1, "b": 2, "c": 3},
    ) == [1, 2]
    assert get_executable_args(
        "a, 1",
        {"a": 1, "b": 2, "c": 3},
    ) == [1, 1]
    assert get_executable_args(
        "a, b, c",
        {"a": 1, "b": 2, "c": 3},
    ) == [1, 2, 3]
    assert get_executable_args(
        "",
        {"a": 1, "b": 2, "c": 3},
    ) == [""]
    assert (
        not get_executable_args(
            "None",
            {"a": 1, "b": 2, "c": 3},
        )
    )
    assert get_executable_args(
        "a, b, c",
        {"a": 1, "b": 2},
    ) == [1, 2, "c"]
