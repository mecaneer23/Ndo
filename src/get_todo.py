# pylint: disable=global-statement, missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

import curses
from typing import Any

from src.class_mode import Mode
from src.class_todo import Todo
from src.get_args import INDENT


def set_header(stdscr: Any, message: str) -> None:
    stdscr.addstr(
        0, 0, message.ljust(stdscr.getmaxyx()[1]), curses.A_BOLD | curses.color_pair(2)
    )


def wgetnstr_success(todo: Todo, chars: list[str]) -> Todo:
    todo.set_display_text("".join(chars))
    return todo


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
    for _ in range(2):  # skip the `;5`
        win.getch()
    direction = win.getch()
    if direction == 67:  # right arrow
        chars, position = handle_ctrl_right_arrow(chars, position)
    elif direction == 68:  # left arrow
        chars, position = handle_ctrl_left_arrow(chars, position)
    return chars, position


def handle_escape(
    stdscr_win: tuple[Any, Any],
    chars: list[str],
    position: int,
    mode: Mode | None,
    todo: Todo,
) -> tuple[list[str], int] | None:
    stdscr_win[1].nodelay(True)
    escape = stdscr_win[1].getch()  # skip `[`
    if escape == -1:  # escape
        set_mode_true(mode)
        return None
    if escape == 100:  # ctrl + delete
        return handle_ctrl_delete(chars, position)
    stdscr_win[1].nodelay(False)
    try:
        subch = stdscr_win[1].getch()
    except KeyboardInterrupt:
        return None
    if subch == 68:  # left arrow
        chars, position = handle_left_arrow(chars, position)
    elif subch == 67:  # right arrow
        chars, position = handle_right_arrow(chars, position)
    elif subch == 51:  # delete
        chars, position = handle_delete(stdscr_win[1], chars, position)
    elif subch == 49:  # ctrl + arrow
        chars, position = handle_ctrl_arrow(stdscr_win[1], chars, position)
    elif subch == 72:  # home
        position = 0
    elif subch == 70:  # end
        position = len(chars)
    elif subch == 90:  # shift + tab
        todo.dedent()
        set_header(stdscr_win[0], f"Tab level: {todo.indent_level // INDENT} tabs")
        stdscr_win[0].refresh()
    else:
        raise ValueError(repr(subch))
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
    while True:
        if position == len(chars):
            if len(chars) + 1 >= win.getmaxyx()[1] - 1:
                return wgetnstr_success(todo, chars)
            win.addstr(1, len(chars) + 1, "█")
        for i, char in enumerate("".join(chars).ljust(win.getmaxyx()[1] - 2)):
            win.addstr(1, i + 1, char, curses.A_REVERSE if i == position else 0)
        win.refresh()
        try:
            input_char = win.getch()
        except KeyboardInterrupt:  # ctrl+c
            toggle_mode(mode)
            return original
        if input_char in (10, 13, -1):  # enter
            # might need to continue on -1
            # I don't know which character it represents
            break
        if input_char == 27:  # any escape sequence `^[`
            next_step = handle_escape((stdscr, win), chars, position, mode, todo)
            if next_step is None:
                return original
            chars, position = next_step
            continue
        if input_char in (24, 11):  # ctrl + x/k
            toggle_mode(mode)
            return wgetnstr_success(todo, chars)
        if input_char == 9:  # tab
            todo.indent()
            set_header(stdscr, f"Tab level: {todo.indent_level // INDENT} tabs")
            stdscr.refresh()
            continue
        if input_char in (8, 127, 263):  # backspace
            chars, position = handle_backspace(chars, position)
            continue
        if input_char == 23:  # ctrl + backspace
            chars, position = handle_ctrl_backspace(chars, position)
            continue
        chars, position = handle_ascii(chars, position, input_char)

    return wgetnstr_success(todo, chars)
