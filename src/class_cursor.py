# pylint: disable=missing-docstring

from enum import Enum
from typing import Any, Iterable

from src.class_todo import Todos, TodoList
from src.keys import Key


class Direction(Enum):
    UP = 0
    DOWN = 1
    NONE = 2


class Positions(list[int]):
    def __init__(self, iterable: Iterable[int]):
        super().__init__(iterable)


class Cursor:
    def __init__(self, position: int, *positions: int) -> None:
        self.positions: Positions = Positions([position, *positions])
        self.direction: Direction = Direction.NONE

    def __len__(self) -> int:
        return len(self.positions)

    def __str__(self) -> str:
        return str(self.positions[0])

    def __int__(self) -> int:
        return self.positions[0]

    def __contains__(self, child: int) -> bool:
        return child in self.positions

    def get(self) -> Positions:
        return self.positions

    def get_first(self) -> int:
        return self.positions[0]

    def get_last(self) -> int:
        return self.positions[-1]

    def set_to(self, position: int) -> None:
        self.positions = Positions([position])

    def todo_set_to(self, todo_position: TodoList) -> Todos:
        self.positions[0] = todo_position[1]
        return todo_position[0]

    def todos_override(self, todos: Todos, positions: Positions) -> Todos:
        self.positions = positions
        return todos

    def slide_up(self) -> None:
        if min(self.positions) == 0:
            return
        self.positions.insert(0, min(self.positions) - 1)
        self.positions.pop()

    def slide_down(self, max_len: int) -> None:
        if max(self.positions) >= max_len - 1:
            return
        self.positions.append(max(self.positions) + 1)
        self.positions.pop(0)

    def select_next(self) -> None:
        self.positions.append(max(self.positions) + 1)
        self.positions.sort()

    def deselect_next(self) -> None:
        if len(self.positions) > 1:
            self.positions.remove(max(self.positions))

    def deselect_prev(self) -> None:
        if len(self.positions) > 1:
            self.positions.remove(min(self.positions))

    def select_prev(self) -> None:
        self.positions.append(min(self.positions) - 1)
        self.positions.sort()

    def get_deletable(self) -> Positions:
        return Positions([min(self.positions) for _ in self.positions])

    def multiselect_down(self, max_len: int) -> None:
        if max(self.positions) >= max_len - 1:
            return
        if len(self.positions) == 1 or self.direction == Direction.DOWN:
            self.select_next()
            self.direction = Direction.DOWN
            return
        self.deselect_prev()

    def multiselect_up(self) -> None:
        if min(self.positions) == 0 and self.direction == Direction.UP:
            return
        if len(self.positions) == 1 or self.direction == Direction.UP:
            self.select_prev()
            self.direction = Direction.UP
            return
        self.deselect_next()

    def multiselect_top(self) -> None:
        for _ in range(self.positions[0], 0, -1):
            self.multiselect_up()

    def multiselect_bottom(self, max_len: int) -> None:
        for _ in range(self.positions[0], max_len):
            self.multiselect_down(max_len)

    def multiselect_to(self, position: int, max_len: int) -> None:
        direction = -1 if position < self.positions[0] else 1
        for _ in range(self.positions[0], position, direction):
            if direction == 1:
                self.multiselect_down(max_len)
                continue
            self.multiselect_up()

    def multiselect_from(self, stdscr: Any, first_digit: int, max_len: int) -> None:
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
                self.multiselect_to(self.positions[0] - int(total), max_len)
            elif subch == Key.j:
                self.multiselect_to(self.positions[0] + int(total), max_len)
            elif subch in Key.digits():
                total += str(Key.normalize_ascii_digit_to_digit(subch))
                continue
            return

    def multiselect_all(self, max_len: int) -> None:
        self.positions = Positions(range(0, max_len))
