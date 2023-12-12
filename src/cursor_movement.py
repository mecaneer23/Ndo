"""
Various ways to move a cursor represented by an int
"""

# pylint: disable=missing-function-docstring

from typing import Any

from src.class_todo import Todo
from src.keys import Key
from src.utils import clamp


def relative_cursor_to(
    win: Any, todos: list[Todo], selected: int, first_digit: int
) -> int:
    total = str(first_digit)
    while True:
        try:
            key = win.getch()
        except Key.ctrl_c:
            return selected
        if key in (Key.up, Key.k):
            return cursor_to(
                selected - int(total),
                len(todos),
            )
        if key in (Key.down, Key.j):
            return cursor_to(
                selected + int(total),
                len(todos),
            )
        if key in (Key.g, Key.G):
            return cursor_to(int(total) - 1, len(todos))
        if key in Key.digits():
            total += str(Key.normalize_ascii_digit_to_digit(key))
            continue
        return selected


def cursor_up(selected: int, len_todos: int) -> int:
    return clamp(selected - 1, 0, len_todos)


def cursor_down(selected: int, len_todos: int) -> int:
    return clamp(selected + 1, 0, len_todos)


def cursor_top(len_todos: int) -> int:
    return clamp(0, 0, len_todos)


def cursor_bottom(len_todos: int) -> int:
    return clamp(len_todos, 0, len_todos)


def cursor_to(position: int, len_todos: int) -> int:
    return clamp(position, 0, len_todos)
