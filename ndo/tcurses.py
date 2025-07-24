#!/usr/bin/env python3
"""
A Tkinter interface that feels like programming with curses
"""

from functools import wraps
from math import log2
from threading import Thread
from tkinter import BooleanVar, Event, Text, Tk
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class _CursesWindow:  # pylint: disable=too-many-instance-attributes
    @staticmethod
    def _updates_screen(func: Callable[..., None]) -> Callable[..., None]:
        @wraps(func)
        def _inner(
            self: "_CursesWindow",
            *args: list[Any],
            **kwargs: dict[Any, Any],
        ) -> None:
            screen.configure(state="normal")
            func(self, *args, **kwargs)
            screen.configure(state="disabled")

        return _inner

    def __init__(
        self,
        text: Text,
        width_height: tuple[int, int],
        begin_yx: tuple[int, int],
    ) -> None:
        self.screen = text
        self.width = width_height[0]
        self.height = width_height[1]
        self.begin_yx = begin_yx
        self.timeout_delay = -1
        self.keys: list[int] = []
        self.has_key = BooleanVar()
        self.has_key.set(False)
        root.bind("<Key>", self._handle_key)
        self.buffer: list[str] = []
        self.stored_attr: int = 0
        self.stored_x: int = 0
        self.stored_y: int = 0

    def __del__(self):
        root.bind("<Key>", stdscr._handle_key)

    def _handle_key(  # pylint: disable=too-many-return-statements
        self,
        event: "Event[Any]",
    ) -> None:
        if self.has_key.get() or event.keysym.endswith(("_R", "_L")):
            return
        if event.keysym_num == 99:  # ctrl+c
            raise KeyboardInterrupt()
        self.has_key.set(True)
        state = int(event.state)
        ctrl = (state & 0x4) != 0
        alt = (state & 0x8) != 0 or (state & 0x80) != 0
        shift = (state & 0x1) != 0
        if event.keycode == 9:  # escape
            self.keys.append(27)
            self.keys.append(-1)
            return
        special_keys: dict[int, _Key] = {
            22: _Key("Backspace", 8, ctrl=23),
            23: _Key("Tab", 9, shift=353),
            # Maybe shift tab should be 2 shift escapes + 90?
            36: _Key("Return", 10),
            110: _Key("Home", 72, escape="none" * 2),
            111: _Key("Up", 259),
            113: _Key("Left", 68, escape="none" * 2 + "ctrl" * 4),
            114: _Key("Right", 67, escape="none" * 2 + "ctrl" * 4),
            115: _Key("End", 72, escape="none" * 2),
            116: _Key("Down", 258),
            119: _Key("Delete", 330, ctrl=100, escape="ctrl"),
            # Maybe delete should be 3 none escapes + 51?
        }
        if event.keycode in special_keys:
            if shift:
                self.keys.extend(special_keys[event.keycode].get_shift())
                return
            if ctrl:
                self.keys.extend(special_keys[event.keycode].get_ctrl())
                return
            self.keys.extend(special_keys[event.keycode].get())
            return
        if repr(event.char).startswith("'\\x"):
            self.keys.append(int(repr(event.char)[3:-1], 16))
            return
        if alt:
            self.keys.append(27)  # escape
            self.keys.append(event.keysym_num)
            return
        self.keys.append(event.keysym_num)

    def getch(self) -> int:
        """Get a character from the list of keys pressed"""
        if self.timeout_delay > 0:
            running = BooleanVar()
            root.after(self.timeout_delay, running.set, True)
            root.wait_variable(running)
            self.has_key.set(False)
            if len(self.keys) > 0:
                return self.keys.pop(0)
            return -1
        if len(self.keys) == 0:
            root.wait_variable(self.has_key)
        self.has_key.set(False)
        return self.keys.pop(0)

    def timeout(self, delay: int) -> None:
        """Set timeout delay"""
        self.timeout_delay = delay

    def _parse_attrs(self, attrs: int) -> list[str]:
        possible_attrs: dict[int, str] = dict(
            (value, name)
            for name, value in globals().items()
            if isinstance(value, int)
        )
        possible_returns = {
            "A_BOLD": "bold",
            "COLOR_BLACK": "black",
            "COLOR_RED": "red",
            "COLOR_GREEN": "green",
            "COLOR_YELLOW": "yellow",
            "COLOR_BLUE": "blue",
            "COLOR_MAGENTA": "magenta",
            "COLOR_CYAN": "cyan",
            "COLOR_WHITE": "white",
        }
        potential = [
            possible_attrs[2 ** (len(str(attrs)) - 1 - pos)]
            for pos, val in enumerate(str(attrs))
            if val == "1"
        ]
        output: list[str] = []
        for item in potential:
            if (attrs >> 1) % 2 == 1:  # if attrs ends with 1_, standout
                if item.startswith("COLOR_"):
                    output.append(f"{possible_returns[item]}*")
                continue
            output.append(possible_returns[item])
        return output

    @_updates_screen
    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        """Add a string to the screen"""
        y_pos = self.begin_yx[0] + y
        x_pos = self.begin_yx[1] + x
        self.screen.replace(
            f"{y_pos + 1}.{x_pos}",
            f"{y_pos + 1}.{x_pos + len(text)}",
            text,
            self._parse_attrs(int(bin(attr)[2:])),
        )

    def getmaxyx(self) -> tuple[int, int]:
        """Get window height and width"""
        return self.height, self.width

    def addch(self, y: int, x: int, char: str, attr: int = 0) -> None:
        """Add a character to the screen"""
        self.buffer.append(char)
        if len(self.buffer) == 1:
            self.stored_x = x
            self.stored_y = y
        if (
            attr not in {self.stored_attr, 0}
            or char == "\n"
            or len(self.buffer) + self.stored_x >= self.width
        ):
            self.addstr(
                self.stored_y,
                self.stored_x,
                "".join(self.buffer),
                self.stored_attr,
            )
            self.stored_attr = attr
            self.buffer.clear()

    def nodelay(self, flag: bool = True) -> None:
        """
        If flag is True, getch() will be non-blocking.
        Cannot be unset in tcurses.
        """
        _ = flag

    def box(self) -> None:
        """Draw a border around the current window"""
        self.addstr(
            0,
            0,
            ACS_ULCORNER + ACS_HLINE * (self.width - 2) + ACS_URCORNER,
        )
        for i in range(self.height - 2):
            self.addch(i + 1, 0, ACS_VLINE)
        for i in range(self.height - 2):
            self.addch(i + 1, self.width - 1, ACS_VLINE)
        self.addstr(
            self.height - 1,
            0,
            ACS_LLCORNER + ACS_HLINE * (self.width - 2) + ACS_LRCORNER,
        )

    def hline(self, y: int, x: int, ch: str, n: int) -> None:
        """
        Display a horizontal line starting at (y, x)
        with length n consisting of the character ch.
        """
        self.addstr(y, x, ch * n)

    def refresh(self) -> None:
        """Sync display. Not necessary for tcurses as is non-buffered"""
        return

    @_updates_screen
    def clear(self) -> None:
        """Clear the screen"""
        for row in range(
            self.begin_yx[0] + 1, self.begin_yx[0] + 1 + self.height
        ):
            self.screen.replace(
                f"{row}.{self.begin_yx[1]}",
                f"{row}.{self.width + self.begin_yx[1]}",
                " " * self.width,
            )

    def keypad(self, flag: bool) -> None:
        """
        If flag is True, enable keypad mode.
        If flag is False, disable keypad mode.
        """
        _ = flag
        raise NotImplementedError("tcurses keypad")


