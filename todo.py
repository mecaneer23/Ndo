#!/usr/bin/env python3
# pyright: reportMissingModuleSource=false
# pylint: disable=no-name-in-module, missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

import curses
from pathlib import Path
from re import match as re_match
from sys import exit as sys_exit
from typing import Any, Callable

from pyfiglet import figlet_format as big
from pyperclip import copy, paste

from src.class_cursor import Cursor
from src.class_history import UndoRedo
from src.class_mode import Mode
from src.class_todo import Todo
from src.get_args import (
    CONTROLS_BEGIN_INDEX,
    CONTROLS_END_INDEX,
    FILENAME,
    HEADER,
    HELP_FILE,
    NO_GUI,
)
from src.get_todo import hline, set_header, wgetnstr
from src.md_to_py import md_table_to_lines
from src.print_todos import make_printable_sublist, print_todos

PRINT_HISTORY = False
HISTORY_FILE = "debugging/log.txt"

COLORS = {
    "Red": 1,
    "Green": 2,
    "Yellow": 3,
    "Blue": 4,
    "Magenta": 5,
    "Cyan": 6,
    "White": 7,
}


def read_file(filename: Path) -> str:
    if not filename.exists():
        with filename.open("w"):
            return ""
    with filename.open() as file_obj:
        return file_obj.read()


def validate_file(raw_data: str) -> list[Todo]:
    if len(raw_data) == 0:
        return []
    usable_data: list[Todo] = []
    for line in raw_data.split("\n"):
        if len(line) == 0:
            usable_data.append(Todo())  # empty todo
        elif re_match(r"^( *)?([+-])\d? .*$", line):
            usable_data.append(Todo(line))
        elif re_match(r"^( *\d )?.*$", line):
            usable_data.append(Todo(line))  # note
        else:
            raise ValueError(f"Invalid todo: {line}")
    return usable_data


def is_file_externally_updated(filename: Path, todos: list[Todo]) -> bool:
    with filename.open() as file_obj:
        return not validate_file(file_obj.read()) == todos


def clamp(counter: int, minimum: int, maximum: int) -> int:
    return min(max(counter, minimum), maximum - 1)


def update_file(filename: Path, lst: list[Todo]) -> int:
    with filename.open("w", newline="\n") as file_obj:
        return file_obj.write("\n".join(map(repr, lst)))


