# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

import curses
from typing import Any, Callable

from src.class_mode import Mode
from src.class_todo import Todo
from src.get_args import INDENT


def set_header(stdscr: Any, message: str) -> None:
    stdscr.addstr(
        0, 0, message.ljust(stdscr.getmaxyx()[1]), curses.A_BOLD | curses.color_pair(2)
    )


def hline(win: Any, y_loc: int, x_loc: int, char: str | int, width: int) -> None:
    win.addch(y_loc, x_loc, curses.ACS_LTEE)
    win.hline(y_loc, x_loc + 1, char, width - 2)
    win.addch(y_loc, x_loc + width - 1, curses.ACS_RTEE)


def ensure_valid(win: Any) -> None:
    if win.getmaxyx()[0] < 3:
        raise ValueError(
            "Window is too short, it won't be able to\
            display the minimum 1 line of text."
        )
    if win.getmaxyx()[0] > 3:
        raise NotImplementedError("Multiline text editing is not supported")


def init_todo(todo: Todo, prev_todo: Todo) -> Todo:
    if todo.is_empty():
        todo.set_indent_level(prev_todo.indent_level)
        todo.set_color(prev_todo.color)
        if not prev_todo.has_box():
            todo.box_char = None
    return todo


def handle_right_arrow(chars: list[str], position: int) -> tuple[list[str], int]:
    if position < len(chars):
        position += 1
    return chars, position


def handle_ctrl_right_arrow(chars: list[str], position: int) -> tuple[list[str], int]:
    while True:
        if position >= len(chars) - 1:
            break
        position += 1
        if chars[position] == " ":
            break
    return chars, position


def handle_left_arrow(chars: list[str], position: int) -> tuple[list[str], int]:
    if position > 0:
        position -= 1
    return chars, position


def handle_ctrl_left_arrow(chars: list[str], position: int) -> tuple[list[str], int]:
    while True:
        if position <= 0:
            break
        position -= 1
        if chars[position] == " ":
            break
    return chars, position


def handle_ctrl_delete(chars: list[str], position: int) -> tuple[list[str], int]:
    if position < len(chars) - 1:
        chars.pop(position)
        position -= 1
    while True:
        if position >= len(chars) - 1:
            break
        position += 1
        if chars[position] == " ":
            break
        chars.pop(position)
        position -= 1
    return chars, position


def set_mode_true(mode: Mode | None) -> None:
    if mode is not None:
        mode.toggle_mode = True


def handle_delete(win: Any, chars: list[str], position: int) -> tuple[list[str], int]:
    win.getch()  # skip the `~`
    if position < len(chars):
        chars.pop(position)
    return chars, position


def handle_ctrl_arrow(
    win: Any, chars: list[str], position: int
) -> tuple[list[str], int]:
    for _ in ";5":
        win.getch()
    options = {
        67: ("right arrow", handle_ctrl_right_arrow),
        68: ("left arrow", handle_ctrl_left_arrow),
    }
    direction = win.getch()
    if direction in options:
        chars, position = options[direction][1](chars, position)
    return chars, position


def handle_delete_modifiers(
    stdscr_win: tuple[Any, Any], todo: Todo, chars: list[str], position: int
) -> tuple[list[str], int]:
    try:
        input_char = stdscr_win[1].getch()
    except KeyboardInterrupt:
        return chars, position
    if input_char == 126:  # ~
        return handle_delete(stdscr_win[1], chars, position)
    if input_char == 59:  # ;
        # `2~` refers to the shift key,
        # however it is the same length as
        # `3~`, which refers to the alt key.
        # As we ignore the value of the
        # character and only use the length,
        # shift+delete and alt+delete
        # can both be used interchangably to
        # perform this task.
        for _ in "2~":
            stdscr_win[1].getch()
        handle_toggle_note_todo(stdscr_win[0], todo)
    return chars, position


def handle_toggle_note_todo(
    stdscr: Any, todo: Todo
) -> None:
    toggle_note_todo(todo)
    set_header(stdscr, "Note" if todo.box_char is None else "Todo")
    stdscr.refresh()


