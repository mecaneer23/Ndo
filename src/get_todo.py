"""Open a text input box, implement typing, and return text input"""

from typing import Callable, Iterable, NamedTuple, cast

from src.class_mode import SingleLineMode, SingleLineModeImpl
from src.class_todo import BoxChar, Todo
from src.get_args import INDENT, UI_TYPE, UiType
from src.keyboard_input_helpers import get_executable_args
from src.keys import Key
from src.utils import Color, alert, set_header

if UI_TYPE == UiType.ANSI:
    import src.acurses as curses
elif UI_TYPE == UiType.TKINTER:
    import src.tcurses as curses  # type: ignore
else:
    import curses  # type: ignore


class _Chars(list[str]):
    """A list of characters; an alias for `list[str]`"""

    def __init__(self, iterable: Iterable[str]):
        super().__init__(iterable)


class _EditString(NamedTuple):
    """
    An Editable string. Takes in parameters `string` and `position`.
    These should be represented as `Chars` and `int` respectively.
    """

    string: _Chars
    position: int


def hline(
    win: curses.window,
    y_loc: int,
    x_loc: int,
    char: str | int,
    width: int,
) -> None:
    """
    Display a horizontal line starting at (y_loc, x_loc)
    with width `width` consisting of the character `char`
    """
    win.addch(y_loc, x_loc, cast(str, curses.ACS_LTEE))
    win.hline(y_loc, x_loc + 1, cast(str, char), width - 2)
    win.addch(y_loc, x_loc + width - 1, cast(str, curses.ACS_RTEE))


def _ensure_valid(win: curses.window) -> None:
    if win.getmaxyx()[0] < 3:
        raise ValueError(
            "Window is too short, it won't be able to\
            display the minimum 1 line of text.",
        )
    if win.getmaxyx()[0] > 3:
        raise NotImplementedError("Multiline text editing is not supported")


def _init_todo(todo: Todo, prev_todo: Todo, mode: SingleLineModeImpl) -> Todo:
    if todo.is_empty():
        todo.set_indent_level(prev_todo.get_indent_level())
        todo.set_color(prev_todo.get_color())
        if not prev_todo.has_box():
            todo.set_box_char(BoxChar.NONE)
    if mode.is_off():
        todo.set_box_char(BoxChar.NONE)
    return todo


def _handle_right_arrow(chars: _Chars, position: int) -> _EditString:
    if position < len(chars):
        position += 1
    return _EditString(chars, position)


def _handle_ctrl_right_arrow(chars: _Chars, position: int) -> _EditString:
    while True:
        if position >= len(chars) - 1:
            break
        position += 1
        if chars[position] == " ":
            break
    return _EditString(chars, position)


def _handle_left_arrow(chars: _Chars, position: int) -> _EditString:
    if position > 0:
        position -= 1
    return _EditString(chars, position)


def _handle_ctrl_left_arrow(chars: _Chars, position: int) -> _EditString:
    while True:
        if position <= 0:
            break
        position -= 1
        if chars[position] == " ":
            break
    return _EditString(chars, position)


def _handle_ctrl_delete(chars: _Chars, position: int) -> _EditString:
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
    return _EditString(chars, position)


def _handle_delete(chars: _Chars, position: int) -> _EditString:
    if position < len(chars):
        chars.pop(position)
    return _EditString(chars, position)


def _handle_escape(
    stdscr: curses.window,
    win: curses.window,
    chars: _Chars,
    position: int,
) -> _EditString | None:
    win.nodelay(True)
    if win.getch() == Key.nodelay_escape:
        win.nodelay(False)
        return None
    win.nodelay(False)
    try:
        input_char = win.getch()
    except KeyboardInterrupt:
        return None
    if input_char == Key.ctrl_delete:
        return _handle_ctrl_delete(chars, position)
    return _error_passthrough(stdscr, str(input_char), chars, position)


def _handle_toggle_note_todo(
    stdscr: curses.window, todo: Todo, chars: _Chars, position: int
) -> _EditString:
    _toggle_note_todo(todo)
    set_header(stdscr, "Todo" if todo.has_box() else "Note")
    stdscr.refresh()
    return _EditString(chars, position)


def _handle_indent(
    stdscr: curses.window,
    todo: Todo,
    chars: _Chars,
    position: int,
) -> _EditString:
    todo.indent()
    set_header(stdscr, f"Tab level: {todo.get_indent_level() // INDENT} tabs")
    stdscr.refresh()
    return _EditString(chars, position)


def _handle_dedent(
    stdscr: curses.window,
    todo: Todo,
    chars: _Chars,
    position: int,
) -> _EditString:
    todo.dedent()
    set_header(stdscr, f"Tab level: {todo.get_indent_level() // INDENT} tabs")
    stdscr.refresh()
    return _EditString(chars, position)


def _handle_home(chars: _Chars) -> _EditString:
    return _EditString(chars, 0)


def _handle_end(chars: _Chars) -> _EditString:
    return _EditString(chars, len(chars))


def _error_passthrough(
    stdscr: curses.window,
    key_name: str,
    chars: _Chars | None = None,
    position: int | None = None,
) -> _EditString:
    alert(stdscr, f"Key `{key_name}` is not supported")
    return (
        _EditString(chars, position)
        if chars is not None and position is not None
        else _EditString(_Chars({}), 0)
    )


def _handle_new_todo(chars: _Chars, position: int, mode: SingleLineModeImpl) -> str:
    mode.set_once()
    mode.set_extra_data("".join(chars[position:]))
    return "".join(chars[:position])


