"""
For some reason curses initscr doesn't work on python3.12,
presumably due to a compilation bug or something. This
module provides a functional workaround.

Thanks to https://github.com/zephyrproject-rtos/windows-curses/issues/50
for the inspiration.

This file also serves as a partial replacement for curses, so it is
unnecessary to import tcurses.
"""

import curses
from typing import Any, Callable, TypeVar

import _curses

T = TypeVar("T")


def initscr() -> curses.window:
    """Return a stdscr that should be properly initialized"""
    stdscr = _curses.initscr()
    for key, value in _curses.__dict__.items():
        if key[0:4] == "ACS_" or key in ("LINES", "COLS"):
            setattr(curses, key, value)
    return stdscr


# def wrapper(
#     func: Callable[Concatenate[curses.window, P], R],
#     /,
#     *args: P.args,
#     **kwargs: P.kwargs
# ) -> R:
def wrapper(func: Callable[..., T], /, *args: list[Any], **kwds: dict[str, Any]) -> T:
    """
    Wrapper function that initializes curses and calls another function,
    restoring normal keyboard/screen behavior on error.
    The callable object 'func' is then passed the main window 'stdscr'
    as its first argument, followed by any other arguments passed to
    wrapper().
    """

    try:
        stdscr = initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        _curses.start_color()
        return func(stdscr, *args, **kwds)
    finally:
        if "stdscr" in locals():
            stdscr.keypad(False)  # pyright: ignore
            curses.echo()
            curses.nocbreak()
            curses.endwin()
