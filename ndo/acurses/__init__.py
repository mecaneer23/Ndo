"""An ANSI interface that feels like programming with curses"""
# ruff: noqa: TRY003, EM101

from functools import singledispatchmethod
from itertools import compress, count
from os import get_terminal_size
from queue import Empty as queue_empty  # noqa: N813
from queue import Queue
from sys import argv, stdin, stdout
from threading import Lock, Thread
from time import time as now
from types import TracebackType
from typing import Any, Callable, Self, TypeVar, overload

from ndo.keys import Key

try:
    from termios import (
        TCSADRAIN,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType]
        tcgetattr,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType]
        tcsetattr,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType]
    )
    from tty import (
        setcbreak,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType]
    )
except ImportError:
    from ndo.acurses.windows import (
        TCSADRAIN,
        init_windows,
        setcbreak,
        tcgetattr,
        tcsetattr,
    )
    init_windows()


_T = TypeVar("_T")

# https://www.w3.org/TR/xml-entity-names/025.html
ACS_RTEE = "┤"
ACS_LTEE = "├"
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

_KEYPAD_KEYS: dict[str, Key] = {
    "27-91-65": Key.up_arrow,
    "27-91-66": Key.down_arrow,
    "27-91-67": Key.right_arrow,
    "27-91-68": Key.left_arrow,
    "27-91-51-126": Key.delete,
    "27-91-53-126": Key.page_up,
    "27-91-54-126": Key.page_down,
    "27-91-90": Key.shift_tab,
    "27-91-49-59-53-68": Key.ctrl_left_arrow,
    "27-91-49-59-53-67": Key.ctrl_right_arrow,
    "27-91-72": Key.home,
    "27-91-70": Key.end,
    "27-91-51-59-50-126": Key.shift_delete,
    "27-91-51-59-126": Key.alt_delete,
}
_SHORT_TIME_SECONDS = 0.01


class error(Exception):  # pylint: disable=invalid-name  # noqa: N801, N818
    """
    Exception raised when a curses library function returns an error.
    Not implemented for acurses.
    """


