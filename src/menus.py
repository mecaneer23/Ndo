"""
Various helpful menus and their helper functions.
"""

# pylint: disable=missing-function-docstring

from typing import Any, Callable

try:
    from pyfiglet import figlet_format as big

    FIGLET_FORMAT_EXISTS = True
except ImportError:
    FIGLET_FORMAT_EXISTS = False  # pyright: ignore[reportConstantRedefinition]

from src.class_cursor import Cursor
from src.class_todo import Todo, TodoList, Todos
from src.get_args import (
    CONTROLS_BEGIN_INDEX,
    CONTROLS_END_INDEX,
    FILENAME,
    HELP_FILE,
    TKINTER_GUI,
)
from src.get_todo import get_todo, hline
from src.io import update_file
from src.keys import Key
from src.md_to_py import md_table_to_lines
from src.print_todos import make_printable_sublist
from src.utils import Color, clamp, overflow, set_header

if TKINTER_GUI:
    from tcurses import curses  # pylint: disable=import-error
else:
    import curses


def _simple_scroll_keybinds(
    win: Any, cursor: int, len_lines: int, len_new_lines: int
) -> int:
    try:
        key = win.getch()
    except Key.ctrl_c:
        return -1
    if key in (Key.up, Key.k):
        cursor = clamp(cursor - 1, 0, len_lines - 2)
    elif key in (Key.down, Key.j, Key.enter):
        cursor = clamp(cursor + 1, 0, len_lines - len_new_lines - 1)
    else:
        return -1
    return cursor


def _get_move_options(
    len_list: int, additional_options: dict[int, Callable[[int], int]]
) -> dict[int, Callable[[int], int]]:
    defaults: dict[int, Callable[[int], int]] = {
        Key.k: lambda cursor: cursor - 1,
        Key.j: lambda cursor: cursor + 1,
        Key.g: lambda _: 0,
        Key.G: lambda _: len_list - 1,
    }
    return defaults | additional_options


def help_menu(parent_win: Any) -> None:
    parent_win.clear()
    set_header(parent_win, "Help (k/j to scroll):")
    lines: list[str] = []
    for line in md_table_to_lines(
        CONTROLS_BEGIN_INDEX,
        CONTROLS_END_INDEX,
        str(HELP_FILE),
        ("<kbd>", "</kbd>", "(arranged alphabetically)"),
    ):
        lines.append(line[:-2])
    win = curses.newwin(
        min(parent_win.getmaxyx()[0] - 1, len(lines) + 2),
        len(lines[0]) + 2,
        1,
        (parent_win.getmaxyx()[1] - (len(lines[0]) + 1)) // 2,
    )
    win.box()
    parent_win.refresh()
    cursor = 0
    win.addstr(1, 1, lines[0])
    hline(win, 2, 0, curses.ACS_HLINE, win.getmaxyx()[1])
    while True:
        new_lines, _, _ = make_printable_sublist(
            win.getmaxyx()[0] - 4, lines[2:], cursor, 0
        )
        for i, line in enumerate(new_lines):
            win.addstr(i + 3, 1, line)
        win.refresh()
        cursor = _simple_scroll_keybinds(win, cursor, len(lines), len(new_lines))
        if cursor < 0:
            break
    parent_win.clear()


def magnify(stdscr: Any, todos: Todos, selected: Cursor) -> None:
    if not FIGLET_FORMAT_EXISTS:
        set_header(stdscr, "Magnify dependency not available")
        return
    stdscr.clear()
    set_header(stdscr, "Magnifying...")
    lines = big(  # pyright: ignore
        todos[int(selected)].display_text, width=stdscr.getmaxyx()[1]
    ).split("\n")
    lines.append("")
    lines = [line.ljust(stdscr.getmaxyx()[1] - 2) for line in lines]
    cursor = 0
    while True:
        new_lines, _, _ = make_printable_sublist(
            stdscr.getmaxyx()[0] - 2, lines, cursor, 0
        )
        for i, line in enumerate(new_lines):
            stdscr.addstr(i + 1, 1, line)
        stdscr.refresh()
        cursor = _simple_scroll_keybinds(stdscr, cursor, len(lines), len(new_lines))
        if cursor < 0:
            break
    stdscr.refresh()
    stdscr.clear()


