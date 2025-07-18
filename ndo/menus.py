"""
Various helpful menus and their helper functions.
"""

from collections.abc import Iterator
from functools import partial
from typing import Callable, cast

try:
    from pyfiglet import figlet_format as big

    FIGLET_FORMAT_EXISTS = True
except ImportError:
    FIGLET_FORMAT_EXISTS = False  # pyright: ignore[reportConstantRedefinition]

import ndo.get_todo
from ndo.color import Color
from ndo.get_args import FILENAME
from ndo.get_args import curses_module as curses
from ndo.io_ import update_file
from ndo.keys import Key
from ndo.md_to_py import md_table_to_lines
from ndo.print_todos import make_printable_sublist
from ndo.selection import Selection
from ndo.todo import Todo, Todos
from ndo.ui_protocol import CursesWindow
from ndo.utils import clamp, overflow
from ndo.window_interactions import alert, set_header

_REVERSE_NAME = "Reverse current"


def hline(
    win: CursesWindow,
    y_loc: int,
    x_loc: int,
    char: str | int,
    width: int,
) -> None:
    """
    Display a horizontal line starting at (y_loc, x_loc)
    with width `width` consisting of the character `char`
    """
    win.addch(y_loc, x_loc, cast("str", curses.ACS_LTEE))
    win.hline(y_loc, x_loc + 1, cast("str", char), width - 2)
    win.addch(y_loc, x_loc + width - 1, cast("str", curses.ACS_RTEE))


def _simple_scroll_keybinds(
    win: CursesWindow,
    cursor: int,
    len_lines: int,
    len_new_lines: int,
) -> int:
    try:
        key = Key(win.getch())
    except KeyboardInterrupt:
        return -1
    if key in (Key.up_arrow, Key.k):
        cursor = clamp(cursor - 1, 0, len_lines - 2)
    elif key in (Key.down_arrow, Key.j, Key.enter):
        cursor = clamp(cursor + 1, 0, len_lines - len_new_lines - 1)
    else:
        return -1
    return cursor


def _get_move_options(
    len_list: int,
    additional_options: dict[Key, Callable[[int], int]],
) -> dict[Key, Callable[[int], int]]:
    defaults: dict[Key, Callable[[int], int]] = {
        Key.k: lambda cursor: cursor - 1,
        Key.j: lambda cursor: cursor + 1,
        Key.g: lambda _: 0,
        Key.G: lambda _: len_list - 1,
    }
    return defaults | additional_options


def help_menu(
    parent_win: CursesWindow,
    filename: str,
    begin_index: int,
    end_index: int,
) -> None:
    """Show a scrollable help menu, generated from the README"""
    parent_win.clear()
    set_header(parent_win, "Help (k/j to scroll):")
    lines = md_table_to_lines(
        begin_index,
        end_index,
        filename,
        frozenset({"<kbd>", "</kbd>", "(arranged alphabetically)"}),
    )
    ncols = len(lines[0]) + 2
    parent_width = parent_win.getmaxyx()[1]
    if ncols > parent_width:
        alert(
            parent_win,
            (
                f"Window width too small: {parent_width}. "
                f"Must be at least {ncols}."
            ),
        )
        return
    win = curses.newwin(
        min(parent_win.getmaxyx()[0] - 1, len(lines) + 2),
        ncols,
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
            win.getmaxyx()[0] - 4,
            lines[2:],
            cursor,
            0,
        )
        for i, line in enumerate(new_lines):
            win.addstr(i + 3, 1, line)
        win.refresh()
        cursor = _simple_scroll_keybinds(
            win,
            cursor,
            len(lines),
            len(new_lines),
        )
        if cursor < 0:
            break


def magnify_menu(
    stdscr: CursesWindow,
    todos: Todos,
    selected: Selection,
) -> None:
    """
    Magnify the first line of the current selection using pyfiglet.

    The magnified content is scrollable if it should be.
    """
    if not FIGLET_FORMAT_EXISTS:
        alert(
            stdscr,
            "Magnify dependency not available:"
            "try running `pip install pyfiglet`",
        )
        return
    stdscr.clear()
    set_header(stdscr, "Magnifying...")
    lines = big(  # pyright: ignore[reportPossiblyUnboundVariable]
        todos[int(selected)].get_display_text(),
        width=stdscr.getmaxyx()[1],
    ).split("\n")
    lines.append("")
    lines = [line.ljust(stdscr.getmaxyx()[1] - 2) for line in lines]
    cursor = 0
    while True:
        new_lines, _, _ = make_printable_sublist(
            stdscr.getmaxyx()[0] - 2,
            lines,
            cursor,
            0,
        )
        for i, line in enumerate(new_lines):
            stdscr.addstr(i + 1, 1, line)
        stdscr.refresh()
        cursor = _simple_scroll_keybinds(
            stdscr,
            cursor,
            len(lines),
            len(new_lines),
        )
        if cursor < 0:
            break
    stdscr.refresh()
    stdscr.clear()


