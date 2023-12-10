"""
General utilities, useful across multiple other files
"""

from typing import Any

from src.get_args import TKINTER_GUI

if TKINTER_GUI:
    from tcurses import curses
else:
    import curses


def clamp(number: int, minimum: int, maximum: int) -> int:
    """
    Clamp a number in between a minimum and maximum.
    """
    return min(max(number, minimum), maximum - 1)


def set_header(stdscr: Any, message: str) -> None:
    """
    Set the header to a specific message.
    """
    stdscr.addstr(
        0, 0, message.ljust(stdscr.getmaxyx()[1]), curses.A_BOLD | curses.color_pair(2)
    )
