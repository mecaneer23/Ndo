#!/usr/bin/env python3
"""Entry point for Ndo. This module mostly binds keypresses to various functions"""

from pathlib import Path
from sys import exit as sys_exit
from typing import Callable, TypeAlias

from src.class_cursor import Cursor
from src.class_history import UndoRedo
from src.class_mode import SingleLineMode, SingleLineModeImpl
from src.class_todo import BoxChar, FoldedState, Todo, Todos
from src.clipboard import CLIPBOARD_EXISTS, copy_todo, paste_todo
from src.get_args import (
    FILENAME,
    GUI_TYPE,
    HEADER,
    NO_GUI,
    GuiType,
)
from src.get_todo import get_todo
from src.io import file_string_to_todos, read_file, update_file
from src.keys import Key
from src.menus import (
    color_menu,
    get_newwin,
    help_menu,
    magnify_menu,
    search_menu,
    sort_menu,
)
from src.print_todos import print_todos
from src.utils import alert, clamp, set_header

if GUI_TYPE == GuiType.ANSI:
    import src.acurses as curses
    from src.acurses import wrapper
elif GUI_TYPE == GuiType.TKINTER:
    import src.tcurses as curses  # type: ignore
    from src.tcurses import wrapper
else:
    import curses  # type: ignore

    from src.working_initscr import wrapper


# Migrate the following once Python 3.12 is more common
# type PossibleArgs = ...
PossibleArgs: TypeAlias = (
    Todo | int | UndoRedo | SingleLineModeImpl | Cursor | curses.window | Todos
)


def get_file_modified_time(filename: Path) -> float:
    """
    Return the most recent modification time for a given file

    st_ctime should return the most recent modification time cross platform
    """
    return filename.stat().st_ctime  # pyright: ignore


