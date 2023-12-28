# pylint: disable=missing-class-docstring, import-error
# pylint: disable=missing-function-docstring, missing-module-docstring

from typing import Any, Callable, Iterable, NamedTuple

from src.class_mode import SingleLineMode, SingleLineModeImpl
from src.class_todo import BoxChar, Todo
from src.get_args import INDENT, TKINTER_GUI
from src.keys import Key
from src.utils import set_header

if TKINTER_GUI:
    from tcurses import curses
else:
    import curses


class Chars(list[str]):
    def __init__(self, iterable: Iterable[str]):
        super().__init__(iterable)


class EditString(NamedTuple):
    """
    An Editable string. Takes in parameters `string` and `position`.
    These should be represented as `Chars` and `int` respectively.
    """

    string: Chars
    position: int


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


def init_todo(todo: Todo, prev_todo: Todo, mode: SingleLineModeImpl) -> Todo:
    if todo.is_empty():
        todo.set_indent_level(prev_todo.indent_level)
        todo.set_color(prev_todo.color)
        if not prev_todo.has_box():
            todo.box_char = BoxChar.NONE
    if mode.is_off():
        todo.box_char = BoxChar.NONE
    return todo


def handle_right_arrow(chars: Chars, position: int) -> EditString:
    if position < len(chars):
        position += 1
    return EditString(chars, position)


def handle_ctrl_right_arrow(chars: Chars, position: int) -> EditString:
    while True:
        if position >= len(chars) - 1:
            break
        position += 1
        if chars[position] == " ":
            break
    return EditString(chars, position)


def handle_left_arrow(chars: Chars, position: int) -> EditString:
    if position > 0:
        position -= 1
    return EditString(chars, position)


def handle_ctrl_left_arrow(chars: Chars, position: int) -> EditString:
    while True:
        if position <= 0:
            break
        position -= 1
        if chars[position] == " ":
            break
    return EditString(chars, position)


def handle_ctrl_delete(chars: Chars, position: int) -> EditString:
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
    return EditString(chars, position)


def handle_delete(chars: Chars, position: int) -> EditString:
    if position < len(chars):
        chars.pop(position)
    return EditString(chars, position)


def handle_ctrl_arrow(win: Any, chars: Chars, position: int) -> EditString:
    for _ in ";5":
        win.getch()
    options: dict[int, Callable[[Chars, int], EditString]] = {
        Key.right_arrow: handle_ctrl_right_arrow,
        Key.left_arrow: handle_ctrl_left_arrow,
    }
    direction = win.getch()
    if direction in options:
        chars, position = options[direction](chars, position)
    return EditString(chars, position)


def handle_delete_modifiers(
    stdscr_win: tuple[Any, Any], todo: Todo, chars: Chars, position: int
) -> EditString:
    try:
        input_char = stdscr_win[1].getch()
    except KeyboardInterrupt:
        return EditString(chars, position)
    if input_char == Key.tilde:
        return handle_delete(chars, position)
    if input_char == Key.semi_colon:
        try:
            modifier = stdscr_win[1].getch()
        except KeyboardInterrupt:
            return EditString(chars, position)
        stdscr_win[1].getch()  # skip `~`
        if modifier == Key.modifier_ctrl:
            return handle_ctrl_delete(chars, position)
        if modifier in (Key.modifier_shift, Key.modifier_alt):
            handle_toggle_note_todo(stdscr_win[0], todo)
    return EditString(chars, position)


def handle_toggle_note_todo(stdscr: Any, todo: Todo) -> None:
    toggle_note_todo(todo)
    set_header(stdscr, "Note" if todo.box_char == BoxChar.NONE else "Todo")
    stdscr.refresh()


def handle_indent_dedent(
    stdscr: Any, todo: Todo, action: str, chars: Chars, position: int
) -> EditString:
    if action == "indent":
        todo.indent()
    elif action == "dedent":
        todo.dedent()
    set_header(stdscr, f"Tab level: {todo.indent_level // INDENT} tabs")
    stdscr.refresh()
    return EditString(chars, position)


def handle_home(chars: Chars) -> EditString:
    return EditString(chars, 0)


def handle_end(chars: Chars) -> EditString:
    return EditString(chars, len(chars))


