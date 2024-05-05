"""
General utilities, useful across multiple other files
"""

from enum import Enum
from itertools import tee
from typing import Iterable, NamedTuple

from src.get_args import UI_TYPE, UiType

if UI_TYPE == UiType.ANSI:
    import src.acurses as curses
elif UI_TYPE == UiType.TKINTER:
    import src.tcurses as curses  # type: ignore
else:
    import curses  # type: ignore


class Chunk(NamedTuple):
    """
    A chunk of text that can be toggled on or off based on a condition
    """

    condition: bool
    text: str

    @staticmethod
    def join(*chunks: "Chunk") -> str:
        """Join chunks with a True condition into one string"""
        return "".join([item for condition, item in chunks if condition])


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

    def as_char(self) -> str:
        """Get lowercase first letter of color"""
        return self.name[0].lower()

    @staticmethod
    def from_first_char(char: str) -> "Color":
        """Return the color corresponding to its first character"""
        return {
            "r": Color.RED,
            "g": Color.GREEN,
            "y": Color.YELLOW,
            "b": Color.BLUE,
            "m": Color.MAGENTA,
            "c": Color.CYAN,
            "w": Color.WHITE,
        }[char]

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


def set_header(stdscr: curses.window, message: str) -> None:
    """
    Set the header to a specific message.
    """
    stdscr.addstr(
        0,
        0,
        message.ljust(stdscr.getmaxyx()[1]),
        curses.A_BOLD | curses.color_pair(2),
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


def _chunk_message(message: str, width: int) -> Iterable[str]:
    left = 0
    right = width + 1
    while True:
        right -= 1
        if right >= len(message):
            yield message[left:]
            break
        if message[right] == " ":
            yield message[left:right]
            left = right + 1
            right += width
            continue
        if right == left:
            yield message[left : left + width]
            continue


def alert(stdscr: curses.window, message: str) -> int:
    """
    Show a box with a message, similar to a JavaScript alert.

    Press any key to close (pressed key is returned).
    """
    set_header(stdscr, "Alert! Press any key to close")
    stdscr.refresh()
    border_width = 2
    max_y, max_x = stdscr.getmaxyx()
    height_chunk, width_chunk, chunks = tee(
        _chunk_message(message, max_x * 3 // 4 - border_width),
        3,
    )
    width = len(max(width_chunk, key=len)) + border_width
    height = sum(1 for _ in height_chunk) + border_width
    win = curses.newwin(height, width, max_y // 2 - height, max_x // 2 - width // 2)
    win.clear()
    win.box()
    for index, chunk in enumerate(chunks, start=1):
        win.addstr(index, border_width // 2, chunk)
    win.refresh()
    return stdscr.getch()
