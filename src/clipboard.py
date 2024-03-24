"""
Clipboard functionality. If pyperclip is available, use it,
otherwise support copy/paste functionality only within Ndo.
"""

try:
    from pyperclip import copy, paste

    CLIPBOARD_EXISTS = True
except ImportError:
    CLIPBOARD_EXISTS = False  # pyright: ignore[reportConstantRedefinition]

from src.class_cursor import Cursor
from src.class_todo import Todo, TodoList, Todos
from src.cursor_movement import cursor_down
from src.get_args import FILENAME, TKINTER_GUI
from src.io import update_file
from src.menus import alert

if TKINTER_GUI:
    import src.tcurses as curses
else:
    import curses  # type: ignore


def copy_todo(
    stdscr: curses.window, todos: Todos, selected: Cursor, copied_todo: Todo
) -> None:
    """
    Set `copied_todo` to be a duplicate of the first selected Todo.
    If possible, also copy to the clipboard.
    """
    copied_todo.set_text(repr(todos[int(selected)]))
    if not CLIPBOARD_EXISTS:
        alert(
            stdscr,
            "Copy dependency not available: try running `pip install pyperclip`",
        )
        return
    copy(todos[int(selected)].get_display_text())  # pyright: ignore


def _todo_from_clipboard(
    stdscr: curses.window, todos: Todos, selected: int, copied_todo: Todo
) -> Todos:
    """Retrieve copied_todo and insert into todo list"""
    if not CLIPBOARD_EXISTS:
        alert(
            stdscr,
            "Paste dependency not available: try running `pip install pyperclip`",
        )
        return todos
    todo = paste()  # pyright: ignore
    if copied_todo.get_display_text() == todo:
        todos.insert(selected + 1, Todo(repr(copied_todo)))
        return todos
    if "\n" in todo:
        return todos
    todos.insert(selected + 1, Todo(f"- {todo}"))
    return todos


def paste_todo(
    stdscr: curses.window, todos: Todos, selected: int, copied_todo: Todo
) -> TodoList:
    """Paste a todo from copied_todo or clipboard if available"""
    temp = todos.copy()
    todos = _todo_from_clipboard(stdscr, todos, selected, copied_todo)
    stdscr.clear()
    if temp != todos:
        selected = cursor_down(selected, len(todos))
    update_file(FILENAME, todos)
    return TodoList(todos, selected)
