"""
Various ways to move a cursor represented by an int
"""

from src.class_todo import Todos
from src.get_args import TKINTER_GUI
from src.keys import Key
from src.utils import clamp

if TKINTER_GUI:
    import src.tcurses as curses
else:
    import curses  # type: ignore


def relative_cursor_to(
    win: curses.window, todos: Todos, selected: int, first_digit: int
) -> int:
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
            return clamp(
                selected - int(total),
                0,
                len(todos),
            )
        if key in (Key.down, Key.j):
            return clamp(
                selected + int(total),
                0,
                len(todos),
            )
        if key in (Key.g, Key.G):
            return clamp(int(total) - 1, 0, len(todos))
        if key in Key.digits():
            total += str(Key.normalize_ascii_digit_to_digit(key))
            continue
        return selected


def cursor_down(selected: int, len_todos: int) -> int:
    """Move the cursor down one position if possible"""
    return clamp(selected + 1, 0, len_todos)
