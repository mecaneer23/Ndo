"""
Various ways to move a cursor represented by an int
"""

from typing import Any

from src.class_todo import Todos
from src.keys import Key
from src.utils import clamp


def _cursor_to(position: int, len_todos: int) -> int:
    return clamp(position, 0, len_todos)


def relative_cursor_to(win: Any, todos: Todos, selected: int, first_digit: int) -> int:
    """
    Move the cursor to the specified position relative to the current position.

    Because the trigger can only be a single keypress, this function also uses a
    window object to getch until the user presses g or shift + g. This allows
    for relative movement greater than 9 lines away.
    """
    total = str(first_digit)
    while True:
        try:
            key = win.getch()
        except Key.ctrl_c:
            return selected
        if key in (Key.up, Key.k):
            return _cursor_to(
                selected - int(total),
                len(todos),
            )
        if key in (Key.down, Key.j):
            return _cursor_to(
                selected + int(total),
                len(todos),
            )
        if key in (Key.g, Key.G):
            return _cursor_to(int(total) - 1, len(todos))
        if key in Key.digits():
            total += str(Key.normalize_ascii_digit_to_digit(key))
            continue
        return selected


def cursor_up(selected: int, len_todos: int) -> int:
    """Move the cursor up one position if possible"""
    return clamp(selected - 1, 0, len_todos)


def cursor_down(selected: int, len_todos: int) -> int:
    """Move the cursor down one position if possible"""
    return clamp(selected + 1, 0, len_todos)


def cursor_top(len_todos: int) -> int:
    """Move the cursor to the top of the list"""
    return clamp(0, 0, len_todos)


def cursor_bottom(len_todos: int) -> int:
    """Move the cursor to the bottom of the list"""
    return clamp(len_todos, 0, len_todos)
