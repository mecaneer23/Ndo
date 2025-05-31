"""
Clipboard functionality. If pyperclip is available, use it,
otherwise support copy/paste functionality only within Ndo.
"""

try:
    from pyperclip import copy, paste

    CLIPBOARD_EXISTS = True
except ImportError:
    CLIPBOARD_EXISTS = False  # pyright: ignore[reportConstantRedefinition]

from ndo.cursor import Cursor
from ndo.get_args import FILENAME
from ndo.io_ import update_file
from ndo.todo import Todo, Todos
from ndo.ui_protocol import CursesWindow
from ndo.window_interactions import alert


def copy_todos(
    stdscr: CursesWindow,
    todos: Todos,
    selected: Cursor,
    copied_todos: Todos,
) -> None:
    """
    Set `copied_todos` to be a duplicate of the selected Todo(s).
    If possible, also copy to the clipboard.
    """
    copied_todos.clear()
    for pos in selected.get():
        copied_todos.append(todos[pos])
    if not CLIPBOARD_EXISTS:
        alert(
            stdscr,
            "Copied internally. External copy dependency not "
            "available: try running `pip install pyperclip`",
        )
        return
    try:
        copy(  # pyright: ignore[reportPossiblyUnboundVariable]
            "\n".join(
                [todos[pos].get_display_text() for pos in selected.get()],
            ),
        )
    except OSError as err:
        exec_format_error = 8
        if err.errno == exec_format_error:
            alert(
                stdscr,
                "OSError: clip.exe format error, continuing without copy. "
                "Consider restarting WSL.",
            )
            return
        raise OSError from err


def _insert_copied_todos(
    copied_todos: Todos,
    todos: Todos,
    selected: int,
) -> Todos:
    """
    Insert copied_todos into todos at the selected position.
    """
    for pos, todo in enumerate(copied_todos, start=1):
        todos.insert(selected + pos, Todo(repr(todo)))
    return todos


def _todos_from_clipboard(
    stdscr: CursesWindow,
    todos: Todos,
    selected: int,
    copied_todos: Todos,
) -> Todos:
    """Retrieve copied_todos and insert into todo list"""
    if not CLIPBOARD_EXISTS:
        todos = _insert_copied_todos(copied_todos, todos, selected)
        alert(
            stdscr,
            "Pasting from internal buffer. External paste dependency "
            "not available: try running `pip install pyperclip`",
        )
        return todos
    pasted = paste()  # pyright: ignore[reportPossiblyUnboundVariable]
    if "\n".join(todo.get_display_text() for todo in copied_todos) == pasted:
        return _insert_copied_todos(copied_todos, todos, selected)
    for index, line in enumerate(pasted.strip().split("\n"), start=1):
        todos.insert(selected + index, Todo(f"- {line}"))
    return todos


def paste_todos(
    stdscr: CursesWindow,
    todos: Todos,
    selected: Cursor,
    copied_todos: Todos,
) -> Todos:
    """Paste todos from copied_todos or clipboard if available"""
    temp = todos.copy()
    todos = _todos_from_clipboard(stdscr, todos, int(selected), copied_todos)
    stdscr.clear()
    if temp != todos:
        selected.single_down(len(todos))
    update_file(FILENAME, todos)
    return todos
