"""
Helper module to handle printing a list of Todo objects
"""

# ruff: noqa: FBT001, FBT003

from collections.abc import Iterator
from dataclasses import astuple, dataclass
from functools import cache
from itertools import count
from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, cast

from ndo.color import Color
from ndo.cursor import Cursor
from ndo.get_args import (
    BULLETS,
    ENUMERATE,
    INDENT,
    RELATIVE_ENUMERATE,
    SIMPLE_BOXES,
    STRIKETHROUGH,
    UI_TYPE,
    UiType,
)
from ndo.get_args import curses_module as curses
from ndo.todo import Todo, Todos
from ndo.ui_protocol import CursesWindow
from ndo.utils import Chunk
from ndo.window_interactions import get_extra_info_attrs

_T = TypeVar("_T")
_ANSI_RESET = "\033[0m"
_ANSI_STRIKETHROUGH = "\033[9m"
_ANSI_BOLD = "\033[1m"
_DEBUG_FOLD = False
_SIMPLE_BOX_WIDTH = 3 if SIMPLE_BOXES else 0


@dataclass
class SublistItems(
    Generic[_T],
    tuple[list[_T], int, int] if TYPE_CHECKING else object,
):  # pylint: disable=useless-object-inheritance
    """
    Pseudo-NamedTuple representing a slice of a
    list of T, an index within that list,
    and a start value to be passed into
    make_printable_sublist.

    slice: list[T]
    cursor: int
    start: int

    If `int` values aren't provided, they are initialized to 0.

    This class is implemented as a pseudo-NamedTuple rather than
    a typing.NamedTuple because of a bug with generic NamedTuples
    in Python3.10.
    """

    slice: list[_T]
    cursor: int = 0
    start: int = 0

    def __iter__(self) -> Iterator[list[_T] | int]:
        """
        Allows unpacking of SublistItems instances.
        """
        return iter(astuple(self))


class _DisplayText(NamedTuple):
    """Represent the display text of a todo item, ready to be printed"""

    prefix: str
    text: str


