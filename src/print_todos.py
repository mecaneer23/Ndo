# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

from typing import Any, TypeVar
from os import get_terminal_size
import curses

from src.class_todo import Todo
from src.class_cursor import Cursor
from src.get_args import (
    INDENT,
    STRIKETHROUGH,
    SIMPLE_BOXES,
    BULLETS,
    ENUMERATE,
    RELATIVE_ENUMERATE,
)


T = TypeVar("T")


def get_bullet(indentation_level: int) -> str:
    symbols = [
        "•",
        "◦",
        "▪",
        "▫",
    ]
    return symbols[indentation_level // INDENT % len(symbols)]


def make_printable_sublist(
    height: int,
    lst: list[T],
    cursor: int,
    distance: int = -1,
    prev_start: int = -1,
) -> tuple[list[T], int, int]:
    start = prev_start if prev_start > 0 else 0
    if len(lst) < height:
        return lst, cursor, start
    if distance == 0:
        return lst[cursor : min(cursor + height, len(lst))], 0, 0
    distance = height // 4 if distance < 0 else distance
    if cursor <= distance + start - 1:
        start = max(0, cursor - distance + 1)
    elif cursor > height - distance + start:
        start = cursor - height + distance
    end = start + height
    if end > len(lst):
        end = len(lst)
        start = end - height
    return lst[start:end], cursor - start, start


def info_message(win: Any, height: int, width: int) -> None:
    text = [
        "Ndo - an ncurses todo application",
        "",
        "by Gabriel Natenshon",
        "Press `o` to add a new todo",
        "Or press `h` to view a help menu",
    ]
    maxlen = len(max(text, key=len))
    for i, line in enumerate(text):
        win.addstr(height // 3 + i, (width - maxlen) // 2, line.center(maxlen))


def get_height_width(win: Any | None, length: int) -> tuple[int, int]:
    if win is None:
        width, height = get_terminal_size()
        return height, width
    height, width = win.getmaxyx()
    if length == 0:
        info_message(win, height, width)
        raise RuntimeError("No todos to display")
    return height, width


def get_display_string(
    todos: list[Todo],
    i_todo: tuple[int, Todo],
    relative: int,
    highlight: range,
    height_width: tuple[int, int],
) -> str:
    i, todo = i_todo
    _, width = height_width
    if i in highlight and todo.is_empty():
        return "⎯" * 8
    chunks: tuple[tuple[bool, str], ...] = (
        (True, todo.indent_level * " "),
        (not todo.is_empty() and not SIMPLE_BOXES, todo.get_box()),
        (not todo.is_empty() and SIMPLE_BOXES, todo.get_simple_box()),
        (not todo.has_box() and BULLETS, f"{get_bullet(todo.indent_level)} "),
        (ENUMERATE and not RELATIVE_ENUMERATE, f"{todos.index(todo) + 1}. "),
        (RELATIVE_ENUMERATE, f"{relative + 1}. "),
        (True, todo.display_text),
    )
    return "".join([item for condition, item in chunks if condition])[
        : width - 1
    ].ljust(width - 1, " ")


def print_todo(
    win: Any, todo: Todo, display_string: str, i: int, highlight: range
) -> None:
    counter = 0
    while counter < len(display_string) - 1:
        if (
            STRIKETHROUGH
            and todo.is_toggled()
            and todo.indent_level + 2
            < counter - 1
            < len(display_string.strip()) + todo.indent_level
        ):
            win.addch(i + 1, counter, "\u0336")
        try:
            win.addch(
                i + 1,
                counter,
                display_string[counter],
                curses.color_pair(todo.color or 7)
                | (curses.A_STANDOUT if i in highlight else 0),
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
        counter += 1


def print_todos(
    win: Any, todos: list[Todo], selected: Cursor, prev_start: int = 0
) -> int:
    try:
        height, width = get_height_width(win, len(todos))
    except RuntimeError:
        return 0
    new_todos, temp_selected, prev_start = make_printable_sublist(
        height - 1, todos, int(selected), prev_start=prev_start
    )
    highlight = range(temp_selected, len(selected) + temp_selected)
    for relative, (i, todo) in zip(
        [*range(temp_selected - 1, -1, -1), int(selected), *range(0, len(new_todos))],
        enumerate(new_todos),
    ):
        display_string = get_display_string(
            todos, (i, todo), relative, highlight, (height, width)
        )
        if win is None:
            print(
                "\u001b["
                + str(
                    {
                        1: 31,
                        2: 32,
                        3: 33,
                        4: 34,
                        5: 35,
                        6: 36,
                        7: 37,
                    }[todo.color]
                )
                + "m"
                + display_string
                + "\u001b[0m"
            )
            continue
        print_todo(win, todo, display_string, i, highlight)
    if win is None:
        return 0
    for i in range(height - len(new_todos) - 1):
        win.addstr(i + len(new_todos) + 1, 0, " " * (width - 1))
    return prev_start
