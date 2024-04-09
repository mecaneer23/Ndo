"""
Helpers for storing a cursor, or a position in a list.

Especially helpful for storing a cursor which might span
multiple consecutive positions.
"""

from enum import Enum
from typing import Iterable

from src.class_todo import Todos, TodoList
from src.get_args import TKINTER_GUI
from src.keys import Key

if TKINTER_GUI:
    import src.tcurses as curses
else:
    import curses  # type: ignore


class _Direction(Enum):
    UP = 0
    DOWN = 1
    NONE = 2


class Positions(list[int]):
    """
    Wrapper for a list of indices of positions
    """

    def __init__(self, iterable: Iterable[int]):
        super().__init__(iterable)


class Cursor:
    """
    Store position(s) in a list using a `Positions` object

    Especially helpful for storing a cursor which might span
    multiple consecutive positions
    """

    def __init__(self, position: int, *positions: int) -> None:
        self.positions: Positions = Positions([position, *positions])
        self.direction: _Direction = _Direction.NONE

    def __len__(self) -> int:
        return len(self.positions)

    def __str__(self) -> str:
        return str(self.positions[0])

    def __repr__(self) -> str:
        return " ".join(map(str, self.positions))

    def __int__(self) -> int:
        return self.positions[0]

    def __contains__(self, child: int) -> bool:
        return child in self.positions

    def get(self) -> Positions:
        """Return a `Positions` object holding the current cursor"""
        return self.positions

    def get_first(self) -> int:
        """Return the top-most selected position"""
        return self.positions[0]

    def get_last(self) -> int:
        """Return the bottom-most selected position"""
        return self.positions[-1]

    def set_to(self, position: int) -> None:
        """Replace the entire cursor with a new single position"""
        self.positions = Positions([position])

    def todo_set_to(self, todo_position: TodoList) -> Todos:
        """
        Replace the entire cursor with a new single position
        and pass the todo portion of the `TodoList` through
        the method.
        """
        self.positions[0] = todo_position[1]
        return todo_position[0]

    def todos_override(self, todos: Todos, positions: Positions) -> Todos:
        """
        Replace the cursor with a new `Positions`, and pass the
        todos through the method.
        """
        self.positions = positions
        return todos

    def slide_up(self, single: bool = False) -> None:
        """Shift each value in the cursor up by 1"""
        if min(self.positions) == 0:
            return
        if single:
            self.positions = Positions([min(self.positions) - 1])
            return
        self.positions.insert(0, min(self.positions) - 1)
        self.positions.pop()

    def slide_down(self, max_len: int, single: bool = False) -> None:
        """Shift each value in the cursor down by 1"""
        if max(self.positions) >= max_len - 1:
            return
        if single:
            self.positions = Positions([max(self.positions) + 1])
            return
        self.positions.append(max(self.positions) + 1)
        self.positions.pop(0)

    def _select_next(self) -> None:
        """Extend the cursor down by 1"""
        self.positions.append(max(self.positions) + 1)

    def _deselect_next(self) -> None:
        """Retract the cursor by 1"""
        if len(self.positions) > 1:
            self.positions.remove(max(self.positions))

    def _deselect_prev(self) -> None:
        """Remove the first position of the cursor"""
        if len(self.positions) > 1:
            self.positions.remove(min(self.positions))

    def _select_prev(self) -> None:
        """Extend the cursor up by 1"""
        self.positions.insert(0, min(self.positions) - 1)

    def get_deletable(self) -> Positions:
        """
        Return a Positions object with each value
        set to the minimum position of the current
        Cursor
        """
        return Positions([min(self.positions) for _ in self.positions])

    def multiselect_down(self, max_len: int) -> None:
        """Extend the cursor down by 1"""
        if max(self.positions) >= max_len - 1:
            return
        if len(self.positions) == 1 or self.direction == _Direction.DOWN:
            self._select_next()
            self.direction = _Direction.DOWN
            return
        self._deselect_prev()

    def multiselect_up(self) -> None:
        """Extend the cursor up by 1"""
        if min(self.positions) == 0 and self.direction == _Direction.UP:
            return
        if len(self.positions) == 1 or self.direction == _Direction.UP:
            self._select_prev()
            self.direction = _Direction.UP
            return
        self._deselect_next()

    def multiselect_top(self) -> None:
        """
        Select every position between 0 and
        the current top of the selection
        """
        for _ in range(self.positions[0], 0, -1):
            self.multiselect_up()

    def multiselect_bottom(self, max_len: int) -> None:
        """
        Select every position between the
        current top of the selection and
        the `max_len` of the list
        """
        for _ in range(self.positions[0], max_len):
            self.multiselect_down(max_len)

    def _multiselect_to(self, position: int, max_len: int) -> None:
        """Select from current position up or down `position`"""
        direction = -1 if position < self.positions[0] else 1
        for _ in range(self.positions[0], position, direction):
            if direction == 1:
                self.multiselect_down(max_len)
                continue
            self.multiselect_up()

    def multiselect_from(
        self, stdscr: curses.window, first_digit: int, max_len: int
    ) -> None:
        """
        Move the cursor to the specified position relative to the current position.

        Because the trigger can only be a single keypress, this function also uses a
        window object to getch until the user presses g or shift + g. This allows
        for relative movement greater than 9 lines away.
        """
        total = str(first_digit)
        while True:
            try:
                key = stdscr.getch()
            except KeyboardInterrupt:  # exit on ^C
                return
            if key != Key.escape:  # not an escape sequence
                return
            stdscr.nodelay(True)
            subch = stdscr.getch()  # alt + ...
            stdscr.nodelay(False)
            if subch == Key.k:
                self._multiselect_to(self.positions[0] - int(total), max_len)
            elif subch == Key.j:
                self._multiselect_to(self.positions[0] + int(total), max_len)
            elif subch in Key.digits():
                total += str(Key.normalize_ascii_digit_to_digit(subch))
                continue
            return

    def multiselect_all(self, max_len: int) -> None:
        """Set internal positions to entirity of list"""
        self.positions = Positions(range(0, max_len))
