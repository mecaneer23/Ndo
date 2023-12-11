#!/usr/bin/env python3
# pyright: reportMissingModuleSource=false
# pylint: disable=no-name-in-module, import-error, missing-docstring

from os import stat
from pathlib import Path
from sys import exit as sys_exit
from typing import Any, Callable

from src.class_cursor import Cursor
from src.class_history import UndoRedo
from src.class_mode import SingleLineMode, SingleLineModeImpl
from src.class_todo import Todo
from src.clipboard import CLIPBOARD_EXISTS, copy_todo, paste_todo
from src.cursor_movement import (
    cursor_bottom,
    cursor_down,
    cursor_top,
    cursor_up,
    relative_cursor_to,
)
from src.get_args import (
    FILENAME,
    HEADER,
    NO_GUI,
    TKINTER_GUI,
)
from src.get_todo import set_header, wgetnstr
from src.io import file_string_to_todos, read_file, update_file
from src.keys import Key
from src.menus import color_menu, get_newwin, help_menu, magnify, search, sort_menu
from src.print_todos import print_todos
from src.utils import clamp

if TKINTER_GUI:
    from tcurses import curses
else:
    import curses

PRINT_HISTORY = False
HISTORY_FILE = "debugging/log.txt"


def get_file_modified_time(filename: Path) -> float:
    return stat(filename).st_ctime