def color_menu(parent_win: CursesWindow, original: Color) -> Color:
    """
    Show a menu to choose a color.
    Return the chosen Color or Color.NONE if cancelled.
    """
    parent_win.clear()
    set_header(parent_win, "Colors:")
    lines = [
        i.ljust(len(max(Color.as_dict(), key=len))) for i in Color.as_dict()
    ]
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
            key = Key(win.getch())
        except KeyboardInterrupt:
            return Color.NONE
        return_options: dict[Key, Callable[[], Color]] = {
            Key.q: lambda: Color.NONE,
            Key.escape: lambda: Color.NONE,
            Key.enter: partial(Color, Color.as_dict()[lines[cursor].strip()]),
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


def _get_sorting_methods() -> dict[str, Callable[[Todos], str | int]]:
    return {
        "Alphabetical": lambda section: section[0].get_display_text(),
        "Completed last": lambda section: 1 if section[0].is_toggled() else 0,
        "Color (alphabetical)": lambda section: section[0]
        .get_color()
        .as_char(),
        _REVERSE_NAME: lambda _: "",
    }


def _get_min_indent_level(todos: Todos, selected: Selection) -> int:
    """
    Get the minimum indent level of the selected todos.
    """
    if len(selected) == 0:
        return 0
    return min(todos[pos].get_indent_level() for pos in selected.get())


def _get_indented_sections(todos: Todos, min_indent_level: int) -> list[Todos]:
    indented_sections: list[Todos] = []
    section: Todos = Todos([])
    for todo in todos:
        if todo.get_indent_level() > min_indent_level:
            section.append(todo)
            continue
        if len(section) > 0:
            indented_sections.append(section)
        section = Todos([todo])
    indented_sections.append(section)
    return indented_sections


def _sort_by(method: str, todos: Todos, selected: Selection) -> Todos:
    """
    Sort a `Todos` object by the given method. The passed in `Todos`
    object should contain the full list of todos, not just the selected ones.

    Sort the full list only if one or all todos are selected,
    otherwise sort only the selection.
    """
    key = _get_sorting_methods()[method]
    selected_todo: Todo | None = None
    if len(selected) == 1:
        selected_todo = todos[int(selected)]
        selected.multiselect_all(len(todos))
    sorted_todos = Todos([])
    sections = _get_indented_sections(
        Todos(todos[selected.get_first() : selected.get_last() + 1]),
        _get_min_indent_level(todos, selected),
    )
    sort_iterable = (
        reversed(sections)
        if method == _REVERSE_NAME
        else sorted(sections, key=key)
    )
    for section in sort_iterable:
        for todo in section:
            sorted_todos.append(todo)
    full_todos = Todos(
        todos[: selected.get_first()]
        + sorted_todos
        + todos[selected.get_last() + 1 :],
    )
    update_file(FILENAME, full_todos)
    if selected_todo is not None:
        selected.set(sorted_todos.index(selected_todo))
    return full_todos


def sort_menu(
    parent_win: CursesWindow,
    todos: Todos,
    selected: Selection,
) -> Todos:
    """
    Show a menu to choose a method to sort the `Todos`.
    Immediately sort the list and return the sorted list.
    """
    parent_win.clear()
    set_header(parent_win, "Sort by:")
    lines = list(_get_sorting_methods().keys())
    len_longest_line = len(max(lines, key=len))
    win = curses.newwin(
        len(lines) + 2,
        len_longest_line + 2,
        1,
        (parent_win.getmaxyx()[1] - (len_longest_line + 1)) // 2,
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
            key = Key(win.getch())
        except KeyboardInterrupt:
            return todos
        enter = partial(_sort_by, lines[cursor], todos, selected)
        return_options: dict[Key, Callable[..., Todos]] = {
            Key.q: lambda: todos,
            Key.escape: lambda: todos,
            Key.enter: enter,
            Key.enter_: enter,
        }
        if key in return_options:
            return return_options[key]()
        if key not in move_options:
            continue
        func = move_options[key]
        cursor = func(cursor)
        cursor = clamp(cursor, 0, len(lines))
        parent_win.refresh()
        win.refresh()


def get_newwin(stdscr: CursesWindow) -> CursesWindow:
    """
    Create a curses.newwin in the center of the
    screen based on the width and height of the
    window passed in.
    """
    max_y, max_x = stdscr.getmaxyx()
    return curses.newwin(3, max_x * 3 // 4, max_y // 2 - 3, max_x // 8)


def get_search_sequence(stdscr: CursesWindow) -> str:
    """
    Open a menu to search for a given string.
    """
    sequence = (
        ndo.get_todo.InputTodo(
            stdscr,
            get_newwin(stdscr),
            Todo(),
            Todo(),
            header_string="Searching...",
        )
        .get_todo()
        .get_display_text()
    )
    stdscr.clear()
    return sequence


def _get_search_todos(
    todos: Todos,
    selected: Selection,
) -> Iterator[tuple[int, Todo]]:
    start = int(selected) + 1
    yield from enumerate(todos[start:], start=start)
    yield from enumerate(todos[: start - 1])


def next_search_location(
    sequence: str,
    todos: Todos,
    selected: Selection,
) -> None:
    """
    Move the cursor to the next position where the current
    search sequence exists
    """
    for i, todo in _get_search_todos(todos, selected):
        if sequence in todo.get_display_text():
            selected.set(i)
            return
