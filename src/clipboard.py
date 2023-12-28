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
    CLIPBOARD_EXISTS = False  # pyright: ignore[reportConstantRedefinition]

from src.class_cursor import Cursor
from src.class_todo import Todo, Todos, TodoList
from src.cursor_movement import cursor_down
from src.get_args import FILENAME
from src.io import update_file


def copy_todo(todos: Todos, selected: Cursor, copied_todo: Todo) -> None:
    copied_todo.call_init(todos[int(selected)].text)
    if CLIPBOARD_EXISTS:
        copy(todos[int(selected)].display_text)  # pyright: ignore


def todo_from_clipboard(todos: Todos, selected: int, copied_todo: Todo) -> Todos:
    if not CLIPBOARD_EXISTS:
        return todos
    todo = paste()  # pyright: ignore
    if copied_todo.display_text == todo:
        todos.insert(selected + 1, Todo(copied_todo.text))
        return todos
    if "\n" in todo:
        return todos
    todos.insert(selected + 1, Todo(f"- {todo}"))
    return todos


def paste_todo(stdscr: Any, todos: Todos, selected: int, copied_todo: Todo) -> TodoList:
    temp = todos.copy()
    todos = todo_from_clipboard(todos, selected, copied_todo)
    stdscr.clear()
    if temp != todos:
        selected = cursor_down(selected, len(todos))
    update_file(FILENAME, todos)
    return TodoList(todos, selected)
