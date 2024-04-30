"""
Helpers for storing and retrieving TodoList object records.
"""

from typing import NamedTuple

from src.class_cursor import Cursor, Positions
from src.class_todo import Todo, Todos


class TodoList(NamedTuple):
    """
    An object representing the todos
    and a cursor (Positions) within the list
    """

    todos: Todos
    cursor: Positions


class _Restorable:
    """
    Back up and save a TodoList object, one snippet in time.
    """

    SEPARATOR = " |SEP|"

    def __init__(self, todos: Todos, selected: Cursor) -> None:
        self.stored: str = self.SEPARATOR.join([repr(todo) for todo in todos])
        self.first: int = selected.get_first()
        self.last: int = selected.get_last()

    def get(self) -> TodoList:
        """
        Convert stored TodoList object out of internal format.

        Return the stored TodoList object.
        """

        return TodoList(
            Todos([Todo(line) for line in self.stored.split(self.SEPARATOR)]),
            Positions(range(self.first, self.last + 1)),
        )

    def __repr__(self) -> str:
        return (
            self.stored.replace(self.SEPARATOR, ", ") + f": {self.first}..{self.last}"
        )


class UndoRedo:
    """
    Store and retrieve TodoList objects.
    """

    def __init__(self) -> None:
        self._history: list[_Restorable] = []
        self._index: int = -1

    def add(self, todos: Todos, selected: Cursor) -> None:
        """
        Add a TodoList to the history.
        Backs up current state for potential retrieval later.
        """

        self._history.append(_Restorable(todos, selected))
        self._index = len(self._history) - 1

    def undo(self) -> TodoList:
        """
        Return the previous TodoList state.
        """
        if self._index > 0:
            self._index -= 1
        return self._history[self._index].get()

    def redo(self) -> TodoList:
        """
        Return the next TodoList state, if it exists
        """
        if self._index < len(self._history) - 1:
            self._index += 1
        return self._history[self._index].get()

    def __repr__(self) -> str:
        return (
            "\n".join(
                f"{'>' if i == self._index else ' '}  {v}"
                for i, v in enumerate(self._history)
            )
            + f"\nlength: ({len(self._history)})\nindex: ({self._index})"
        )
