#!/usr/bin/env python3
"""
Entry point for Ndo. This module mostly binds keypresses to various functions
"""
# ruff: noqa: FBT003

from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path
from sys import exit as sys_exit
from typing import Callable, NamedTuple, TypeAlias

from ndo.clipboard import CLIPBOARD_EXISTS, copy_todos, paste_todos
from ndo.color import Color
from ndo.get_args import (
    CONTROLS_BEGIN_INDEX,
    CONTROLS_END_INDEX,
    FILENAME,
    HEADER,
    HELP_FILE,
    RENAME,
    UI_TYPE,
    UiType,
)
from ndo.get_args import curses_module as curses
from ndo.get_args import wrapper_func as wrapper
from ndo.get_todo import InputTodo
from ndo.history import UndoRedo
from ndo.io_ import file_string_to_todos, read_file, update_file
from ndo.keyboard_input_helpers import get_executable_args
from ndo.keys import Key
from ndo.menus import (
    color_menu,
    get_newwin,
    get_search_sequence,
    help_menu,
    magnify_menu,
    next_search_location,
    sort_menu,
)
from ndo.mode import SingleLineMode, SingleLineModeImpl
from ndo.print_todos import print_todos
from ndo.selection import Selection
from ndo.tab_size import format_todos
from ndo.todo import BoxChar, FoldedState, Todo, Todos
from ndo.ui_protocol import CursesWindow
from ndo.utils import NewTodoPosition, Response, clamp
from ndo.window_interactions import alert, set_header

# Migrate the following once Python 3.12 is more common
# type _PossibleArgs = ...
_PossibleArgs: TypeAlias = (
    Todo
    | int
    | UndoRedo
    | SingleLineModeImpl
    | Selection
    | CursesWindow
    | Todos
    | NewTodoPosition
    | str
)


def get_file_modified_time(filename: Path) -> float:
    """
    Return the most recent modification time for a given file

    st_ctime should return the most recent modification time cross platform
    """
    return filename.stat().st_ctime  # pyright: ignore[reportDeprecated]


def _remove_todo(todos: Todos, index: int) -> Todos:
    """Remove the Todo at `index"""
    if len(todos) < 1:
        return todos
    todos.pop(index)
    return todos


def _move_todo(todos: Todos, group: int, destination: int) -> Todos:
    """Move the todo(s) in `group` to `destination`"""
    if min(group, destination) >= 0 and max(group, destination) < len(todos):
        todos.insert(group, todos.pop(destination))
    return todos


def _todo_top_no_move(todos: Todos, selected: Selection) -> Todos:
    """
    Move the selected todo(s) to the top of the list without moving selection
    """
    if len(todos) == 0:
        return todos
    group = todos[selected.get_first() : selected.get_last() + 1]
    for item in group:
        todos.remove(item)
    todos = Todos(group + todos)
    update_file(FILENAME, todos)
    return todos


def todo_top_down_one(todos: Todos, selected: Selection) -> Todos:
    """
    Move the selected todo(s) to the top of the list, moving selection down one
    """
    todos = _todo_top_no_move(todos, selected)
    selected.single_down(len(todos))
    return todos


def todo_top(todos: Todos, selected: Selection) -> Todos:
    """Move the selected todo(s) to the top of the list"""
    todos = _todo_top_no_move(todos, selected)
    selected.set(0, len(selected))
    return todos


def todo_up(todos: Todos, selected: Selection) -> Todos:
    """Move the selected todo(s) up"""
    todos = _move_todo(todos, selected.get_last(), selected.get_first() - 1)
    update_file(FILENAME, todos)
    selected.slide_up()
    return todos


def todo_down(todos: Todos, selected: Selection) -> Todos:
    """Move the selected todo(s) down"""
    todos = _move_todo(todos, selected.get_first(), selected.get_last() + 1)
    update_file(FILENAME, todos)
    selected.slide_down(len(todos))
    return todos


def _selection_from_offset(selected: Selection, offset: NewTodoPosition) -> int:
    """
    Return the index of the Todo to insert a new Todo at,
    based on the current selection and the offset.
    """
    if offset == NewTodoPosition.CURRENT:
        return selected.get_first()
    return selected.get_last() + offset.value


