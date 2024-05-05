"""Open a text input box, implement typing, and return text input"""

from typing import Any, Callable, Iterable, NamedTuple, cast

from src.class_mode import SingleLineMode, SingleLineModeImpl
from src.class_todo import BoxChar, Todo
from src.get_args import INDENT, GUI_TYPE, GuiType
from src.keys import Key
from src.utils import Color, alert, set_header

if GUI_TYPE == GuiType.ANSI:
    import src.acurses as curses
elif GUI_TYPE == GuiType.TKINTER:
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


def _handle_ctrl_arrow(win: curses.window, chars: _Chars, position: int) -> _EditString:
    for _ in ";5":
        win.getch()
    options: dict[int, Callable[[_Chars, int], _EditString]] = {
        Key.right_arrow: _handle_ctrl_right_arrow,
        Key.left_arrow: _handle_ctrl_left_arrow,
    }
    direction = win.getch()
    if direction in options:
        chars, position = options[direction](chars, position)
    return _EditString(chars, position)


def _handle_delete_modifiers(
    stdscr_win: tuple[curses.window, curses.window],
    todo: Todo,
    chars: _Chars,
    position: int,
) -> _EditString:
    try:
        input_char = stdscr_win[1].getch()
    except KeyboardInterrupt:
        return _EditString(chars, position)
    if input_char == Key.tilde:
        return _handle_delete(chars, position)
    if input_char == Key.semi_colon:
        try:
            modifier = stdscr_win[1].getch()
        except KeyboardInterrupt:
            return _EditString(chars, position)
        stdscr_win[1].getch()  # skip `~`
        if modifier == Key.modifier_ctrl:
            return _handle_ctrl_delete(chars, position)
        if modifier in (Key.modifier_shift, Key.modifier_alt):
            _handle_toggle_note_todo(stdscr_win[0], todo)
    return _EditString(chars, position)


def _handle_toggle_note_todo(stdscr: curses.window, todo: Todo) -> None:
    _toggle_note_todo(todo)
    set_header(stdscr, "Todo" if todo.has_box() else "Note")
    stdscr.refresh()


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


def _passthrough(
    stdscr: curses.window,
    edit_string: _EditString,
    key_name: str,
) -> _EditString:
    alert(stdscr, f"Key `{key_name}` is not supported")
    return edit_string


def _handle_new_todo(chars: _Chars, position: int, mode: SingleLineModeImpl) -> str:
    mode.set_once()
    mode.set_extra_data("".join(chars[position:]))
    return "".join(chars[:position])


def _handle_escape(
    stdscr_win: tuple[curses.window, curses.window],
    chars: _Chars,
    position: int,
    mode: SingleLineModeImpl,
    todo: Todo,
) -> _EditString | None | str:
    stdscr_win[1].nodelay(True)
    if stdscr_win[1].getch() == Key.nodelay_escape:
        mode.set_on()
        return None
    stdscr_win[1].nodelay(False)
    try:
        subch = stdscr_win[1].getch()
    except KeyboardInterrupt:
        return None
    if subch == Key.down_arrow:
        return _handle_new_todo(chars, position, mode)

    subch_table: dict[int, tuple[Callable[..., _EditString], tuple[Any, ...]]] = {
        Key.left_arrow: (_handle_left_arrow, (chars, position)),
        Key.right_arrow: (_handle_right_arrow, (chars, position)),
        Key.up_arrow: (
            _passthrough,
            (stdscr_win[0], _EditString(chars, position), "up arrow"),
        ),
        Key.modifier_delete: (
            _handle_delete_modifiers,
            (stdscr_win, todo, chars, position),
        ),
        Key.ctrl_arrow: (_handle_ctrl_arrow, (stdscr_win[1], chars, position)),
        Key.home: (
            _handle_home,
            (chars,),
        ),
        Key.end: (
            _handle_end,
            (chars,),
        ),
        Key.dedent: (
            _handle_dedent,
            (stdscr_win[0], todo, chars, position),
        ),
    }
    if subch not in subch_table:
        alert(stdscr_win[0], f"Invalid key: {subch}")
        return _EditString(chars, position)
    func, args = subch_table[subch]
    return func(*args)


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


def _handle_ascii(chars: _Chars, position: int, input_char: int) -> _EditString:
    chars.insert(position, chr(input_char))
    if position < len(chars):
        position += 1
    return _EditString(chars, position)


def _toggle_note_todo(todo: Todo) -> None:
    if not todo.has_box():
        todo.set_box_char(BoxChar.MINUS)
        return
    todo.set_box_char(BoxChar.NONE)


def _get_chars_position(
    input_char: int,
    stdscr_win: tuple[curses.window, curses.window],
    chars_position_todo: tuple[_Chars, int, Todo],
    mode: SingleLineModeImpl,
) -> _EditString | None | str:
    chars, position, todo = chars_position_todo
    if input_char == Key.escape:
        return _handle_escape(stdscr_win, chars, position, mode, todo)
    if input_char == Key.tab:
        return _handle_indent(stdscr_win[0], todo, chars, position)
    backspace_table = {
        Key.backspace: _handle_backspace,
        Key.backspace_: _handle_backspace,
        Key.backspace__: _handle_backspace,
        Key.ctrl_backspace: _handle_ctrl_backspace,
    }
    if input_char in backspace_table:
        return backspace_table[input_char](chars, position)
    return _handle_ascii(chars, position, input_char)


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
            If the window is too long to display the maximum
            n characters.

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
    while True:
        if len(chars) + 1 >= win.getmaxyx()[1] - 1:
            return todo.set_display_text(
                _set_once(mode, chars, position, todo.get_color()),
            )
        if position == len(chars):
            win.addch(1, len(chars) + 1, "█")
        for i, char in enumerate("".join(chars).ljust(win.getmaxyx()[1] - 2)):
            win.addch(
                1, i + 1, char, curses.A_STANDOUT if i == position else curses.A_NORMAL
            )
        win.refresh()
        try:
            input_char = win.getch()
        except KeyboardInterrupt:  # ctrl+c
            mode.set_on()
            return original
        if input_char in (Key.enter, Key.enter_):
            break
        if input_char in (Key.ctrl_k, Key.ctrl_x):
            mode.toggle()
            break
        next_step = _get_chars_position(
            input_char,
            (stdscr, win),
            (chars, position, todo),
            mode,
        )
        if next_step is None:
            return original
        if isinstance(next_step, str):
            mode.set_extra_data(f"{todo.get_color().as_char()} {mode.get_extra_data()}")
            return todo.set_display_text(next_step)
        chars, position = next_step

    return todo.set_display_text("".join(chars))
