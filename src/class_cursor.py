"""
Helpers for storing a cursor, or a position in a list.

Especially helpful for storing a cursor which might span
multiple consecutive positions.
"""

from enum import Enum

# from functools import wraps
# from typing import Any, Callable, Iterable, TypeVar
from typing import TypeVar

from src.class_todo import Todos
from src.get_args import UI_TYPE, UiType
from src.keys import Key
from src.utils import clamp

if UI_TYPE == UiType.ANSI:
    import src.acurses as curses
elif UI_TYPE == UiType.TKINTER:
    import src.tcurses as curses  # type: ignore
else:
    import curses  # type: ignore


T = TypeVar("T")


class _Direction(Enum):
    UP = 0
    DOWN = 1
    NONE = 2


class Positions:
    """
    Store a group of consecutive ints
    """

    @classmethod
    def from_start(cls, start: int) -> "Positions":
        """Construct a Positions object from a single int"""
        return cls(start, start + 1)

    def __init__(self, start: int, stop: int) -> None:
        self._start = start
        self._stop = stop

    def get_start(self) -> int:
        """Getter for start"""
        return self._start

    def get_stop(self) -> int:
        """Getter for stop"""
        return self._stop

    def __len__(self) -> int:
        return self._stop - self._start

    def __contains__(self, child: int) -> bool:
        return self._start <= child < self._stop

    def as_range(self) -> range:
        """Getter for Positions represented as an iterator"""
        return range(self._start, self._stop)

    def raise_start(self, amount: int) -> None:
        """Raise start by `amount`"""
        self._start += amount

    def raise_stop(self, amount: int) -> None:
        """Raise stop by `amount`"""
        self._stop += amount