class _Singleton:
    """A class for which only one instance can exist concurrently"""

    _instance: Self | None = None
    _lock: Lock = Lock()

    def __new__(cls) -> Self:
        with cls._lock:
            if cls._instance is not None:
                msg = f"Only one instance of {cls.__name__} is allowed."
                raise RuntimeError(msg)
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def destroy(cls) -> None:
        """Manually destroys the instance"""
        with cls._lock:
            if cls._instance is None:
                msg = f"No instance of {cls.__name__} to destroy."
                raise RuntimeError(msg)
            cls._instance = None

    def __enter__(self) -> "_Singleton":
        """Enter context manager"""
        return self

    def __exit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit context manager"""
        self.destroy()
        _ = type_, value, traceback


class _Getch(_Singleton):
    def __init__(self) -> None:
        self._block = True
        self._raw_input: Queue[int] = Queue()
        self._started = False

    def start(self) -> None:
        """Start the thread that fills the queue if not already started"""
        if self._started:
            return
        Thread(target=self._fill_queue, daemon=True).start()
        self._started = True

    def is_started(self) -> bool:
        """Return whether the queue filling thread has been started"""
        return self._started

    def _fill_queue(self) -> None:
        """
        As keys are pressed, add them to a queue (self._raw_input)

        This function should likely be run as a thread.
        """
        while True:
            self._raw_input.put(ord(stdin.read(1)), block=self._block)

    def get(self, timeout: float | None = None) -> int:
        """Get an item from the queue"""
        return self._raw_input.get(timeout != 0, timeout=timeout)

    def is_blocking(self) -> bool:
        """Return whether the Getch object is blocking"""
        return self._block

    def set_blocking(self, block: bool) -> None:  # noqa: FBT001
        """Set blocking status"""
        self._block = block


class _CursesWindow:  # pylint: disable=too-many-instance-attributes
    _GETCH = _Getch()

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

        self._stored_keys: Queue[int] = Queue()

        self._keypad: bool = False

        self._attrs = 0

        self._timeout: float | None = None

        if not _CursesWindow._GETCH.is_started():
            _CursesWindow._GETCH.start()

    def getch(self) -> int:
        """
        Get a character. Note that the integer returned
        does not have to be in ASCII range: function keys,
        keypad keys and so on are represented by numbers
        higher than 255. In no-delay mode, return -1 if
        there is no input, otherwise wait until a key is
        pressed.
        """
        if not _CursesWindow._GETCH.is_blocking():
            try:
                return self._stored_keys.get(block=False)
            except queue_empty:
                return -1
        if not self._stored_keys.empty():
            return self._stored_keys.get()

        chars = self._get_current_from_buffer()
        keys = (
            _KEYPAD_KEYS
            if _CursesWindow._GETCH.is_blocking() and self._keypad
            else {}
        )
        key = "-".join(map(str, chars))
        if key in keys:
            return keys[key].value
        for char in chars:
            self._stored_keys.put(char)
        return self._stored_keys.get()

    def _get_current_from_buffer(self) -> list[int]:
        char = _CursesWindow._GETCH.get(self._timeout)
        current = [char]
        if char == Key.escape:
            esc = now()
            while now() - esc < _SHORT_TIME_SECONDS:
                try:
                    char = _CursesWindow._GETCH.get(_SHORT_TIME_SECONDS)
                except queue_empty:
                    break
                if char not in current:
                    current.append(char)
        return current

    def move(self, new_y: int, new_x: int) -> None:
        """Move cursor to (new_y, new_x)"""
        pos_y = self._begin_y + new_y
        pos_x = self._begin_x + new_x
        if pos_y < 0:
            msg = f"new y position too small: {pos_y}"
            raise error(msg)
        if pos_x < 0:
            msg = f"new x position too small: {pos_x}"
            raise error(msg)
        if pos_y > self._begin_y + self._height:
            msg = f"new y position too large: {pos_y}"
            raise error(msg)
        if pos_x > self._begin_x + self._width:
            msg = f"new x position too large: {pos_x}"
            raise error(msg)
        stdout.write(f"\033[{pos_y + 1};{pos_x + 1}H")

    def _parse_attrs(self, attrs: int) -> str:
        """Convert a binary `attrs` into ANSI escape codes"""
        decimal_bits = 10
        ansi_background_bit_shifted = 4
        ansi_foreground_bit_shifted = 3
        output = ""
        iattrs = bin(attrs | self._attrs)[2:]
        background = 0
        for ansi_code in compress(count(len(iattrs) - 1, -1), map(int, iattrs)):
            if ansi_code // decimal_bits == ansi_background_bit_shifted:
                background = ansi_code
                continue
            ansi_str = str(ansi_code)
            if (
                ansi_code // decimal_bits == ansi_foreground_bit_shifted
                and background != 0
            ):
                ansi_str = f"{ansi_code};{background}"
            output += f"\033[{ansi_str}m"
        return output

    @singledispatchmethod
    def _addstr(
        self,
        _: object,
        __: None = None,
        ___: None = None,
        ____: None = None,
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
        stdout.write(f"{ansi_attrs}{text[: self._width]}")
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
        """Add the contents of the buffer to the screen and clear the buffer."""
        self.addstr(
            self._stored_y,
            self._stored_x,
            "".join(self._buffer),
            self._stored_attr,
        )
        self._buffer.clear()

    def addch(self, y: int, x: int, char: str, attr: int = 0) -> None:
        """Add a character to the screen"""
        if (
            attr != self._stored_attr
            or y != self._stored_y
            or x - self._stored_x > 1
        ):
            if self._buffer:
                self._clear_buffer()
            self._stored_attr = attr
            self._stored_x = x
            self._stored_y = y
        self._buffer.append(char)

    def nodelay(self, flag: bool = True) -> None:  # noqa: FBT001, FBT002
        """If flag is True, getch() will be non-blocking"""
        _CursesWindow._GETCH.set_blocking(not flag)

    def box(self) -> None:
        """Draw a border around the current window"""
        if self._width < 0:
            msg = f"width too small: {self._width}"
            raise error(msg)
        if self._height < 0:
            msg = f"height too small: {self._height}"
            raise error(msg)
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
        """Clear the screen (by overwriting every character with a space)"""
        self.move(0, 0)
        for i in range(self._height):
            self.addstr(i, 0, " " * self._width)
        stdout.flush()

    def timeout(self, delay: float) -> None:
        """
        Set blocking or non-blocking read behavior for
        the window. If delay is negative, blocking read
        is used (which will wait indefinitely for input).
        If delay is zero, then non-blocking read is used,
        and getch() will return -1 if no input is waiting.
        If delay is positive, then getch() will block for
        delay milliseconds, and return -1 if there is
        still no input at the end of that time.
        """
        self._timeout = delay

    def keypad(self, flag: bool = False) -> None:  # noqa: FBT001, FBT002
        """
        If flag is True, escape sequences generated by some
        keys (keypad, function keys) will be interpreted by
        curses. If flag is False, escape sequences will be
        left as is in the input stream.
        """
        self._keypad = flag

    def attron(self, attr: int) -> None:
        """
        Add attribute attr from the “background” set
        applied to all writes to the current window.
        """
        self._attrs |= attr

    def attroff(self, attr: int) -> None:
        """
        Remove attribute attr from the “background” set
        applied to all writes to the current window.
        """
        self._attrs ^= attr

    def attrset(self, attr: int) -> None:
        """
        Set the “background” set of attributes to attr.
        This set is initially 0 (no attributes).
        """
        self._attrs = attr


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
    """
    Initialize the library. Return a window object which represents
    the whole screen.
    """
    return _CursesWindow()


def wrapper(
    func: Callable[..., _T],
    /,
    *args: list[Any],
    **kwds: dict[str, Any],
) -> _T:
    """
    Wrapper function that initializes curses and calls another function,
    restoring normal keyboard/screen behavior on error.
    The callable object 'func' is then passed the main window 'stdscr'
    as its first argument, followed by any other arguments passed to
    wrapper().
    """

    fd = stdin.fileno()
    old_settings = tcgetattr(fd)  # pyright: ignore[reportUnknownVariableType]

    program_name = argv[0].rsplit("/", 1)[-1].rsplit(".", 1)[0]
    try:
        setcbreak(fd)
        # SAVE_CURSOR = \033[s
        # CLEAR_SCREEN = \033[2J
        # CURSOR_HOME = \033[H
        # _curses.start_color()
        stdout.write(f"\033[?1049h\033[H\033[22t\033]0;{program_name}\007")
        stdout.flush()
        stdscr = initscr()
        stdscr.keypad(True)  # noqa: FBT003
        return func(stdscr, *args, **kwds)
    finally:
        if "stdscr" in locals():
            # RESET_COLOR = \033[39;49m
            stdout.write("\033[?1049l\033[23t\033[?25h")
            stdout.flush()
            tcsetattr(fd, TCSADRAIN, old_settings)  # pyright: ignore[reportUnknownArgumentType]


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
    if pair_number < 0 or pair_number >= len(_color_pairs):
        msg = (
            "Invalid color pair number, make sure to call "
            f"init_pair({pair_number}, ...) before calling "
            "this function"
        )
        raise ValueError(msg)
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