def _get_bullet(indentation_level: int) -> str:
    symbols = (
        "•",
        "◦",
        "▪",
        "▫",
    )
    return symbols[indentation_level // INDENT % len(symbols)]


def _get_checkmark(simple: bool) -> str:
    return "X" if simple else "✓"


def make_printable_sublist(
    height: int,
    lst: list[_T],
    cursor: int,
    distance: int = -1,
    prev_start: int = -1,
) -> SublistItems[_T]:
    """
    Return a tuple including:
        - a slice of a list with length <= height
        focused around the cursor
        - Index of the cursor pointing to the same
        element as before, but adjusted for the slice
        - prev_start value, to be passed back into
        this function

    Args:
        height:
            window height or max length of returned list
        lst:
            list of objects to be sliced
        cursor:
            an index of the original list corresponding to a cursor
        distance:
            default distance from the top or bottom of the list to clamp
            the cursor. If the length of the list is 20 and distance is 5,
            make_printable_sublist will try to clamp the cursor between
            index 5 and 15.
        prev_start:
            enter the previous cursor position. If this is the first
            time you are calling this function, pass in a value < 1.
    """
    start = max(0, prev_start)
    if len(lst) < height or height < 0:
        return SublistItems(lst, cursor, start)
    if distance == 0:
        return SublistItems(lst[cursor : min(cursor + height, len(lst))])
    distance = height // 4 if distance < 0 else distance
    if cursor <= distance + start - 1:
        start = max(0, cursor - distance + 1)
    elif cursor > height - distance + start:
        start = cursor - height + distance
    end = start + height
    if end > len(lst):
        end = len(lst)
        start = end - height
    return SublistItems(lst[start:end], cursor - start, start)


def _info_message(stdscr: CursesWindow, height: int, width: int) -> None:
    text = (
        "Ndo - an ncurses todo application",
        "",
        "by Gabriel Natenshon",
        "Press `o` to add a new todo",
        "Or press `h` to view a help menu",
    )
    maxlen = len(max(text, key=len))
    for i, line in enumerate(text):
        stdscr.addstr(
            height // 3 + i,
            (width - maxlen) // 2,
            line.center(maxlen),
        )


def _get_height_width(stdscr: CursesWindow | None) -> tuple[int, int]:
    if stdscr is None:
        return 0, 0
    return stdscr.getmaxyx()


def _add_ellipsis(
    string: str,
    prefix_len: int,
    max_length: int,
) -> str:
    """
    Add an ellipsis to the end of a string
    if len(`string`) + `prefix_len` > `max_length`.

    The length of the returned string should have
    `len` == `max_length` - `prefix_len`
    (unless `max_length` is less than len(`ellipsis`))
    """
    if prefix_len + len(string) <= max_length:
        return string
    ellipsis = "..." if SIMPLE_BOXES else "…"
    return string[: max_length - len(ellipsis) - prefix_len] + ellipsis


def _get_enumeration_info(
    relative_pos: int,
    absolute_pos: int,
    zfill_width: int,
    adjusted_highlight: range,
) -> str:
    if not (ENUMERATE or RELATIVE_ENUMERATE):
        return ""

    pos = relative_pos if RELATIVE_ENUMERATE else absolute_pos + 1
    justify = str.ljust if absolute_pos in adjusted_highlight else str.rjust

    return justify(str(pos), zfill_width) + " "


def _get_display_strings(
    todo: Todo,
    should_highlight: bool,
    enumeration_info: str,
    width: int,
) -> _DisplayText:
    """
    Return a tuple of strings representing a single todo item,
    to be printed to the screen

    The strings are ordered and should be printed in order.

    1. Meta information about the item's position
    2. The todo display text
    """
    if should_highlight and todo.is_empty():
        return _DisplayText("─" * (width - 1), "")
    before_footers = Chunk.join(
        Chunk(True, todo.get_indent_level() * " "),
        Chunk(
            not todo.is_empty() and not SIMPLE_BOXES and not BULLETS,
            todo.get_box(),
        ),
        Chunk(
            not todo.is_empty() and SIMPLE_BOXES and not BULLETS,
            todo.get_simple_box(),
        ),
        Chunk(
            not todo.is_empty()
            and todo.has_box()
            and BULLETS
            and not todo.is_toggled(),
            f"{_get_bullet(todo.get_indent_level())} ",
        ),
        Chunk(
            not todo.is_empty()
            and todo.has_box()
            and BULLETS
            and todo.is_toggled(),
            f"{_get_checkmark(SIMPLE_BOXES)} ",
        ),
        Chunk(
            UI_TYPE == UiType.NONE and todo.is_toggled(),
            _ANSI_STRIKETHROUGH,
        ),
        Chunk(
            UI_TYPE == UiType.NONE
            and BULLETS
            and todo.get_display_text().startswith("#"),
            _ANSI_BOLD,
        ),
        Chunk(not _DEBUG_FOLD, todo.get_display_text()),
        Chunk(todo.is_folded_parent(), "› ..."),  # noqa: RUF001
        Chunk(todo.is_folded() and _DEBUG_FOLD, "FOLDED"),
        # Chunk(todo._folded == FoldedState.DEFAULT and _DEBUG_FOLD, "DEFAULT"),
    ).ljust(width - 1 - len(enumeration_info), " ")
    return _DisplayText(
        enumeration_info,
        (
            before_footers
            + Chunk.join(
                Chunk(UI_TYPE == UiType.NONE, _ANSI_RESET),
                Chunk(width == 0, " "),
            )
            if UI_TYPE == UiType.NONE
            else _add_ellipsis(
                before_footers,
                len(enumeration_info),
                width - 1,
            )
        ),
    )


@cache
def _find_first_alphanum(text: str) -> int:
    for index, char in enumerate(text, start=_SIMPLE_BOX_WIDTH):
        if char.isalpha():
            return index
    return -1


def _get_strikethrough_range(display_string: str) -> range:
    return range(
        _find_first_alphanum(display_string),
        len(display_string.rstrip()),
    )


def _get_attrs(
    should_strikethrough: bool,
    todo: Todo,
    position: int,
    highlight: range,
) -> int:
    """Return the attributes for the current todo item"""
    attrs = curses.color_pair(todo.get_color().as_int())
    if position in highlight:
        attrs |= curses.A_STANDOUT
    if should_strikethrough and UI_TYPE == UiType.ANSI:
        attrs |= cast(
            "int",
            curses.A_STRIKETHROUGH,  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        )
    if BULLETS and todo.get_display_text().startswith("#"):
        attrs |= curses.A_BOLD
    return attrs


def _print_todo(
    stdscr: CursesWindow,
    todo: Todo,
    display_strings: _DisplayText,
    todo_print_position: tuple[int, int],
    highlight: range,
) -> None:
    """
    todo_print_position is a tuple containing the
    todo_position and print_position, which are
    normally the same
    """
    counter = 0
    position, print_position = todo_print_position
    prefix_attrs = (
        curses.A_STANDOUT | curses.color_pair(todo.get_color().as_int())
        if position in highlight
        else get_extra_info_attrs()
    )
    for column, char in enumerate(display_strings.prefix):
        stdscr.addch(
            position + 1,
            column,
            char,
            prefix_attrs,
        )
    strikethrough_range = _get_strikethrough_range(display_strings.text)
    while counter < len(display_strings.text):
        should_strikethrough = (
            STRIKETHROUGH
            and todo.is_toggled()
            and counter in strikethrough_range
        )
        stdscr.addch(
            print_position + 1,
            len(display_strings.prefix) + counter,
            display_strings.text[counter],
            _get_attrs(
                should_strikethrough,
                todo,
                position,
                highlight,
            ),
        )
        if should_strikethrough and UI_TYPE == UiType.CURSES:
            stdscr.addch(print_position + 1, counter, "\u0336")
        counter += 1


def _color_to_ansi(color: int) -> str:
    if not Color.is_valid(color):
        msg = f"Invalid color code: {color}"
        raise ValueError(msg)
    return f"\u001b[3{color}m"


def print_todos(
    stdscr: CursesWindow | None,
    todos: Todos,
    selected: Cursor,
    prev_start: int = 0,
) -> int:
    """
    Output list of Todo objects to a curses stdscr or stdout.

    Returns a prev_start to be used in the next call to print_todos.
    (Interally calls make_printable_sublist with that value).
    """

    height, width = _get_height_width(stdscr)
    if len(todos) == 0 and stdscr is not None:
        _info_message(stdscr, height, width)
        return 0
    new_todos, temp_selected, prev_start = make_printable_sublist(
        height - 1,
        todos,
        int(selected),
        prev_start=prev_start,
    )
    new_todos = Todos(new_todos)
    highlight = range(temp_selected, len(selected) + temp_selected)
    print_position = -1  # used only with folding
    for relative_pos, (position, todo), absolute_pos in zip(
        [
            *range(temp_selected, 0, -1),
            int(selected) + 1,
            *range(1, len(new_todos) + 1),
        ],
        enumerate(new_todos),
        count(prev_start),
    ):
        print_position += 1
        if stdscr is None:
            display_strings = _get_display_strings(
                new_todos[position],
                False,
                (
                    str(absolute_pos + 1).rjust(len(str(len(todos)))) + " "
                    if ENUMERATE or RELATIVE_ENUMERATE
                    else ""
                ),
                width,
            )
            print(  # noqa: T201
                display_strings.prefix
                + _color_to_ansi(todo.get_color().as_int())
                + display_strings.text,
            )
            continue
        if not todo.is_folded() or _DEBUG_FOLD:
            _print_todo(
                stdscr,
                todo,
                _get_display_strings(
                    new_todos[position],
                    position in highlight,
                    _get_enumeration_info(
                        relative_pos,
                        absolute_pos,
                        len(str(len(todos))) + 1,
                        selected.get(),
                    ),
                    width,
                ),
                (position, print_position),
                highlight,
            )
            continue
        print_position -= 1
    if stdscr is None:
        return 0
    for position in range(height - len(new_todos) - 1):
        stdscr.addstr(position + len(new_todos) + 1, 0, " " * (width - 1))
    return prev_start
