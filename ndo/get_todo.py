"""Open a text input box, implement typing, and return text input"""

from collections.abc import Iterable
from typing import Callable, NamedTuple

from ndo.get_args import (
    HELP_FILE,
    INDENT,
    INPUT_BEGIN_INDEX,
    INPUT_END_INDEX,
    UI_TYPE,
    UiType,
)
from ndo.keys import Key
from ndo.menus import help_menu
from ndo.mode import SingleLineMode, SingleLineModeImpl
from ndo.todo import BoxChar, Todo
from ndo.utils import NewTodoPosition, alert, chunk_message, set_header

if UI_TYPE == UiType.ANSI:
    import ndo.acurses as curses
elif UI_TYPE == UiType.TKINTER:
    import ndo.tcurses as curses
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

    _HEADER_STRING = "Insert mode: <Alt>+<h> for help"

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

    def _move_right(self) -> _EditString:
        """Move the cursor to the right"""
        if self._position < len(self._chars):
            self._position += 1
        return _EditString(self._chars, self._position)

    def _word_right(self) -> _EditString:
        """Move the cursor right by a word"""
        while True:
            if self._position >= len(self._chars) - 1:
                break
            self._position += 1
            if not self._chars[self._position].isalnum():
                break
        return _EditString(self._chars, self._position)

    def _move_left(self) -> _EditString:
        """Move the cursor to the left"""
        if self._position > 0:
            self._position -= 1
        return _EditString(self._chars, self._position)

    def _word_left(self) -> _EditString:
        """Move the cursor left by a word"""
        while True:
            if self._position <= 0:
                break
            self._position -= 1
            if not self._chars[self._position].isalnum():
                break
        return _EditString(self._chars, self._position)

    def _delete_right_word(self) -> _EditString:
        """Remove the word to the right of the cursor"""
        if self._position < len(self._chars) - 1:
            self._chars.pop(self._position)
            self._position -= 1
        while True:
            if self._position >= len(self._chars) - 1:
                break
            self._position += 1
            if not self._chars[self._position].isalnum():
                break
            self._chars.pop(self._position)
            self._position -= 1
        return _EditString(self._chars, self._position)

    def _handle_delete(self) -> _EditString:
        if self._position < len(self._chars):
            self._chars.pop(self._position)
        return _EditString(self._chars, self._position)

    def _handle_help_menu(self) -> _EditString:
        """Wrapper for ndo.menus.help_menu()"""
        help_menu(
            self._stdscr,
            str(HELP_FILE),
            INPUT_BEGIN_INDEX,
            INPUT_END_INDEX,
        )
        self._stdscr.clear()
        self._win.box()
        set_header(self._stdscr, self._HEADER_STRING)
        self._stdscr.refresh()
        return _EditString(self._chars, self._position)

    def _handle_escape(self) -> bool:
        """
        Handle escape sequences (including just `esc` key).

        Return whether input window should close.
        """
        self._win.nodelay(True)  # noqa: FBT003
        try:
            input_char = Key(self._win.getch())
        except KeyboardInterrupt:
            return True
        self._win.nodelay(False)  # noqa: FBT003
        table: dict[Key, Callable[[], _EditString]] = {
            Key.ctrl_backspace: self._delete_left_word,
            Key.ctrl_backspace_: self._delete_left_word,
            Key.ctrl_backspace__: self._delete_left_word,
            Key.backspace__: self._delete_left_word,
            Key.ctrl_delete: self._delete_right_word,
            Key.alt_h: self._handle_help_menu,
        }
        if input_char == Key.nodelay_escape:
            return True
        if input_char not in table:
            self._error_passthrough(str(input_char))
            return False
        self._chars, self._position = table[input_char]()
        return False

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

    def _move_start(self) -> _EditString:
        """Move the cursor to the beginning of the string"""
        return _EditString(self._chars, 0)

    def _move_end(self) -> _EditString:
        """Move the cursor to the end of the string"""
        return _EditString(self._chars, len(self._chars))

    def _error_passthrough(
        self,
        key_name: str,
    ) -> _EditString:
        """
        Display an alert message for unsupported keys and
        return chars and position
        """
        alert(self._stdscr, f"Key `{key_name}` is not supported")
        return _EditString(self._chars, self._position)

    def _handle_new_todo(self) -> str:
        self._mode.set_once(NewTodoPosition.CURRENT)
        first_section = "".join(self._chars[: self._position])
        second_section = "".join(self._chars[self._position :])
        self._mode.set_extra_data(
            self._todo.get_header() + first_section,
        )
        return second_section

    def _handle_backspace(self) -> _EditString:
        if self._position > 0:
            self._position -= 1
            self._chars.pop(self._position)
        return _EditString(self._chars, self._position)

    def _delete_left_word(self) -> _EditString:
        """Remove the word to the left of the cursor"""
        while True:
            if self._position <= 0:
                break
            self._position -= 1
            if not self._chars[self._position].isalnum():
                self._chars.pop(self._position)
                break
            self._chars.pop(self._position)
        return _EditString(self._chars, self._position)

    def _handle_printable(self, input_char: Key) -> _EditString:
        self._chars.insert(self._position, chr(input_char.value))
        if self._position < len(self._chars):
            self._position += 1
        return _EditString(self._chars, self._position)

    def _toggle_note_todo(self) -> None:
        if not self._todo.has_box():
            self._todo.set_box_char(BoxChar.MINUS)
            return
        self._todo.set_box_char(BoxChar.NONE)

    def _set_once(self) -> str:
        position = (
            NewTodoPosition.NEXT
            if self._position == len(self._chars)
            else NewTodoPosition.CURRENT
        )
        self._mode.set_once(position)
        string = "".join(self._chars)
        two_lines = (
            string.rsplit(None, 1)
            if self._position > len(self._chars) - 1
            else [string[: self._position], string[self._position :]]
        )
        if string.endswith(" "):
            two_lines[-1] += " "
        header = self._todo.get_header().strip()
        if len(two_lines) == 1:
            line = two_lines[0]
            self._mode.set_extra_data(f"{header} {line[-1]}")
            return line[:-1]
        self._mode.set_extra_data(f"{header} {two_lines[position.value]}")
        return two_lines[int(not bool(position.value))]

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

    def _should_exit(self, input_char: Key) -> bool:
        if input_char in (Key.ctrl_k, Key.ctrl_x):
            self._mode.toggle()
            return True
        return input_char in (Key.enter, Key.enter_)

    def _simple_to_handle(
        self,
        input_char: Key,
        key_handlers: dict[Key, Callable[..., _EditString]],
    ) -> bool:
        if input_char in key_handlers:
            self._chars, self._position = key_handlers[Key(input_char)]()
            return True
        if chr(input_char.value).isprintable():
            self._handle_printable(input_char)
            return True
        if input_char == Key.up_arrow:
            self._error_passthrough("up arrow")
            return True
        return False

    def _handle_long_display_text(self, max_width: int) -> Todo:
        """Split a long message into chunks"""
        self._mode.set_once(NewTodoPosition.NEXT)
        chunks = chunk_message("".join(self._chars), max_width)
        first_chunk = next(chunks)
        self._mode.set_extra_data(" ".join(chunks))
        return self._todo.set_display_text(first_chunk)

    def get_todo(self) -> Todo:
        """External method to get a todo object from the user"""
        set_header(self._stdscr, self._HEADER_STRING)
        self._stdscr.refresh()

        original = self._todo.copy()

        key_handlers: dict[Key, Callable[..., _EditString]] = {
            Key.left_arrow: self._move_left,
            Key.right_arrow: self._move_right,
            Key.backspace: self._handle_backspace,
            Key.backspace_: self._handle_backspace,
            Key.backspace__: self._handle_backspace,
            Key.ctrl_backspace: self._delete_left_word,
            Key.shift_tab: self._handle_dedent,
            Key.shift_tab_windows: self._handle_dedent,
            Key.tab: self._handle_indent,
            Key.ctrl_left_arrow: self._word_left,
            Key.ctrl_right_arrow: self._word_right,
            Key.home: self._move_start,
            Key.end: self._move_end,
            Key.delete: self._handle_delete,
            Key.shift_delete: self._handle_toggle_note_todo,
            Key.alt_delete: self._handle_toggle_note_todo,
        }

        max_width = self._win.getmaxyx()[1] - 2
        if len(self._chars) >= max_width:
            return self._handle_long_display_text(max_width)

        while True:
            if len(self._chars) >= max_width:
                return self._todo.set_display_text(
                    self._set_once(),
                )
            self._display()
            try:
                input_char = Key(self._win.getch())
            except KeyboardInterrupt:
                self._mode.set_on()
                return original
            if self._should_exit(input_char):
                return self._todo.set_display_text("".join(self._chars))
            if input_char == Key.escape:
                if self._handle_escape():
                    self._mode.set_on()
                    return original
                continue
            if input_char == Key.down_arrow:
                return self._todo.set_display_text(self._handle_new_todo())
            if self._simple_to_handle(input_char, key_handlers):
                continue
            self._error_passthrough(str(input_char))
