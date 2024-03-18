"""
Helpers for storing and retrieving TodoList object records.
"""

from src.class_todo import Todo, Todos, TodoList


class _Restorable:
    """
    Back up and save a TodoList object, one snippet in time.
    """

    SEPARATOR = " |SEP|"

    def __init__(self, todos: Todos, selected: int) -> None:
        self.stored: str = self.SEPARATOR.join([repr(todo) for todo in todos])
        self.selected: int = selected

    def get(self) -> TodoList:
        """
        Convert stored TodoList object out of internal format.

        Return the stored TodoList object.
        """

        stored = self.stored.split(self.SEPARATOR)
        return TodoList(Todos([Todo(line) for line in stored]), self.selected)

    def __repr__(self) -> str:
        return self.stored.replace(self.SEPARATOR, ", ") + f": {self.selected}"


class UndoRedo:
    """
    Store and retrieve TodoList objects.
    """

    def __init__(self) -> None:
        self.history: list[_Restorable] = []
        self.index: int = -1

    def add(self, todos: Todos, selected: int) -> None:
        """
        Add a TodoList to the history.
        Backs up current state for potential retrieval later.
        """

        self.history.append(_Restorable(todos, selected))
        self.index = len(self.history) - 1

    def undo(self) -> TodoList:
        """
        Return the previous TodoList state.
        """
        if self.index > 0:
            self.index -= 1
        return self.history[self.index].get()

    def redo(self) -> TodoList:
        """
        Return the next TodoList state, if it exists
        """
        if self.index < len(self.history) - 1:
            self.index += 1
        return self.history[self.index].get()

    def __repr__(self) -> str:
        return (
            "\n".join(
                f"{'>' if i == self.index else ' '}  {v}"
                for i, v in enumerate(self.history)
            )
            + f"\nlength: ({len(self.history)})\nindex: ({self.index})"
        )
