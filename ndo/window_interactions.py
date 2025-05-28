"""
Utility functions for interacting with curses and curses-like interfaces.
"""

from itertools import tee

from ndo.color import Color
from ndo.get_args import curses_module as curses
from ndo.ui_protocol import CursesWindow
from ndo.utils import chunk_message


def get_extra_info_attrs() -> int:
    """
    Get the attributes for extra information.

    This seems like it could just be a constant, but color pairs
    must be initialized before they can be used. It's challenging
    to ensure that initialization prior to this file being imported,
    so a function is used so the color_pair function doesn't fail.
    """
    return curses.A_BOLD | curses.color_pair(Color.GREEN.as_int())


def set_header(stdscr: CursesWindow, message: str) -> None:
    """
    Set the header to a specific message.
    """
    stdscr.addstr(
        0,
        0,
        message.ljust(stdscr.getmaxyx()[1]),
        get_extra_info_attrs(),
    )


def alert(stdscr: CursesWindow, message: str) -> int:
    """
    Show a box with a message, similar to a JavaScript alert.

    Press any key to close (pressed key is returned).
    """
    set_header(stdscr, "Alert! Press any key to close")
    stdscr.refresh()
    border_width = 2
    max_y, max_x = stdscr.getmaxyx()
    height_chunk, width_chunk, chunks = tee(
        chunk_message(message, max_x * 3 // 4 - border_width),
        3,
    )
    width = len(max(width_chunk, key=len)) + border_width
    height = sum(1 for _ in height_chunk) + border_width
    if height > max_y:
        # This can theoretically recur forever if this branch
        # is accessed with a super small window
        # (one too small to show this text).
        # That said, this is so unlikely to happen, that
        # I don't think it's worth handling.
        return alert(
            stdscr,
            "Message too long to display in window, "
            "please try again with a shorter message or a larger window.",
        )
    win = curses.newwin(
        height,
        width,
        max_y // 2 - height // 2,
        max_x // 2 - width // 2,
    )
    win.clear()
    win.box()
    for index, chunk in enumerate(chunks, start=1):
        win.addstr(index, border_width // 2, chunk)
    win.refresh()
    key = stdscr.getch()
    stdscr.clear()
    return key