def handle_escape(
    stdscr_win: tuple[Any, Any],
    chars: Chars,
    position: int,
    mode: SingleLineModeImpl,
    todo: Todo,
) -> EditString | None:
    stdscr_win[1].nodelay(True)
    if stdscr_win[1].getch() == -1:  # check for escape
        mode.set_on()
        return None
    stdscr_win[1].nodelay(False)
    try:
        subch = stdscr_win[1].getch()
    except KeyboardInterrupt:
        return None
    subch_table: dict[int, tuple[Callable[..., EditString], tuple[Any, ...]]] = {
        Key.left_arrow: (handle_left_arrow, (chars, position)),
        Key.right_arrow: (handle_right_arrow, (chars, position)),
        Key.modifier_delete: (
            handle_delete_modifiers,
            (stdscr_win, todo, chars, position),
        ),
        Key.ctrl_arrow: (handle_ctrl_arrow, (stdscr_win[1], chars, position)),
        Key.home: (
            handle_home,
            (chars,),
        ),
        Key.end: (
            handle_end,
            (chars,),
        ),
        Key.indent_dedent: (
            handle_indent_dedent,
            (stdscr_win[0], todo, "dedent", chars, position),
        ),
    }
    func, args = subch_table[subch]
    return func(*args)


def handle_backspace(chars: Chars, position: int) -> EditString:
    if position > 0:
        position -= 1
        chars.pop(position)
    return EditString(chars, position)


def handle_ctrl_backspace(chars: Chars, position: int) -> EditString:
    while True:
        if position <= 0:
            break
        position -= 1
        if chars[position] == " ":
            chars.pop(position)
            break
        chars.pop(position)
    return EditString(chars, position)


def handle_ascii(chars: Chars, position: int, input_char: int) -> EditString:
    chars.insert(position, chr(input_char))
    if position < len(chars):
        position += 1
    return EditString(chars, position)


def toggle_note_todo(todo: Todo) -> None:
    if todo.box_char == BoxChar.NONE:
        todo.box_char = BoxChar.MINUS
        return
    todo.box_char = BoxChar.NONE


def get_chars_position(
    input_char: int,
    stdscr_win: tuple[Any, Any],
    chars_position_todo: tuple[Chars, int, Todo],
    mode: SingleLineModeImpl,
    backspace_table: dict[int, Callable[..., EditString]],
) -> EditString | None:
    chars, position, todo = chars_position_todo
    if input_char == Key.escape:
        return handle_escape(stdscr_win, chars, position, mode, todo)
    if input_char == Key.tab:
        return handle_indent_dedent(stdscr_win[0], todo, "indent", chars, position)
    if input_char in backspace_table:
        return backspace_table[input_char](chars, position)
    return handle_ascii(chars, position, input_char)


def set_once(mode: SingleLineModeImpl, chars: Chars) -> str:
    mode.set_once()
    two_lines = "".join(chars).rsplit(None, 1)
    if len(two_lines) == 1:
        line = two_lines[0]
        mode.set_extra_data(line[-1])
        return line[:-1]
    mode.set_extra_data(two_lines[1])
    return two_lines[0]


def get_todo(
    stdscr: Any,
    win: Any,
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

    ensure_valid(win)
    todo = init_todo(todo, prev_todo, mode)
    original = todo.copy()
    chars = Chars(todo.display_text)
    position = len(chars)
    win.box()
    win.nodelay(False)
    backspace_table = {
        Key.backspace: handle_backspace,
        Key.backspace_: handle_backspace,
        Key.backspace__: handle_backspace,
        Key.ctrl_backspace: handle_ctrl_backspace,
    }
    while True:
        if len(chars) + 1 >= win.getmaxyx()[1] - 1:
            return todo.set_display_text(set_once(mode, chars))
        if position == len(chars):
            win.addstr(1, len(chars) + 1, "█")
        for i, char in enumerate("".join(chars).ljust(win.getmaxyx()[1] - 2)):
            win.addstr(1, i + 1, char, curses.A_STANDOUT if i == position else 0)
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
        next_step = get_chars_position(
            input_char, (stdscr, win), (chars, position, todo), mode, backspace_table
        )
        if next_step is None:
            return original
        chars, position = next_step

    return todo.set_display_text("".join(chars))
