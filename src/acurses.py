"""An ANSI interface that feels like programming with curses"""

# TODO: Windows support, see the following link
# https://github.com/python/cpython/blob/3.12/Lib/getpass.py

from sys import stdin
from termios import TCSADRAIN, tcgetattr, tcsetattr
from tty import setcbreak
from typing import Any, Callable, TypeVar

_T = TypeVar("_T")


class _CursesWindow:  # pylint: disable=too-many-instance-attributes
    # def __init__(self) -> None:

    def getch(self) -> int:
        """
        Get a character. Note that the integer returned
        does not have to be in ASCII range: function keys,
        keypad keys and so on are represented by numbers
        higher than 255. In no-delay mode, return -1 if
        there is no input, otherwise wait until a key is
        pressed.
        """
        return ord(stdin.read(1))


window = _CursesWindow  # pylint: disable=invalid-name


def initscr() -> window:
    """Initialize the library. Return a window object which represents the whole screen."""
    return _CursesWindow()


def wrapper(func: Callable[..., _T], /, *args: list[Any], **kwds: dict[str, Any]) -> _T:
    """
    Wrapper function that initializes curses and calls another function,
    restoring normal keyboard/screen behavior on error.
    The callable object 'func' is then passed the main window 'stdscr'
    as its first argument, followed by any other arguments passed to
    wrapper().
    """

    try:
        fd = stdin.fileno()
        old_settings = tcgetattr(fd)
        setcbreak(fd)
        stdscr = initscr()
        # curses.noecho()
        # stdscr.keypad(True)
        # _curses.start_color()
        return func(stdscr, *args, **kwds)
    finally:
        if "stdscr" in locals():
            tcsetattr(fd, TCSADRAIN, old_settings)
        #     stdscr.keypad(False)  # pyright: ignore
        #     curses.echo()
        #     curses.nocbreak()
        #     curses.endwin()