def handle_escape(
    stdscr_win: tuple[Any, Any],
    chars: list[str],
    position: int,
    mode: Mode | None,
    todo: Todo,
) -> tuple[list[str], int] | None:
    stdscr_win[1].nodelay(True)
    escape = stdscr_win[1].getch()  # skip `[`
    escape_table: dict[
        int, tuple[Callable[..., tuple[list[str], int] | None], tuple[Any, ...]]
    ] = {
        100: (handle_ctrl_delete, (chars, position)),
        -1: (set_mode_true, (mode,)),
    }
    if escape in escape_table:
        func, args = escape_table[escape]
        return func(*args)
    stdscr_win[1].nodelay(False)
    try:
        subch = stdscr_win[1].getch()
    except KeyboardInterrupt:
        return None
    subch_table: dict[
        int, tuple[Callable[..., tuple[list[str], int]], tuple[Any, ...]]
    ] = {
        68: (handle_left_arrow, (chars, position)),
        67: (handle_right_arrow, (chars, position)),
        51: (handle_delete_modifiers, (stdscr_win, todo, chars, position)),
        49: (handle_ctrl_arrow, (stdscr_win[1], chars, position)),
        72: (lambda chars: (chars, 0), (chars,)),  # home
        70: (lambda chars: (chars, len(chars)), (chars,)),  # end
    }
    if subch in subch_table:
        func, args = subch_table[subch]
        chars, position = func(*args)
    elif subch == 90:  # shift + tab
        todo.dedent()
        set_header(stdscr_win[0], f"Tab level: {todo.indent_level // INDENT} tabs")
        stdscr_win[0].refresh()
    return chars, position


def handle_backspace(chars: list[str], position: int) -> tuple[list[str], int]:
    if position > 0:
        position -= 1
        chars.pop(position)
    return chars, position


def handle_ctrl_backspace(chars: list[str], position: int) -> tuple[list[str], int]:
    while True:
        if position <= 0:
            break
        position -= 1
        if chars[position] == " ":
            chars.pop(position)
            break
        chars.pop(position)
    return chars, position


def toggle_mode(mode: Mode | None) -> None:
    if mode is not None:
        mode.toggle()


def handle_ascii(
    chars: list[str], position: int, input_char: int
) -> tuple[list[str], int]:
    chars.insert(position, chr(input_char))
    if position < len(chars):
        position += 1
    return chars, position


def toggle_note_todo(todo: Todo) -> None:
    if todo.box_char is None:
        todo.box_char = "-"
        return
    todo.box_char = None


def wgetnstr(
    stdscr: Any,
    win: Any,
    todo: Todo,
    prev_todo: Todo,
    mode: Mode | None = None,
) -> Todo:
    """
    Reads a string from the given window. Returns a todo from the user
    Functions like a JavaScript alert box for user input.

    Args:
        stdscr (Window object):
            Main window of the entire program. Only used in
            calls to set_header().
        win (Window object):
            The window to read from. The entire window
            will be used, so a curses.newwin() should be
            generated specifically for use with this
            function. As a box will be created around the
            window's border, the window must have a minimum
            height of 3 characters. The width will determine
            a maximum value of n.
        todo (Todo):
            Pass a Todo object to initially occupy the window.
        prev_todo (Todo):
            Pass a Todo object to copy the color, indentation
            level, box character, etc from. This is only used
            if `todo` is empty.
        mode (Mode, optional):
            If adding todos in entry mode (used for rapid
            repetition), allow toggling of that mode by
            passing a Mode object.

    Raises:
        ValueError:
            If the window is too short to display the minimum
            1 line of text.
        NotImplementedError:
            If the window is too long to display the maximum
            n characters.

    Returns:
        Todo: Similar to the built in input() function,
        returns a Todo object containing the user's entry.
    """

    ensure_valid(win)
    todo = init_todo(todo, prev_todo)
    original = todo
    chars = list(todo.display_text)
    position = len(chars)
    win.box()
    win.nodelay(False)
    backspace_table = {
        8: handle_backspace,
        127: handle_backspace,
        263: handle_backspace,
        23: handle_ctrl_backspace,
    }
    while True:
        if position == len(chars):
            if len(chars) + 1 >= win.getmaxyx()[1] - 1:
                break
            win.addstr(1, len(chars) + 1, "█")
        for i, char in enumerate("".join(chars).ljust(win.getmaxyx()[1] - 2)):
            win.addstr(1, i + 1, char, curses.A_STANDOUT if i == position else 0)
        win.refresh()
        try:
            input_char = win.getch()
        except KeyboardInterrupt:  # ctrl+c
            toggle_mode(mode)
            return original
        if input_char in (10, 13):  # enter
            break
        if input_char == 27:  # any escape sequence `^[`
            next_step = handle_escape((stdscr, win), chars, position, mode, todo)
            if next_step is None:
                return original
            chars, position = next_step
            continue
        if input_char in (24, 11):  # ctrl + x/k
            toggle_mode(mode)
            break
        if input_char == 9:  # tab
            todo.indent()
            set_header(stdscr, f"Tab level: {todo.indent_level // INDENT} tabs")
            stdscr.refresh()
            continue
        if input_char in backspace_table:
            chars, position = backspace_table[input_char](chars, position)
            continue
        chars, position = handle_ascii(chars, position, input_char)

    todo.set_display_text("".join(chars))
    return todo
