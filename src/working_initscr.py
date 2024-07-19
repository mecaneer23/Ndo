"""
For some reason curses initscr doesn't work on python3.12,
presumably due to a compilation bug or something. This
module provides a functional workaround.

Thanks to https://github.com/zephyrproject-rtos/windows-curses/issues/50
for the inspiration.
"""

import curses
from typing import Callable, Concatenate, ParamSpec, TypeVar

import _curses

P = ParamSpec("P")
R = TypeVar("R")


def initscr() -> curses.window:
    """Return a stdscr that should be properly initialized"""
    stdscr = _curses.initscr()
    for key, value in _curses.__dict__.items():
        if key[0:4] == "ACS_" or key in ("LINES", "COLS"):
            setattr(curses, key, value)
    return stdscr  # pyright: ignore[reportReturnType]


def wrapper(
    func: Callable[Concatenate[curses.window, P], R],
    /,
    *args: P.args,
    **kwds: P.kwargs,
) -> R:
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