def insert_todo(
    stdscr: Any, todos: list[Todo], index: int, mode: Mode | None = None
) -> list[Todo]:
    max_y, max_x = stdscr.getmaxyx()
    todo = wgetnstr(
        stdscr,
        curses.newwin(3, max_x * 3 // 4, max_y // 2 - 3, max_x // 8),
        todo=Todo(),
        prev_todo=todos[index - 1] if len(todos) > 0 else Todo(),
        mode=mode,
    )
    if todo.is_empty():
        return todos
    todos.insert(index, todo)
    return todos


def insert_empty_todo(todos: list[Todo], index: int) -> list[Todo]:
    todos.insert(index, Todo())
    return todos


def search(stdscr: Any, todos: list[Todo], selected: Cursor) -> None:
    set_header(stdscr, "Searching...")
    stdscr.refresh()
    max_y, max_x = stdscr.getmaxyx()
    sequence = wgetnstr(
        stdscr,
        curses.newwin(3, max_x * 3 // 4, max_y // 2 - 3, max_x // 8),
        Todo(),
        Todo(),
    ).display_text
    stdscr.clear()
    for i, todo in enumerate(todos[int(selected) :], start=int(selected)):
        if sequence in todo.display_text:
            break
    else:
        selected.set_to(0)
        return
    selected.set_to(i)


def remove_todo(todos: list[Todo], index: int) -> list[Todo]:
    if len(todos) < 1:
        return todos
    todos.pop(index)
    return todos


def move_todos(todos: list[Todo], selected: int, destination: int) -> list[Todo]:
    if min(selected, destination) >= 0 and max(selected, destination) < len(todos):
        todos.insert(selected, todos.pop(destination))
    return todos


def simple_scroll_keybinds(
    win: Any, cursor: int, len_lines: int, len_new_lines: int
) -> int:
    try:
        key = win.getch()
    except KeyboardInterrupt:  # exit on ^C
        return -1
    if key in (259, 107):  # up | k
        cursor = clamp(cursor - 1, 0, len_lines - 2)
    elif key in (258, 106, 10):  # down | j | enter
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
        new_lines, _ = make_printable_sublist(
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
    stdscr.clear()
    set_header(stdscr, "Magnifying...")
    lines = big(todos[int(selected)].display_text, width=stdscr.getmaxyx()[1]).split(
        "\n"
    )
    lines.append("")
    lines = [line.ljust(stdscr.getmaxyx()[1] - 2) for line in lines]
    cursor = 0
    while True:
        new_lines, _ = make_printable_sublist(
            stdscr.getmaxyx()[0] - 1, lines, cursor, 0
        )
        for i, line in enumerate(new_lines):
            stdscr.addstr(i + 1, 1, line)
        stdscr.refresh()
        cursor = simple_scroll_keybinds(stdscr, cursor, len(lines), len(new_lines))
        if cursor < 0:
            break
    stdscr.refresh()
    stdscr.clear()


def get_color(color: str) -> int:
    return COLORS[color]


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
    selected = original - 1
    while True:
        parent_win.refresh()
        for i, line in enumerate(lines):
            win.addstr(
                i + 1,
                1,
                line,
                curses.color_pair(get_color(line.strip()))
                | (curses.A_REVERSE if i == selected else 0),
            )
        try:
            key = win.getch()
        except KeyboardInterrupt:
            return original
        if key == 107:  # k
            selected -= 1
        elif key == 106:  # j
            selected += 1
        elif key == 103:  # g
            selected = 0
        elif key == 71:  # G
            selected = len(lines)
        elif key in (113, 27):  # q | esc
            return original
        elif key == 10:  # enter
            return get_color(lines[selected].strip())
        elif key in range(49, 56):  # numbers
            selected = key - 49
        else:
            continue
        selected = clamp(selected, 0, len(lines))
        parent_win.refresh()
        win.refresh()


def get_indented_sections(todos: list[Todo]) -> list[list[Todo]]:
    indented_sections = []
    section = []
    for todo in todos:
        if todo.indent_level > 0:
            section.append(todo)
            continue
        if len(section) > 0:
            indented_sections.append(section)
        section = [todo]
    indented_sections.append(section)
    return indented_sections


def get_sorting_methods() -> dict[str, Callable[..., str]]:
    return {
        "Alphabetical": lambda top_level_todo: top_level_todo[0].display_text,
        "Completed": lambda top_level_todo: "1"
        if top_level_todo[0].is_toggled()
        else "0",
        "Color": lambda top_level_todo: str(top_level_todo[0].color),
    }


def sort_by(method: str, todos: list[Todo], selected: Cursor) -> tuple[list[Todo], int]:
    key = get_sorting_methods()[method]
    selected_todo = todos[int(selected)]
    sorted_todos = []
    for section in sorted(get_indented_sections(todos), key=key):
        for todo in section:
            sorted_todos.append(todo)
    update_file(FILENAME, sorted_todos)
    return sorted_todos, sorted_todos.index(selected_todo)


def sort_menu(
    parent_win: Any, todos: list[Todo], selected: Cursor
) -> tuple[list[Todo], int]:
    parent_win.clear()
    set_header(parent_win, "Sort by:")
    lines = list(get_sorting_methods().keys())
    win = curses.newwin(
        len(lines) + 2,
        len(lines[0]) + 2,
        1,
        (parent_win.getmaxyx()[1] - (len(max(lines, key=len)) + 1)) // 2,
    )
    win.box()
    cursor = 0
    while True:
        parent_win.refresh()
        for i, line in enumerate(lines):
            win.addstr(
                i + 1,
                1,
                line,
                curses.A_REVERSE if i == cursor else 0,
            )
        try:
            key = win.getch()
        except KeyboardInterrupt:
            return todos, cursor
        if key == 107:  # k
            cursor -= 1
        elif key == 106:  # j
            cursor += 1
        elif key == 103:  # g
            cursor = 0
        elif key == 71:  # G
            cursor = len(lines)
        elif key in (113, 27):  # q | esc
            return todos, cursor
        elif key == 10:  # enter
            return sort_by(lines[cursor], todos, selected)
        else:
            continue
        cursor = clamp(cursor, 0, len(lines))
        parent_win.refresh()
        win.refresh()


def todo_from_clipboard(
    todos: list[Todo], selected: int, copied_todo: Todo
) -> list[Todo]:
    todo = paste()
    if copied_todo.display_text == todo:
        todos.insert(selected + 1, Todo(copied_todo.text))
        return todos
    if "\n" in todo:
        return todos
    todos.insert(selected + 1, Todo(f"- {todo}"))
    return todos


def cursor_up(selected: int, len_todos: int) -> int:
    return clamp(selected - 1, 0, len_todos)


def cursor_down(selected: int, len_todos: int) -> int:
    return clamp(selected + 1, 0, len_todos)


def cursor_top(len_todos: int) -> int:
    return clamp(0, 0, len_todos)


def cursor_bottom(len_todos: int) -> int:
    return clamp(len_todos, 0, len_todos)


def cursor_to(position: int, len_todos: int) -> int:
    return clamp(position, 0, len_todos)


def todo_up(todos: list[Todo], selected: Cursor) -> tuple[list[Todo], list[int]]:
    todos = move_todos(todos, selected.positions[-1], selected.positions[0] - 1)
    update_file(FILENAME, todos)
    selected.slide_up()
    return todos, selected.positions


def todo_down(todos: list[Todo], selected: Cursor) -> tuple[list[Todo], list[int]]:
    todos = move_todos(todos, selected.positions[0], selected.positions[-1] + 1)
    update_file(FILENAME, todos)
    selected.slide_down(len(todos))
    return todos, selected.positions


def new_todo_next(
    stdscr: Any,
    todos: list[Todo],
    selected: int,
    mode: Mode | None = None,
) -> tuple[list[Todo], int]:
    """
    Insert a new todo item below the current cursor position and update the todo list.

    Args:
        stdscr (Any): The standard screen object for terminal UI.
        todos (list[Todo]): The list of todos.
        selected (int): The current cursor position.
        mode (Mode | None): The editing mode (optional).

    Returns:
        tuple[list[Todo], int]: A tuple containing the updated list of todos and the
        new cursor position.
    """
    temp = todos.copy()
    todos = insert_todo(
        stdscr,
        todos,
        selected + 1,
        mode,
    )
    stdscr.clear()
    if temp != todos:
        selected = cursor_down(selected, len(todos))
    update_file(FILENAME, todos)
    return todos, selected


def new_todo_current(stdscr: Any, todos: list[Todo], selected: int) -> list[Todo]:
    todos = insert_todo(stdscr, todos, selected)
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def delete_todo(
    stdscr: Any, todos: list[Todo], selected: Cursor
) -> tuple[list[Todo], int]:
    positions = selected.get_deletable()
    for pos in positions:
        todos = remove_todo(todos, pos)
    selected.set_to(clamp(int(selected), 0, len(todos)))
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos, int(selected)


def color_todo(stdscr: Any, todos: list[Todo], selected: Cursor) -> list[Todo]:
    new_color = color_menu(stdscr, todos[int(selected)].color)
    for pos in selected.positions:
        todos[pos].set_color(new_color)
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def edit_todo(stdscr: Any, todos: list[Todo], selected: int) -> list[Todo]:
    max_y, max_x = stdscr.getmaxyx()
    todo = todos[selected].display_text
    ncols = (
        max(max_x * 3 // 4, len(todo) + 3) if len(todo) < max_x - 1 else max_x * 3 // 4
    )
    begin_x = max_x // 8 if len(todo) < max_x - 1 - ncols else (max_x - ncols) // 2
    edited_todo = wgetnstr(
        stdscr,
        curses.newwin(3, ncols, max_y // 2 - 3, begin_x),
        todo=todos[selected],
        prev_todo=Todo(),
    )
    if edited_todo.is_empty():
        return todos
    todos[selected] = edited_todo
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def copy_todo(todos: list[Todo], selected: Cursor, copied_todo: Todo) -> None:
    copy(todos[int(selected)].display_text)
    copied_todo.call_init(todos[int(selected)].text)


def paste_todo(
    stdscr: Any, todos: list[Todo], selected: int, copied_todo: Todo
) -> tuple[list[Todo], int]:
    temp = todos.copy()
    todos = todo_from_clipboard(todos, selected, copied_todo)
    stdscr.clear()
    if temp != todos:
        selected = cursor_down(selected, len(todos))
    update_file(FILENAME, todos)
    return todos, selected


def blank_todo(todos: list[Todo], selected: int) -> tuple[list[Todo], int]:
    insert_empty_todo(todos, selected + 1)
    selected = cursor_down(selected, len(todos))
    update_file(FILENAME, todos)
    return todos, selected


def toggle(todos: list[Todo], selected: Cursor) -> list[Todo]:
    for pos in selected.positions:
        todos[pos].toggle()
    update_file(FILENAME, todos)
    return todos


def remove_file(filename: Path) -> int:
    filename.unlink()
    return 0


def quit_program(todos: list[Todo], edits: int) -> int:
    if is_file_externally_updated(FILENAME, todos):
        todos = validate_file(read_file(FILENAME))
    if edits < 2:
        return remove_file(FILENAME)
    return update_file(FILENAME, todos)


def relative_cursor_to(
    win: Any, todos: list[Todo], selected: int, first_digit: int
) -> int:
    total = str(first_digit)
    while True:
        try:
            key = win.getch()
        except KeyboardInterrupt:  # exit on ^C
            return selected
        if key in (259, 107):  # up | k
            return cursor_to(
                selected - int(total),
                len(todos),
            )
        if key in (258, 106):  # down | j
            return cursor_to(
                selected + int(total),
                len(todos),
            )
        if key in (103, 71):  # g | G
            return cursor_to(int(total) - 1, len(todos))
        if key in range(48, 58):  # digits
            total += str(key - 48)
            continue
        return selected


def indent(todos: list[Todo], selected: Cursor) -> tuple[list[Todo], int]:
    for pos in selected.positions:
        todos[pos].indent()
    update_file(FILENAME, todos)
    return todos, selected.positions[0]


def dedent(todos: list[Todo], selected: Cursor) -> tuple[list[Todo], int]:
    for pos in selected.positions:
        todos[pos].dedent()
    update_file(FILENAME, todos)
    return todos, selected.positions[0]


def toggle_todo_note(todos: list[Todo], selected: Cursor) -> None:
    for pos in selected.positions:
        todo = todos[pos]
        todo.box_char = None if todo.has_box() else "-"
    update_file(FILENAME, todos)


def handle_cursor_up(todos: list[Todo], selected: Cursor) -> None:
    selected.set_to(cursor_up(int(selected), len(todos)))


def handle_cursor_down(todos: list[Todo], selected: Cursor) -> None:
    selected.set_to(cursor_down(int(selected), len(todos)))


def handle_new_todo_next(
    stdscr: Any, todos: list[Todo], selected: Cursor, mode: Mode
) -> list[Todo]:
    return selected.todo_set_to(
        new_todo_next(
            stdscr,
            todos,
            int(selected),
            mode,
        )
    )


def handle_delete_todo(
    stdscr: Any, todos: list[Todo], selected: Cursor, copied_todo: Todo
) -> list[Todo]:
    if len(todos) > 0:
        copy_todo(todos, selected, copied_todo)
    return selected.todo_set_to(delete_todo(stdscr, todos, selected))


def handle_undo(selected: Cursor, history: UndoRedo) -> list[Todo]:
    todos = selected.todo_set_to(history.undo())
    update_file(FILENAME, todos)
    return todos


def handle_redo(selected: Cursor, history: UndoRedo) -> list[Todo]:
    todos = selected.todo_set_to(history.redo())
    update_file(FILENAME, todos)
    return todos


def handle_edit(
    stdscr: Any,
    todos: list[Todo],
    selected: Cursor,
):
    if len(todos) <= 0:
        return todos
    return edit_todo(stdscr, todos, int(selected))


def handle_to_top(todos: list[Todo], selected: Cursor) -> None:
    selected.set_to(cursor_top(len(todos)))


def handle_to_bottom(todos: list[Todo], selected: Cursor) -> None:
    selected.set_to(cursor_bottom(len(todos)))


def handle_paste(
    stdscr: Any,
    todos: list[Todo],
    selected: Cursor,
    copied_todo: Todo,
) -> list[Todo]:
    return selected.todo_set_to(
        paste_todo(
            stdscr,
            todos,
            int(selected),
            copied_todo,
        )
    )


def handle_insert_blank_todo(
    todos: list[Todo],
    selected: Cursor,
) -> list[Todo]:
    return selected.todo_set_to(blank_todo(todos, int(selected)))


def handle_todo_down(
    todos: list[Todo],
    selected: Cursor,
) -> list[Todo]:
    return selected.todos_override(*todo_down(todos, selected))


def handle_todo_up(
    todos: list[Todo],
    selected: Cursor,
):
    return selected.todos_override(*todo_up(todos, selected))


def handle_indent(
    todos: list[Todo],
    selected: Cursor,
) -> list[Todo]:
    return selected.todo_set_to(indent(todos, selected))


def handle_dedent(
    todos: list[Todo],
    selected: Cursor,
) -> list[Todo]:
    return selected.todo_set_to(dedent(todos, selected))


def handle_sort_menu(
    stdscr: Any,
    todos: list[Todo],
    selected: Cursor,
) -> list[Todo]:
    return selected.todo_set_to(sort_menu(stdscr, todos, selected))


def handle_digits(stdscr: Any, todos: list[Todo], selected: Cursor, digit: int) -> None:
    selected.set_to(relative_cursor_to(stdscr, todos, int(selected), digit - 48))


def handle_enter(
    stdscr: Any, todos: list[Todo], selected: Cursor, mode: Mode
) -> list[Todo]:
    prev_todo = todos[int(selected)] if len(todos) > 0 else Todo()
    if prev_todo.has_box():
        return toggle(todos, selected)
    return selected.todo_set_to(new_todo_next(stdscr, todos, int(selected), mode))


def print_history(history: UndoRedo) -> None:
    if PRINT_HISTORY:
        with open(HISTORY_FILE, "w", encoding="utf-8") as log_file:
            print(history, file=log_file)


def init() -> None:
    curses.use_default_colors()
    curses.curs_set(0)
    for i, color in enumerate(
        [
            curses.COLOR_RED,
            curses.COLOR_GREEN,
            curses.COLOR_YELLOW,
            curses.COLOR_BLUE,
            curses.COLOR_MAGENTA,
            curses.COLOR_CYAN,
            curses.COLOR_WHITE,
        ],
        start=1,
    ):
        curses.init_pair(i, color, -1)


def main(stdscr: Any, header: str) -> int:
    init()
    todos = validate_file(read_file(FILENAME))
    selected = Cursor(0)
    history = UndoRedo()
    mode = Mode(True)
    copied_todo = Todo()
    edits = len(todos)
    # if adding a new feature that updates `todos`,
    # make sure it also calls update_file()
    keys: dict[int, tuple[str, Callable[..., Any], str]] = {
        9: ("tab", handle_indent, "todos, selected"),
        10: ("enter", handle_enter, "stdscr, todos, selected, mode"),
        11: ("ctrl + k", mode.toggle, "None"),
        18: ("ctrl + r", handle_redo, "selected, history"),
        24: ("ctrl + x", mode.toggle, "None"),
        27: ("esc sequence", lambda: None, "None"),
        45: ("-", handle_insert_blank_todo, "todos, selected"),
        47: ("/", search, "stdscr, todos, selected"),
        48: ("0", handle_digits, "stdscr, todos, selected, 48"),
        49: ("1", handle_digits, "stdscr, todos, selected, 49"),
        50: ("2", handle_digits, "stdscr, todos, selected, 50"),
        51: ("3", handle_digits, "stdscr, todos, selected, 51"),
        52: ("4", handle_digits, "stdscr, todos, selected, 52"),
        53: ("5", handle_digits, "stdscr, todos, selected, 53"),
        54: ("6", handle_digits, "stdscr, todos, selected, 54"),
        55: ("7", handle_digits, "stdscr, todos, selected, 55"),
        56: ("8", handle_digits, "stdscr, todos, selected, 56"),
        57: ("9", handle_digits, "stdscr, todos, selected, 57"),
        71: ("G", handle_to_bottom, "todos, selected"),
        74: ("J", selected.multiselect_down, "len(todos)"),
        75: ("K", selected.multiselect_up, "None"),
        79: ("O", new_todo_current, "stdscr, todos, int(selected"),
        98: ("b", magnify, "stdscr, todos, selected"),
        99: ("c", color_todo, "stdscr, todos, selected"),
        100: ("d", handle_delete_todo, "stdscr, todos, selected, copied_todo"),
        103: ("g", handle_to_top, "todos, selected"),
        104: ("h", help_menu, "stdscr"),
        105: ("i", handle_edit, "stdscr, todos, selected"),
        106: ("j", handle_cursor_down, "todos, selected"),
        107: ("k", handle_cursor_up, "todos, selected"),
        111: ("o", handle_new_todo_next, "stdscr, todos, selected, mode"),
        112: ("p", handle_paste, "stdscr, todos, selected, copied_todo"),
        115: ("s", handle_sort_menu, "stdscr, todos, selected"),
        117: ("u", handle_undo, "selected, history"),
        121: ("y", copy_todo, "todos, selected, copied_todo"),
        258: ("down", handle_cursor_down, "todos, selected"),
        259: ("up", handle_cursor_up, "todos, selected"),
        330: ("delete", toggle_todo_note, "todos, selected"),
        351: ("shift + tab", handle_dedent, "todos, selected"),
        353: ("shift + tab", handle_dedent, "todos, selected"),
        426: (
            "alt + j (on windows)",
            handle_todo_down,
            "todos, selected",
        ),
        427: (
            "alt + k (on windows)",
            handle_todo_up,
            "todos, selected",
        ),
    }
    esc_keys: dict[int, tuple[str, Callable[..., Any], str]] = {
        71: ("alt + G", selected.multiselect_bottom, "len(todos)"),
        103: ("alt + g", selected.multiselect_top, "None"),
        106: ("alt + j", handle_todo_down, "todos, selected"),
        107: ("alt + k", handle_todo_up, "todos, selected"),
        48: ("0", selected.multiselect_from, "stdscr, 0, len(todos)"),
        49: ("1", selected.multiselect_from, "stdscr, 1, len(todos)"),
        50: ("2", selected.multiselect_from, "stdscr, 2, len(todos)"),
        51: ("3", selected.multiselect_from, "stdscr, 3, len(todos)"),
        52: ("4", selected.multiselect_from, "stdscr, 4, len(todos)"),
        53: ("5", selected.multiselect_from, "stdscr, 5, len(todos)"),
        54: ("6", selected.multiselect_from, "stdscr, 6, len(todos)"),
        55: ("7", selected.multiselect_from, "stdscr, 7, len(todos)"),
        56: ("8", selected.multiselect_from, "stdscr, 8, len(todos)"),
        57: ("9", selected.multiselect_from, "stdscr, 9, len(todos)"),
    }
    history.add(todos, int(selected))
    print_history(history)

    while True:
        edits += 1
        if is_file_externally_updated(FILENAME, todos):
            todos = validate_file(read_file(FILENAME))
        set_header(stdscr, f"{header}:")
        print_todos(stdscr, todos, selected)
        stdscr.refresh()
        if mode.is_not_on():
            todos = handle_new_todo_next(stdscr, todos, selected, mode)
            continue
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:  # exit on ^C
            return quit_program(todos, edits)
        if key == 113:  # q
            return quit_program(todos, edits)
        if key in keys:
            _, func, args = keys[key]
            if key == 27:
                stdscr.nodelay(True)
                key = stdscr.getch()
                stdscr.nodelay(False)
                if key == -1:  # escape, otherwise skip `[`
                    return quit_program(todos, edits)
                if key not in esc_keys:
                    continue
                _, func, args = esc_keys[key]
            possible_args = {
                "0": 0,
                "1": 1,
                "2": 2,
                "3": 3,
                "4": 4,
                "5": 5,
                "6": 6,
                "7": 7,
                "8": 8,
                "9": 9,
                "48": 48,
                "49": 49,
                "50": 50,
                "51": 51,
                "52": 52,
                "53": 53,
                "54": 54,
                "55": 55,
                "56": 56,
                "57": 57,
                "copied_todo": copied_todo,
                "history": history,
                "len(todos)": len(todos),
                "mode": mode,
                "None": "None",
                "selected": selected,
                "stdscr": stdscr,
                "todos": todos,
            }
            possible_todos = func(
                *[possible_args[arg] for arg in args.split(", ") if arg != "None"]
            )
            if possible_todos is not None:
                todos = possible_todos
            del possible_todos
            if key not in (18, 117):  # redo/undo
                history.add(todos, int(selected))
            print_history(history)
            continue
        edits -= 1


if __name__ == "__main__":
    if NO_GUI:
        print(f"{HEADER}:")
        print_todos(None, validate_file(read_file(FILENAME)), Cursor(0))
        sys_exit()
    curses.wrapper(main, header=HEADER)
