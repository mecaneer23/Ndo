# pylint: disable=global-statement, missing-class-docstring
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
        # "▫",
    ]
    return symbols[indentation_level // INDENT % len(symbols)]


def strikethrough(text: str) -> str:
    return "\u0336".join(text) if STRIKETHROUGH else text


def make_printable_sublist(
    height: int, lst: list[T], cursor: int, distance: int = -1
) -> tuple[list[T], int]:
    if len(lst) < height:
        return lst, cursor
    distance = height * 3 // 7 if distance < 0 else distance
    start = max(0, cursor - distance)
    end = min(len(lst), start + height)
    # If len(sublist) < height, stop moving list and resume moving cursor
    if end - start < height:
        start = len(lst) - height
        end = len(lst)
    return lst[start:end], cursor - start


def info_message(win: Any, height: int, width: int) -> None:
    text = [
        "Ndo - an ncurses todo application",
        "",
        "by Gabriel Natenshon",
        "Type `o` to add a new todo",
    ]
    maxlen = len(max(text, key=len))
    for i, line in enumerate(text):
        win.addstr(height // 3 + i, (width - maxlen) // 2, line.center(maxlen))


def print_todos(win: Any, todos: list[Todo], selected: Cursor) -> None:
    if win is None:
        width, height = get_terminal_size()
    else:
        height, width = win.getmaxyx()
        if len(todos) < 1:
            info_message(win, height, width)
            return
    new_todos, temp_selected = make_printable_sublist(height - 1, todos, int(selected))
    highlight = range(temp_selected, len(selected) + temp_selected)
    for relative, (i, todo) in zip(
        [*range(temp_selected - 1, -1, -1), int(selected), *range(0, len(new_todos))],
        enumerate(new_todos),
    ):
        if todo.color is None:
            raise ValueError(f"Invalid color for `{todo}`")
        display_string = (
            "".join(
                [
                    todo.indent_level * " ",
                    todo.get_box() if not todo.is_empty() and not SIMPLE_BOXES else "",
                    todo.get_simple_box()
                    if not todo.is_empty() and SIMPLE_BOXES
                    else "",
                    (
                        f"{get_bullet(todo.indent_level)} "
                        if not todo.has_box() and BULLETS
                        else ""
                    ),
                    (
                        f"{todos.index(todo) + 1}. "
                        if ENUMERATE and not RELATIVE_ENUMERATE
                        else ""
                    ),
                    f"{relative + 1}. " if RELATIVE_ENUMERATE else "",
                    (
                        strikethrough(todo.display_text)
                        if todo.is_toggled()
                        else todo.display_text
                    ),
                ]
            )
            if i not in highlight or not todo.is_empty()
            else "⎯" * 8
        )[: width - 1].ljust(width - 1, " ")
        counter = 0
        if win is None:
            print(
                {
                    1: "\u001b[31m",
                    2: "\u001b[32m",
                    3: "\u001b[33m",
                    4: "\u001b[34m",
                    5: "\u001b[35m",
                    6: "\u001b[36m",
                    7: "\u001b[37m",
                }[todo.color]
                + display_string
                + "\u001b[0m"
            )
            continue
        while counter < len(display_string) - 1:
            try:
                win.addch(
                    i + 1,
                    counter,
                    display_string[counter],
                    curses.color_pair(todo.color or 7)
                    | (curses.A_REVERSE if i in highlight else 0),
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
    if win is None:
        return
    for i in range(height - len(new_todos) - 1):
        win.addstr(i + len(new_todos) + 1, 0, " " * (width - 1))
