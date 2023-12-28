# pylint: disable=missing-class-docstring, too-many-ancestors, unused-argument
# pylint: disable=missing-function-docstring, missing-module-docstring, multiple-statements

from tkinter import Text
from typing import Any, Callable, TypeVar

T = TypeVar("T")

class curses:  # pylint: disable=invalid-name
    ERR: int
    OK: int
    A_NORMAL: int
    A_STANDOUT: int
    A_BOLD: int

    COLOR_BLACK: int
    COLOR_RED: int
    COLOR_GREEN: int
    COLOR_YELLOW: int
    COLOR_BLUE: int
    COLOR_MAGENTA: int
    COLOR_CYAN: int
    COLOR_WHITE: int

    ACS_RTEE: str
    ACS_LTEE: str
    ACS_HLINE: str
    ACS_VLINE: str
    ACS_URCORNER: str
    ACS_ULCORNER: str
    ACS_LRCORNER: str
    ACS_LLCORNER: str
    @staticmethod
    def use_default_colors() -> None: ...
    @staticmethod
    def curs_set(visibility: int) -> None: ...
    @staticmethod
    def init_pair(pair_number: int, fg: int, bg: int) -> None: ...
    @staticmethod
    def color_pair(pair_number: int) -> int: ...
    @staticmethod
    def newwin(nlines: int, ncols: int, begin_y: int = 0, begin_x: int = 0) -> Screen: ...  # pylint: disable=used-before-assignment
    @staticmethod
    def wrapper(
        func: Callable[..., T], *args: list[Any], **kwargs: dict[str, Any]
    ) -> T: ...
    @staticmethod
    def nocbreak() -> None: ...
    @staticmethod
    def echo(__flag: bool = True) -> None: ...
    @staticmethod
    def endwin() -> None: ...
    @staticmethod
    def initscr() -> Screen: ...  # pylint: disable=used-before-assignment


    class error(Exception): ...

class _Key:
    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        no_modifiers: int,
        /,
        shift: int = 0,
        alt: int = 0,
        ctrl: int = 0,
        escape: str = "",
    ) -> None: ...
    def get(self) -> list[int]: ...
    def get_shift(self) -> list[int]: ...
    def get_alt(self) -> list[int]: ...
    def get_ctrl(self) -> list[int]: ...

class Screen:
    def __init__(
        self, text: Text, width_height: tuple[int, int], begin_yx: tuple[int, int]
    ) -> None: ...
    def getch(self) -> int: ...
    def timeout(self, delay: int) -> None: ...
    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None: ...
    def getmaxyx(self) -> tuple[int, int]: ...
    def addch(self, y: int, x: int, char: str, attr: int = 0) -> None: ...
    def nodelay(self, flag: bool = True) -> None: ...
    def box(self) -> None: ...
    def hline(self, y: int, x: int, ch: str, n: int) -> None: ...
    def refresh(self) -> None: ...
    def clear(self) -> None: ...
