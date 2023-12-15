"""
General utilities, useful across multiple other files
"""

from collections import UserList
from enum import Enum
from typing import Any, Iterable, NamedTuple, TypeVar

from src.get_args import TKINTER_GUI

if TKINTER_GUI:
    from tcurses import curses
else:
    import curses


class SingleTypeList(UserList):
    """
    Baseclass to inherit from for any list
    type which can only hold one type.

    Should not be used directly.

    Example:

    class Todos(SingleTypeList):
        def __init__(self, iterable):
            super().__init__(iterable)
            self.base = Todo

    """

    T = TypeVar("T")

    def _validate_number(self, value: T) -> T:
        if isinstance(value, self.base):
            return value
        raise TypeError(f"{self.base.__name__} expected, got {type(value).__name__}")

    def __init__(self, iterable: Iterable[Any]) -> None:
        self.base: Any = object
        super().__init__(self._validate_number(item) for item in iterable)

    def __setitem__(self, index: int, item: Any) -> None:
        self.data[index] = self._validate_number(item)

    def insert(self, index: int, item: Any) -> None:  # pylint: disable=W0237
        self.data.insert(index, self._validate_number(item))

    def append(self, item: Any) -> None:
        self.data.append(self._validate_number(item))

    def extend(self, other: Iterable[Any]) -> None:
        if isinstance(other, type(self)):
            self.data.extend(other)
        else:
            self.data.extend(self._validate_number(item) for item in other)


class Chunk(NamedTuple):
    """
    A chunk of text that can be toggled on or off based on a condition
    """

    condition: bool
    text: str


class Color(Enum):
    """
    Standardized colors for Ndo
    """

    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7

    def as_int(self) -> int:
        """
        Main getter for Ndo colors
        """
        return self.value

    @staticmethod
    def as_dict() -> dict[str, int]:
        """
        Get all colors represented as a mapping of color name to corresponding int value
        """
        return dict((color.name.capitalize(), color.value) for color in Color)


def clamp(number: int, minimum: int, maximum: int) -> int:
    """
    Clamp a number in between a minimum and maximum.
    """
    return min(max(number, minimum), maximum - 1)


def set_header(stdscr: Any, message: str) -> None:
    """
    Set the header to a specific message.
    """
    stdscr.addstr(
        0, 0, message.ljust(stdscr.getmaxyx()[1]), curses.A_BOLD | curses.color_pair(2)
    )


def overflow(counter: int, minimum: int, maximum: int) -> int:
    """
    Similar to clamp(), but instead of keeping a counter between
    two values, by leaving it at the min or max end, it wraps over
    the top or bottom.
    """
    if counter >= maximum:
        return minimum + (counter - maximum)
    if counter < minimum:
        return maximum - (minimum - counter)
    return counter