def new_todo(  # noqa: PLR0913
    stdscr: CursesWindow,
    todos: Todos,
    selected: Selection,
    default_todo: Todo,
    offset: NewTodoPosition,
    mode: SingleLineModeImpl | None = None,
) -> Todos:
    """
    Using the get_todo menu, prompt the user for a new Todo.
    Add the new Todo to the list of Todos (`todos`) at the
    specified index.
    """
    if mode is None:
        mode = SingleLineModeImpl(SingleLineMode.NONE)
    temp = todos.copy()
    index = 0
    if len(todos) > 0:
        index = _selection_from_offset(selected, offset)
    todo = InputTodo(
        stdscr,
        get_newwin(stdscr),
        todo=default_todo.copy(),
        style_information=todos[index - 1] if len(todos) > 0 else Todo(),
        mode=mode,
    ).get_todo()
    if not todo.is_empty():
        todos.insert(index, todo)
    if temp == todos:
        return todos
    stdscr.clear()
    selected.set(index)
    update_file(FILENAME, todos)
    return todos


def delete_todo(
    stdscr: CursesWindow,
    todos: Todos,
    selected: Selection,
    copied_todos: Todos,
) -> Todos:
    """Remove each Todo in `selected` from the list"""
    if len(todos) > 0 and CLIPBOARD_EXISTS:
        copy_todos(stdscr, todos, selected, copied_todos)
    for _ in selected:
        todos = _remove_todo(todos, selected.get_first())
    selected.set(clamp(int(selected), 0, len(todos)))
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def color_todo(
    stdscr: CursesWindow,
    todos: Todos,
    selected: Selection,
) -> Todos:
    """
    Open a color menu. Set each Todo in `selected`
    to the returned color.
    """
    if len(selected) == 0:
        alert(stdscr, "No todo items for which to modify the color")
        return todos
    new_color = color_menu(stdscr, todos[int(selected)].get_color())
    if new_color is Color.NONE:
        return todos
    for pos in selected.get():
        todos[pos].set_color(new_color)
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def edit_todo(
    stdscr: CursesWindow,
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
    border_width = 2
    length = len(todos[selected].get_display_text()) + border_width
    ncols = (
        max(max_x * 3 // 4, length + 3)
        if length < max_x - border_width
        else max_x * 3 // 4
    )
    begin_x = max_x // 8 if length < max_x - 1 - ncols else (max_x - ncols) // 2
    edited_todo = InputTodo(
        stdscr,
        curses.newwin(3, ncols, max_y // 2 - 3, begin_x),
        todo=todos[selected],
        style_information=Todo(),
        mode=mode,
    ).get_todo()
    if edited_todo.is_empty():
        return todos
    todos[selected] = edited_todo
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def blank_todo(todos: Todos, selected: Selection) -> Todos:
    """Create an empty Todo object"""
    todos.insert(selected.get_last() + 1, Todo())
    selected.single_down(len(todos))
    update_file(FILENAME, todos)
    return todos


def blank_todo_above(todos: Todos, selected: Selection) -> Todos:
    """Create an empty Todo object above the current selection"""
    position = selected.get_first()
    todos.insert(position, Todo())
    selected.set(position)
    update_file(FILENAME, todos)
    return todos


def _toggle(todos: Todos, selected: Selection) -> Todos:
    """Toggle the completion of each todo in the selected region"""
    for pos in selected.get():
        todos[pos].toggle()
    update_file(FILENAME, todos)
    return todos


def _remove_file(filename: Path) -> int:
    """Delete a file from the file system. NOT UNDOABLE"""
    filename.unlink()
    return 0


def quit_program(todos: Todos, prev_time: float) -> int:
    """Exit the program, writing to disk first"""
    todos, _ = update_modified_time(prev_time, todos)
    if len(todos) == 0:
        return _remove_file(FILENAME)
    return update_file(FILENAME, todos)


def indent(todos: Todos, selected: Selection) -> Todos:
    """Indent selected todos"""
    for pos in selected.get():
        todos[pos].indent()
    update_file(FILENAME, todos)
    return todos


def dedent(todos: Todos, selected: Selection) -> Todos:
    """Un-indent selected todos"""
    for pos in selected.get():
        todos[pos].dedent()
    update_file(FILENAME, todos)
    return todos


def _toggle_todo_note(todos: Todos, selected: Selection) -> None:
    if len(todos) == 0:
        return
    for pos in selected.get():
        todo = todos[pos]
        todo.set_box_char(BoxChar.NONE if todo.has_box() else BoxChar.MINUS)
    update_file(FILENAME, todos)


def _handle_undo(selected: Selection, history: UndoRedo) -> Todos:
    todo_list = history.undo()
    selected.set(todo_list.start, todo_list.stop)
    update_file(FILENAME, todo_list.todos)
    return todo_list.todos


def _handle_redo(selected: Selection, history: UndoRedo) -> Todos:
    todo_list = history.redo()
    selected.set(todo_list.start, todo_list.stop)
    update_file(FILENAME, todo_list.todos)
    return todo_list.todos


def _set_fold_state_under(
    state: FoldedState,
    parent_indent_level: int,
    todos: Todos,
    start_index: int,
) -> None:
    index = start_index
    while True:
        index += 1
        if (
            index == len(todos)
            or todos[index].get_indent_level() <= parent_indent_level
        ):
            break
        todos[index].set_folded(state)


def _set_folded(
    stdscr: CursesWindow,
    todos: Todos,
    selected: Selection,
) -> None:
    """
    Set the selected todo as a folder parent
    and set all todos indented below it as folded
    """
    for pos in selected.get():
        parent = todos[pos]
        index = pos + 1
        if (
            pos == len(todos) - 1
            or todos[index].get_indent_level() <= parent.get_indent_level()
        ):
            continue
        parent.set_folded(FoldedState.PARENT)
        todos[index].set_folded(FoldedState.FOLDED)
        _set_fold_state_under(
            FoldedState.FOLDED,
            parent.get_indent_level(),
            todos,
            index,
        )
        stdscr.clear()


def _unset_folded(
    stdscr: CursesWindow,
    todos: Todos,
    selected: Selection,
) -> None:
    """
    If the selected todo is a folder parent,
    unfold the selected todo and all folded
    todos below it.
    """
    for pos in selected.get():
        parent = todos[pos]
        if not parent.is_folded_parent():
            continue
        parent.set_folded(FoldedState.DEFAULT)
        _set_fold_state_under(
            FoldedState.DEFAULT,
            parent.get_indent_level(),
            todos,
            pos,
        )
        stdscr.clear()


def _handle_enter(
    stdscr: CursesWindow,
    todos: Todos,
    selected: Selection,
    mode: SingleLineModeImpl,
) -> Todos:
    if len(todos) > 0 and todos[int(selected)].has_box():
        return _toggle(todos, selected)
    return new_todo(
        stdscr,
        todos,
        selected,
        Todo(),
        NewTodoPosition.NEXT,
        mode=mode,
    )


def _handle_alert(
    stdscr: CursesWindow,
    todos: Todos,
    selected: Selection,
) -> None:
    """Display the selected todo in an alert window"""

    if len(todos) == 0:
        alert(stdscr, "No todos to display")
        return

    if (
        len({todos[pos].get_indent_level() for pos in selected.get()}) == 1
        or len(selected) == 1
    ):
        alert(
            stdscr,
            "\n".join(todos[pos].get_display_text() for pos in selected.get()),
        )
        return

    alert(
        stdscr,
        "\n".join(
            todos[pos].get_indented_display_text() for pos in selected.get()
        ),
    )


class _MainInputResult(NamedTuple):
    """
    Represent one type of result from _get_main_input()
    """

    should_exit: bool
    todos: Todos
    key: Key = Key(-1)


def _raise_keyboard_interrupt() -> None:
    raise KeyboardInterrupt


def _get_main_input(
    stdscr: CursesWindow,
    todos: Todos,
    keys_esckeys: tuple[
        dict[Key, tuple[Callable[..., Todos | None], str]],
        dict[Key, tuple[Callable[..., Todos | None], str]],
    ],
    possible_args: dict[str, _PossibleArgs],
) -> _MainInputResult | Key:
    try:
        if (key := Key(stdscr.getch())) == Key.q:
            _raise_keyboard_interrupt()
    except KeyboardInterrupt:
        return _MainInputResult(True, todos)
    if key not in keys_esckeys[0]:
        alert(
            stdscr,
            f"Invalid key: `{key}` | `{chr(key.value)}`. Press `h` for help.",
        )
        return Key(-1)
    func, args = keys_esckeys[0][Key(key)]
    if key == Key.escape:
        stdscr.nodelay(True)
        key = Key(stdscr.getch())
        stdscr.nodelay(False)
        if key == Key.nodelay_escape:
            return _MainInputResult(True, todos)
        if key not in keys_esckeys[1]:
            alert(
                stdscr,
                f"Invalid key after escape: `{key}` | `{chr(key.value)}`. "
                "Press `h` for help.",
            )
            return Key(-1)
        func, args = keys_esckeys[1][Key(key)]
    possible_todos = func(
        *get_executable_args(
            args,
            possible_args,
        ),
    )
    if isinstance(possible_todos, Todos):
        return _MainInputResult(False, possible_todos, key)
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


def _get_lines_to_join(selected: Selection) -> Iterator[int]:
    """
    Return a sequence of integers corresponding to lines to combine (in
    reverse order).

    The last item should be the line prior to the selection unless the
    selection includes the first line (0). Yield the last item at the beginning
    as well as at the end.
    """

    zeroith_item = selected.get_first() - 1
    yield zeroith_item if zeroith_item >= 0 else selected.get_first()
    yield from reversed(selected.get())
    if zeroith_item >= 0:
        yield zeroith_item


def join_lines(todos: Todos, selected: Selection) -> None:
    """Combine current line with previous line by concatenation."""

    selection = _get_lines_to_join(selected)
    ending_selection_location = next(selection)

    for addend, captain in pairwise(selection):
        todos[captain].set_display_text(
            todos[captain].get_display_text()
            + " "
            + todos[addend].get_display_text(),
        )
        todos.pop(addend)
    selected.set(ending_selection_location)
    update_file(FILENAME, todos)


def _handle_rename(stdscr: CursesWindow) -> Response:
    if not FILENAME.exists():
        return Response(404, f"{FILENAME} doesn't exist")
    new_filename_as_todo = InputTodo(
        stdscr,
        get_newwin(stdscr),
        todo=Todo(str(FILENAME)),
        style_information=Todo(),
    ).get_todo()
    if new_filename_as_todo.is_empty():
        return Response(400, "New filename is empty")
    new_filename = new_filename_as_todo.get_display_text()
    if new_filename == str(FILENAME):
        return Response(409, "File name wasn't changed")
    if Path(new_filename).exists():
        return Response(409, f"{new_filename} already exists")
    FILENAME.rename(new_filename)
    return Response(200, "Success!")


def _handle_help_menu(stdscr: CursesWindow) -> None:
    """Wrapper for ndo.menus.help_menu()"""
    help_menu(
        stdscr,
        str(HELP_FILE),
        CONTROLS_BEGIN_INDEX,
        CONTROLS_END_INDEX,
    )
    stdscr.clear()


def _copy_alert(
    stdscr: CursesWindow,
    todos: Todos,
    selected: Selection,
    copied_todos: Todos,
) -> None:
    """Copy a todo and show an alert with information"""
    copy_todos(stdscr, todos, selected, copied_todos)
    alert(
        stdscr,
        f"Copied {len(selected)} to-do item{'' if len(selected) == 1 else 's'}",
    )


def main(stdscr: CursesWindow) -> Response:
    """
    The main function for Ndo. Mainly provides keybindings
    for the various functions and contains mainloop.

    -------

    Directory of main() variables:

    todos:
    main list of Todo objects - initialized with
    contents of `FILENAME`

    selected:
    main Selection object for tracking position
    within the list of Todo objects. Initialized at 0

    sublist_top:
    Only used in print_todos() to keep track of relative
    position and ensure the list renders correctly

    history:
    UndoRedo object, stores history for calls to undo/redo

    single_line_state:
    Used to insert multiple Todos simultaneously whenever
    necessary. This is a "global" object that stores state.

    copied_todos:
    Todos which store metadata about todos, such as
    color and indentation level. Used for copy/paste
    operations.

    file_modified_time:
    Last time of file modification. Used to determine
    when to overwrite the save file.
    """
    _init()
    if RENAME:
        return _handle_rename(stdscr)
    todos = file_string_to_todos(read_file(FILENAME))
    selected = Selection(0, todos)
    history = UndoRedo()
    single_line_state = SingleLineModeImpl(SingleLineMode.ON)
    copied_todos: Todos = Todos(())
    file_modified_time = get_file_modified_time(FILENAME)
    sequence = ""

    def _update_sequence(
        stdscr: CursesWindow,
        todos: Todos,
        selected: Selection,
    ) -> None:
        """Side-effect-only wrapper for get_search_sequence"""
        nonlocal sequence
        sequence = get_search_sequence(stdscr)
        if sequence not in todos[selected.get_first()].get_display_text():
            next_search_location(sequence, todos, selected)

    # if adding a new feature that updates `todos`,
    # make sure it also calls update_file()
    keys: dict[Key, tuple[Callable[..., Todos | None], str]] = {
        Key.ctrl_a: (selected.multiselect_all, "len(todos)"),
        Key.ctrl_f: (_update_sequence, "stdscr, todos, selected"),
        Key.backspace: (join_lines, "todos, selected"),
        Key.backspace_: (join_lines, "todos, selected"),
        Key.backspace__: (join_lines, "todos, selected"),
        Key.tab: (indent, "todos, selected"),
        Key.enter: (
            _handle_enter,
            "stdscr, todos, selected, single_line_state",
        ),
        Key.enter_: (
            _handle_enter,
            "stdscr, todos, selected, single_line_state",
        ),
        Key.ctrl_k: (single_line_state.toggle, "None"),
        Key.ctrl_r: (_handle_redo, "selected, history"),
        Key.ctrl_x: (single_line_state.toggle, "None"),
        Key.escape: (lambda: None, "None"),
        Key.minus: (blank_todo, "todos, selected"),
        Key.slash: (_update_sequence, "stdscr, todos, selected"),
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
        Key.T: (todo_top_down_one, "todos, selected"),
        Key.uppercase_O: (
            new_todo,
            "stdscr, todos, selected, Todo(), CURRENT, single_line_state",
        ),
        # Key.open_bracket: (_set_folded, "stdscr, todos, selected"),
        # Key.close_bracket: (_unset_folded, "stdscr, todos, selected"),
        Key.underscore: (blank_todo_above, "todos, selected"),
        Key.a: (_handle_alert, "stdscr, todos, selected"),
        Key.b: (magnify_menu, "stdscr, todos, selected"),
        Key.c: (color_todo, "stdscr, todos, selected"),
        Key.d: (delete_todo, "stdscr, todos, selected, copied_todos"),
        Key.g: (selected.to_top, "None"),
        Key.h: (_handle_help_menu, "stdscr"),
        Key.i: (edit_todo, "stdscr, todos, int(selected), single_line_state"),
        Key.j: (selected.single_down, "len(todos)"),
        Key.k: (selected.single_up, "len(todos)"),
        Key.n: (next_search_location, "sequence, todos, selected"),
        Key.o: (
            new_todo,
            "stdscr, todos, selected, Todo(), NEXT, single_line_state",
        ),
        Key.p: (paste_todos, "stdscr, todos, selected, copied_todos"),
        Key.s: (sort_menu, "stdscr, todos, selected"),
        Key.t: (todo_top, "todos, selected"),
        Key.u: (_handle_undo, "selected, history"),
        Key.y: (_copy_alert, "stdscr, todos, selected, copied_todos"),
        Key.down_arrow: (selected.single_down, "len(todos)"),
        Key.up_arrow: (selected.single_up, "len(todos)"),
        Key.delete: (_toggle_todo_note, "todos, selected"),
        Key.shift_tab_windows: (dedent, "todos, selected"),
        Key.shift_tab: (dedent, "todos, selected"),
        Key.alt_j_windows: (todo_down, "todos, selected"),
        Key.alt_k_windows: (todo_up, "todos, selected"),
    }
    esc_keys: dict[Key, tuple[Callable[..., Todos | None], str]] = {
        Key.alt_J: (selected.multiselect_bottom, "len(todos)"),
        Key.alt_K: (selected.multiselect_top, "None"),
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
    set_header(stdscr, f"{HEADER}:")
    sublist_top = print_todos(stdscr, todos, selected, 0)
    stdscr.refresh()
    format_todos(stdscr, todos)

    while True:
        todos, file_modified_time = update_modified_time(
            file_modified_time,
            todos,
        )
        set_header(stdscr, f"{HEADER}:")
        sublist_top = print_todos(stdscr, todos, selected, sublist_top)
        stdscr.refresh()
        if single_line_state.is_off():
            todos = new_todo(
                stdscr,
                todos,
                selected,
                Todo(),
                NewTodoPosition.NEXT,
                single_line_state,
            )
            continue
        if single_line_state.is_once():
            single_line_state.set_on()
            todos = new_todo(
                stdscr,
                todos,
                selected,
                Todo(single_line_state.get_extra_data()),
                single_line_state.get_offset(),
                single_line_state,
            )
            continue
        main_input = _get_main_input(
            stdscr,
            todos,
            (keys, esc_keys),
            {
                "copied_todos": copied_todos,
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
                "NEXT": NewTodoPosition.NEXT,
                "CURRENT": NewTodoPosition.CURRENT,
                "sequence": sequence,
            },
        )
        key = main_input
        if isinstance(main_input, _MainInputResult):
            if main_input.should_exit:
                quit_program(main_input.todos, file_modified_time)
                return Response(0, "Quit successfully")
            todos = main_input.todos
            key = main_input.key
        if key not in (  # redo/undo
            Key.ctrl_r,
            Key.u,
        ):
            history.add(todos, selected)


def run() -> None:
    """Run Ndo"""
    if UI_TYPE == UiType.NONE:
        print(f"{HEADER}:")  # noqa: T201
        print_todos(
            None,
            file_string_to_todos(read_file(FILENAME)),
            Selection(0, Todos(())),
        )
        sys_exit()

    status, msg = wrapper(main)
    if status != 0:
        print(f"{status}: {msg}")  # noqa: T201
    sys_exit(status)


if __name__ == "__main__":
    run()
