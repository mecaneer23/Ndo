# pylint: disable=global-statement, missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

from typing import Any

from src.class_todo import Todo


class Cursor:
    def __init__(self, position: int, *positions: int) -> None:
        self.positions: list[int] = [position, *positions]
        self.direction: str | None = None

    def __len__(self) -> int:
        return len(self.positions)

    def __str__(self) -> str:
        return str(self.positions[0])

    def __int__(self) -> int:
        return self.positions[0]

    def __contains__(self, child: int) -> bool:
        return child in self.positions

    def set_to(self, position: int) -> None:
        self.positions = [position]

    def todo_set_to(self, todo_position: tuple[list[Todo], int]) -> list[Todo]:
        self.positions[0] = todo_position[1]
        return todo_position[0]

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

    def get_deletable(self) -> list[int]:
        return [min(self.positions) for _ in self.positions]

    def multiselect_down(self, max_len: int) -> None:
        if max(self.positions) >= max_len - 1:
            return
        if len(self.positions) == 1 or self.direction == "down":
            self.select_next()
            self.direction = "down"
            return
        self.deselect_prev()

    def multiselect_up(self) -> None:
        if min(self.positions) == 0 and self.direction == "up":
            return
        if len(self.positions) == 1 or self.direction == "up":
            self.select_prev()
            self.direction = "up"
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
            if key != 27:  # not an escape sequence
                return
            stdscr.nodelay(True)
            subch = stdscr.getch()  # alt + ...
            stdscr.nodelay(False)
            if subch == 107:  # k
                self.multiselect_to(self.positions[0] - int(total), max_len)
            elif subch == 106:  # j
                self.multiselect_to(self.positions[0] + int(total), max_len)
            elif subch in range(48, 58):  # digits
                total += str(subch - 48)
                continue
            return
