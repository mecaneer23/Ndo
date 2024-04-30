"""
Helper module to handle printing a list of Todo objects
"""

from functools import cache
from typing import Generic, NamedTuple, TypeVar, cast

from src.class_cursor import Cursor
from src.class_todo import FoldedState, Todo, Todos
from src.get_args import (
    BULLETS,
    ENUMERATE,
    GUI_TYPE,
    INDENT,
    RELATIVE_ENUMERATE,
    SIMPLE_BOXES,
    STRIKETHROUGH,
    GuiType,
)
from src.utils import Chunk, Color

if GUI_TYPE == GuiType.ANSI:
    import src.acurses as curses
elif GUI_TYPE == GuiType.TKINTER:
    import src.tcurses as curses  # type: ignore
else:
    import curses  # type: ignore


T = TypeVar("T")
_ANSI_RESET = "\u001b[0m"
_ANSI_STRIKETHROUGH = "\033[9m\b"
DEBUG_FOLD = False


class SublistItems(Generic[T], NamedTuple):
    """
    NamedTuple representing a slice of a
    list of T, an index within that list,
    and a start value to be passed into
    make_printable_sublist.

    slice: list[T]
    cursor: int
    start: int

    if `int` values aren't provided, they are initialized to 0
    """

    slice: list[T]
    cursor: int = 0
    start: int = 0


def _get_bullet(indentation_level: int) -> str:
    symbols = (
        "•",
        "◦",
        "▪",
        "▫",
    )
    return symbols[indentation_level // INDENT % len(symbols)]


def make_printable_sublist(
    height: int,
    lst: list[T],
    cursor: int,
    distance: int = -1,
    prev_start: int = -1,
) -> SublistItems[T]:
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
    start = prev_start if prev_start > 0 else 0
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


def _info_message(stdscr: curses.window, height: int, width: int) -> None:
    text = (
        "Ndo - an ncurses todo application",
        "",
        "by Gabriel Natenshon",
        "Press `o` to add a new todo",
        "Or press `h` to view a help menu",
    )
    maxlen = len(max(text, key=len))
    for i, line in enumerate(text):
        stdscr.addstr(height // 3 + i, (width - maxlen) // 2, line.center(maxlen))


def _get_height_width(stdscr: curses.window | None, length: int) -> tuple[int, int]:
    if stdscr is None:
        return 0, 0
    height, width = stdscr.getmaxyx()
    if length == 0:
        _info_message(stdscr, height, width)
        raise RuntimeError("No todos to display")
    return height, width


def _get_display_string(  # pylint: disable=too-many-arguments
    todos: Todos,
    position: int,
    relative_pos: int,
    highlight: range,
    width: int,
    print_to_stdout: bool,
) -> str:
    todo = todos[position]
    if position in highlight and todo.is_empty():
        return "⎯" * 8
    return Chunk.join(
        Chunk(True, todo.get_indent_level() * " "),
        Chunk(not todo.is_empty() and not SIMPLE_BOXES, todo.get_box()),
        Chunk(not todo.is_empty() and SIMPLE_BOXES, todo.get_simple_box()),
        Chunk(
            not todo.has_box() and BULLETS,
            f"{_get_bullet(todo.get_indent_level())} ",
        ),
        Chunk(ENUMERATE and not RELATIVE_ENUMERATE, f"{todos.index(todo) + 1}. "),
        Chunk(RELATIVE_ENUMERATE, f"{relative_pos + 1}. "),
        Chunk(print_to_stdout and todo.is_toggled(), _ANSI_STRIKETHROUGH),
        Chunk(not DEBUG_FOLD, todo.get_display_text()),
        Chunk(todo.is_folded_parent(), "› ..."),
        Chunk(todo.is_folded() and DEBUG_FOLD, "FOLDED"),
        Chunk(todo._folded == FoldedState.DEFAULT and DEBUG_FOLD, "DEFAULT"),
        Chunk(print_to_stdout, _ANSI_RESET),
        Chunk(width == 0, " "),
    )[: width - 1].ljust(width - 1, " ")


@cache
def _find_first_alphanum(text: str) -> int:
    for index, char in enumerate(text):
        if char.isalpha():
            return index
    return -1


def _is_within_strikethrough_range(
    counter: int,
    display_string: str,
    window_width: int,
) -> bool:
    # make sure to test with -s and -sx
    # issue lies with Alacritty terminal

    # This only works if the display string is smaller than the window width
    # offset = len(display_string.rstrip()) - len(todo.get_display_text())

    offset = _find_first_alphanum(display_string)
    return (
        offset - 1
        < counter
        < window_width - (window_width - len(display_string.rstrip()))
    )


def _print_todo(
    stdscr: curses.window,
    todo: Todo,
    display_string: str,
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
    while counter < len(display_string) - 1:
        should_strikethrough = (
            STRIKETHROUGH
            and todo.is_toggled()
            and _is_within_strikethrough_range(
                counter,
                display_string,
                stdscr.getmaxyx()[1],
            )
        )
        attrs = curses.color_pair(todo.get_color().as_int() or Color.WHITE.as_int())
        if position in highlight:
            attrs |= curses.A_STANDOUT
        if should_strikethrough and GUI_TYPE == GuiType.ANSI:
            attrs |= cast(int, curses.A_STRIKETHROUGH)  # pyright: ignore
        try:
            stdscr.addch(
                print_position + 1,
                counter,
                display_string[counter],
                attrs,
            )
        except OverflowError:
            # This function call will throw an OverflowError if
            # the terminal doesn't support the box character as it
            # is technically a wide character. By `continue`-ing,
            # we don't print the box character and indirectly
            # prompt the user to use the -x option and use simple
            # boxes when printing.
            counter += 1
            continue
        if should_strikethrough and GUI_TYPE == GuiType.CURSES:
            stdscr.addch(print_position + 1, counter, "\u0336")
        counter += 1


def _color_to_ansi(color: int) -> str:
    ansi_codes: dict[int, int] = {
        1: 31,
        2: 32,
        3: 33,
        4: 34,
        5: 35,
        6: 36,
        7: 37,
    }
    return f"\u001b[{ansi_codes[color]}m"


def print_todos(
    stdscr: curses.window | None,
    todos: Todos,
    selected: Cursor,
    prev_start: int = 0,
) -> int:
    """
    Output list of Todo objects to a curses stdscr or stdout.

    Returns a prev_start to be used in the next call to print_todos.
    (Interally calls make_printable_sublist with that value).
    """

    try:
        height, width = _get_height_width(stdscr, len(todos))
    except RuntimeError:
        return 0
    new_todos, temp_selected, prev_start = make_printable_sublist(
        height - 1,
        list(todos),
        int(selected),
        prev_start=prev_start,
    )
    highlight = range(temp_selected, len(selected) + temp_selected)
    print_position = -1
    for relative, (position, todo) in zip(
        [*range(temp_selected - 1, -1, -1), int(selected), *range(0, len(new_todos))],
        enumerate(new_todos),
    ):
        print_position += 1
        if stdscr is None:
            print(
                _color_to_ansi(todo.get_color().as_int())
                + _get_display_string(
                    Todos(new_todos),
                    position,
                    relative,
                    range(0),
                    width,
                    True,
                ),
            )
            continue
        if not todo.is_folded() or DEBUG_FOLD:
            _print_todo(
                stdscr,
                todo,
                _get_display_string(
                    Todos(new_todos),
                    position,
                    relative,
                    highlight,
                    width,
                    False,
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
