"""
Tests for ndo.print_todos.py
"""
# ruff: noqa: S101
# pylint: disable=missing-function-docstring

import pytest

from ndo.print_todos import (
    SublistItems,
    _add_ellipsis,  # type: ignore[reportPrivateUsage]
    _color_to_ansi,  # type: ignore[reportPrivateUsage]
    _DisplayText,  # type: ignore[reportPrivateUsage]
    _get_bullet,  # type: ignore[reportPrivateUsage]
    _get_checkmark,  # type: ignore[reportPrivateUsage]
    _get_display_strings,  # type: ignore[reportPrivateUsage]
    _get_enumeration_info,  # type: ignore[reportPrivateUsage]
    make_printable_sublist,
)
from ndo.todo import Todo


@pytest.mark.parametrize(
    ("indent_level", "expected"),
    [(0, "•"), (2, "◦"), (4, "▪"), (6, "▫"), (8, "•")],
)
def test_get_bullet(indent_level: int, expected: str) -> None:
    assert _get_bullet(indent_level) == expected


@pytest.mark.parametrize(("simple", "expected"), [(True, "X"), (False, "✓")])
def test_get_checkmark(simple: bool, expected: str) -> None:  # noqa: FBT001
    assert _get_checkmark(simple) == expected


@pytest.mark.parametrize(
    ("simple_boxes", "string", "prefix_len", "max_length", "expected"),
    [
        # SIMPLE_BOXES = False (unicode "…")
        (False, "Hello", 0, 5, "Hello"),
        (False, "Hello", 2, 7, "Hello"),
        (False, "Hello world", 0, 8, "Hello w…"),
        (False, "Hello world", 2, 10, "Hello w…"),
        (False, "abcdefg", 3, 7, "abc…"),
        (False, "abc", 0, 2, "a…"),
        # SIMPLE_BOXES = True (ascii "...")
        (True, "Hello", 0, 5, "Hello"),
        (True, "Hello", 2, 7, "Hello"),
        (True, "Hello world", 0, 9, "Hello ..."),
        (True, "Hello world", 2, 11, "Hello ..."),
        (True, "abcdefg", 3, 8, "ab..."),
        (True, "abc", 0, 2, "ab..."),
    ],
)
def test_add_ellipsis(  # noqa: PLR0913
    monkeypatch: pytest.MonkeyPatch,
    simple_boxes: bool,  # noqa: FBT001
    string: str,
    prefix_len: int,
    max_length: int,
    expected: str,
) -> None:
    monkeypatch.setattr("ndo.print_todos.SIMPLE_BOXES", simple_boxes)
    result = _add_ellipsis(string, prefix_len, max_length)
    assert result == expected


def test_make_printable_sublist_short_list() -> None:
    lst = list(range(3))
    result = make_printable_sublist(5, lst, 1)
    assert isinstance(result, SublistItems)
    assert result.slice == lst


def test_make_printable_sublist_windowed() -> None:
    lst = list(range(20))
    result = make_printable_sublist(5, lst, 10)
    assert isinstance(result.slice, list)
    slice_len = 5
    assert len(result.slice) <= slice_len


@pytest.mark.parametrize(
    ("rel", "abs_", "highlight", "expected"),
    [
        (1, 2, range(1, 3), str(3).ljust(2) + " "),
        (2, 3, range(4, 6), str(4).rjust(2) + " "),
    ],
)
def test_get_enumeration_info(
    rel: int,
    abs_: int,
    highlight: range,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ndo.print_todos.ENUMERATE", True)
    monkeypatch.setattr("ndo.print_todos.RELATIVE_ENUMERATE", False)
    result = _get_enumeration_info(rel, abs_, 2, highlight)
    assert result == expected


@pytest.mark.parametrize("color", [1, 2, 3, 4, 5, 6, 7])
def test_color_to_ansi_valid(color: int) -> None:
    ansi = _color_to_ansi(color)
    assert ansi.startswith("\u001b[3")


def test_color_to_ansi_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid color code: 8"):
        _color_to_ansi(8)


def test_get_display_strings_returns_display_text() -> None:
    todo = Todo("- Hello")
    result = _get_display_strings(todo, False, "1 ", 80)  # noqa: FBT003
    assert isinstance(result, _DisplayText)
    assert result.prefix.startswith("1 ")
    assert "Hello" in result.text
