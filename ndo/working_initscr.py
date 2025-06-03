"""
For some reason curses initscr doesn't work on python3.12,
presumably due to a compilation bug or something. This
module provides a functional workaround.

Thanks to https://github.com/zephyrproject-rtos/windows-curses/issues/50
for the inspiration.
"""

# pylint: disable=wrong-import-order

import _curses
import curses
from typing import Callable, Concatenate, ParamSpec, TypeVar

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
    func: Callable[Concatenate[..., P], R],
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
        stdscr.keypad(True)  # noqa: FBT003
        _curses.start_color()
        return func(stdscr, *args, **kwds)
    finally:
        if "stdscr" in locals():
            stdscr.keypad(False)  # type: ignore[reportPossiblyUnbound]  # noqa: FBT003
            curses.echo()
            curses.nocbreak()
            curses.endwin()
