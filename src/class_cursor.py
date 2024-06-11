"""
Helpers for storing a cursor, or a position in a list.

Especially helpful for storing a cursor which might span
multiple consecutive positions.
"""

from enum import Enum

# from functools import wraps
# from typing import Any, Callable, Iterable, TypeVar
from typing import Iterable, TypeVar

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

    def __init__(self, position: int, todos: Todos) -> None:
        self._positions: Positions = Positions([position])
        self._direction: _Direction = _Direction.NONE
        # self._todos: Todos = todos
        _ = todos

    def __len__(self) -> int:
        return len(self._positions)

    def __str__(self) -> str:
        return str(self._positions[0])

    def __repr__(self) -> str:
        return " ".join(map(str, self._positions))

    def __int__(self) -> int:
        return self._positions[0]

    def __contains__(self, child: int) -> bool:
        return child in self._positions

    def get(self) -> Positions:
        """Return a `Positions` object holding the current cursor"""
        return self._positions

    def get_first(self) -> int:
        """Return the top-most selected position"""
        return self._positions[0]

    def get_last(self) -> int:
        """Return the bottom-most selected position"""
        return self._positions[-1]

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
        self._positions = Positions([position])

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
        if min(self._positions) == 0:
            return
        self.set_to(min(self._positions) - 1)
        # while self.todos[self.get_first()].is_folded():
        #     self.multiselect_up()

    def slide_up(self) -> None:
        """Shift each value in the cursor up by 1"""
        if min(self._positions) == 0:
            return
        self._positions.insert(0, min(self._positions) - 1)
        self._positions.pop()

    def single_down(self, max_len: int) -> None:
        """Move a cursor with length 1 down by 1"""
        if len(self._positions) == max_len:
            self.set_to(min(self._positions))
        if max(self._positions) >= max_len - 1:
            return
        self.set_to(max(self._positions) + 1)

    def slide_down(self, max_len: int) -> None:
        """Shift each value in the cursor down by 1"""
        if max(self._positions) >= max_len - 1:
            return
        self._positions.append(max(self._positions) + 1)
        self._positions.pop(0)

    def to_top(self) -> None:
        """Move the cursor to the top"""
        self.set_to(0)

    def to_bottom(self, len_list: int) -> None:
        """Move the cursor to the bottom"""
        self.set_to(len_list - 1)

    def _select_next(self) -> None:
        """Extend the cursor down by 1"""
        self._positions.append(max(self._positions) + 1)

    def _deselect_next(self) -> None:
        """Retract the cursor by 1"""
        if len(self._positions) > 1:
            self._positions.remove(max(self._positions))

    def _deselect_prev(self) -> None:
        """Remove the first position of the cursor"""
        if len(self._positions) > 1:
            self._positions.remove(min(self._positions))

    def _select_prev(self) -> None:
        """Extend the cursor up by 1"""
        self._positions.insert(0, min(self._positions) - 1)

    def get_deletable(self) -> Positions:
        """
        Return a Positions object with each value
        set to the minimum position of the current
        Cursor
        """
        return Positions([min(self._positions) for _ in self._positions])

    def multiselect_down(self, max_len: int) -> None:
        """Extend the cursor down by 1"""
        if max(self._positions) >= max_len - 1:
            return
        if len(self._positions) == 1 or self._direction == _Direction.DOWN:
            self._select_next()
            self._direction = _Direction.DOWN
            return
        self._deselect_prev()

    def multiselect_up(self) -> None:
        """Extend the cursor up by 1"""
        if min(self._positions) == 0 and self._direction == _Direction.UP:
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
        for _ in range(self._positions[0], 0, -1):
            self.multiselect_up()

    def multiselect_bottom(self, max_len: int) -> None:
        """
        Select every position between the
        current top of the selection and
        the `max_len` of the list
        """
        for _ in range(self._positions[0], max_len):
            self.multiselect_down(max_len)

    def _multiselect_to(self, position: int, max_len: int) -> None:
        """Select from current position up or down `position`"""
        direction = -1 if position < self._positions[0] else 1
        for _ in range(self._positions[0], position, direction):
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
            except Key.ctrl_c:
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
                operation(self._positions[0] - int(total), max_len)
            elif key == Key.j:
                operation(self._positions[0] + int(total), max_len)
            elif key in (Key.g, Key.G):
                operation(int(total) - 1, max_len)
            elif key in Key.digits():
                total += str(Key.normalize_ascii_digit_to_digit(key))
                continue
            return

    def multiselect_all(self, max_len: int) -> None:
        """Set internal positions to entirity of list"""
        self._positions = Positions(range(0, max_len))