ERR = -1
OK = 0
A_NORMAL = 0
A_STANDOUT = 2**1
A_BOLD = 2**2

COLOR_BLACK = 2**10
COLOR_RED = 2**11
COLOR_GREEN = 2**12
COLOR_YELLOW = 2**13
COLOR_BLUE = 2**14
COLOR_MAGENTA = 2**15
COLOR_CYAN = 2**16
COLOR_WHITE = 2**17

# https://www.w3.org/TR/xml-entity-names/025.html
ACS_RTEE = "⊣"
ACS_LTEE = "⊢"
ACS_HLINE = "─"
ACS_VLINE = "│"
ACS_URCORNER = "┐"
ACS_ULCORNER = "┌"
ACS_LRCORNER = "┘"
ACS_LLCORNER = "└"

_color_pairs: list[tuple[int, int]] = [(7, 0)]

window = _CursesWindow  # pylint: disable=invalid-name


def use_default_colors() -> None:
    """Allow using default colors. Not yet implemented."""
    return


def curs_set(visibility: int) -> None:
    """Set the cursor state. Not yet implemented."""
    _ = visibility


def _get_usable_color(bit_represented: int) -> int:
    return int(log2(bit_represented) % 10)


def init_pair(pair_number: int, fg: int, bg: int) -> None:
    """
    Change the definition of a color-pair. It takes three arguments:
    the number of the color-pair to be changed, the foreground color
    number, and the background color number. The value of pair_number
    must be between 1 and COLOR_PAIRS - 1 (the 0 color pair is wired
    to white on black and cannot be changed). The value of fg and bg
    arguments must be between 0 and COLORS - 1, or, after calling
    use_default_colors(), -1. If the color-pair was previously
    initialized, the screen is refreshed and all occurrences of that
    color-pair are changed to the new definition.
    """
    bg = max(bg, 2**10)
    _color_pairs.insert(
        pair_number, (_get_usable_color(fg), _get_usable_color(bg))
    )


def color_pair(pair_number: int) -> int:
    """
    Return the attribute value for displaying text
    in the specified color pair.
    """
    fg, bg = _color_pairs[pair_number]
    return 2 ** (10 + fg) | 2 ** (10 + bg)


# def newwin(
#     nlines: int,
#     ncols: int,
#     begin_y: int = 0,
#     begin_x: int = 0,
# ) -> _CursesWindow:
#     """
#     Return a new window, whose left-upper corner is at (begin_y, begin_x),
#     and whose height/width is nlines/ncols.
#     """
#     return _CursesWindow(screen, (ncols, nlines), (begin_y, begin_x))


