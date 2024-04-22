"""An ANSI interface that feels like programming with curses"""

from functools import singledispatchmethod
from itertools import compress, count
from os import get_terminal_size, name
from sys import stdin, stdout
from typing import Any, Callable, TypeVar, overload

try:
    from termios import TCSADRAIN, tcgetattr, tcsetattr  # type: ignore
    from tty import setcbreak  # type: ignore
except ImportError:
    from msvcrt import getwch, putwch  # type: ignore

    def _write(string: str) -> int:
        for ch in string:
            putwch(ch)
        return 0

    stdin.read = lambda _=-1: getwch()  # type: ignore
    stdout.write = _write
    stdout.flush = lambda: None

IS_WINDOWS = name == "nt"

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

A_NORMAL = 2**0
A_BOLD = 2**1
A_DIM = 2**2
A_ITALIC = 2**3
A_UNDERLINE = 2**4
A_BLINK = 2**5
A_STANDOUT = 2**7
A_REVERSE = 2**7
A_INVIS = 2**8
A_STRIKETHROUGH = 2**9

COLOR_BLACK = 2**30
COLOR_RED = 2**31
COLOR_GREEN = 2**32
COLOR_YELLOW = 2**33
COLOR_BLUE = 2**34
COLOR_MAGENTA = 2**35
COLOR_CYAN = 2**36
COLOR_WHITE = 2**37
FOREGROUND_DEFAULT = 2**39
BACKGROUND_DEFAULT = 2**49

_ANSI_RESET = "\033[0m"

_KEYS: dict[int, tuple[int, ...]] = {27: (27, -1)}


class _CursesWindow:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        /,
        width: int = -1,
        height: int = -1,
        begin_y: int = 0,
        begin_x: int = 0,
    ) -> None:
        self._height = height if height > -1 else get_terminal_size()[1]
        self._width = width if width > -1 else get_terminal_size()[0]
        self._begin_y = begin_y
        self._begin_x = begin_x

        self._buffer: list[str] = []
        self._stored_attr: int = 0
        self._stored_y: int = 0
        self._stored_x: int = 0

        self._stored_keys: list[int] = []

    def getch(self) -> int:
        """
        Get a character. Note that the integer returned
        does not have to be in ASCII range: function keys,
        keypad keys and so on are represented by numbers
        higher than 255.
        """
        if self._stored_keys:
            return self._stored_keys.pop(0)
        char = ord(stdin.read(1))
        keys = _KEYS.get(char, (char,))
        if len(keys) == 0:
            raise NotImplementedError(
                f"Pressing {char} hasn't been implemented yet in this context"
            )
        for key in keys[1:]:
            self._stored_keys.append(key)
        return keys[0]

    def move(self, new_y: int, new_x: int) -> None:
        """Move cursor to (new_y, new_x)"""
        pos_y = self._begin_y + new_y
        pos_x = self._begin_x + new_x
        if pos_y < 0:
            raise ValueError("new y position too small")
        if pos_x < 0:
            raise ValueError("new x position too small")
        if pos_y > self._begin_y + self._height:
            raise ValueError("new y position too large")
        if pos_x > self._begin_x + self._width:
            raise ValueError("new x position too large")
        stdout.write(f"\033[{pos_y + 1};{pos_x + 1}H")

    def _parse_attrs(self, attrs: int) -> str:
        """Convert a binary `attrs` into ANSI escape codes"""
        output = ""
        iattrs = bin(attrs)[2:]
        background = 0
        for ansi_code in compress(count(len(iattrs) - 1, -1), map(int, iattrs)):
            if ansi_code // 10 == 4:
                background = ansi_code
                continue
            if ansi_code // 10 == 3 and background != 0:
                ansi_code = f"{ansi_code};{background}"
            output += f"\033[{ansi_code}m"
        return output

    @singledispatchmethod
    def _addstr(
        self, _: object, __: None = None, ___: None = None, ____: None = None
    ) -> None:
        _ = __
        _ = ___
        _ = ____
        raise NotImplementedError("Cannot add NoneType: not a string")

    @overload
    def addstr(self, text: str, attr: int = 0) -> None: ...

    @overload
    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None: ...

    def addstr(self, *args: Any, **kwargs: Any) -> None:
        """Add a string to the screen at a specific position"""
        self._addstr(*args, **kwargs)

    @_addstr.register(str)
    def _(self, text: str, attr: int = 0) -> None:
        ansi_attrs = self._parse_attrs(attr)
        stdout.write(f"{ansi_attrs}{text[:self._width]}")
        if ansi_attrs:
            stdout.write(_ANSI_RESET)
        stdout.flush()

    @_addstr.register(int)
    def _(self, y: int, x: int, text: str, attr: int = 0) -> None:
        self.move(y, x)
        self.addstr(text, attr)

    def refresh(self) -> None:
        """Sync display"""
        self._clear_buffer()
        stdout.flush()

    def getmaxyx(self) -> tuple[int, int]:
        """Get window height and width"""
        return self._height, self._width

    def _clear_buffer(self) -> None:
        self.addstr(
            self._stored_y,
            self._stored_x,
            "".join(self._buffer),
            self._stored_attr,
        )
        self._buffer.clear()

    def addch(self, y: int, x: int, char: str, attr: int = 0) -> None:
        """Add a character to the screen"""
        if attr != self._stored_attr or y != self._stored_y:
            if self._buffer:
                self._clear_buffer()
            self._stored_attr = attr
            self._stored_x = x
            self._stored_y = y
        self._buffer.append(char)

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
            ACS_ULCORNER + ACS_HLINE * (self._width - 2) + ACS_URCORNER,
        )
        for i in range(self._height - 2):
            self.addstr(i + 1, 0, ACS_VLINE)
        for i in range(self._height - 2):
            self.addstr(i + 1, self._width - 1, ACS_VLINE)
        self.addstr(
            self._height - 1,
            0,
            ACS_LLCORNER + ACS_HLINE * (self._width - 2) + ACS_LRCORNER,
        )

    def hline(self, y: int, x: int, ch: str, n: int) -> None:
        """
        Display a horizontal line starting at (y, x)
        with length n consisting of the character ch.
        """
        self.addstr(y, x, ch * n)

    def clear(self) -> None:
        """Clear the screen"""
        self.move(0, 0)
        for i in range(self._height):
            self.addstr(i, 0, " " * self._width)
        stdout.flush()


