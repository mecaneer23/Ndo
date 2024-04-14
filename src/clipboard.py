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
from src.class_todo import Todo, Todos
from src.get_args import FILENAME, GUI_TYPE, GuiType
from src.io import update_file
from src.utils import alert

if GUI_TYPE == GuiType.ANSI:
    import src.acurses as curses
elif GUI_TYPE == GuiType.TKINTER:
    import src.tcurses as curses  # type: ignore
else:
    import curses  # type: ignore


def copy_todo(
    stdscr: curses.window,
    todos: Todos,
    selected: Cursor,
    copied_todo: Todo,
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
    stdscr: curses.window,
    todos: Todos,
    selected: int,
    copied_todo: Todo,
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
        todo = todo.strip()
        for index, line in enumerate(todo.split("\n"), start=1):
            todos.insert(selected + index, Todo(f"- {line}"))
        return todos
    todos.insert(selected + 1, Todo(f"- {todo}"))
    return todos


def paste_todo(
    stdscr: curses.window,
    todos: Todos,
    selected: Cursor,
    copied_todo: Todo,
) -> Todos:
    """Paste a todo from copied_todo or clipboard if available"""
    temp = todos.copy()
    todos = _todo_from_clipboard(stdscr, todos, int(selected), copied_todo)
    stdscr.clear()
    if temp != todos:
        selected.single_down(len(todos))
    update_file(FILENAME, todos)
    return todos