def wrapper(
    func: Callable[..., T], /, *args: list[Any], **kwargs: dict[str, Any]
) -> T:
    """
    Initialize tcurses and call another callable object, func, which
    should be the rest of your tcurses-using application. If the
    application raises an exception, this function will restore the
    terminal to a sane state before re-raising the exception and
    generating a traceback. The callable object func is then passed
    the main window `stdscr` as its first argument, followed by any
    other arguments passed to wrapper(). Before calling func, wrapper()
    turns on cbreak mode, turns off echo, enables the terminal keypad,
    and initializes colors if the terminal has color support. On exit
    (whether normally or by exception) it restores cooked mode, turns
    on echo, and disables the terminal keypad.
    """

    def worker(q: list[T]):
        q.append(func(stdscr, *args, **kwargs))

    def check_thread():
        if not func_thread.is_alive():
            root.quit()
            return
        root.after(100, check_thread)

    result_queue: list[T] = []
    func_thread = Thread(target=worker, args=(result_queue,))
    func_thread.start()
    root.after(100, check_thread)
    root.mainloop()
    func_thread.join()
    if len(result_queue) == 1:
        return result_queue[0]
    raise RuntimeError("tcurses quit unexpectedly")


def nocbreak() -> None:
    """Leave cbreak mode. Return to normal “cooked” mode with line buffering."""
    return


def echo(flag: bool = True) -> None:
    """
    Enter echo mode. In echo mode, each character input is
    echoed to the screen as it is entered.
    """
    _ = flag


def endwin() -> None:
    """De-initialize the library, and return terminal to normal status."""
    return


def initscr() -> _CursesWindow:
    """
    Initialize the library. Return a window object
    which represents the whole screen.
    """
    raise NotImplementedError("initscr not implemented, use wrapper instead")


class error(Exception):  # pylint: disable=invalid-name
    """Exception raised when a curses library function returns an error."""


class _Key:  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        no_modifiers: int,
        /,
        shift: int = 0,
        alt: int = 0,
        ctrl: int = 0,
        escape: str = "",
    ) -> None:
        self.name = name
        self.no_modifiers = no_modifiers
        self.shift = shift if shift > 0 else no_modifiers
        self.alt = alt if alt > 0 else no_modifiers
        self.ctrl = ctrl if ctrl > 0 else no_modifiers
        self.nones = escape.count("none")
        self.escape_ctrl = escape.count("ctrl")
        self.escape_shift = escape.count("shift")
        self.escape_alt = escape.count("alt")

    def get(self) -> list[int]:
        """Return a list of keys"""
        return self._inner_get(self.no_modifiers, self.nones)

    def _inner_get(self, value: int, escape_count: int):
        output: list[int] = []
        for _ in range(escape_count):
            output.append(27)
        output.append(value)
        return output

    def get_shift(self) -> list[int]:
        """Returns list of keys with shift pressed"""
        return self._inner_get(self.shift, self.escape_shift)

    def get_alt(self) -> list[int]:
        """Returns list of keys with alt pressed"""
        return self._inner_get(self.alt, self.escape_alt)

    def get_ctrl(self) -> list[int]:
        """Returns list of keys with control pressed"""
        return self._inner_get(self.ctrl, self.escape_ctrl)


root = Tk()
# use multiprocessing
root.protocol("WM_DELETE_WINDOW", root.destroy)
WIDTH = 100
HEIGHT = 30
screen = Text(
    root,
    width=WIDTH,
    height=HEIGHT,
    font="Terminal 12",
    foreground="black",
    background="white",
)
screen.insert(
    f"{0}.{1}",
    "\n".join(WIDTH * " " for _ in range(HEIGHT)),
)
screen.pack()
screen.focus_set()
screen.tag_configure("bold", font="Terminal 12 bold")
screen.tag_configure("black", foreground="black", background="white")
screen.tag_configure("red", foreground="red", background="white")
screen.tag_configure("green", foreground="green", background="white")
screen.tag_configure("yellow", foreground="yellow", background="white")
screen.tag_configure("blue", foreground="blue", background="white")
screen.tag_configure("cyan", foreground="cyan", background="white")
screen.tag_configure("magenta", foreground="magenta", background="white")
screen.tag_configure("white", foreground="black", background="white")
screen.tag_configure("black*", background="black", foreground="white")
screen.tag_configure("red*", background="red", foreground="white")
screen.tag_configure("green*", background="green", foreground="white")
screen.tag_configure("yellow*", background="yellow", foreground="white")
screen.tag_configure("blue*", background="blue", foreground="white")
screen.tag_configure("cyan*", background="cyan", foreground="white")
screen.tag_configure("magenta*", background="magenta", foreground="white")
screen.tag_configure("white*", background="black", foreground="white")
screen.configure(state="disabled")

stdscr = _CursesWindow(screen, (WIDTH, HEIGHT), (0, 0))

def fail() -> None:
    """
    Raise NotImplementedError with a message that tcurses is not fully
    implemented.
    """
    msg = (
        "tcurses is not fully implemented. Use ANSI (acurses) or standard "
        "curses UI to run your application."
    )
    raise NotImplementedError(msg)

fail()