def insert_todo(
    stdscr: curses.window,
    todos: Todos,
    index: int,
    default_todo: Todo = Todo(),
    mode: SingleLineModeImpl = SingleLineModeImpl(SingleLineMode.NONE),
) -> Todos:
    """
    Using the get_todo menu, prompt the user for a new Todo.
    Add the new Todo to the list of Todos (`todos`) at the
    specified `index`.
    """
    todo = get_todo(
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


def insert_empty_todo(todos: Todos, index: int) -> Todos:
    """Add an empty Todo to `todos` at `index`"""
    todos.insert(index, Todo())
    return todos


def remove_todo(todos: Todos, index: int) -> Todos:
    """Remove the Todo at `index"""
    if len(todos) < 1:
        return todos
    todos.pop(index)
    return todos


def move_todo(todos: Todos, selected: int, destination: int) -> Todos:
    """Move the todo(s) at `selected` to `destination`"""
    if min(selected, destination) >= 0 and max(selected, destination) < len(todos):
        todos.insert(selected, todos.pop(destination))
    return todos


def todo_up(todos: Todos, selected: Cursor) -> Todos:
    """Move the selected todo(s) up"""
    todos = move_todo(todos, selected.get_last(), selected.get_first() - 1)
    update_file(FILENAME, todos)
    selected.slide_up()
    return todos


def todo_down(todos: Todos, selected: Cursor) -> Todos:
    """Move the selected todo(s) down"""
    todos = move_todo(todos, selected.get_first(), selected.get_last() + 1)
    update_file(FILENAME, todos)
    selected.slide_down(len(todos))
    return todos


def new_todo_next(
    stdscr: curses.window,
    todos: Todos,
    selected: Cursor,
    default_todo: Todo,
    mode: SingleLineModeImpl = SingleLineModeImpl(SingleLineMode.NONE),
) -> Todos:
    """
    Insert a new todo item below the current
    cursor position and update the todo list
    """
    temp = todos.copy()
    todos = insert_todo(
        stdscr,
        todos,
        int(selected) + 1,
        default_todo=default_todo.copy(),
        mode=mode,
    )
    stdscr.clear()
    if temp != todos:
        selected.single_down(len(todos))
    update_file(FILENAME, todos)
    return todos


def new_todo_current(stdscr: curses.window, todos: Todos, selected: int) -> Todos:
    """
    Insert a new todo item at the current cursor
    position, moving the rest of the list down
    """
    todos = insert_todo(stdscr, todos, selected)
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def delete_todo(
    stdscr: curses.window,
    todos: Todos,
    selected: Cursor,
    copied_todo: Todo,
) -> Todos:
    """Remove each Todo in `selected` from the list"""
    if len(todos) > 0 and CLIPBOARD_EXISTS:
        copy_todo(stdscr, todos, selected, copied_todo)
    for pos in selected.get_deletable():
        todos = remove_todo(todos, pos)
    selected.set_to(clamp(int(selected), 0, len(todos)))
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def color_todo(stdscr: curses.window, todos: Todos, selected: Cursor) -> Todos:
    """
    Open a color menu. Set each Todo in `selected`
    to the returned color.
    """
    new_color = color_menu(stdscr, todos[int(selected)].get_color())
    for pos in selected.get():
        todos[pos].set_color(new_color)
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def edit_todo(
    stdscr: curses.window,
    todos: Todos,
    selected: int,
    mode: SingleLineModeImpl,
) -> Todos:
    """
    Open a get_todo input box with the current todo contents. Set
    the todo to the edited contents.
    """
    if len(todos) <= 0:
        return todos
    max_y, max_x = stdscr.getmaxyx()
    todo = todos[selected].get_display_text()
    ncols = (
        max(max_x * 3 // 4, len(todo) + 3) if len(todo) < max_x - 1 else max_x * 3 // 4
    )
    begin_x = max_x // 8 if len(todo) < max_x - 1 - ncols else (max_x - ncols) // 2
    edited_todo = get_todo(
        stdscr,
        curses.newwin(3, ncols, max_y // 2 - 3, begin_x),
        todo=todos[selected],
        prev_todo=Todo(),
        mode=mode,
    )
    if edited_todo.is_empty():
        return todos
    todos[selected] = edited_todo
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def blank_todo(todos: Todos, selected: Cursor) -> Todos:
    """Create an empty Todo object"""
    insert_empty_todo(todos, int(selected) + 1)
    selected.single_down(len(todos))
    update_file(FILENAME, todos)
    return todos


def toggle(todos: Todos, selected: Cursor) -> Todos:
    """Toggle the completion of each todo in the selected region"""
    for pos in selected.get():
        todos[pos].toggle()
    update_file(FILENAME, todos)
    return todos


def remove_file(filename: Path) -> int:
    """Delete a file from the file system. NOT UNDOABLE"""
    filename.unlink()
    return 0


def quit_program(todos: Todos, prev_time: float) -> int:
    """Exit the program, writing to disk first"""
    todos, _ = update_modified_time(prev_time, todos)
    if len(todos) == 0:
        return remove_file(FILENAME)
    return update_file(FILENAME, todos)


def indent(todos: Todos, selected: Cursor) -> Todos:
    """Indent selected todos"""
    for pos in selected.get():
        todos[pos].indent()
    update_file(FILENAME, todos)
    return todos


def dedent(todos: Todos, selected: Cursor) -> Todos:
    """Un-indent selected todos"""
    for pos in selected.get():
        todos[pos].dedent()
    update_file(FILENAME, todos)
    return todos


def _toggle_todo_note(todos: Todos, selected: Cursor) -> None:
    if len(todos) == 0:
        return
    for pos in selected.get():
        todo = todos[pos]
        todo.set_box_char(BoxChar.NONE if todo.has_box() else BoxChar.MINUS)
    update_file(FILENAME, todos)


def _handle_undo(selected: Cursor, history: UndoRedo) -> Todos:
    todos = selected.override_passthrough(*history.undo())
    update_file(FILENAME, todos)
    return todos


def _handle_redo(selected: Cursor, history: UndoRedo) -> Todos:
    todos = selected.override_passthrough(*history.redo())
    update_file(FILENAME, todos)
    return todos


def _set_fold_state_under(
    state: FoldedState,
    parent_indent_level: int,
    todos: Todos,
    start_index: int,
) -> None:
    index = start_index
    while True:
        index += 1
        if todos[index].get_indent_level() > parent_indent_level:
            todos[index].set_folded(state)
            continue
        break


def _set_folded(stdscr: curses.window, todos: Todos, selected: int) -> None:
    """
    Set the selected todo as a folder parent
    and set all todos indented below it as folded
    """
    parent = todos[selected]
    index = selected + 1
    if todos[index].get_indent_level() <= parent.get_indent_level():
        return
    parent.set_folded(FoldedState.PARENT)
    todos[index].set_folded(FoldedState.FOLDED)
    _set_fold_state_under(FoldedState.FOLDED, parent.get_indent_level(), todos, index)
    stdscr.clear()


def _unset_folded(stdscr: curses.window, todos: Todos, selected: int) -> None:
    """
    If the selected todo is a folder parent,
    unfold the selected todo and all folded
    todos below it.
    """
    parent = todos[selected]
    if not parent.is_folded_parent():
        return
    parent.set_folded(FoldedState.DEFAULT)
    _set_fold_state_under(
        FoldedState.DEFAULT,
        parent.get_indent_level(),
        todos,
        selected,
    )
    stdscr.clear()


def _handle_enter(
    stdscr: curses.window,
    todos: Todos,
    selected: Cursor,
    mode: SingleLineModeImpl,
) -> Todos:
    if len(todos) > 0 and todos[int(selected)].has_box():
        return toggle(todos, selected)
    return new_todo_next(stdscr, todos, selected, Todo(), mode=mode)


def _handle_alert(stdscr: curses.window, todos: Todos, selected: int) -> None:
    """Display the selected todo in an alert window"""

    alert(stdscr, todos[selected].get_display_text())


def _get_possible_todos(
    func: Callable[..., Todos | None],
    args: str,
    possible_args: dict[str, PossibleArgs],
) -> Todos | None:
    params: list[PossibleArgs] = []
    for arg in args.split(", "):
        if arg.isdigit():
            params.append(int(arg))
            continue
        if arg != "None":
            params.append(possible_args[arg])
    return func(*params)


def _get_main_input(
    stdscr: curses.window,
    todos: Todos,
    keys_esckeys: tuple[
        dict[int, tuple[Callable[..., Todos | None], str]],
        dict[int, tuple[Callable[..., Todos | None], str]],
    ],
    possible_args: dict[str, PossibleArgs],
) -> int | Todos:
    try:
        key: int = stdscr.getch()
    except Key.ctrl_c:
        return todos
    if key == Key.q:
        return todos
    if key not in keys_esckeys[0]:
        alert(stdscr, f"Invalid key: `{key}` | `{chr(key)}`. Press `h` for help.")
        return -1
    func, args = keys_esckeys[0][key]
    if key == Key.escape:
        stdscr.nodelay(True)
        key = stdscr.getch()
        stdscr.nodelay(False)
        if key == Key.nodelay_escape:
            return todos
        if key not in keys_esckeys[1]:
            alert(
                stdscr,
                f"Invalid key after escape: `{key}` | `{chr(key)}`. Press `h` for help.",
            )
            return -1
        func, args = keys_esckeys[1][key]
    possible_todos = _get_possible_todos(
        func,
        args,
        possible_args,
    )
    if isinstance(possible_todos, Todos):
        todos = possible_todos
    return key


def _init() -> None:
    curses.use_default_colors()
    curses.curs_set(0)
    for i, color in enumerate(
        (
            curses.COLOR_RED,
            curses.COLOR_GREEN,
            curses.COLOR_YELLOW,
            curses.COLOR_BLUE,
            curses.COLOR_MAGENTA,
            curses.COLOR_CYAN,
            curses.COLOR_WHITE,
        ),
        start=1,
    ):
        curses.init_pair(i, color, -1)


def update_modified_time(prev_time: float, todos: Todos) -> tuple[Todos, float]:
    """Return most recent todos and most recent modification time."""
    current_time = get_file_modified_time(FILENAME)
    if prev_time != current_time:
        todos = file_string_to_todos(read_file(FILENAME))
    return todos, current_time


def join_lines(todos: Todos, selected: Cursor) -> None:
    """Combine current line with previous line by concatenation."""
    if len(selected) > 1 or len(todos) < 2:
        return

    prev_todo = int(selected) - 1
    current_todo = int(selected)

    todos[prev_todo].set_display_text(
        f"{todos[prev_todo].get_display_text()} "
        + todos[current_todo].get_display_text(),
    )
    selected.slide_up()
    todos.pop(current_todo)
    update_file(FILENAME, todos)


def main(stdscr: curses.window) -> int:
    """
    The main function for Ndo. Mainly provides keybindings
    for the various functions and contains mainloop.

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

    file_modified_time:
    Last time of file modification. Used to determine
    when to overwrite the save file.
    """
    _init()
    todos = file_string_to_todos(read_file(FILENAME))
    selected = Cursor(0, todos)
    sublist_top = 0
    history = UndoRedo()
    single_line_state = SingleLineModeImpl(SingleLineMode.ON)
    copied_todo = Todo()
    file_modified_time = get_file_modified_time(FILENAME)
    # if adding a new feature that updates `todos`,
    # make sure it also calls update_file()
    keys: dict[int, tuple[Callable[..., Todos | None], str]] = {
        Key.ctrl_a: (selected.multiselect_all, "len(todos)"),
        Key.backspace: (join_lines, "todos, selected"),
        Key.backspace_: (join_lines, "todos, selected"),
        Key.backspace__: (join_lines, "todos, selected"),
        Key.tab: (indent, "todos, selected"),
        Key.enter: (_handle_enter, "stdscr, todos, selected, single_line_state"),
        Key.enter_: (_handle_enter, "stdscr, todos, selected, single_line_state"),
        Key.ctrl_k: (single_line_state.toggle, "None"),
        Key.ctrl_r: (_handle_redo, "selected, history"),
        Key.ctrl_x: (single_line_state.toggle, "None"),
        Key.escape: (lambda: None, "None"),
        Key.minus: (blank_todo, "todos, selected"),
        Key.slash: (search_menu, "stdscr, todos, selected"),
        Key.zero: (selected.relative_to, "stdscr, 0, len(todos), True"),
        Key.one: (selected.relative_to, "stdscr, 1, len(todos), True"),
        Key.two: (selected.relative_to, "stdscr, 2, len(todos), True"),
        Key.three: (selected.relative_to, "stdscr, 3, len(todos), True"),
        Key.four: (selected.relative_to, "stdscr, 4, len(todos), True"),
        Key.five: (selected.relative_to, "stdscr, 5, len(todos), True"),
        Key.six: (selected.relative_to, "stdscr, 6, len(todos), True"),
        Key.seven: (selected.relative_to, "stdscr, 7, len(todos), True"),
        Key.eight: (selected.relative_to, "stdscr, 8, len(todos), True"),
        Key.nine: (selected.relative_to, "stdscr, 9, len(todos), True"),
        Key.G: (selected.to_bottom, "len(todos)"),
        Key.J: (selected.multiselect_down, "len(todos)"),
        Key.K: (selected.multiselect_up, "None"),
        Key.O: (new_todo_current, "stdscr, todos, int(selected)"),
        # Key.open_bracket: (_set_folded, "stdscr, todos, int(selected)"),
        # Key.close_bracket: (_unset_folded, "stdscr, todos, int(selected)"),
        Key.a: (_handle_alert, "stdscr, todos, int(selected)"),
        Key.b: (magnify_menu, "stdscr, todos, selected"),
        Key.c: (color_todo, "stdscr, todos, selected"),
        Key.d: (delete_todo, "stdscr, todos, selected, copied_todo"),
        Key.g: (selected.to_top, "None"),
        Key.h: (help_menu, "stdscr"),
        Key.i: (edit_todo, "stdscr, todos, int(selected), single_line_state"),
        Key.j: (selected.single_down, "len(todos)"),
        Key.k: (selected.single_up, "len(todos)"),
        Key.o: (new_todo_next, "stdscr, todos, selected, Todo(), single_line_state"),
        Key.p: (paste_todo, "stdscr, todos, selected, copied_todo"),
        Key.s: (sort_menu, "stdscr, todos, selected"),
        Key.u: (_handle_undo, "selected, history"),
        Key.y: (copy_todo, "stdscr, todos, selected, copied_todo"),
        Key.down: (selected.single_down, "len(todos)"),
        Key.up: (selected.single_up, "len(todos)"),
        Key.delete: (_toggle_todo_note, "todos, selected"),
        Key.shift_tab_windows: (dedent, "todos, selected"),
        Key.shift_tab: (dedent, "todos, selected"),
        Key.alt_j_windows: (todo_down, "todos, selected"),
        Key.alt_k_windows: (todo_up, "todos, selected"),
    }
    esc_keys: dict[int, tuple[Callable[..., Todos | None], str]] = {
        Key.alt_G: (selected.multiselect_bottom, "len(todos)"),
        Key.alt_g: (selected.multiselect_top, "None"),
        Key.alt_j: (todo_down, "todos, selected"),
        Key.alt_k: (todo_up, "todos, selected"),
        Key.zero: (selected.relative_to, "stdscr, 0, len(todos), False"),
        Key.one: (selected.relative_to, "stdscr, 1, len(todos), False"),
        Key.two: (selected.relative_to, "stdscr, 2, len(todos), False"),
        Key.three: (selected.relative_to, "stdscr, 3, len(todos), False"),
        Key.four: (selected.relative_to, "stdscr, 4, len(todos), False"),
        Key.five: (selected.relative_to, "stdscr, 5, len(todos), False"),
        Key.six: (selected.relative_to, "stdscr, 6, len(todos), False"),
        Key.seven: (selected.relative_to, "stdscr, 7, len(todos), False"),
        Key.eight: (selected.relative_to, "stdscr, 8, len(todos), False"),
        Key.nine: (selected.relative_to, "stdscr, 9, len(todos), False"),
    }
    history.add(todos, selected)

    while True:
        todos, file_modified_time = update_modified_time(file_modified_time, todos)
        set_header(stdscr, f"{HEADER}:")
        sublist_top = print_todos(stdscr, todos, selected, sublist_top)
        stdscr.refresh()
        if single_line_state.is_off():
            todos = new_todo_next(stdscr, todos, selected, Todo(), single_line_state)
            continue
        if single_line_state.is_once():
            todos = new_todo_next(
                stdscr,
                todos,
                selected,
                Todo(single_line_state.get_extra_data()),
                single_line_state,
            )
            single_line_state.set_on()
            continue
        next_step = _get_main_input(
            stdscr,
            todos,
            (keys, esc_keys),
            {
                "copied_todo": copied_todo,
                "int(selected)": int(selected),
                "history": history,
                "len(todos)": len(todos),
                "Todo()": Todo(),
                "single_line_state": single_line_state,
                "selected": selected,
                "stdscr": stdscr,
                "todos": todos,
                "True": True,
                "False": False,
            },
        )
        if isinstance(next_step, Todos):
            return quit_program(next_step, file_modified_time)
        if next_step not in (
            Key.ctrl_r,
            Key.u,
        ):  # redo/undo
            history.add(todos, selected)


if __name__ == "__main__":
    if NO_GUI:
        print(f"{HEADER}:")
        print_todos(
            None,
            file_string_to_todos(read_file(FILENAME)),
            Cursor(0, Todos(())),
        )
        sys_exit()

    wrapper(main)
