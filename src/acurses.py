"""An ANSI interface that feels like programming with curses"""

# TODO: Windows support, see the following link
# https://github.com/python/cpython/blob/3.12/Lib/getpass.py

# TODO: continue implementation with inspiration from following
# https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html

from os import get_terminal_size
from sys import stdin, stdout
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
FOREGROUND_DEFAULT = 10**39
BACKGROUND_DEFAULT = 10**49

_ANSI_RESET = "\033[0m"


class _CursesWindow:
    def __init__(
        self,
        /,
        width: int = -1,
        height: int = -1,
        begin_y: int = 0,
        begin_x: int = 0,
    ) -> None:
        self.width = width
        self.height = height
        self.begin_y = begin_y
        self.begin_x = begin_x

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
        # TODO: might need to add 1 to both args to account for offset
        stdout.write(f"\033[{self.begin_y + new_y};{self.begin_x + new_x}H")

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
        stdout.write(f"{self._parse_attrs(attr)}{text}{_ANSI_RESET}")

    def refresh(self) -> None:
        """Sync display"""
        self._clear_buffer()
        stdout.flush()

    def _get_width(self) -> int:
        return self.width if self.width > -1 else get_terminal_size()[0]

    def _get_height(self) -> int:
        return self.height if self.height > -1 else get_terminal_size()[1]

    def getmaxyx(self) -> tuple[int, int]:
        """Get window height and width"""
        return self._get_height(), self._get_width()

    def _clear_buffer(self, attr: int = -1) -> None:
        self.addstr(
            self.stored_y, self.stored_x, "".join(self.buffer), self.stored_attr
        )
        if attr != -1:
            self.stored_attr = attr
        self.buffer.clear()

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
            self._clear_buffer(attr)

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
            self.addstr(i + 2, 0, ACS_VLINE)
        for i in range(self._get_height() - 2):
            self.addstr(i + 2, self._get_width(), ACS_VLINE)
        self.addstr(
            self._get_height(),
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


def use_default_colors() -> None:
    """Allow using default colors. Not yet implemented."""
    return


def curs_set(visibility: int) -> None:
    """Set the cursor state. Not yet implemented."""
    _ = visibility


window = _CursesWindow  # pylint: disable=invalid-name
_color_pairs: list[int] = [FOREGROUND_DEFAULT]


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
        stdout.write("\033[s\033[2J\033[H")
        stdout.flush()
        stdscr = initscr()
        # _curses.start_color()
        return func(stdscr, *args, **kwds)
    finally:
        if "stdscr" in locals():
            stdout.write("\033[39;49m\033[0m\033[2J\033[H")
            stdout.flush()
            tcsetattr(fd, TCSADRAIN, old_settings)


def init_pair(pair_number: int, fg: int, bg: int) -> None:
    """
    Change the definition of a color-pair. It takes three arguments:
    the number of the color-pair to be changed, the foreground color
    number, and the background color number. The value of pair_number
    must be between 1 and COLOR_PAIRS - 1 (the 0 color pair is wired
    to white on black and cannot be changed). The value of fg and bg
    arguments must be between 0 and COLORS - 1, or, after calling
    use_default_colors(), -1.
    """
    # TODO: may need to use ansi "fg;bg" rather than combined
    _color_pairs.insert(pair_number, fg)  # | (max(bg, COLOR_BLACK) * 10**10))


def color_pair(pair_number: int) -> int:
    """
    Return the attribute value for displaying text
    in the specified color pair.
    """
    return _color_pairs[pair_number]


def newwin(
    nlines: int, ncols: int, begin_y: int = 0, begin_x: int = 0
) -> _CursesWindow:
    """
    Return a new window, whose left-upper corner is at (begin_y, begin_x),
    and whose height/width is nlines/ncols.
    """
    return _CursesWindow(ncols, nlines, begin_y, begin_x)


def _main(stdscr: window):
    use_default_colors()
    for i, color in enumerate(
        [
            COLOR_RED,
            COLOR_GREEN,
            COLOR_YELLOW,
            COLOR_BLUE,
            COLOR_MAGENTA,
            COLOR_CYAN,
            COLOR_WHITE,
        ],
        start=1,
    ):
        init_pair(i, color, -1)
    stdscr.addstr(10, 1, "Hello, world!", color_pair(6))
    stdscr.box()
    stdscr.refresh()
    # win = newwin(3, 20, 10, 10)
    # win.clear()
    # win.box()
    # win.addstr(1, 1, "Bold text", color_pair(2))
    # win.clear()
    # stdscr.addstr(1, 1, "Bold text", color_pair(5) | A_STANDOUT)
    while True:
        x = stdscr.getch()
        print(x)
        if x == 27:
            y = stdscr.getch()
            print(str(y) + ":")
        if x == 113:
            break


if __name__ == "__main__":
    wrapper(_main)
