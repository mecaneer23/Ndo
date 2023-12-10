"""
Clipboard functionality. If pyperclip is available, use it,
otherwise support copy/paste functionality only within Ndo.
"""

# pylint: disable=missing-function-docstring

from typing import Any

try:
    from pyperclip import copy, paste

    CLIPBOARD_EXISTS = True
except ImportError:
    CLIPBOARD_EXISTS = False

from src.class_cursor import Cursor
from src.class_todo import Todo
from src.cursor_movement import cursor_down
from src.get_args import FILENAME
from src.io import update_file
from src.utils import set_header


def todo_from_clipboard(
    stdscr: Any, todos: list[Todo], selected: int, copied_todo: Todo
) -> list[Todo]:
    if not CLIPBOARD_EXISTS:
        set_header(stdscr, "Clipboard functionality not available")
        return todos
    todo = paste()  # pyright: ignore
    if copied_todo.display_text == todo:
        todos.insert(selected + 1, Todo(copied_todo.text))
        return todos
    if "\n" in todo:
        return todos
    todos.insert(selected + 1, Todo(f"- {todo}"))
    return todos


def copy_todo(
    stdscr: Any, todos: list[Todo], selected: Cursor, copied_todo: Todo
) -> None:
    if not CLIPBOARD_EXISTS:
        set_header(stdscr, "Clipboard functionality not available")
        return
    copy(todos[int(selected)].display_text)  # pyright: ignore
    copied_todo.call_init(todos[int(selected)].text)


def paste_todo(
    stdscr: Any, todos: list[Todo], selected: int, copied_todo: Todo
) -> tuple[list[Todo], int]:
    temp = todos.copy()
    todos = todo_from_clipboard(stdscr, todos, selected, copied_todo)
    stdscr.clear()
    if temp != todos:
        selected = cursor_down(selected, len(todos))
    update_file(FILENAME, todos)
    return todos, selected