def use_default_colors() -> None:
    """Allow using default colors. Not yet implemented."""
    return


def curs_set(visibility: int) -> None:
    """Set the cursor state. 0 for invisible, 1 for normal"""
    if visibility == 0:
        stdout.write("\033[?25l")
    elif visibility == 1:
        stdout.write("\033[?25h")
    else:
        raise NotImplementedError("Invalid visibility level")
    stdout.flush()


window = _CursesWindow  # pylint: disable=invalid-name
_color_pairs: list[int] = [FOREGROUND_DEFAULT | BACKGROUND_DEFAULT]


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

    if not IS_WINDOWS:
        fd = stdin.fileno()
        old_settings = tcgetattr(fd)  # type: ignore

    try:
        if not IS_WINDOWS:
            setcbreak(fd)  # type: ignore
        stdout.write("\033[s\033[2J\033[H")
        stdout.flush()
        stdscr = initscr()
        # _curses.start_color()
        return func(stdscr, *args, **kwds)
    finally:
        if "stdscr" in locals():
            stdout.write("\033[39;49m\033[0m\033[2J\033[H\033[?25h")
            stdout.flush()
            if not IS_WINDOWS:
                tcsetattr(fd, TCSADRAIN, old_settings)  # type: ignore


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
    _color_pairs.insert(pair_number, fg | max(bg * 2**10, BACKGROUND_DEFAULT))


def color_pair(pair_number: int) -> int:
    """
    Return the attribute value for displaying text
    in the specified color pair.
    """
    return _color_pairs[pair_number]


def newwin(
    nlines: int,
    ncols: int,
    begin_y: int = 0,
    begin_x: int = 0,
) -> _CursesWindow:
    """
    Return a new window, whose left-upper corner is at (begin_y, begin_x),
    and whose height/width is nlines/ncols.
    """
    return _CursesWindow(ncols, nlines, begin_y, begin_x)
