"""
Various helpful menus and their helper functions.
"""

# pylint: disable=missing-function-docstring

from typing import Any, Callable

try:
    from pyfiglet import figlet_format as big

    FIGLET_FORMAT_EXISTS = True
except ImportError:
    FIGLET_FORMAT_EXISTS = False

from src.class_cursor import Cursor
from src.class_todo import Todo
from src.get_args import (
    CONTROLS_BEGIN_INDEX,
    CONTROLS_END_INDEX,
    HELP_FILE,
    TKINTER_GUI,
)
from src.get_todo import hline
from src.keys import Key
from src.md_to_py import md_table_to_lines
from src.print_todos import make_printable_sublist
from src.utils import clamp, overflow, set_header

if TKINTER_GUI:
    from tcurses import curses
else:
    import curses


COLORS = {
    "Red": 1,
    "Green": 2,
    "Yellow": 3,
    "Blue": 4,
    "Magenta": 5,
    "Cyan": 6,
    "White": 7,
}


def get_color(color: str) -> int:
    return COLORS[color]


def simple_scroll_keybinds(
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


def help_menu(parent_win: Any) -> None:
    parent_win.clear()
    set_header(parent_win, "Help (k/j to scroll):")
    lines = []
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
        cursor = simple_scroll_keybinds(win, cursor, len(lines), len(new_lines))
        if cursor < 0:
            break
    parent_win.clear()


def magnify(stdscr: Any, todos: list[Todo], selected: Cursor) -> None:
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
        cursor = simple_scroll_keybinds(stdscr, cursor, len(lines), len(new_lines))
        if cursor < 0:
            break
    stdscr.refresh()
    stdscr.clear()


def color_menu(parent_win: Any, original: int) -> int:
    parent_win.clear()
    set_header(parent_win, "Colors:")
    lines = [i.ljust(len(max(COLORS.keys(), key=len))) for i in COLORS]
    win = curses.newwin(
        len(lines) + 2,
        len(lines[0]) + 2,
        1,
        (parent_win.getmaxyx()[1] - (len(lines[0]) + 1)) // 2,
    )
    win.box()
    move_options: dict[int, Callable[[int], int]] = {
        Key.k: lambda cursor: cursor - 1,
        Key.j: lambda cursor: cursor + 1,
        Key.g: lambda _: 0,
        Key.G: lambda _: len(lines) - 1,
        Key.one: lambda _: 0,
        Key.two: lambda _: 1,
        Key.three: lambda _: 2,
        Key.four: lambda _: 3,
        Key.five: lambda _: 4,
        Key.six: lambda _: 5,
        Key.seven: lambda _: 6,
    }
    cursor = original - 1
    while True:
        parent_win.refresh()
        for i, line in enumerate(lines):
            win.addstr(
                i + 1,
                1,
                line,
                curses.color_pair(get_color(line.strip()))
                | (curses.A_STANDOUT if i == cursor else 0),
            )
        try:
            key = win.getch()
        except KeyboardInterrupt:
            return original
        return_options: dict[int, Callable[[], int]] = {
            Key.q: lambda: original,
            Key.escape: lambda: original,
            Key.enter: lambda: get_color(lines[cursor].strip()),
        }
        if key in move_options:
            move_func = move_options[key]
            cursor = move_func(cursor)
        elif key in return_options:
            return_func = return_options[key]
            return return_func()
        else:
            continue
        cursor = overflow(cursor, 0, len(lines))
        parent_win.refresh()
        win.refresh()