class Cursor:
    """
    Store potentially multiple consectutive position(s) using a
    `Positions` object
    """

    def __init__(self, position: int, todos: Todos) -> None:
        self._positions: Positions = Positions.from_start(position)
        self._direction: _Direction = _Direction.NONE
        # self._todos: Todos = todos
        _ = todos

    def __len__(self) -> int:
        return len(self._positions)

    def __str__(self) -> str:
        return str(self.get_first())

    def __repr__(self) -> str:
        return " ".join(map(str, self._positions.as_range()))

    def __int__(self) -> int:
        return self.get_first()

    def __contains__(self, child: int) -> bool:
        return child in self._positions

    def __iter__(self) -> range:
        return self.get()

    def get(self) -> range:
        """Return a iterable object holding the current cursor"""
        return self._positions.as_range()

    def get_first(self) -> int:
        """Return the top-most selected position"""
        return self._positions.get_start()

    def get_last(self) -> int:
        """Return the bottom-most selected position"""
        return self._positions.get_stop() - 1

    # @staticmethod
    # def _updates_cursor(
    #     direction: _Direction = _Direction.NONE,
    # ) -> Callable[[Callable[..., T]], Callable[..., T]]:
    #     """
    #     Decorate every function that updates the cursor.
    #     This function ensures folded todos are handled
    #     properly. This basically treats each folded group
    #     of todos like its own individual todo.
    #     """

    #     def _decorator(func: Callable[..., T]) -> Callable[..., T]:
    #         @wraps(func)
    #         def _inner(self: "Cursor", *args: list[Any], **kwargs: dict[Any, Any]) -> T:
    #             for pos in self._positions:
    #                 # if not self._todos[pos].is_folded_parent():
    #                 # break
    #                 count = 0
    #                 while True:
    #                     count += 1
    #                     if not self._todos[pos + count].is_folded():
    #                         break
    #                     if direction == _Direction.UP:
    #                         self.multiselect_up()
    #                         continue
    #                     if direction == _Direction.DOWN:
    #                         self.multiselect_down(len(self._todos))
    #                         continue
    #                     if direction == _Direction.NONE:
    #                         func(self, *args, **kwargs)
    #             return func(self, *args, **kwargs)

    #         return _inner

    #     return _decorator

    def set_to(self, position: int) -> None:
        """Replace the entire cursor with a new single position"""
        self._positions = Positions.from_start(position)

    def override_passthrough(self, passthrough: T, positions: Positions) -> T:
        """
        Replace the cursor with a new `Positions`, and pass the
        passthrough through the method.
        """
        self._positions = positions
        return passthrough

    def single_up(self, max_len: int) -> None:
        """Move a cursor with length 1 up by 1"""
        if len(self._positions) == max_len:
            self.set_to(0)
            return
        if self.get_first() == 0:
            return
        self.set_to(self.get_first() - 1)
        # while self.todos[self.get_first()].is_folded():
        #     self.multiselect_up()

    def slide_up(self) -> None:
        """Shift each value in the cursor up by 1"""
        if self.get_first() == 0:
            return
        self._positions.raise_start(-1)
        self._positions.raise_stop(-1)

    def single_down(self, max_len: int) -> None:
        """Move a cursor with length 1 down by 1"""
        if len(self._positions) == max_len:
            self.set_to(self.get_first())
        if self.get_last() >= max_len - 1:
            return
        self.set_to(self.get_last() + 1)

    def slide_down(self, max_len: int) -> None:
        """Shift each value in the cursor down by 1"""
        if self.get_last() >= max_len - 1:
            return
        self._positions.raise_start(1)
        self._positions.raise_stop(1)

    def to_top(self) -> None:
        """Move the cursor to the top"""
        self.set_to(0)

    def to_bottom(self, len_list: int) -> None:
        """Move the cursor to the bottom"""
        self.set_to(len_list - 1)

    def _select_next(self) -> None:
        """Extend the cursor down by 1"""
        self._positions.raise_stop(1)

    def _deselect_next(self) -> None:
        """Retract the cursor by 1"""
        if len(self._positions) > 1:
            self._positions.raise_stop(-1)

    def _deselect_prev(self) -> None:
        """Remove the first position of the cursor"""
        if len(self._positions) > 1:
            self._positions.raise_start(1)

    def _select_prev(self) -> None:
        """Extend the cursor up by 1"""
        self._positions.raise_start(-1)

    def get_deletable(self) -> list[int]:
        """
        Return a list with the same length as the
        current internal `positions` with each value
        set to the minimum position of the current
        Cursor
        """
        return [self.get_first() for _ in self._positions.as_range()]

    def multiselect_down(self, max_len: int) -> None:
        """Extend the cursor down by 1"""
        if self.get_last() >= max_len - 1:
            return
        if len(self._positions) == 1 or self._direction == _Direction.DOWN:
            self._select_next()
            self._direction = _Direction.DOWN
            return
        self._deselect_prev()

    def multiselect_up(self) -> None:
        """Extend the cursor up by 1"""
        if self.get_first() == 0 and self._direction == _Direction.UP:
            return
        if len(self._positions) == 1 or self._direction == _Direction.UP:
            self._select_prev()
            self._direction = _Direction.UP
            return
        self._deselect_next()

    def multiselect_top(self) -> None:
        """
        Select every position between 0 and
        the current top of the selection
        """
        for _ in range(self.get_first(), 0, -1):
            self.multiselect_up()

    def multiselect_bottom(self, max_len: int) -> None:
        """
        Select every position between the
        current bottom of the selection and
        the `max_len` of the list
        """
        for _ in range(self.get_last() - 1, max_len):
            self.multiselect_down(max_len)

    def _multiselect_to(self, position: int, max_len: int) -> None:
        """Select from current position up or down `position`"""
        direction = -1 if position < self.get_first() else 1
        for _ in range(self.get_first(), position, direction):
            if direction == 1:
                self.multiselect_down(max_len)
                continue
            self.multiselect_up()

    def _set_to_clamp(self, position: int, max_len: int) -> None:
        """Set the current position to the given position if between 0 and maxlen"""
        self.set_to(clamp(position, 0, max_len))

    def relative_to(
        self,
        stdscr: curses.window,
        first_digit: int,
        max_len: int,
        single: bool,
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
            except KeyboardInterrupt:
                return
            operation = self._set_to_clamp
            if not single:
                operation = self._multiselect_to
                if key != Key.escape:  # not an escape sequence
                    return
                stdscr.nodelay(True)
                key = stdscr.getch()  # alt + ...
                stdscr.nodelay(False)
            if key == Key.k:
                operation(self.get_first() - int(total), max_len)
            elif key == Key.j:
                operation(self.get_first() + int(total), max_len)
            elif key in (Key.g, Key.G):
                operation(int(total) - 1, max_len)
            elif key in Key.digits():
                total += str(Key.normalize_ascii_digit_to_digit(key))
                continue
            return

    def multiselect_all(self, max_len: int) -> None:
        """Set internal positions to entirity of list"""
        self._positions = Positions(0, max_len)
