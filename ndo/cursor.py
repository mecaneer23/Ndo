"""
Helpers for storing a cursor, or a position in a list.

Especially helpful for storing a cursor which might span
multiple consecutive positions.
"""
# ruff: noqa: ERA001

from collections.abc import Iterator
from enum import Enum

# from functools import wraps
# from typing import Any, Callable, Iterable, TypeVar
from typing import TypeVar

from ndo.keys import Key
from ndo.todo import Todos
from ndo.ui_protocol import CursesWindow
from ndo.utils import clamp

T = TypeVar("T")


class _Direction(Enum):
    UP = 0
    DOWN = 1
    NONE = 2


class Cursor:
    """Store potentially multiple consectutive position(s)"""

    def __init__(self, start: int, todos: Todos) -> None:
        self._start = start
        self._stop = start + 1
        self._direction: _Direction = _Direction.NONE
        # self._todos: Todos = todos
        _ = todos

    def __len__(self) -> int:
        return self._stop - self._start

    def __str__(self) -> str:
        return str(self.get_first())

    def __repr__(self) -> str:
        return " ".join(map(str, self.get()))

    def __int__(self) -> int:
        return self.get_first()

    def __contains__(self, child: int) -> bool:
        return self._start <= child < self._stop

    def __iter__(self) -> Iterator[int]:
        return iter(self.get())

    def get(self) -> range:
        """Return a iterable object holding the current cursor"""
        return range(self._start, self._stop)

    def get_first(self) -> int:
        """Return the top-most selected position"""
        return self._start

    def get_last(self) -> int:
        """Return the bottom-most selected position"""
        return self._stop - 1

    def _raise_start(self, amount: int) -> None:
        """Raise start by `amount`"""
        self._start += amount

    def _raise_stop(self, amount: int) -> None:
        """Raise stop by `amount`"""
        self._stop += amount

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
            # def _inner(self: "Cursor", *args: list[Any], **kwargs: dict[Any, Any]) -> T:
    #             for pos in self:
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

    def set(self, start: int, stop: int = -1) -> None:
        """
        Setter for Cursor

        - `start` must be non-negative.

        - If `stop` is omitted or negative, set a single-position cursor at
        `start`.

        - If `stop` is provided and non-negative, set the range from
        `start` to `stop`.
        """
        self._start = max(start, 0)
        self._stop = start + 1 if stop < 0 else stop

    def single_up(self, max_len: int) -> None:
        """Move a cursor with length 1 up by 1"""
        if len(self) == max_len or self.get_first() == 0:
            self.set(0)
            return
        self.set(self.get_first() - 1)
        # while self.todos[self.get_first()].is_folded():
        #     self.multiselect_up()

    def slide_up(self) -> None:
        """Shift each value in the cursor up by 1"""
        if self.get_first() == 0:
            return
        self._raise_start(-1)
        self._raise_stop(-1)

    def single_down(self, max_len: int) -> None:
        """Move a cursor with length 1 down by 1"""
        if len(self) == max_len:
            self.set(self.get_last())
            return
        if self.get_last() >= max_len - 1:
            self.set(self.get_last())
            return
        self.set(self.get_last() + 1)

    def slide_down(self, max_len: int) -> None:
        """Shift each value in the cursor down by 1"""
        if self.get_last() >= max_len - 1:
            return
        self._raise_start(1)
        self._raise_stop(1)

    def to_top(self) -> None:
        """Move the cursor to the top"""
        self.set(0)

    def to_bottom(self, len_list: int) -> None:
        """Move the cursor to the bottom"""
        self.set(len_list - 1)

    def get_deletable(self) -> list[int]:
        """
        Return a list with the same length as the
        current internal `positions` with each value
        set to the minimum position of the current
        Cursor
        """
        return [self.get_first() for _ in self.get()]

    def multiselect_down(self, max_len: int) -> None:
        """Extend the cursor down by 1"""
        if self.get_last() >= max_len - 1:
            return
        if len(self) == 1 or self._direction == _Direction.DOWN:
            self._raise_stop(1)
            self._direction = _Direction.DOWN
            return
        if len(self) > 1:
            self._raise_start(1)

    def multiselect_up(self) -> None:
        """Extend the cursor up by 1"""
        if self.get_first() == 0 and self._direction == _Direction.UP:
            return
        if len(self) == 1 or self._direction == _Direction.UP:
            self._raise_start(-1)
            self._direction = _Direction.UP
            return
        if len(self) > 1:
            self._raise_stop(-1)

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
        """
        Set the current position to the given position if between 0 and maxlen
        """
        self.set(clamp(position, 0, max_len))

    def relative_to(
        self,
        stdscr: CursesWindow,
        first_digit: int,
        max_len: int,
        single: bool,  # noqa: FBT001
    ) -> None:
        """
        Move the cursor to the specified position relative to the current
        position.

        Because the trigger can only be a single keypress, this function also
        uses a window object to getch until the user presses g or shift + g.
        This allows for relative movement greater than 9 lines away.
        """
        total = str(first_digit)
        while True:
            try:
                key = Key(stdscr.getch())
            except KeyboardInterrupt:
                return
            operation = self._set_to_clamp
            if not single:
                operation = self._multiselect_to
                if key != Key.escape:  # not an escape sequence
                    return
                stdscr.nodelay(True)  # noqa: FBT003
                key = Key(stdscr.getch())  # alt + ...
                stdscr.nodelay(False)  # noqa: FBT003
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
        self._start = 0
        self._stop = max_len