def _handle_backspace(chars: _Chars, position: int) -> _EditString:
    if position > 0:
        position -= 1
        chars.pop(position)
    return _EditString(chars, position)


def _handle_ctrl_backspace(chars: _Chars, position: int) -> _EditString:
    while True:
        if position <= 0:
            break
        position -= 1
        if chars[position] == " ":
            chars.pop(position)
            break
        chars.pop(position)
    return _EditString(chars, position)


def _handle_printable(chars: _Chars, position: int, input_char: int) -> _EditString:
    chars.insert(position, chr(input_char))
    if position < len(chars):
        position += 1
    return _EditString(chars, position)


def _toggle_note_todo(todo: Todo) -> None:
    if not todo.has_box():
        todo.set_box_char(BoxChar.MINUS)
        return
    todo.set_box_char(BoxChar.NONE)


def _set_once(
    mode: SingleLineModeImpl,
    chars: _Chars,
    position: int,
    color: Color,
) -> str:
    mode.set_once()
    string = "".join(chars)
    two_lines = (
        string.rsplit(None, 1)
        if position > len(chars) - 1
        else (string[:position], string[position:])
    )
    if len(two_lines) == 1:
        line = two_lines[0]
        mode.set_extra_data(f"{color.as_char()} {line[-1]}")
        return line[:-1]
    mode.set_extra_data(f"{color.as_char()} {two_lines[1]}")
    return two_lines[0]


def get_todo(
    stdscr: curses.window,
    win: curses.window,
    todo: Todo,
    prev_todo: Todo,
    mode: SingleLineModeImpl = SingleLineModeImpl(SingleLineMode.NONE),
) -> Todo:
    """
    Reads a string from the given window. Returns a todo from the user.
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
        mode SingleLineMode:
            If adding todos in entry mode (used for rapid
            repetition), allow toggling of that mode by
            passing a Mode object.

    Raises:
        ValueError:
            If the window is too short to display the minimum
            1 line of text.
        NotImplementedError:
            If the window is more than 3 characters tall, as
            multiline text editing isn't supported.

    Returns:
        Todo: Similar to the built in input() function,
        returns a Todo object containing the user's entry.
    """

    _ensure_valid(win)
    todo = _init_todo(todo, prev_todo, mode)
    original = todo.copy()
    chars = _Chars(todo.get_display_text())
    position = len(chars)
    win.box()
    win.nodelay(False)
    win.keypad(True)

    keys: dict[int, tuple[Callable[..., _EditString], str]] = {
        Key.left_arrow: (_handle_left_arrow, "chars, position"),
        Key.right_arrow: (_handle_right_arrow, "chars, position"),
        Key.up_arrow: (
            _error_passthrough,
            "stdscr, up arrow, chars, position",
        ),
        Key.backspace: (_handle_backspace, "chars, position"),
        Key.backspace_: (_handle_backspace, "chars, position"),
        Key.backspace__: (_handle_backspace, "chars, position"),
        Key.ctrl_backspace: (_handle_ctrl_backspace, "chars, position"),
        Key.shift_tab: (_handle_dedent, "stdscr, todo, chars, position"),
        Key.shift_tab_windows: (_handle_dedent, "stdscr, todo, chars, position"),
        Key.tab: (_handle_indent, "stdscr, todo, chars, position"),
        Key.ctrl_left_arrow: (_handle_ctrl_left_arrow, "chars, position"),
        Key.ctrl_right_arrow: (_handle_ctrl_right_arrow, "chars, position"),
        Key.home: (_handle_home, "chars"),
        Key.end: (_handle_end, "chars"),
        Key.delete: (_handle_delete, "chars, position"),
        Key.shift_delete: (_handle_toggle_note_todo, "stdscr, todo, chars, position"),
        Key.alt_delete: (_handle_toggle_note_todo, "stdscr, todo, chars, position"),
    }

    while True:
        if len(chars) + 1 >= win.getmaxyx()[1] - 1:
            return todo.set_display_text(
                _set_once(mode, chars, position, todo.get_color()),
            )
        for i, char in enumerate("".join(chars).ljust(win.getmaxyx()[1] - 2)):
            win.addstr(  # Don't use addch; output should not be buffered
                1,
                i + 1,
                char,
                curses.A_STANDOUT if i == position else curses.A_NORMAL,
            )
        win.refresh()
        try:
            input_char = win.getch()
        except KeyboardInterrupt:
            mode.set_on()
            return original
        if input_char == Key.escape:
            possible_chars_position = _handle_escape(
                stdscr,
                win,
                chars,
                position,
            )
            if possible_chars_position is None:
                mode.set_on()
                return original
            chars, position = possible_chars_position
            continue
        if input_char in (Key.enter, Key.enter_):
            break
        if input_char in (Key.ctrl_k, Key.ctrl_x):
            mode.toggle()
            break
        if input_char == Key.down_arrow:
            mode.set_extra_data(f"{todo.get_color().as_char()} {mode.get_extra_data()}")
            return todo.set_display_text(_handle_new_todo(chars, position, mode))
        if input_char in keys:
            func, joined_args = keys[input_char]
            chars, position = func(
                *get_executable_args(
                    joined_args,
                    {
                        "chars": chars,
                        "position": position,
                        "stdscr": stdscr,
                        "todo": todo,
                    },
                )
            )
            continue
        if chr(input_char).isprintable():
            chars, position = _handle_printable(chars, position, input_char)
            continue
        _error_passthrough(stdscr, str(input_char))

    return todo.set_display_text("".join(chars))
