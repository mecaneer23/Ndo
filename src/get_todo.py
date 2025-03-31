"""Open a text input box, implement typing, and return text input"""

from collections.abc import Iterable
from typing import Callable, NamedTuple, cast

from src.class_mode import SingleLineMode, SingleLineModeImpl
from src.class_todo import BoxChar, Todo
from src.get_args import INDENT, UI_TYPE, UiType
from src.keys import Key
from src.utils import Color, alert, set_header

if UI_TYPE == UiType.ANSI:
    import src.acurses as curses
elif UI_TYPE == UiType.TKINTER:
    import src.tcurses as curses
else:
    import curses


class _Chars(list[str]):
    """A list of characters; an alias for `list[str]`"""

    def __init__(self, iterable: Iterable[str]) -> None:
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
    win.addch(y_loc, x_loc, cast("str", curses.ACS_LTEE))
    win.hline(y_loc, x_loc + 1, cast("str", char), width - 2)
    win.addch(y_loc, x_loc + width - 1, cast("str", curses.ACS_RTEE))


class InputTodo:
    """
    Reads a string from the given window. Returns a todo from the user.
    Functions like a JavaScript alert box for user input.

    Once class is instantiated, call get_todo()

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

    def __init__(
        self,
        stdscr: curses.window,
        win: curses.window,
        todo: Todo,
        prev_todo: Todo,
        mode: SingleLineModeImpl | None = None,
    ) -> None:
        self._stdscr = stdscr
        self._win = win
        self._todo = todo
        self._prev_todo = prev_todo
        self._mode = (
            SingleLineModeImpl(SingleLineMode.NONE) if mode is None else mode
        )
        self._ensure_valid()
        self._init_todo()
        self._chars = _Chars(todo.get_display_text())
        self._position = len(self._chars)

        self._win.box()
        self._win.nodelay(False)  # noqa: FBT003
        self._win.keypad(True)  # noqa: FBT003

    def _ensure_valid(self) -> None:
        min_line_amount = 1
        border_total_width = 2
        if self._win.getmaxyx()[0] < min_line_amount + border_total_width:
            msg = "Window is too short, it won't be able to\
                display the minimum 1 line of text."
            raise ValueError(msg)
        if self._win.getmaxyx()[0] > min_line_amount + border_total_width:
            msg = "Multiline text editing is not supported"
            raise NotImplementedError(msg)

    def _init_todo(self) -> None:
        if self._todo.is_empty():
            self._todo.set_indent_level(self._prev_todo.get_indent_level())
            self._todo.set_color(self._prev_todo.get_color())
            if not self._prev_todo.has_box():
                self._todo.set_box_char(BoxChar.NONE)
        if self._mode.is_off():
            self._todo.set_box_char(BoxChar.NONE)

    def _handle_right_arrow(self) -> _EditString:
        if self._position < len(self._chars):
            self._position += 1
        return _EditString(self._chars, self._position)

    def _handle_ctrl_right_arrow(self) -> _EditString:
        while True:
            if self._position >= len(self._chars) - 1:
                break
            self._position += 1
            if self._chars[self._position] == " ":
                break
        return _EditString(self._chars, self._position)

    def _handle_left_arrow(self) -> _EditString:
        if self._position > 0:
            self._position -= 1
        return _EditString(self._chars, self._position)

    def _handle_ctrl_left_arrow(self) -> _EditString:
        while True:
            if self._position <= 0:
                break
            self._position -= 1
            if self._chars[self._position] == " ":
                break
        return _EditString(self._chars, self._position)

    def _handle_ctrl_delete(self) -> _EditString:
        if self._position < len(self._chars) - 1:
            self._chars.pop(self._position)
            self._position -= 1
        while True:
            if self._position >= len(self._chars) - 1:
                break
            self._position += 1
            if self._chars[self._position] == " ":
                break
            self._chars.pop(self._position)
            self._position -= 1
        return _EditString(self._chars, self._position)

    def _handle_delete(self) -> _EditString:
        if self._position < len(self._chars):
            self._chars.pop(self._position)
        return _EditString(self._chars, self._position)

    def _handle_escape(self) -> _EditString | None:
        self._win.nodelay(True)  # noqa: FBT003
        if self._win.getch() == Key.nodelay_escape:
            self._win.nodelay(False)  # noqa: FBT003
            return None
        self._win.nodelay(False)  # noqa: FBT003
        try:
            input_char = self._win.getch()
        except KeyboardInterrupt:
            return None
        if input_char == Key.ctrl_delete:
            return self._handle_ctrl_delete()
        return self._error_passthrough(str(input_char))

    def _handle_toggle_note_todo(self) -> _EditString:
        self._toggle_note_todo()
        set_header(self._stdscr, "Todo" if self._todo.has_box() else "Note")
        self._stdscr.refresh()
        return _EditString(self._chars, self._position)

    def _handle_indent(self) -> _EditString:
        self._todo.indent()
        set_header(
            self._stdscr,
            f"Tab level: {self._todo.get_indent_level() // INDENT} tabs",
        )
        self._stdscr.refresh()
        return _EditString(self._chars, self._position)

    def _handle_dedent(self) -> _EditString:
        self._todo.dedent()
        set_header(
            self._stdscr,
            f"Tab level: {self._todo.get_indent_level() // INDENT} tabs",
        )
        self._stdscr.refresh()
        return _EditString(self._chars, self._position)

    def _handle_home(self) -> _EditString:
        return _EditString(self._chars, 0)

    def _handle_end(self) -> _EditString:
        return _EditString(self._chars, len(self._chars))

    def _error_passthrough(
        self,
        key_name: str,
    ) -> _EditString:
        alert(self._stdscr, f"Key `{key_name}` is not supported")
        return _EditString(self._chars, self._position)

    def _handle_new_todo(self) -> str:
        self._mode.set_once()
        self._mode.set_extra_data("".join(self._chars[self._position :]))
        return "".join(self._chars[: self._position])

    def _handle_backspace(self) -> _EditString:
        if self._position > 0:
            self._position -= 1
            self._chars.pop(self._position)
        return _EditString(self._chars, self._position)

    def _handle_ctrl_backspace(self) -> _EditString:
        while True:
            if self._position <= 0:
                break
            self._position -= 1
            if self._chars[self._position] == " ":
                self._chars.pop(self._position)
                break
            self._chars.pop(self._position)
        return _EditString(self._chars, self._position)

    def _handle_printable(self, input_char: int) -> _EditString:
        self._chars.insert(self._position, chr(input_char))
        if self._position < len(self._chars):
            self._position += 1
        return _EditString(self._chars, self._position)

    def _toggle_note_todo(self) -> None:
        if not self._todo.has_box():
            self._todo.set_box_char(BoxChar.MINUS)
            return
        self._todo.set_box_char(BoxChar.NONE)

    def _set_once(self, color: Color) -> str:
        self._mode.set_once()
        string = "".join(self._chars)
        two_lines = (
            string.rsplit(None, 1)
            if self._position > len(self._chars) - 1
            else (string[: self._position], string[self._position :])
        )
        if len(two_lines) == 1:
            line = two_lines[0]
            self._mode.set_extra_data(f"{color.as_char()} {line[-1]}")
            return line[:-1]
        self._mode.set_extra_data(f"{color.as_char()} {two_lines[1]}")
        return two_lines[0]

    def _display(self) -> None:
        for i, char in enumerate(
            "".join(self._chars).ljust(self._win.getmaxyx()[1] - 2),
        ):
            self._win.addstr(  # avoid addch; output should not be buffered
                1,
                i + 1,
                char,
                curses.A_STANDOUT if i == self._position else curses.A_NORMAL,
            )
        self._win.refresh()

    def _should_exit(self, input_char: int) -> bool:
        if input_char in (Key.ctrl_k, Key.ctrl_x):
            self._mode.toggle()
            return True
        return input_char in (Key.enter, Key.enter_)

    def _simple_to_handle(
        self,
        input_char: int,
        key_handlers: dict[int, Callable[..., _EditString]],
    ) -> bool:
        if input_char in key_handlers:
            self._chars, self._position = key_handlers[input_char]()
            return True
        if chr(input_char).isprintable():
            self._handle_printable(input_char)
            return True
        if input_char == Key.up_arrow:
            self._error_passthrough("up arrow")
            return True
        return False

    def get_todo(self) -> Todo:
        """External method to get a todo object from the user"""
        original = self._todo.copy()

        key_handlers: dict[int, Callable[..., _EditString]] = {
            Key.left_arrow: self._handle_left_arrow,
            Key.right_arrow: self._handle_right_arrow,
            Key.backspace: self._handle_backspace,
            Key.backspace_: self._handle_backspace,
            Key.backspace__: self._handle_backspace,
            Key.ctrl_backspace: self._handle_ctrl_backspace,
            Key.shift_tab: self._handle_dedent,
            Key.shift_tab_windows: self._handle_dedent,
            Key.tab: self._handle_indent,
            Key.ctrl_left_arrow: self._handle_ctrl_left_arrow,
            Key.ctrl_right_arrow: self._handle_ctrl_right_arrow,
            Key.home: self._handle_home,
            Key.end: self._handle_end,
            Key.delete: self._handle_delete,
            Key.shift_delete: self._handle_toggle_note_todo,
            Key.alt_delete: self._handle_toggle_note_todo,
        }

        while True:
            if len(self._chars) + 1 >= self._win.getmaxyx()[1] - 1:
                return self._todo.set_display_text(
                    self._set_once(self._todo.get_color()),
                )
            self._display()
            try:
                input_char = self._win.getch()
            except KeyboardInterrupt:
                self._mode.set_on()
                return original
            if self._simple_to_handle(input_char, key_handlers):
                continue
            if self._should_exit(input_char):
                return self._todo.set_display_text("".join(self._chars))
            if input_char == Key.escape:
                possible_chars_position = self._handle_escape()
                if possible_chars_position is None:
                    self._mode.set_on()
                    return original
                self._chars, self._position = possible_chars_position
                continue
            if input_char == Key.down_arrow:
                self._mode.set_extra_data(
                    f"{self._todo.get_color().as_char()} "
                    f"{self._mode.get_extra_data()}",
                )
                return self._todo.set_display_text(self._handle_new_todo())
            self._error_passthrough(str(input_char))
