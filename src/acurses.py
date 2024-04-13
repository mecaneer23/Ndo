"""An ANSI interface that feels like programming with curses"""

# TODO: Windows support, see the following link
# https://github.com/python/cpython/blob/3.12/Lib/getpass.py

# TODO: continue implementation with inspiration from following
# https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html

from os import get_terminal_size
from sys import stdin
from termios import TCSADRAIN, tcgetattr, tcsetattr
from tty import setcbreak
from typing import Any, Callable, TypeVar

_T = TypeVar("_T")

# https://www.w3.org/TR/xml-entity-names/025.html
ACS_RTEE = "⊣"
ACS_LTEE = "⊢"
ACS_HLINE = "─"
ACS_VLINE = "│"
ACS_URCORNER = "┐"
ACS_ULCORNER = "┌"
ACS_LRCORNER = "┘"
ACS_LLCORNER = "└"

ERR = -1
OK = 0

A_NORMAL = 10**0
A_BOLD = 10**1
A_DIM = 10**2
A_ITALIC = 10**3
A_UNDERLINE = 10**4
A_BLINK = 10**5
A_STANDOUT = 10**7
A_REVERSE = 10**7
A_INVIS = 10**8
A_STRIKETHROUGH = 10**9

COLOR_BLACK = 10**30
COLOR_RED = 10**31
COLOR_GREEN = 10**32
COLOR_YELLOW = 10**33
COLOR_BLUE = 10**34
COLOR_MAGENTA = 10**35
COLOR_CYAN = 10**36
COLOR_WHITE = 10**37

_ANSI_RESET = "\033[0m"


class _CursesWindow:  # pylint: disable=too-many-instance-attributes
    def __init__(self) -> None:
        self.buffer: list[str] = []
        self.stored_attr: int = 0
        self.stored_x: int = 0
        self.stored_y: int = 0

    def getch(self) -> int:
        """
        Get a character. Note that the integer returned
        does not have to be in ASCII range: function keys,
        keypad keys and so on are represented by numbers
        higher than 255.
        """
        return ord(stdin.read(1))

    def move(self, new_y: int, new_x: int) -> None:
        """Move cursor to (new_y, new_x)"""
        print(f"\033[{new_y};{new_x}H", end="")

    def _parse_attrs(self, attrs: int) -> str:
        """Convert a binary `attrs` into ANSI escape codes"""
        output = ""
        for pos, val in enumerate(str(attrs)):
            if val == "0":
                continue
            output += f"\033[{len(str(attrs)) - 1 - pos}m"
        return output

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        """Add a string to the screen at a specific position"""
        self.move(y, x)
        print(f"{self._parse_attrs(attr)}{text}{_ANSI_RESET}", end="")

    def refresh(self) -> None:
        """Sync display. Not necessary for acurses as it's currently non-buffered"""
        return

    def _get_width(self) -> int:
        return get_terminal_size()[0]

    def _get_height(self) -> int:
        return get_terminal_size()[1]

    def getmaxyx(self) -> tuple[int, int]:
        """Get window height and width"""
        return self._get_height(), self._get_width()

    def addch(self, y: int, x: int, char: str, attr: int = 0) -> None:
        """Add a character to the screen"""
        self.buffer.append(char)
        if len(self.buffer) == 1:
            self.stored_x = x
            self.stored_y = y
        if (
            attr not in {self.stored_attr, 0}
            or char == "\n"
            or len(self.buffer) + self.stored_x >= self._get_width()
        ):
            self.addstr(
                self.stored_y, self.stored_x, "".join(self.buffer), self.stored_attr
            )
            self.stored_attr = attr
            self.buffer.clear()

    def nodelay(self, flag: bool = True) -> None:
        """
        If flag is True, getch() will be non-blocking.
        Cannot be unset in acurses.
        """
        _ = flag

    def box(self) -> None:
        """Draw a border around the current window"""
        self.addstr(
            0,
            0,
            ACS_ULCORNER + ACS_HLINE * (self._get_width() - 2) + ACS_URCORNER,
        )
        for i in range(self._get_height() - 2):
            self.addch(i + 1, 0, ACS_VLINE)
        for i in range(self._get_height() - 2):
            self.addch(i + 1, self._get_width() - 1, ACS_VLINE)
        self.addstr(
            self._get_height() - 1,
            0,
            ACS_LLCORNER + ACS_HLINE * (self._get_width() - 2) + ACS_LRCORNER,
        )

    def hline(self, y: int, x: int, ch: str, n: int) -> None:
        """
        Display a horizontal line starting at (y, x)
        with length n consisting of the character ch.
        """
        self.addstr(y, x, ch * n)

    def clear(self) -> None:
        """Clear the screen"""
        raise NotImplementedError("\033[2J")


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

    fd = stdin.fileno()
    old_settings = tcgetattr(fd)

    try:
        setcbreak(fd)
        stdscr = initscr()
        # _curses.start_color()
        return func(stdscr, *args, **kwds)
    finally:
        if "stdscr" in locals():
            tcsetattr(fd, TCSADRAIN, old_settings)


def _main(stdscr: window):
    # curses.use_default_colors()
    # for i, color in enumerate(
    #     [
    #         curses.COLOR_RED,
    #         curses.COLOR_GREEN,
    #         curses.COLOR_YELLOW,
    #         curses.COLOR_BLUE,
    #         curses.COLOR_MAGENTA,
    #         curses.COLOR_CYAN,
    #         curses.COLOR_WHITE,
    #     ],
    #     start=1,
    # ):
    #     curses.init_pair(i, color, -1)
    stdscr.addstr(10, 1, "Hello, world!")
    # stdscr.addstr(10, 1, "Hello, world!", curses.color_pair(7))
    # scr.box()
    # win = curses.newwin(3, 20, 10, 10)
    # win.clear()
    # win.box()
    # win.addstr(1, 1, "Bold text", curses.color_pair(2))
    # win.clear()
    # scr.addstr(1, 1, "Bold text", curses.color_pair(5) | curses.A_STANDOUT)
    while True:
        x = stdscr.getch()
        print(x)
        if x == 27:
            y = stdscr.getch()
            print(str(y) + ":")
        if x == 113:
            break


if __name__ == "__main__":
    # wrapper(_main)
    pass
