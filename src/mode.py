"""
Helpers to handle switching mode between one line
at a time and multiple lines at a time.
"""

from enum import Enum

from src.utils import NewTodoPosition


class SingleLineMode(Enum):
    """
    Enum for mode

    OFF:
        multiple line mode

    ON:
        the default - one line at a time

    NONE:
        non-nullable None type

    ONLY_ONCE:
        represent a state which turns SingleLineMode off for just one line

    """

    OFF = 0
    ON = 1
    NONE = 2
    ONLY_ONCE = 3


class SingleLineModeImpl:
    """Implementation and helper methods for SingleLineMode"""

    def __init__(self, mode: "SingleLineMode") -> None:
        self._mode: SingleLineMode = mode
        self._extra_data: str = ""
        self._offset: NewTodoPosition = NewTodoPosition.NEXT

    def toggle(self) -> None:
        """Toggle between ON and OFF"""
        if self._mode == SingleLineMode.ON:
            self._mode = SingleLineMode.OFF
        elif self._mode == SingleLineMode.OFF:
            self._mode = SingleLineMode.ON

    def is_off(self) -> bool:
        """Return if mode is OFF"""
        return self._mode == SingleLineMode.OFF

    def is_once(self) -> bool:
        """Return if mode is ONLY_ONCE"""
        return self._mode == SingleLineMode.ONLY_ONCE

    def set_on(self) -> None:
        """Set mode to ON"""
        self._mode = SingleLineMode.ON

    def set_once(self, new_todo_position: NewTodoPosition) -> None:
        """Set mode to ONLY_ONCE"""
        self._mode = SingleLineMode.ONLY_ONCE
        self._offset = new_todo_position

    def get_offset(self) -> NewTodoPosition:
        """Return offset, set in call to set_once"""
        return self._offset

    def get_extra_data(self) -> str:
        """
        Return extra data, which is any string

        `extra_data` allows for linking important
        information to the Mode object - likely
        used for ONLY_ONCE
        """
        return self._extra_data

    def set_extra_data(self, extra_data: str) -> None:
        """
        Set extra data, which is any string

        `extra_data` allows for linking important
        information to the Mode object - likely
        used for ONLY_ONCE
        """
        self._extra_data = extra_data

    def __repr__(self) -> str:
        return f"{self._mode} {self._extra_data}"