def color_menu(parent_win: Any, original: Color) -> Color:
    parent_win.clear()
    set_header(parent_win, "Colors:")
    lines = [i.ljust(len(max(Color.as_dict(), key=len))) for i in Color.as_dict()]
    win = curses.newwin(
        len(lines) + 2,
        len(lines[0]) + 2,
        1,
        (parent_win.getmaxyx()[1] - (len(lines[0]) + 1)) // 2,
    )
    win.box()
    move_options = _get_move_options(
        len(lines),
        {
            Key.one: lambda _: 0,
            Key.two: lambda _: 1,
            Key.three: lambda _: 2,
            Key.four: lambda _: 3,
            Key.five: lambda _: 4,
            Key.six: lambda _: 5,
            Key.seven: lambda _: 6,
        },
    )
    cursor = original.as_int() - 1
    while True:
        parent_win.refresh()
        for i, line in enumerate(lines):
            win.addstr(
                i + 1,
                1,
                line,
                curses.color_pair(Color.as_dict()[line.strip()])
                | (curses.A_STANDOUT if i == cursor else 0),
            )
        try:
            key = win.getch()
        except KeyboardInterrupt:
            return original
        return_options: dict[int, Callable[[], Color]] = {
            Key.q: lambda: original,
            Key.escape: lambda: original,
            Key.enter: lambda: Color(Color.as_dict()[lines[cursor].strip()]),
        }
        if key in move_options:
            move_func = move_options[key]
            cursor = move_func(cursor)
        elif key in return_options:
            return return_options[key]()
        else:
            continue
        cursor = overflow(cursor, 0, len(lines))
        parent_win.refresh()
        win.refresh()


def _get_sorting_methods() -> dict[str, Callable[[Todos], str]]:
    return {
        "Alphabetical": lambda top_level_todo: top_level_todo[0].display_text,
        "Completed": lambda top_level_todo: "1"
        if top_level_todo[0].is_toggled()
        else "0",
        "Color": lambda top_level_todo: str(top_level_todo[0].color),
    }


def _get_indented_sections(todos: Todos) -> list[Todos]:
    indented_sections: list[Todos] = []
    section: Todos = Todos([])
    for todo in todos:
        if todo.indent_level > 0:
            section.append(todo)
            continue
        if len(section) > 0:
            indented_sections.append(section)
        section = Todos([todo])
    indented_sections.append(section)
    return indented_sections


def _sort_by(method: str, todos: Todos, selected: Cursor) -> TodoList:
    key = _get_sorting_methods()[method]
    selected_todo = todos[int(selected)]
    sorted_todos = Todos([])
    for section in sorted(_get_indented_sections(todos), key=key):
        for todo in section:
            sorted_todos.append(todo)
    update_file(FILENAME, sorted_todos)
    return TodoList(sorted_todos, sorted_todos.index(selected_todo))


def sort_menu(parent_win: Any, todos: Todos, selected: Cursor) -> TodoList:
    parent_win.clear()
    set_header(parent_win, "Sort by:")
    lines = list(_get_sorting_methods().keys())
    win = curses.newwin(
        len(lines) + 2,
        len(lines[0]) + 2,
        1,
        (parent_win.getmaxyx()[1] - (len(max(lines, key=len)) + 1)) // 2,
    )
    win.box()
    move_options = _get_move_options(len(lines), {})
    cursor = 0
    while True:
        parent_win.refresh()
        for i, line in enumerate(lines):
            win.addstr(
                i + 1,
                1,
                line,
                curses.A_STANDOUT if i == cursor else 0,
            )
        try:
            key = win.getch()
        except KeyboardInterrupt:
            return TodoList(todos, int(selected))
        return_options: dict[int, Callable[..., TodoList]] = {
            Key.q: lambda: TodoList(todos, int(selected)),
            Key.escape: lambda: TodoList(todos, int(selected)),
            Key.enter: lambda: _sort_by(lines[cursor], todos, selected),
        }
        if key in move_options:
            func = move_options[key]
            cursor = func(cursor)
        elif key in return_options:
            return return_options[key]()
        else:
            continue
        cursor = clamp(cursor, 0, len(lines))
        parent_win.refresh()
        win.refresh()


def get_newwin(stdscr: Any) -> Any:
    """
    Create a curses.newwin in the center of the
    screen based on the width and height of the
    window passed in.
    """
    max_y, max_x = stdscr.getmaxyx()
    return curses.newwin(3, max_x * 3 // 4, max_y // 2 - 3, max_x // 8)


def search(stdscr: Any, todos: Todos, selected: Cursor) -> None:
    set_header(stdscr, "Searching...")
    stdscr.refresh()
    sequence = get_todo(
        stdscr,
        get_newwin(stdscr),
        Todo(),
        Todo(),
    ).display_text
    stdscr.clear()
    for i, todo in enumerate(todos[int(selected) :], start=int(selected)):
        if sequence in todo.display_text:
            selected.set_to(i)
            return
    selected.set_to(0)
    return
