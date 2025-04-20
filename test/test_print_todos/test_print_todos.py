"""
Tests for ndo.print_todos.py
"""
# ruff: noqa: ANN201, S101
# pylint: disable=missing-function-docstring
# pyright: ignore[reportPrivateUsage]

import pytest

from ndo.print_todos import (
    SublistItems,
    _add_ellipsis,
    _color_to_ansi,
    _DisplayText,
    _get_bullet,
    _get_checkmark,
    _get_display_strings,
    _get_enumeration_info,
    make_printable_sublist,
)
from ndo.todo import Todo


@pytest.mark.parametrize(
    "indent_level, expected",
    [(0, "•"), (2, "◦"), (4, "▪"), (6, "▫"), (8, "•")],
)
def test_get_bullet(indent_level: int, expected: str) -> None:
    assert _get_bullet(indent_level) == expected


@pytest.mark.parametrize("simple, expected", [(True, "X"), (False, "✓")])
def test_get_checkmark(simple: bool, expected: str) -> None:
    assert _get_checkmark(simple) == expected


def test_add_ellipsis_should_not_truncate() -> None:
    result = _add_ellipsis("Hello", 0, 10, False)
    assert result == "Hello"


def test_add_ellipsis_should_truncate() -> None:
    result = _add_ellipsis("Hello world!", 0, 8, False)
    assert result.startswith("Hell")


def test_make_printable_sublist_short_list() -> None:
    lst = list(range(3))
    result = make_printable_sublist(5, lst, 1)
    assert isinstance(result, SublistItems)
    assert result.slice == lst


def test_make_printable_sublist_windowed() -> None:
    lst = list(range(20))
    result = make_printable_sublist(5, lst, 10)
    assert isinstance(result.slice, list)
    assert len(result.slice) <= 5


@pytest.mark.parametrize(
    "rel, abs, highlight, expected",
    [
        (1, 2, range(1, 3), str(3).ljust(2) + " "),
        (2, 3, range(4, 6), str(4).rjust(2) + " "),
    ],
)
def test_get_enumeration_info(
    rel: int, abs: int, highlight: range, expected: str, monkeypatch
) -> None:
    monkeypatch.setattr("ndo.print_todos.ENUMERATE", True)
    monkeypatch.setattr("ndo.print_todos.RELATIVE_ENUMERATE", False)
    result = _get_enumeration_info(rel, abs, 2, highlight)
    assert result == expected


@pytest.mark.parametrize("color", [1, 2, 3, 4, 5, 6, 7])
def test_color_to_ansi_valid(color: int) -> None:
    ansi = _color_to_ansi(color)
    assert ansi.startswith("\u001b[3")


def test_color_to_ansi_invalid() -> None:
    with pytest.raises(ValueError):
        _color_to_ansi(8)


def test_get_display_strings_returns_display_text() -> None:
    todo = Todo("- Hello")
    result = _get_display_strings(todo, False, "1 ", 80, False)
    assert isinstance(result, _DisplayText)
    assert result.prefix.startswith("1 ")
    assert "Hello" in result.text