def insert_todo(
    stdscr: Any,
    todos: list[Todo],
    index: int,
    default_todo: Todo = Todo(),
    mode: SingleLineModeImpl = SingleLineModeImpl(SingleLineMode.NONE),
) -> list[Todo]:
    todo = wgetnstr(
        stdscr,
        get_newwin(stdscr),
        todo=default_todo,
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


def remove_todo(todos: list[Todo], index: int) -> list[Todo]:
    if len(todos) < 1:
        return todos
    todos.pop(index)
    return todos


def move_todos(todos: list[Todo], selected: int, destination: int) -> list[Todo]:
    if min(selected, destination) >= 0 and max(selected, destination) < len(todos):
        todos.insert(selected, todos.pop(destination))
    return todos


def todo_up(todos: list[Todo], selected: Cursor) -> tuple[list[Todo], list[int]]:
    todos = move_todos(todos, selected.get_last(), selected.get_first() - 1)
    update_file(FILENAME, todos)
    selected.slide_up()
    return todos, selected.get()


def todo_down(todos: list[Todo], selected: Cursor) -> tuple[list[Todo], list[int]]:
    todos = move_todos(todos, selected.get_first(), selected.get_last() + 1)
    update_file(FILENAME, todos)
    selected.slide_down(len(todos))
    return todos, selected.get()


def new_todo_next(
    stdscr: Any,
    todos: list[Todo],
    selected: int,
    default_todo: Todo = Todo(),
    mode: SingleLineModeImpl = SingleLineModeImpl(SingleLineMode.NONE),
) -> tuple[list[Todo], int]:
    """
    Insert a new todo item below the current cursor position and update the todo list.

    Args:
        stdscr (Any): The standard screen object for terminal UI.
        todos (list[Todo]): The list of todos.
        selected (int): The current cursor position.
        mode (SingleLineMode | None): The editing mode (optional).

    Returns:
        tuple[list[Todo], int]: A tuple containing the updated list of todos and the
        new cursor position.
    """
    temp = todos.copy()
    todos = insert_todo(
        stdscr,
        todos,
        selected + 1,
        default_todo=default_todo,
        mode=mode,
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
    for pos in selected.get():
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


def blank_todo(todos: list[Todo], selected: int) -> tuple[list[Todo], int]:
    insert_empty_todo(todos, selected + 1)
    selected = cursor_down(selected, len(todos))
    update_file(FILENAME, todos)
    return todos, selected


def toggle(todos: list[Todo], selected: Cursor) -> list[Todo]:
    for pos in selected.get():
        todos[pos].toggle()
    update_file(FILENAME, todos)
    return todos


def remove_file(filename: Path) -> int:
    filename.unlink()
    return 0


def quit_program(todos: list[Todo], edits: int, prev_time: float) -> int:
    todos, _ = update_modified_time(prev_time, todos)
    if edits < 1:
        return remove_file(FILENAME)
    return update_file(FILENAME, todos)


def indent(todos: list[Todo], selected: Cursor) -> tuple[list[Todo], int]:
    for pos in selected.get():
        todos[pos].indent()
    update_file(FILENAME, todos)
    return todos, selected.get_first()


def dedent(todos: list[Todo], selected: Cursor) -> tuple[list[Todo], int]:
    for pos in selected.get():
        todos[pos].dedent()
    update_file(FILENAME, todos)
    return todos, selected.get_first()


def toggle_todo_note(todos: list[Todo], selected: Cursor) -> None:
    for pos in selected.get():
        todo = todos[pos]
        todo.box_char = None if todo.has_box() else "-"
    update_file(FILENAME, todos)


def handle_cursor_up(todos: list[Todo], selected: Cursor) -> None:
    selected.set_to(cursor_up(int(selected), len(todos)))


def handle_cursor_down(todos: list[Todo], selected: Cursor) -> None:
    selected.set_to(cursor_down(int(selected), len(todos)))


def handle_new_todo_next(
    stdscr: Any,
    todos: list[Todo],
    selected: Cursor,
    mode: SingleLineModeImpl,
    default_todo: Todo = Todo(),
) -> list[Todo]:
    return selected.todo_set_to(
        new_todo_next(
            stdscr,
            todos,
            int(selected),
            default_todo,
            mode,
        )
    )


def handle_delete_todo(
    stdscr: Any, todos: list[Todo], selected: Cursor, copied_todo: Todo
) -> list[Todo]:
    if len(todos) > 0 and CLIPBOARD_EXISTS:
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
    selected.set_to(
        relative_cursor_to(
            stdscr, todos, int(selected), Key.normalize_ascii_digit_to_digit(digit)
        )
    )


def handle_enter(
    stdscr: Any, todos: list[Todo], selected: Cursor, mode: SingleLineModeImpl
) -> list[Todo]:
    prev_todo = todos[int(selected)] if len(todos) > 0 else Todo()
    if prev_todo.has_box():
        return toggle(todos, selected)
    return selected.todo_set_to(new_todo_next(stdscr, todos, int(selected), mode=mode))


def print_history(history: UndoRedo) -> None:
    if PRINT_HISTORY:
        with open(HISTORY_FILE, "w", encoding="utf-8") as log_file:
            print(history, file=log_file)


def get_possible_todos(
    func: Callable[..., list[Todo] | None],
    args: str,
    possible_args: dict[str, Any],
) -> list[Todo] | None:
    params = []
    for arg in args.split(", "):
        if arg.isdigit():
            params.append(int(arg))
            continue
        if arg != "None":
            params.append(possible_args[arg])
    return func(*params)


def get_main_input(
    stdscr: Any,
    todos: list[Todo],
    keys_esckeys: tuple[dict[int, tuple[Callable[..., Any], str]], ...],
    possible_args: dict[str, Any],
) -> int | list[Todo]:
    try:
        key = stdscr.getch()
    except Key.ctrl_c:
        return todos
    if key == Key.q:
        return todos
    if key in keys_esckeys[0]:
        func, args = keys_esckeys[0][key]
        if key == Key.escape:
            stdscr.nodelay(True)
            key = stdscr.getch()
            stdscr.nodelay(False)
            if key == -1:  # escape, otherwise skip `[`
                return todos
            if key not in keys_esckeys[1]:
                return key
            func, args = keys_esckeys[1][key]
        possible_todos = get_possible_todos(
            func,
            args,
            possible_args,
        )
        if possible_todos is not None:
            todos = possible_todos
    return key


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


def update_modified_time(
    prev_time: float, todos: list[Todo]
) -> tuple[list[Todo], float]:
    current_time = get_file_modified_time(FILENAME)
    if prev_time != current_time:
        todos = file_string_to_todos(read_file(FILENAME))
    return todos, current_time


def main(stdscr: Any) -> int:
    """
    The main function for Ndo. Mainly provides keybindings
    for the various functions.

    -------

    Directory of main() variables:

    todos:
    main list of Todo objects - initialized with
    contents of `FILENAME`

    selected:
    main Cursor object for tracking position
    within the list of Todo objects. Initialized at 0

    sublist_top:
    Only used in print_todos() to keep track of relative
    position and ensure the list renders correctly

    history:
    UndoRedo object, stores history for calls to undo/redo

    single_line_state:
    Used to insert multiple Todos simultaneously whenever
    necessary. This is a "global" object that stores state.

    copied_todo:
    A Todo which stores metadata about a todo, such as
    color and indentation level. Used for copy/paste
    operations.

    edits:
    int, used to indicate whether the file was newly
    created and modified or not, determines whether
    to delete file in quit_program()

    file_modified_time:
    Last time of file modification. Used to determine
    when to overwrite the save file.
    """
    init()
    todos = file_string_to_todos(read_file(FILENAME))
    selected = Cursor(0)
    sublist_top = 0
    history = UndoRedo()
    single_line_state = SingleLineModeImpl(SingleLineMode.ON)
    copied_todo = Todo()
    edits = len(todos)
    file_modified_time = get_file_modified_time(FILENAME)
    # if adding a new feature that updates `todos`,
    # make sure it also calls update_file()
    keys: dict[int, tuple[Callable[..., Any], str]] = {
        Key.ctrl_a: (selected.multiselect_all, "len(todos)"),
        Key.tab: (handle_indent, "todos, selected"),
        Key.enter: (handle_enter, "stdscr, todos, selected, single_line_mode"),
        Key.ctrl_k: (single_line_state.toggle, "None"),
        Key.ctrl_r: (handle_redo, "selected, history"),
        Key.ctrl_x: (single_line_state.toggle, "None"),
        Key.escape: (lambda: None, "None"),
        Key.minus: (handle_insert_blank_todo, "todos, selected"),
        Key.slash: (search, "stdscr, todos, selected"),
        Key.zero: (handle_digits, f"stdscr, todos, selected, {Key.zero}"),
        Key.one: (handle_digits, f"stdscr, todos, selected, {Key.one}"),
        Key.two: (handle_digits, f"stdscr, todos, selected, {Key.two}"),
        Key.three: (handle_digits, f"stdscr, todos, selected, {Key.three}"),
        Key.four: (handle_digits, f"stdscr, todos, selected, {Key.four}"),
        Key.five: (handle_digits, f"stdscr, todos, selected, {Key.five}"),
        Key.six: (handle_digits, f"stdscr, todos, selected, {Key.six}"),
        Key.seven: (handle_digits, f"stdscr, todos, selected, {Key.seven}"),
        Key.eight: (handle_digits, f"stdscr, todos, selected, {Key.eight}"),
        Key.nine: (handle_digits, f"stdscr, todos, selected, {Key.nine}"),
        Key.G: (handle_to_bottom, "todos, selected"),
        Key.J: (selected.multiselect_down, "len(todos)"),
        Key.K: (selected.multiselect_up, "None"),
        Key.O: (new_todo_current, "stdscr, todos, int(selected)"),
        Key.b: (magnify, "stdscr, todos, selected"),
        Key.c: (color_todo, "stdscr, todos, selected"),
        Key.d: (handle_delete_todo, "stdscr, todos, selected, copied_todo"),
        Key.g: (handle_to_top, "todos, selected"),
        Key.h: (help_menu, "stdscr"),
        Key.i: (handle_edit, "stdscr, todos, selected"),
        Key.j: (handle_cursor_down, "todos, selected"),
        Key.k: (handle_cursor_up, "todos, selected"),
        Key.o: (handle_new_todo_next, "stdscr, todos, selected, single_line_mode"),
        Key.p: (handle_paste, "stdscr, todos, selected, copied_todo"),
        Key.s: (handle_sort_menu, "stdscr, todos, selected"),
        Key.u: (handle_undo, "selected, history"),
        Key.y: (copy_todo, "todos, selected, copied_todo"),
        Key.down: (handle_cursor_down, "todos, selected"),
        Key.up: (handle_cursor_up, "todos, selected"),
        Key.delete: (toggle_todo_note, "todos, selected"),
        Key.shift_tab_windows: (handle_dedent, "todos, selected"),
        Key.shift_tab: (handle_dedent, "todos, selected"),
        Key.alt_j_windows: (
            handle_todo_down,
            "todos, selected",
        ),
        Key.alt_k_windows: (
            handle_todo_up,
            "todos, selected",
        ),
    }
    esc_keys: dict[int, tuple[Callable[..., Any], str]] = {
        Key.alt_G: (selected.multiselect_bottom, "len(todos)"),
        Key.alt_g: (selected.multiselect_top, "None"),
        Key.alt_j: (handle_todo_down, "todos, selected"),
        Key.alt_k: (handle_todo_up, "todos, selected"),
        Key.zero: (selected.multiselect_from, "stdscr, 0, len(todos)"),
        Key.one: (selected.multiselect_from, "stdscr, 1, len(todos)"),
        Key.two: (selected.multiselect_from, "stdscr, 2, len(todos)"),
        Key.three: (selected.multiselect_from, "stdscr, 3, len(todos)"),
        Key.four: (selected.multiselect_from, "stdscr, 4, len(todos)"),
        Key.five: (selected.multiselect_from, "stdscr, 5, len(todos)"),
        Key.six: (selected.multiselect_from, "stdscr, 6, len(todos)"),
        Key.seven: (selected.multiselect_from, "stdscr, 7, len(todos)"),
        Key.eight: (selected.multiselect_from, "stdscr, 8, len(todos)"),
        Key.nine: (selected.multiselect_from, "stdscr, 9, len(todos)"),
    }
    history.add(todos, int(selected))
    print_history(history)

    while True:
        edits += 1
        todos, file_modified_time = update_modified_time(file_modified_time, todos)
        set_header(stdscr, f"{HEADER}:")
        sublist_top = print_todos(stdscr, todos, selected, sublist_top)
        stdscr.refresh()
        if single_line_state.is_off():
            todos = handle_new_todo_next(stdscr, todos, selected, single_line_state)
            continue
        if single_line_state.is_once():
            todos = handle_new_todo_next(
                stdscr,
                todos,
                selected,
                single_line_state,
                Todo(single_line_state.get_extra_data()),
            )
            single_line_state.set_on()
            continue
        next_step = get_main_input(
            stdscr,
            todos,
            (keys, esc_keys),
            {
                "copied_todo": copied_todo,
                "int(selected)": int(selected),
                "history": history,
                "len(todos)": len(todos),
                "single_line_mode": single_line_state,
                "selected": selected,
                "stdscr": stdscr,
                "todos": todos,
            },
        )
        if isinstance(next_step, list):
            return quit_program(next_step, edits, file_modified_time)
        if isinstance(next_step, int) and next_step not in (
            Key.ctrl_r,
            Key.u,
        ):  # redo/undo
            history.add(todos, int(selected))
        print_history(history)
        edits -= 1


if __name__ == "__main__":
    if NO_GUI:
        print(f"{HEADER}:")
        print_todos(None, file_string_to_todos(read_file(FILENAME)), Cursor(0))
        sys_exit()
    curses.wrapper(main)
