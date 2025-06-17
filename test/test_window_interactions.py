"""
Tests for window_interactions.py
"""

# ruff: noqa: S101#, PLR2004
# pylint: disable=missing-function-docstring

import ndo.acurses as curses
from ndo.window_interactions import alert, get_extra_info_attrs


def test_get_extra_info_attrs() -> None:
    """
    Test that get_extra_info_attrs returns the correct attributes.
    """
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    attrs = get_extra_info_attrs()
    assert attrs == (curses.A_BOLD | curses.color_pair(2))


def test_alert() -> None:
    """
    Test that alert function works correctly.
    """

    def wrapped(stdscr: curses.window) -> int:
        curses.curs_set(0)
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)

        return alert(
            stdscr,
            "This is a colorful test",
            attrs=curses.color_pair(2),
            box_attrs=curses.A_BOLD | curses.color_pair(1),
        )

    assert isinstance(curses.wrapper(wrapped), int)


if __name__ == "__main__":
    test_alert()
